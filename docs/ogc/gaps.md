# Test-suite gaps: OGC abstract tests vs existing validators

**Status: PROPOSAL.** For every abstract test in the OGC document (`ogc/abstract_tests/`), this
table says which existing tool implements it and what is missing. The review criterion set by the
GeoParquet maintainers is that the OGC assertions line up with the tool the community actually
runs for 2.0, `geoparquet-io` (`gpio`), so that tool is the first column. Each abstract test in the
document also carries a NOTE naming the implementing `gpio` check.

Tools audited:

* **gpio** — `geoparquet-io` main at `4ebaa9a` (2026-09-04): `gpio validate` (spec checks, about 44
  named checks, data checks on a 1000-row sample by default) and `gpio check spatial|row-group|compression|bbox|optimization`
  (best-practice checks). Check names below are the `name` field of `gpio validate --format json`,
  with the per-column suffix written `_*`.
* **GPQ** — `gpq validate` (planetlabs/gpq main, 2026-08-30). 1.0-era rule set.
* **GDAL** — `validate_geoparquet.py` (OSGeo/gdal master, 2026-08-14). `--check-data` needed for data rules.
* **Schema** — `format-specs/schema.json` 2.0.0 applied to the `geo` value (GDAL does this; gpio and GPQ do not).
* **Corpus** — `geoparquet/geoparquet-testing` `bad_data/` negative fixtures.

Coverage: **full** = a tool checks the whole statement for 2.0 files; **partial** = part of it, or
with a known defect; **none** = no tool checks it (heuristic-only tests are marked as such).

## Conformance Class Core (`/conf/core/...`)

