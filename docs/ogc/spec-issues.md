# Inconsistencies found in the community specification while drafting the OGC document

**For the SWG chair. Nothing here has been changed in `format-specs/`.** Source:
`format-specs/geoparquet.md` and `schema.json` at `v2.0.0-rc.1` (`main` at `21eba45` differs only by
PR #301) unless a version is given; PR #302 for the covering text. Line numbers refer to
`geoparquet.md` at that tag. Crosswalk row IDs refer to [`crosswalk.md`](crosswalk.md).

The OGC document restates the community specification and does not resolve any of these on its
own. Where the OGC text needed to choose a reading, the choice is recorded here and in
[`CHANGES.md`](CHANGES.md), and the corresponding statement is a NOTE rather than a requirement.

Severity: **H** = a conforming file can be read two ways or a validator must guess; **M** =
wording that does not carry the obligation everyone enforces; **L** = editorial.

## A. Worth fixing before the 2.0.0 tag (cheap, editorial, affect the released text)

| ID | Sev | Where | Issue | Suggested resolution |
| --- | --- | --- | --- | --- |
| SI-9 | H | L80 | The text says the Parquet "crs customization" section "permits several forms … inline PROJJSON, an `<authority>:<code>` string, `srid:<identifier>`, and `projjson:<key_name>`" and links `apache-parquet-format-2.12.0/Geospatial.md`. That tag lists only `srid:` and `projjson:` under "CRS Customization"; inline PROJJSON and `<authority>:<code>` appear in `Geospatial.md` on parquet-format `master` (unreleased text). A reader following the link finds no basis for the two RECOMMENDED forms. | Link the parquet-format revision that contains the wider list once released, or quote the text GeoParquet relies on. The OGC document pins 2.12.0 and inherits this problem. |
| SI-11 | M | L146 vs L180 (OR-4) | Orientation section: RECOMMENDED counterclockwise "if `edges` is `\"spherical\"`"; edges section: "if `edges` is not `\"planar\"`". The second was updated for the geodesic values, the first was not. | Align both on "not planar" (the OGC draft uses "not planar"). |

Both are one-line edits. Everything else below can wait for a 2.0.x or 2.1 discussion.

## B. After the release

| ID | Sev | Where | Issue | Suggested resolution |
| --- | --- | --- | --- | --- |
| SI-12 | H | L148–L180; Parquet `GEOGRAPHY.algorithm` (ED-2) | Nothing ties `edges` to the logical type: `GEOMETRY` implies planar edges and `GEOGRAPHY` carries an `algorithm` whose Parquet default is `SPHERICAL`, while the GeoParquet default for `edges` is `planar`. A `GEOGRAPHY` column with no `edges` member therefore has spherical edges per Parquet and planar edges per GeoParquet. `crs` and `geometry_types` have explicit "MUST match" rules; `edges` has none. `gpio validate` already enforces the match (`v2_edges_consistency`), and fails a GEOGRAPHY column that omits `edges`. | Add: `edges` MUST be consistent with the logical type (`planar` ⇔ `GEOMETRY`; other values ⇔ `GEOGRAPHY` with the same `algorithm`), and state which default applies when `edges` is absent on a `GEOGRAPHY` column. |
| SI-2 | M | L38–L40 (FM-3) | That `primary_column` must name one of the members of `columns` is only implied (it follows from "each geometry column MUST be included in `columns`"). GPQ, GDAL, `geoparquet-testing` and PR #247 all enforce it. The OGC draft states the derivation in a NOTE, not as a requirement. | Add "The value MUST be one of the keys of `columns`." to the `primary_column` row. |
| SI-4 | M | L40, L46 (CM-1) | "Each key is the name of a geometry column in the table" is descriptive; both validators fail files whose `columns` names a column that does not exist. The OGC draft mentions this in a NOTE only. | Add a MUST for the reverse direction, or state that unknown keys are an error. |
| SI-7 | M | L133 (GT-4) | "It is expected that this field is strictly correct" is the only sentence carrying the most-tested data rule (types present must be listed). Not RFC 2119. The OGC draft writes it as SHALL (see CHANGES.md). | Replace with "If `geometry_types` is not empty, it MUST list the geometry type (with dimension suffix) of every geometry in the column." |
| SI-16 | M | PR #302, bbox covering encoding and Bounding Box Columns | The requirements on a bounding box column cover its schema (group, names, order, type, repetition, nesting) but the statement that its values are the bounding box of the geometry in the same row is descriptive. A column full of zeros would satisfy every MUST. The OGC draft describes the values in prose with a NOTE. | Add a MUST for the values. |
| SI-17 | M | L135 (GT-5) | "These MUST match the corresponding Geospatial Types in the Parquet statistics" is unconditional, but `GeospatialStatistics` are optional in Parquet and are per column chunk, so the sentence is unsatisfiable when statistics are absent and ambiguous when chunks differ. The OGC draft conditions the requirement on statistics being present. | "Where geospatial statistics are present, the types they record MUST be consistent with `geometry_types`." |
| SI-18 | M | L5, L62, L89 vs L32 | The Overview says 2.0 "provides guidance for geospatial tools to implement Parquet Geometry and Geography types" and L62 says "Writing that metadata is itself optional — a writer MAY emit only the native Parquet geospatial types", while L32 says a GeoParquet file MUST include the `geo` key and L89 says such a file "is not conformant GeoParquet 2.0". Reconcilable, but readers of L62 may conclude the metadata is optional in GeoParquet. | State once, in the Overview, that a GeoParquet file is one that carries the `geo` metadata, and that native-only files are readable by GeoParquet readers but are not GeoParquet files. |
| SI-5 | L | L42; `schema.json` (CM-4) | Additional implementation-specific fields are allowed "at this level" (file metadata) only; the schema also allows them inside column metadata objects and `scripts/test_json_schema.py` has a valid case for it. | Say explicitly whether additional members are allowed in column metadata objects. |
| SI-8 | L | `schema.json` L38; L210; GPQ | PROJJSON schema versions drift: `schema.json` references v0.7, the OGC:CRS84 example declares `$schema` v0.5, GPQ defaults to v0.6. | Update the example to v0.7. |
| SI-10 | L | L106 (EP-1) | "To be unambiguous, the coordinates must always be qualified with the epoch" reads as an obligation but is background; PR #224 turned it into a SHALL. | Rephrase ("need to be qualified") or make it a MUST if that is intended. |
| SI-13 | L | PR #302 covering text; `schema.json` | "The keys of the covering object MUST be a supported encoding" but the schema has no `additionalProperties: false` on `covering`, so unknown keys validate. | Add `additionalProperties: false` to `covering`, or drop the MUST. |
| SI-14 | L | `schema.json` `columns.minProperties`, `patternProperties ".+"` | At least one geometry column and non-empty column names exist only in the schema; the prose never says a GeoParquet file has at least one geometry column. | One sentence in the Metadata section. |
| SI-19 | L | L56, L106–L108; corpus `epoch-on-unsupported-crs` | The spec does not forbid `epoch` on a static CRS; the corpus treats it as `epoch_unsupported`. | Decide: either "MUST NOT be present unless `crs` is dynamic", or relabel the fixture as a warning case. |
| SI-20 | L | L112 vs 1.1.0 L94 | 2.0 dropped "(using codes for 3D geometry types in the [1001,1007] range)" without saying that XYM (2001–2007) and XYZM (3001–3007) codes are now allowed; the only trace is the `geometry_types` suffix list. | One sentence in the encoding section pointing to the Parquet WKB integer codes. |
| SI-24 | L | `distributing-geoparquet.md` L21 vs L92 vs L98; Portolan formats.md; `gpio check` | Row-group guidance disagrees with itself: the guide's tl;dr says 50 000–150 000 rows, the body says 50 000–200 000 rows and 128–256 MB, `gpio check row-group` reports 64–256 MB as optimal and `gpio check optimization` scores 10 000–50 000 rows for spatial pushdown. Portolan settled on a maximum of 150 000 rows and no lower bound (Chris Holmes, 2026-09-05: lower bounds still need experimentation); the OGC draft states Portolan's maximum as a recommendation. | Align the guide on "at most 150 000 rows" and drop the numbers there is no consensus on. |
| SI-25 | M | L84–L87 vs `gpio validate` `v2_crs_in_parquet_type` | The spec lets writers use `<authority>:<code>` for the Parquet `crs` parameter and recommends it for writers that cannot produce PROJJSON; `gpio validate` fails a 2.0 file whose non-default CRS is not inline PROJJSON in the Parquet type. Tool and spec disagree on a RECOMMENDED form. | Decide which is right; if `gpio` is, the spec's recommendation should change; if the spec is, `gpio` should downgrade the check to a warning. |
| SI-26 | **resolved** | `geoparquet.md` L238 (PR #302, merged 2026-09-07) | The four child fields of a bounding box column had to be named **and ordered** `xmin`, `ymin`, `xmax`, `ymax`, but every Overture Maps release writes them `xmin, xmax, ymin, ymax`, the 1.1.0 specification's own `examples/example.parquet` writes them `xmax, xmin, ymax, ymin`, and so does Apache Sedona's 1.1 test file; no validator had ever checked the order. The community dropped the order rule for the four-field form (Chris Holmes: "sounds good to just drop, especially since Parquet readers address struct fields by name"); the six-field form keeps it. | Done: `/req/covering/bbox-column-structure` and `/conf/covering/bbox-column-structure` follow the merged text. |
| SI-27 | L | `geoparquet.md` `crs`: "PROJJSON object"; `/conf/core/crs-projjson` step 1 "validate the value against the PROJJSON JSON Schema" | The PROJJSON schema's top-level `oneOf` also accepts datums, ellipsoids, prime meridians and operations, so `{"name": "x", "id": {...}}` validates (as an ellipsoid) and a `crs` without `type` passes both the PROJJSON schema and, through the `$ref`, `schema.json`. | Say "a PROJJSON **CRS** object (the `crs` definition of the PROJJSON schema)" in the spec and in the abstract test; consider `$ref: ...#/definitions/crs` in `schema.json`. |
| SI-28 | L | `/conf/core/geometry-types` step 4 | Step 3 is conditional on `geometry_types` being non-empty (empty = unknown) but step 4 (statistics codes vs the list) is not, so read literally an empty list fails whenever statistics list any type (`data/geometry_types/types-unknown-empty.parquet`). | Begin step 4 with "If `geometry_types` is not empty, ...". |
| SI-29 | L | `/conf/distribution/spatial-order` | The pruning metric is undefined for one row group (ideal skip rate 0) and unstated for an extent that is degenerate in one axis or for row-group boxes that wrap the antimeridian (Parquet allows xmin > xmax). Portolan's draft has a separate "row rule" for fewer than five row groups; the OGC text has nothing. | State what the test does below two row groups (skip, or Portolan's row rule) and that wrapping boxes are split at the antimeridian before measuring. |
| SI-30 | L | `geoparquet.md` L91 (`srid:0` SHOULD) and L95 (`crs` MUST be the resolved PROJJSON "or null when the Parquet crs is srid:0") vs `/req/core/crs-consistency` | L91 only *SHOULD*s `srid:0` for an undefined CRS, but L95's MUST ties a `null` GeoParquet `crs` to a Parquet `crs` of `srid:0`, so a `null` next to an unset Parquet `crs` (= OGC:CRS84) already violates the community text; the OGC consistency requirement is derivable, not stricter. Kept as a note because a reader of L91 alone may think otherwise. | Point L91 at L95 ("when the GeoParquet `crs` is `null`, the Parquet `crs` MUST be `srid:0`"), or leave as is. |
| SI-22 | L | L5 (Overview) | The specification never states that a GeoParquet file is an Apache Parquet file; it is assumed throughout. The OGC draft says so in prose with a NOTE, not as a requirement. | One sentence in the Overview or Metadata section, if the SWG wants an explicit anchor for the Parquet reference. |
| SI-23 | L | L112 | The WKB reference links `portal.ogc.org/files/?artifact_id=18241`, which is OGC 06-103r3 (Simple Feature Access 1.2.0, 2006). Parquet `Geospatial.md`, which GeoParquet 2.0 defers to for the encoding, cites 06-103r4 (1.2.1, artifact 25355). The WKB bytes are identical, but the two documents point at different editions. | Link 06-103r4 / artifact 25355. The OGC draft cites 06-103r4. |
| SI-15 | L | `schema.json` at tag `v2.0.0-rc.1` | `version` is `const "2.0.0"` although the tag is `v2.0.0-rc.1`; GDAL's validator special-cases it. | Harmless once 2.0.0 is tagged; note in the release process. |
| SI-21 | L | README.md | The link to `https://docs.ogc.org/DRAFTS/24-013.html` is dead (issue #277). | Remove, or point at the CI-built artefact. |

## C. GeoParquet 1.x only (errata, no action for 2.0)

| ID | Sev | Where | Issue |
| --- | --- | --- | --- |
| SI-1 | L | 1.1.0 L21 vs L102–L153 | "A geometry MUST NOT be a group field or nested in a group" contradicts the 1.1 native `point` encoding, which is a group. Already removed on `main` by PR #234; the released 1.1.0 text is contradictory. |
| SI-6 | L | 1.1.0 L102–L153 (ENC-8) | The native encodings never say that every value in a `"point"` column is a Point, etc. GDAL enforces it. |

## D. Test corpus (for `geoparquet/geoparquet-testing`)

| ID | Where | Issue |
| --- | --- | --- |
| SI-3 | `bad_data/manifest.json` | `primary-column-not-in-columns` is labelled `expected_failure: schema_validation_error`, but JSON Schema cannot express that constraint (the file validates). Relabel, e.g. `primary_column_mismatch`. |
| SI-31 | `bad_data/epoch-on-unsupported-crs.parquet` | The fixture carries a stub `crs` (`{"type": "GeographicCRS", "id": ...}`, no name, datum or coordinate system) that is not valid PROJJSON, so it fails `/conf/core/geo-metadata` and `/conf/core/crs-projjson` besides the epoch problem it means to test; gpio does not notice because `crs_valid` only checks `type`. Give it the full PROJJSON. |
| SI-32 | `data/` | No fixture has more than one row group, so `/conf/distribution/spatial-order` cannot be exercised by the corpus; a small Hilbert-sorted and a shuffled file with 4-10 row groups would cover it (the Rust checker in geoparquet-testing#6 has both as probes). |

## E. Validator defects noticed (to report to the tool maintainers, not spec issues)

These belong to the geoparquet-io, GPQ and GDAL projects. They are listed so the chair can pass them on; they
are not GeoParquet issues.

| Tool | Defect | Rows |
| --- | --- | --- |
| gpio `validate` | `orientation_matches_data_*` is reported as "ring order validation not implemented" (always skipped). | OR-2 |
| gpio `validate` | `bbox_valid_*` accepts 4 or 6 elements only; the 2.0 8-element `bbox` fails. | BB-2 |
| gpio `validate` | `bbox_contains_data_*` reads `bbox[:4]` as xmin, ymin, xmax, ymax, which is wrong for a 6-element bbox (xmin, ymin, zmin, xmax, …); no antimeridian handling. | BB-3 |
| gpio `validate` | `v2_crs_consistency_*` treats a bare `<authority>:<code>` Parquet `crs` as unset (own issue #814), so a genuine mismatch can pass. | CRS-4 |
| gpio `validate` | `geometry_types_list_*` does not check uniqueness; `crs_valid_*` checks only the PROJJSON `type` member, not the schema; `encoding_valid_*` accepts `wkb` in lower case. | GT-2, CRS-1, CM-2 |
| gpio `validate` | Covering checks do not verify that the second path element equals the member name, that all four paths name the same column, the field order, or the `zmin`/`zmax` pairing. | COV-2, BBC-2, BBC-3 |
| gpio `validate` | No check that a `GEOMETRY`/`GEOGRAPHY` column missing from `columns` is an error (2.0 files). | CM-1 |
| GDAL `validate_geoparquet.py` | `assert False, "Unexpected len(bbox)"` on a valid 2.0 8-element `bbox`. | BB-2 |
| GDAL | `map_ogr_geom_type_to_geoparquet[ogr.wkbPoint25D] = "Point"` (should be `"Point Z"`); no XYM/XYZM entries, so 2.0 measured geometries are reported as "unexpected type". | GT-4, ENC-2 |
| GDAL | duplicate-`geometry_types` check is nested under `if "bbox" in column_def` and never runs without a `bbox`. | GT-2 |
| GDAL | enforces the `srid:0` SHOULD as an error; downloads the `2.0.0-rc.1` release schema for `version: 2.0.0` (flagged TODO in the code). | CRS-5, SCH-4 |
| GPQ | 1.0-only: rejects native encodings (1.1), ` M`/` ZM` types, geodesic `edges`, 8-element `bbox`; writes `version: 1.0.0`. | GC-1, GT-1, ED-1, BB-2 |
| GPQ | `GeometryOrientation` checks `orb.Polygon` only; MultiPolygon rings are not checked. | OR-2 |
| GPQ | optional-field rules return on the first column that lacks the field, so later columns are not checked (multi-geometry-column files). | CRS-1, OR-1, ED-1, BB-2, EP-1 |
| GPQ | `GeometryTypes` accepts 2D data against `Point Z` (orb has no Z). | GT-4 |
| geoparquet-testing | `wkb-with-srid-prefix` passes GDAL because OGR accepts EWKB. | ENC-1 |