| Test | gpio validate | GPQ / GDAL / Schema | Corpus | Coverage | What is missing |
| --- | --- | --- | --- | --- | --- |
| geo-metadata | `geo_key_exists`, `metadata_is_json_object`, `geo_metadata_parse` | GPQ 2 rules; GDAL + schema | `missing-geo-metadata`, `geo-invalid-json`, `geo-invalid-utf8` | full | Step 3 (schema validation) only in GDAL. |
| file-metadata | `version_present`, `version_known` (any `1.x`/`2.x`), `version_features_match`, `primary_column_present`, `columns_present`, `primary_column_in_columns` | GPQ; GDAL + schema (`const "2.0.0"`, `minLength`, `minProperties`) | `missing-version`, `version-unknown`, `missing-primary-column`, `missing-columns`, `primary-column-not-in-columns` | full | Exact `2.0.0` value and at least one column only via schema. |
| column-metadata | `encoding_valid_*`, `geometry_types_list_*` per listed column; reverse direction (`geometry_not_grouped_*` fails on a missing column) | GPQ, GDAL reverse direction | — | **partial** | Step 2, a `GEOMETRY`/`GEOGRAPHY` column absent from `columns`, is detected by nobody (gpio iterates the listed columns only; its `version_features_match` looks at native columns for 1.x files only). Needs a fixture. |
| geometry-column-type | `geometry_byte_array_*`, `native_geo_type_present_*`, `v2_native_types_*`, `encoding_valid_*` (accepts `wkb` lower-case too) | GPQ BYTE_ARRAY; schema `const WKB` | — | full | Negative fixture (2.0 metadata on plain BYTE_ARRAY) missing. |
| geometry-column-nesting | `geometry_not_grouped_*` | GPQ | — | full | GDAL none. |
| geometry-column-repetition | `geometry_not_repeated_*` | GPQ | — | full | GDAL none. |
| wkb | `encoding_matches_data_*` (DuckDB decode, sample) | GPQ; GDAL (accepts EWKB) | `wkb-truncated`, `wkb-wrong-type-byte`, `wkb-with-srid-prefix` | partial | Sampled; none checks the ISO variant strictly. |
| axis-order | `coordinates_valid_for_crs_*`, `geography_coordinate_bounds_*` (heuristics) | GDAL range heuristic | `crs-mismatch-schema-vs-geo-metadata` | heuristic | Inherently heuristic. |
| geometry-types | `geometry_types_list_*` (vocabulary incl. ` Z`/` M`/` ZM`; no uniqueness), `geometry_types_match_data_*` (with dimension suffix) | GPQ (no M/ZM; Z not verified); GDAL (Point Z bug); schema `uniqueItems` | `geometry-types-*`, `zm-declared-*` | **partial** | Step 4 (`geometry_types` vs Parquet `geospatial_types`) by nobody: gpio `native_geo_types_match_*` compares statistics with data, not with the metadata. Uniqueness only via schema. |
| crs-projjson | `crs_valid_*` (PROJJSON `type` member present and known) | GPQ (PROJJSON schema); GDAL (schema + PROJ parse) | `crs-invalid-projjson` | full (GDAL/GPQ) | gpio does not validate against the PROJJSON schema. |
| crs-default | `coordinates_valid_for_crs_*`, `v2_crs_consistency_*` (absent vs unset) | GDAL heuristic | `data/crs/crs-default` (positive) | heuristic | Inherently heuristic. |
| crs-consistency | `v2_crs_consistency_*` (semantic, via pyproj; a bare `<authority>:<code>` Parquet `crs` is read as unset, geoparquet-io #814) | GDAL form-level only | none | **partial** | Authority-code combination unverified; fixtures missing (PROJJSON vs different `EPSG:` code; `null` vs defined). |
| epoch | `epoch_valid_*` (number; warns on static CRS, fails on datum ensemble) | schema `type number`; GPQ | `epoch-on-unsupported-crs` (not a spec violation, SI-19) | full | gpio is stricter than the spec (SI-19). |
| orientation-value | `orientation_valid_*` | GPQ; schema `const` | — | full | — |
| orientation-rings | `orientation_matches_data_*` **not implemented** (always skipped) | GDAL `--check-data` (Polygon, MultiPolygon, GeometryCollection); GPQ Polygon only | `orientation-ccw-declared-rings-cw` | full (GDAL) | gpio gap; no MultiPolygon fixture. |
| edges-value | `edges_valid_*` (2.0 vocabulary) | schema `enum`; GPQ planar/spherical only | `data/edges/*` (positive) | full | — |
| bbox-array | `bbox_valid_*` (**4 or 6 only**) | GPQ 4/6 only; GDAL **crashes on 8**; schema 4/6/8 | `data/bbox/*` (positive) | **partial** | No tool accepts the 8-element form correctly; antimeridian ordering (step 2) unchecked. |
| bbox-extent | `bbox_contains_data_*` (sample; uses the first four elements, wrong for a 6-element bbox; no antimeridian) | GPQ (X/Y, antimeridian aware) | `bbox-does-not-contain-geometry` | partial | Z/M ranges unchecked. |
| bbox-crs | `coordinates_valid_for_crs_*` (heuristic) | GDAL heuristic | — | heuristic | Inherently heuristic. |
| media-type | — (`file_extension` is a warning for `/rec/core/file-extension`) | — | — | **none** | Not testable on the file alone. |

## Conformance Class Bounding Box Covering (`/conf/covering/...`)

| Test | gpio validate | GPQ / GDAL / Schema | Corpus | Coverage | What is missing |
| --- | --- | --- | --- | --- | --- |
| keys | `covering_is_object_*` | schema `required [bbox]` (unknown keys pass, SI-13) | — | partial | Unknown keys and a missing `bbox` member detected by nobody (gpio runs the bbox checks only `if "bbox" in covering`). |
| bbox-paths | `covering_bbox_paths_*` (members present, two-element arrays), `covering_bbox_column_exists_*` | schema (shapes, `const` second element) | — | **partial** | Second element equals member name (only schema); same column in all four arrays (nobody). |
| bbox-column-structure | `covering_bbox_structure_*` (at least 4 children named xmin/ymin/xmax/ymax) | — | — | partial | Field order and `zmin`/`zmax` pairing unchecked. |
| bbox-column-type | `covering_bbox_field_types_*` (first four children FLOAT/DOUBLE, same type) | — | — | partial | `zmin`/`zmax` types unchecked. |
| bbox-column-repetition | — | — | — | **none** | Fixtures: `required` bbox on `optional` geometry; bbox present where geometry is null. |
| bbox-column-nesting | `covering_bbox_column_exists_*` (name lookup) | — | — | partial | A nested field with the same name would pass. |

## Conformance Class Cloud-Optimized Distribution (`/conf/distribution/...`, proposal)

Sources for this class are the Portolan specification's GeoParquet rules and the community guide;
the tools are `gpio check` and Portolan's own validator (portolan-sdi/rashid).

| Test | gpio | Portolan validator (rashid) | Coverage | Notes |
| --- | --- | --- | --- | --- |
| geospatial-statistics | `gpio validate` `native_geo_stats_*`; `gpio check optimization` factor 2 | yes (per-row-group statistics rule) | full | Skipped by gpio for remote files. |
| spatial-order | `gpio check spatial` / `check optimization` factor 3; metric moving from consecutive-pair overlap to relative skip rate (PR #774) | yes; metric being changed the same way (portolan-spec PR #188, rashid PR #174) | full, metric in flux | The OGC requirement carries no number; the threshold is the tools'. |

Recommendations (`/rec/distribution/*`) have no abstract tests. The tools still check three of them:
rashid enforces the 150 000-row maximum and `gpio check row-group` reports advisory bands;
`gpio check bbox` fails an undeclared bbox column; `gpio check compression` and `check optimization`
factor 5 report the codec. A file can therefore fail rashid or gpio and still conform to this
class; that is intended (Portolan is the stricter, evolving layer).

## gpio checks that are not requirements of the OGC document

For the maintainers' review criterion in the other direction: what `gpio validate` fails or warns on
that the community specification (and therefore the OGC text) does not require.

| gpio check | What it enforces | Status in the spec / OGC text |
| --- | --- | --- |
| `v2_crs_in_parquet_type_*` | Non-default CRS must be **inline PROJJSON** in the Parquet `crs` parameter | The spec allows `<authority>:<code>` too (L84–L87, `/rec/core/parquet-crs-form`). gpio is stricter; worth a discussion. |
| `v2_edges_consistency_*` | `edges` must equal the GEOGRAPHY `algorithm`; a GEOGRAPHY column with no `edges` fails (default planar vs spherical); non-planar `edges` on GEOMETRY fails | Not in the spec (SI-12). gpio's behaviour is a good candidate wording for the fix. |
| `epoch_valid_*` | `epoch` on a datum ensemble fails; on a static CRS warns | Not in the spec (SI-19). |
| `version_known`, `version_features_match` | Version string is `1.x`/`2.x`; 1.x files must not use `covering` (pre-1.1) or native types | Version compatibility is informative (Clause 9). |
| `native_geo_stats_*`, `native_geo_stats_contains_data_*` | Geospatial statistics present and containing the data | Best practice; now `/req/distribution/geospatial-statistics` in the proposed profile. |
| `native_geo_types_match_*`, `geography_coordinate_bounds_*`, `native_crs_format_*` | Parquet-level rules (statistics vs data, GEOGRAPHY bounds, `crs` string form) | Parquet's rules, referenced normatively, not restated. |
| `coordinates_valid_for_crs_*` | Coordinates within the CRS area of use | Heuristic; used as the axis-order / default-CRS test method. |
| `file_extension` (warning) | `.parquet` extension | `/rec/core/file-extension`. |

## Summary

| | Core (20 tests) | Covering (6 tests) | Distribution (4 tests, proposal) |
| --- | --- | --- | --- |
| full | 10 | 0 | 4 |
| partial | 6 | 5 | 0 |
| none / heuristic only | 4 | 1 | 0 |

Compared with the GPQ/GDAL-only picture, gpio closes the logical-type check, the CRS consistency
check (except the authority-code form), most of the covering structure and, through `gpio check` and
Portolan's validator, the whole proposed distribution class.

## Suggested next steps for the test suite (outside this repository)

1. `geoparquet-io`: implement `orientation_matches_data`; accept the 8-element `bbox` and read a
   6-element bbox correctly in `bbox_contains_data`; resolve `<authority>:<code>` in
   `v2_crs_consistency` (#814); add the unlisted-native-column check (column-metadata step 2) and a
   `geometry_types` vs `geospatial_types` check; enforce the second-element and same-column rules of
   `covering.bbox` paths. With those, `gpio validate` would implement every Core and Covering test
   except the inherently heuristic ones.
2. `geoparquet-testing`: negative fixtures for the rows marked partial or none above.
3. GDAL `validate_geoparquet.py`: fix the 8-element `bbox` assertion and the `Point Z` mapping.
4. A future OGC executable test suite can be a thin wrapper around `gpio validate` and `gpio check`.
