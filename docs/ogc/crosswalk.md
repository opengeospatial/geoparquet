# GeoParquet requirements crosswalk (community spec ↔ schema ↔ OGC draft ↔ validators)

**Status: PROPOSAL for SWG review. Nothing here is final until the maintainers have reviewed it.**

This table lists every normative statement in the community specification and maps it to the
JSON Schema, to the OGC draft requirements in PR #224 / PR #247, and to the two community
validators. It was rebuilt from scratch against the sources below; Chris Holmes's wiki
crosswalk (June 2024) was used as a starting checklist only.

## Sources audited

| Source | Exact revision |
| --- | --- |
| Community spec 1.1 | `format-specs/geoparquet.md` and `schema.json` at tag `v1.1.0` |
| Community spec 2.0 | `format-specs/geoparquet.md` and `schema.json` at tag `v2.0.0-rc.1` (main at `21eba45` differs only by PR #301, a schema description string) |
| PR #224 (OGC template) | branch `ogc-template`, head `a3a9fa3` (ghobona, 2024-12-17) |
| PR #247 (requirements updates) | branch `ogc-requirements-updates`, head `fe68d22` (cholmes, 2024-06-17) |
| GPQ validator | `planetlabs/gpq` main at `067c201` (2026-08-30); rules in `internal/validator/rules.go`; latest release v0.24.0 |
| GDAL validator | `OSGeo/gdal` master `swig/python/gdal-utils/osgeo_utils/samples/validate_geoparquet.py`, last changed `75667c72` (2026-08-14) |
| Test corpus | `geoparquet/geoparquet-testing` main (2.0.0 target), `bad_data/manifest.json` (22 negative files) |
| Parquet format | `apache/parquet-format` tag `apache-parquet-format-2.12.0`, `LogicalTypes.md` and `Geospatial.md` |

Line numbers below (`L15`) refer to `geoparquet.md` at the given tag.

## How to read the table

* **1.1 / 2.0**: the RFC 2119 keyword the statement carries in that version. `—` = statement absent.
  `(implicit)` = the spec states it without a keyword but the validators and the OGC draft treat it as normative.
* **schema.json**: the constraint in the version's schema, or `—`.
* **OGC**: identifier in PR #224 (`R1..R8`, `REC1..REC3` are the eight requirement and three
  recommendation files; letters are the `part::` entries in order) or PR #247 (`247:...`).
  PR #247 files marked *orphan* exist on the branch but are not included in `document.adoc`, so they do not render.
* **GPQ**: rule title from `rules.go`, abbreviated. GPQ runs 16 metadata rules always and 4 data rules unless `--metadata-only`.
* **GDAL**: check in `validate_geoparquet.py`. `schema` = caught only through JSON Schema validation. `--check-data` marks data-scanning checks.
* **Status** uses the vocabulary: `aligned`, `missing in OGC`, `missing in tests`, `conflicting`, `obsolete in 2.0`. Several may apply.

## A. Normative statements in geoparquet.md

### A1. Geometry columns (structure)

| ID | Spec statement | 1.1 | 2.0 | schema.json | OGC (#224/#247) | GPQ | GDAL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GC-1 | Geometry columns MUST be encoded as WKB or the GeoArrow single-geometry native encodings (1.1 L15). In 2.0: MUST be encoded as Parquet `GEOMETRY` or `GEOGRAPHY` logical types annotating BYTE_ARRAY WKB (rc.1 L15). | MUST | MUST (changed) | `encoding` pattern (1.1) / `const "WKB"` (2.0) | R1.A+B (1.0 wording: BYTE_ARRAY + WKB only); 247:R1' A–D (encoding string valid, MUST be "WKB") | `RequiredColumnEncoding` accepts only `WKB` | `schema`; `--check-data` native types via OGR | **conflicting** with 1.1 (OGC and GPQ reject valid native encodings); for 2.0 OGC text lacks the logical-type requirement. |
| GC-2 | Geometry columns MUST be at the root of the schema (1.1 L21, rc.1 L19). | MUST | MUST | — | R2.A | `GeometryUngrouped` (checks root field by name is primitive) | — (implicit: unknown column name → error) | aligned |
| GC-3 | A geometry MUST NOT be a group field or nested in a group (1.1 L21). Removed in PR #234 (2024-06-21) because native encodings *are* group fields. | MUST | — | — | R2.B | `GeometryUngrouped` | — | **conflicting** for 1.1 (contradicts native encodings in the same document); **obsolete in 2.0**. See spec-issue SI-1. |
| GC-4 | Repetition of geometry columns MUST be `required` or `optional` (1.1 L25, rc.1 L23). | MUST | MUST | — | R3.A | `GeometryRepetition` | — | aligned (GDAL has no check) |
| GC-5 | A geometry column MUST NOT be repeated (1.1 L25, rc.1 L23). | MUST | MUST | — | R3.B | `GeometryRepetition` | — | aligned |
| GC-6 | A file MAY have multiple geometry columns with different names (1.1 L25, rc.1 L23). | MAY | MAY | `columns` object, any number of keys | — (permission, no req needed) | all column rules iterate columns | iterates columns | aligned (permission) |
| GC-7 | 2.0 only: WKB geometry columns MUST be stored as BYTE_ARRAY **with a `GEOMETRY` or `GEOGRAPHY` logical type** (rc.1 L114). 1.1: BYTE_ARRAY only (L98). | MUST (BYTE_ARRAY) | MUST (+ logical type) | — | R1.A (BYTE_ARRAY only) | `GeometryDataType` (physical type only) | — (2.0: `_PARQUET_GEO_CRS_` lookup presumes the logical type but no explicit error) | **missing in OGC** (logical type) and **missing in tests** (no validator asserts the logical type; only the test-corpus self-test does). |

### A2. Metadata container

| ID | Spec statement | 1.1 | 2.0 | schema.json | OGC | GPQ | GDAL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MD-1 | File MUST include a `geo` key in `FileMetaData::key_value_metadata` (1.1 L34, rc.1 L32). | MUST | MUST | (schema is applied to its value) | R4.A | `RequiredGeoKey` (fatal) | `'geo' file metadata item missing` | aligned. Corpus: `missing-geo-metadata`. |
| MD-2 | Value MUST be a JSON-encoded UTF-8 string (1.1 L34, rc.1 L32). | MUST | MUST | — | R4.B | `RequiredMetadataType` (JSON object) | `not valid JSON` | aligned. UTF-8 validity itself is not separately tested by either tool (Go/Python decoders reject invalid bytes as a side effect). Corpus: `geo-invalid-json`, `geo-invalid-utf8`. |
| MD-3 | Value MUST validate against the GeoParquet metadata JSON Schema (1.1 L34, rc.1 L32). | MUST | MUST | whole schema | R4.B | GPQ does **not** run schema.json; re-implements a subset | `jsonschema` validation against the released schema for the declared `version` | partially aligned. GPQ subset differs from the schema (see rows FM-1, CM-2, ED-1, BB-2). |
| MD-4 | Additional implementation-specific fields MAY be present at file level; readers should ignore them (1.1 L44, rc.1 L42). | MAY | MAY | top level has no `additionalProperties:false` | — (informative sentence in clause 6 only) | not rejected | not rejected | aligned; **missing in OGC** as a formal permission/recommendation. |

### A3. File metadata fields

| ID | Spec statement | 1.1 | 2.0 | schema.json | OGC | GPQ | GDAL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FM-1 | `version` REQUIRED string, the spec version identifier (1.1 L40, rc.1 L38). Schema pins the exact value. | REQUIRED | REQUIRED | `required`, `type string`, `const "1.1.0"` / `const "2.0.0"` | 247:R-fm.A (*orphan*) "appropriate value in the version key" | `RequiredVersion` (non-empty string, any value) | missing/non-string → error; unknown value → schema download fails → error | **missing in OGC** (#224 has nothing on `version`); GPQ does not check the value. Corpus: `missing-version`, `version-unknown`, `version-1-0-with-2-0-features`. |
| FM-2 | `primary_column` REQUIRED string naming the primary geometry column (1.1 L41, rc.1 L39). | REQUIRED | REQUIRED | `required`, `type string`, `minLength 1` | 247:R-fm.B (*orphan*) | `RequiredPrimaryColumn` | `geo["primary_column"] missing` | **missing in OGC** (#224). Corpus: `missing-primary-column`. |
| FM-3 | `primary_column` value must be one of the keys of `columns` — *implied* by FM-2 + FM-4 + CM-1, never stated with a keyword. | (implicit) | (implicit) | — (not expressible in JSON Schema draft-07) | 247:R-fm.B "MUST be a string that matches one of the column metadata keys" (*orphan*) | `PrimaryColumnInLookup` | `primary_column ... not in listed in geo["columns"]` | **missing in OGC** (#224); spec wording implicit (SI-2). Corpus labels `primary-column-not-in-columns` as `schema_validation_error`, which the schema cannot produce (SI-3). |
| FM-4 | `columns` REQUIRED object keyed by geometry column name (1.1 L42, rc.1 L40). | REQUIRED | REQUIRED | `required`, `type object`, `minProperties 1`, `patternProperties ".+"`, `additionalProperties false` | R4.C (partially); 247:R-cm (*orphan*) | `RequiredColumns` (object of objects; allows empty) | `geo["columns"] missing` | aligned for presence. `minProperties 1` and non-empty key names are schema-only (SCH-1, SCH-2). Corpus: `missing-columns`. |

### A4. Column metadata (presence and shape)

| ID | Spec statement | 1.1 | 2.0 | schema.json | OGC | GPQ | GDAL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CM-1 | Each geometry column in the dataset MUST be included in `columns`, keyed by column name (1.1 L48, rc.1 L46). | MUST | MUST | — | R4.C; 247:R-cm (*orphan*) | reverse direction only: metadata key with no matching Parquet column → fatal `missing geometry column` | reverse direction only: `lists a X column which is not found in the Parquet fields` | **missing in tests** for the stated direction. In 1.x a validator cannot know which unlisted columns are geometries; in 2.0 it can (any `GEOMETRY`/`GEOGRAPHY` column not in `columns`). Reverse direction (keys must exist in the file) is implicit in spec (SI-4). |
| CM-2 | `encoding` REQUIRED string; 1.1 values `WKB`, `point`, `linestring`, `polygon`, `multipoint`, `multilinestring`, `multipolygon` (L52); 2.0 only `WKB` (rc.1 L50). | REQUIRED | REQUIRED (narrowed) | `required`; `pattern ^(WKB\|point\|...)$` (1.1); `const "WKB"` (2.0) | 247:R1'.A–B (*orphan-ish*: R1 is included, but the 4-part text is only on #247) | `RequiredColumnEncoding` (`WKB` only) | `schema` | **conflicting** for 1.1 (GPQ, #247 reject native); aligned for 2.0. Corpus: none for encoding. |
| CM-3 | `geometry_types` REQUIRED array of strings, or empty if unknown (1.1 L53, rc.1 L51). | REQUIRED | REQUIRED | `required`, `type array`, `uniqueItems`, item pattern | 247:R9.A,C (*orphan*) | `RequiredGeometryTypes` | `schema` | **missing in OGC** (#224 has no geometry_types requirement). |
| CM-4 | Additional fields at column level: spec silent (the MAY in MD-4 is stated "at this level" = file level). Schema allows them; `scripts/test_json_schema.py` has `custom_key_column` as valid. | — | — | allowed (no `additionalProperties:false` inside a column object) | — | not rejected | not rejected | **missing in OGC**; spec ambiguity (SI-5). |

### A5. Geometry encoding (WKB, native)

| ID | Spec statement | 1.1 | 2.0 | schema.json | OGC | GPQ | GDAL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ENC-1 | WKB SHOULD be the OGC Simple Features Access Part 1 WKB representation (1.1: "using codes for 3D geometry types in the [1001,1007] range" L94; 2.0 defers details to Parquet Geospatial definitions, rc.1 L112). | SHOULD | SHOULD | — | REC1 (1.0/1.1 wording) | `GeometryEncoding` decodes with `paulmach/orb` WKB (ISO; Z dropped) | `--check-data`: `ogr.CreateGeometryFromWkb` (also accepts EWKB) | aligned for 1.1; for 2.0 REC1's `[1001,1007]` text is stale (Parquet allows XYM 2001–2007, XYZM 3001–3007). Corpus: `wkb-truncated`, `wkb-wrong-type-byte`, `wkb-with-srid-prefix` (EWKB; GDAL accepts EWKB so it will not flag this file). |
| ENC-2 | 1.1: only a subset of WKB is allowed: 2D or 3D geometries of the seven standard types; M values and non-linear types not supported (L96). 2.0: XYZM allowed via Parquet; non-linear still excluded by `geometry_types` vocabulary. | (implicit restriction) | (changed: M allowed) | `geometry_types` pattern `( Z)?` (1.1) / `( Z\| M\| ZM)?` (2.0) | — (only a note in clause 6) | decode failure on non-linear types | `--check-data` `unexpected type for GeoParquet` (map has 2D + 25D only) | **missing in OGC** as a requirement; GDAL map lacks M/ZM → **conflicting** with 2.0 (valid XYM/XYZM data reported as error). |
| ENC-3 | 1.1: WKB geometry columns MUST be stored using the BYTE_ARRAY Parquet type (L98). | MUST | MUST (see GC-7) | — | R1.A | `GeometryDataType` | — | aligned (1.1) |
| ENC-4 | 1.1 note: readers recommended to accept Arrow `BINARY` and `LARGE_BINARY`; writers preferably `BINARY` (L100). Lower-case "recommended", implementation note. | (informative) | — | — | — | — | — | informative; **obsolete in 2.0**. No action. |
| ENC-5 | 1.1 native: coordinates MUST be stored as native numbers using the `DOUBLE` Parquet type in (repeated) groups (L106–108). | MUST | — | — | — | — (GPQ rejects native encodings up front) | `--check-data` via OGR high-level API only (no schema-level check of DOUBLE) | **missing in OGC**; **missing in tests**; **obsolete in 2.0**. |
| ENC-6 | 1.1 native: for non-point types, x/y values MUST be embedded in repeated groups (`LIST` logical type) (L121–123). | MUST | — | — | — | — | — | **missing in OGC**; **missing in tests**; **obsolete in 2.0**. |
| ENC-7 | 1.1 native: there MUST NOT be null values in child/coordinate fields; only the outer geometry group may be null; `required` MAY be used to express this (L148–153). | MUST NOT / MAY | — | — | — | — | — | **missing in OGC**; **missing in tests**; **obsolete in 2.0**. |
| ENC-8 | 1.1 native (implicit): every value in a column with a single-geometry encoding is of that geometry type. Not stated with a keyword. | (implicit) | — | — | — | — | `--check-data`: `does not match the declared encoding` | **missing in OGC**; spec implicit (SI-6); **obsolete in 2.0**. |
| AX-1 | Coordinate axis order in WKB is always (x, y) = (easting/longitude, northing/latitude), overriding the CRS axis order (1.1 L157, rc.1 L118). No keyword. | (implicit) | (implicit) | — | — (informative clause 6.x only) | — | `bbox` geographic range check is the only heuristic | **missing in OGC** as a requirement; not machine-testable except heuristically. Corpus: `crs-mismatch-schema-vs-geo-metadata` is really an axis/CRS-vs-data case. |

### A6. `geometry_types`

| ID | Spec statement | 1.1 | 2.0 | schema.json | OGC | GPQ | GDAL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GT-1 | Accepted values: `Point`, `LineString`, `Polygon`, `MultiPoint`, `MultiLineString`, `MultiPolygon`, `GeometryCollection`; ` Z` suffix for 3D (1.1 L161–165); 2.0 adds ` M` and ` ZM` (rc.1 L126–128). | (list) | (list, extended) | item `pattern` | 247:R9 (*orphan*, no vocabulary) | `RequiredGeometryTypes` vocabulary has 2D + Z only | `schema` | **missing in OGC**; GPQ **conflicting** with 2.0 (rejects ` M`/` ZM`). |
| GT-2 | Values in the list must be unique (1.1 L168, rc.1 L131). | must (lower-case) | must | `uniqueItems: true` | — | — | `schema`; explicit duplicate check exists but only runs when `bbox` is present (indentation bug) | aligned via schema; **missing in OGC**. |
| GT-3 | Empty array explicitly signals unknown types (1.1 L167, rc.1 L130). | (definition) | (definition) | array may be empty | 247:R9.C (*orphan*) | `GeometryTypes` skips check when empty | skips when empty | aligned |
| GT-4 | "It is expected that this field is strictly correct": every geometry type present must be listed, with dimension suffix (1.1 L170, rc.1 L133). No RFC keyword. | (implicit MUST) | (implicit MUST) | — | 247:R9.B (*orphan*) "All geometry types present MUST be included" | `GeometryTypes` (matches `X` or `X Z`; orb drops Z so dimension mismatch is **not** detected) | `--check-data` type in list; maps `wkbPoint25D` to `Point` (bug: should be `Point Z`), no M/ZM | **missing in OGC** (#224); spec wording is not RFC 2119 (SI-7); tests only partially cover dimension. Corpus: `geometry-types-mismatch-*`, `geometry-types-missing-actual-type`, `zm-declared-*`. |
| GT-5 | 2.0 only: `geometry_types` MUST match the Parquet `GeospatialStatistics.geospatial_types` (rc.1 L135). | — | MUST | — | — | — | — | **missing in OGC**; **missing in tests**. |

### A7. CRS and epoch

| ID | Spec statement | 1.1 | 2.0 | schema.json | OGC | GPQ | GDAL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CRS-1 | `crs`, when present and not null, MUST be PROJJSON (1.1 L66; rc.1 L64 "when given in the GeoParquet column-metadata crs field"). | MUST | MUST | `oneOf [$ref projjson v0.7, null]` | R5.A | `OptionalCRS` validates against PROJJSON schema (`$schema` from object, default v0.6) | `schema` (+ PROJ parse via `SetFromUserInput`) | aligned. Note the schema references PROJJSON v0.7 while the spec's CRS84 example declares v0.5 (SI-8). Corpus: `crs-invalid-projjson`. |
| CRS-2 | `crs` MAY be `null` = CRS undefined/unknown; different meaning from absent (1.1 L68,L76; rc.1 L66,L72). | may | may | `type null` alternative | — (only prose in clause 6) | `OptionalCRS` accepts nil | accepted | aligned; **missing in OGC** as a formal statement. |
| CRS-3 | If `crs` key is absent, coordinates MUST be longitude/latitude on WGS84; default is OGC:CRS84 (1.1 L68, rc.1 L66). | MUST | MUST | — | R5.B | — | geographic bbox range check only | aligned in text; not machine-testable (**missing in tests**, inherently). |
| CRS-4 | 2.0 only: geo `crs` MUST describe the same CRS as the Parquet logical-type `crs` property; the two MUST NOT describe different CRSs (rc.1 L52, L74, L95). | — | MUST | — | — | — | 2.0.0 branch: null↔`srid:0`; non-null↔PROJJSON / `auth:code` / WGS 84 name; absent↔absent | **missing in OGC**. GDAL covers form-level consistency, not semantic equality (**partially missing in tests**). |
| CRS-5 | 2.0 only: when geo `crs` is `null`, the Parquet `crs` property SHOULD be `srid:0`; writer SHOULD set `srid:0` for unknown CRS (rc.1 L72, L91). | — | SHOULD | — | — | — | enforced as an **error** (stricter than SHOULD) | **missing in OGC**; GDAL stricter than spec (note for test-suite). |
| CRS-6 | 2.0 only: writer SHOULD use inline PROJJSON or `<authority>:<code>` for the Parquet `crs` property; `<authority>:<code>` RECOMMENDED for writers that cannot produce PROJJSON (rc.1 L84–87). | — | SHOULD / RECOMMENDED | — | — | — | — | **missing in OGC**; **missing in tests**. Also: rc.1 L80 attributes inline PROJJSON and `<authority>:<code>` to the Parquet 2.12.0 "CRS customization" section, which lists only `srid:` and `projjson:`; the wider list is in parquet-format `master` (SI-9). |
| CRS-7 | 2.0 only: a file carrying geo metadata MUST express its CRS there as inline PROJJSON (rc.1 L89, L95). Restatement of CRS-1. | — | MUST | as CRS-1 | — | as CRS-1 | as CRS-1 | duplicate of CRS-1; **missing in OGC** for 2.0 phrasing. |
| CRS-8 | 2.0 only (reader): a GeoParquet 2.0 reader MUST interpret the Parquet `crs` property in both inline PROJJSON and `<authority>:<code>` forms (rc.1 L93). | — | MUST (implementation) | n/a | — | n/a (file validators) | n/a | **missing in OGC**; needs a *reader/implementation* conformance target, not a file test. |
| CRS-9 | 2.0 only (reader): readers SHOULD also parse `srid:<identifier>` and `projjson:<key_name>` (rc.1 L93). | — | SHOULD (implementation) | n/a | — | n/a | n/a | **missing in OGC**. |
| CRS-10 | 2.0 only: `"OGC:CRS84"` and `"EPSG:4326"` authority strings are equivalent to OGC:CRS84 for this spec (rc.1 L259); PROJJSON `id` heuristics (both versions, informative). | (informative) | (normative equivalence) | — | — | — | accepts SRS names `WGS 84`, `WGS 84 (CRS84)` | **missing in OGC**. |
| EP-1 | `epoch` (number, decimal year) applies when `crs` is a dynamic CRS; "coordinates must always be qualified with the epoch" is background prose (1.1 L80–82, rc.1 L106–108). | optional field | optional field | `type number` | R6 "If the crs field defines a dynamic CRS, the coordinates SHALL always be qualified with the epoch" | `OptionalEpoch` (number) | `schema` | **conflicting**: #224 R6 promotes informative background to a SHALL that the community spec does not make (SI-10). Corpus: `epoch-on-unsupported-crs` (not a spec MUST either). |

### A8. Orientation and edges

| ID | Spec statement | 1.1 | 2.0 | schema.json | OGC | GPQ | GDAL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OR-1 | `orientation`, if present, must be `"counterclockwise"` (1.1 L55, L174; rc.1 L53, L140). | must (table) | must | `const "counterclockwise"` | — | `OptionalOrientation` | `schema` | aligned via schema/GPQ; **missing in OGC** as a metadata constraint. |
| OR-2 | When `orientation` is set: all exterior rings MUST be counterclockwise and all interior rings MUST be clockwise (1.1 L174, rc.1 L140). If absent, no assertion is made (L176). | MUST (conditional) | MUST (conditional) | — | R7.A+B stated **unconditionally** | `GeometryOrientation` (Polygon only; MultiPolygon and collections skipped) | `--check-data` `_check_counterclockwise` (Polygon, MultiPolygon, GeometryCollection) | **conflicting**: #224 R7 drops the "if present" condition (Chris's wiki flags this). GPQ misses MultiPolygon. Corpus: `orientation-ccw-declared-rings-cw`. |
| OR-3 | Writers are encouraged but not required to set `orientation` (1.1 L178, rc.1 L144). | (informative) | (informative) | — | — | — | — | informative; no action. |
| OR-4 | RECOMMENDED to set orientation counterclockwise if `edges` is `"spherical"` (1.1 L180, L190). 2.0: L146 says `"spherical"`, L180 says `not "planar"` (inconsistent within rc.1). | RECOMMENDED | RECOMMENDED (two variants) | — | REC2 | — | — | aligned for 1.1; for 2.0 spec is internally inconsistent (SI-11); **missing in tests** (nothing checks the recommendation). |
| ED-1 | `edges` must be one of `planar`, `spherical` (1.1 L56, L184); 2.0 adds `vincenty`, `thomas`, `andoyer`, `karney` (rc.1 L54, L150–176). Default `planar`. | must | must (extended) | `enum` | — | `OptionalEdges` (planar/spherical only) | `schema` | **missing in OGC**; GPQ **conflicting** with 2.0 (rejects the four geodesic values). |
| ED-2 | 2.0 (implicit): relationship between `edges` and the Parquet `GEOGRAPHY.algorithm` / `GEOMETRY` (planar) is not stated; `crs` and `geometry_types` have explicit "MUST match" rules, `edges` does not. | — | (gap) | — | — | — | — | spec gap (SI-12); test corpus self-test `test_geography_has_spherical_edges` assumes a match. |

### A9. Bounding box (column-level `bbox`)

| ID | Spec statement | 1.1 | 2.0 | schema.json | OGC | GPQ | GDAL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BB-1 | `bbox`, if specified, MUST be an array giving the range of each coordinate dimension; geographic CRS: SW then NE corner per RFC 7946 (antimeridian allowed) (1.1 L196, rc.1 L186). | MUST | MUST | `type array`, items number | R8 | `OptionalBbox` (4 or 6 numbers) | `schema` + min/max ordering + geographic range checks | aligned in text. |
| BB-2 | Length: 1.1 → 4 (XY) or 6 (XYZ) (L198); 2.0 → 4, 6, or 8 (XYZM) (rc.1 L190–192); M-only bounds not expressible (L194). | (4\|6) | (4\|6\|8) | `oneOf minItems/maxItems` 4,6 (1.1) / 4,6,8 (2.0) | — (R8 has no lengths) | `OptionalBbox` 4 or 6 only | `assert False, "Unexpected len(bbox)"` for 8 | **conflicting** with 2.0: GPQ rejects 8-element; GDAL crashes on 8-element. **missing in OGC** (lengths). |
| BB-3 | All geometries fall within `bbox` (implied by "range of values … in the geometry coordinates"). | (implicit) | (implicit) | — | R8 (implicitly) | `GeometryBounds` (X/Y only; antimeridian aware) | — | GDAL **missing in tests**. Corpus: `bbox-does-not-contain-geometry`. |
| BB-4 | `bbox` values MUST be in the same CRS as the geometry (1.1 L200, rc.1 L196). New in 1.1 (not in 1.0). | MUST | MUST | — | — | — | geographic range heuristic only | **missing in OGC**; **missing in tests** (not machine-checkable beyond heuristics). |

### A10. Covering and bounding-box columns (1.1; proposed for 2.0 in PR #302)

| ID | Spec statement | 1.1 | 2.0 | schema.json | OGC | GPQ | GDAL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COV-1 | `covering` keys MUST be a supported encoding; only `bbox` is supported (1.1 L204). | MUST | — (rc.1); returns if #302 merges | `covering` requires `bbox`; other keys **not** forbidden (no `additionalProperties:false`) | — | — | `schema` | **missing in OGC**; schema weaker than spec (SI-13); **obsolete in 2.0** pending #302. |
| COV-2 | `bbox` covering format `{"xmin": ["col","xmin"], …}`; second item MUST be `xmin`/`ymin`/`xmax`/`ymax`; all entries MUST use the same column name (1.1 L222). | MUST | — / #302 | 2-item arrays `[string minLength 1, const]`; same-name constraint not expressible | — | — | `schema` | **missing in OGC**; same-column-name rule **missing in tests**. |
| COV-3 | The named column MUST exist in the Parquet file and meet the Bounding Box Column criteria (1.1 L222). | MUST | — / #302 | — | — | — | — | **missing in OGC**; **missing in tests**. |
| BBC-1 | Bounding box column MUST be a Parquet group with 4 or 6 children (1.1 L230). | MUST | — / #302 | — | — | — | — | **missing in OGC**; **missing in tests**. |
| BBC-2 | 2D children MUST be named `xmin`,`ymin`,`xmax`,`ymax` (L238; the order rule was dropped when #302 merged, SI-26). | MUST | — / #302 | — | — | — | — | **missing in OGC**; **missing in tests**. |
| BBC-3 | `zmin`/`zmax` MAY be present; if one is present the other MUST be; 3D order MUST be `xmin,ymin,zmin,xmax,ymax,zmax` (L230). | MAY / MUST | — / #302 | — | — | — | — | **missing in OGC**; **missing in tests**. |
| BBC-4 | Children MUST be `FLOAT` or `DOUBLE` and all MUST use the same type (L230). | MUST | — / #302 | — | — | — | — | **missing in OGC**; **missing in tests**. |
| BBC-5 | Repetition MUST match the geometry column's repetition; a row MUST contain a bbox value iff it contains a geometry; MUST NOT contain a bbox value when geometry is null (L230). | MUST | — / #302 | — | — | — | — | **missing in OGC**; **missing in tests**. |
| BBC-6 | Bounding box column MUST be at the root of the schema and MUST NOT be nested in a group (L232). | MUST | — / #302 | — | — | — | — | **missing in OGC**; **missing in tests**. |

### A11. Other

| ID | Spec statement | 1.1 | 2.0 | schema.json | OGC | GPQ | GDAL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FI-1 | RECOMMENDED to use custom file key/value metadata to indicate a feature-identifier column (1.1 L238, rc.1 L202). | RECOMMENDED | RECOMMENDED | — | REC3 | — | — | aligned; untestable by design. |
| VC-1 | Implementations aware only of an older minor version MUST correctly interpret data written to a newer minor version OR recognise that they cannot (1.1 L295, rc.1 L263). | MUST (implementation) | MUST (implementation) | n/a | — | n/a | n/a | **missing in OGC**; needs implementation target. |
| VC-2 | Implementations SHOULD NOT reject metadata with unknown fields (1.1 L307, rc.1 L278). | SHOULD NOT | SHOULD NOT | n/a | — | n/a | n/a | **missing in OGC**. |
| VC-3 | Implementations SHOULD explicitly validate all field values they rely on (1.1 L308, rc.1 L279). | SHOULD | SHOULD | n/a | — | n/a | n/a | **missing in OGC**. |
| FE-1 | RECOMMENDED file extension `.parquet`; `.geoparquet` SHOULD NOT be used (1.1 L312, rc.1 L283). | RECOMMENDED / SHOULD NOT | same | n/a | — | — | — | **missing in OGC**; **missing in tests** (file-name check trivial to add). |
| MT-1 | If a media type is used, a GeoParquet file MUST use `application/vnd.apache.parquet` (1.1 L316, rc.1 L287). | MUST | MUST | n/a | — | — | — | **missing in OGC**; not file-testable. |

## B. Constraints that exist only in schema.json (no RFC 2119 sentence in geoparquet.md)

| ID | schema.json constraint | 1.1 | 2.0 | OGC | GPQ | GDAL | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SCH-1 | `columns` must have at least one entry (`minProperties: 1`). | yes | yes | — | `RequiredColumns` accepts `{}` | `schema` | **missing in OGC**; spec prose implies it (a GeoParquet file has ≥ 1 geometry column) but never states it (SI-14). |
| SCH-2 | Column names must be non-empty (`patternProperties ".+"` + `additionalProperties: false`). | yes | yes | — | — | `schema` | **missing in OGC**; spec silent. |
| SCH-3 | `primary_column` `minLength: 1`. | yes | yes | — | string check only | `schema` | **missing in OGC**. |
| SCH-4 | `version` `const` equal to the exact release string. | `"1.1.0"` | `"2.0.0"` | — | non-empty only | effectively (downloads schema for that version) | **missing in OGC**. Note: the schema for `2.0.0-rc.1` says `"2.0.0"` while the tag is `v2.0.0-rc.1`; GDAL special-cases this. |
| SCH-5 | `crs` `$ref` to `https://proj.org/schemas/v0.7/projjson.schema.json`. | v0.7 | v0.7 | R5.A (no version) | `$schema` in object or v0.6 default | `schema` (resolves remote or local PROJ copy) | version drift between schema (v0.7), GPQ default (v0.6), spec example (v0.5) — harmless but worth one sentence in the OGC doc (SI-8). |
| SCH-6 | `epoch` `type: number`. | yes | yes | R6 (semantics only) | `OptionalEpoch` | `schema` | aligned. |
| SCH-7 | `bbox` `items: number` + `oneOf` lengths. | 4,6 | 4,6,8 | R8 (no lengths) | 4 or 6 | `schema` | see BB-2. |
| SCH-8 | `covering.bbox` 2-item path arrays with `const` second element; `required [xmin,xmax,ymin,ymax]`. | yes | — (#302 restores) | — | — | `schema` | see COV-2. |

## C. Reverse index: validator rules → rows

### C1. GPQ (`internal/validator/rules.go`, 20 rules)

| GPQ rule title | Rows | Notes |
| --- | --- | --- |
| file must include a "geo" metadata key | MD-1 | fatal |
| metadata must be a JSON object | MD-2 | fatal |
| metadata must include a "version" string | FM-1 | any non-empty string; no version-value check |
| metadata must include a "primary_column" string | FM-2 | |
| metadata must include a "columns" object | FM-4 | allows empty object (SCH-1 gap) |
| column metadata must include the "primary_column" name | FM-3 | |
| column metadata must include a valid "encoding" string | CM-2, GC-1 | `WKB` only → conflicts with 1.1 native encodings |
| column metadata must include a "geometry_types" list | CM-3, GT-1 | vocabulary lacks ` M`/` ZM` → conflicts with 2.0 |
| optional "crs" must be null or a PROJJSON object | CRS-1, CRS-2 | `return nil` on first column without `crs` skips remaining columns (multi-column bug) |
| optional "orientation" must be a valid string | OR-1 | same early-return pattern |
| optional "edges" must be a valid string | ED-1 | planar/spherical only → conflicts with 2.0 |
| optional "bbox" must be an array of 4 or 6 numbers | BB-1, BB-2 | rejects 8 → conflicts with 2.0 |
| optional "epoch" must be a number | EP-1, SCH-6 | |
| geometry columns must not be grouped | GC-2, GC-3 | rejects 1.1 native (group) encodings |
| geometry columns must be stored using the BYTE_ARRAY parquet type | GC-7, ENC-3 | physical type only; no logical-type check |
| geometry columns must be required or optional, not repeated | GC-4, GC-5 | |
| all geometry values match the "encoding" metadata | ENC-1 | data rule; WKB decode |
| all geometry types must be included in the "geometry_types" metadata (if not empty) | GT-3, GT-4 | data rule; Z not verified (orb is 2D) |
| all polygon geometries must follow the "orientation" metadata (if present) | OR-2 | data rule; `orb.Polygon` only, MultiPolygon skipped |
| all geometries must fall within the "bbox" metadata (if present) | BB-3 | data rule; X/Y only |

Not covered by GPQ: MD-3 (schema.json itself), CM-1 forward direction, GC-7 logical type, GT-5, CRS-3..CRS-10, ED-2, BB-4, COV-*, BBC-*, FE-1, MT-1, VC-*. GPQ writes `version: "1.0.0"` (`metadata.go`) and has no 1.1/2.0 awareness.

### C2. GDAL `validate_geoparquet.py`

| Check (function / message) | Rows | Notes |
| --- | --- | --- |
| open with Parquet driver | (precondition) | |
| `'geo' file metadata item missing` | MD-1 | |
| `'geo' metadata item is not valid JSON` | MD-2 | |
| `lacks a 'version' member` / `not a string` | FM-1 | |
| download `schema.json` for declared version; `jsonschema` validate | MD-3, SCH-1..SCH-8, CM-2, CM-3, GT-1, GT-2, OR-1, ED-1, BB-2, EP-1, COV-* | unknown version → cannot download → error (FM-1). `2.0.0` mapped to `2.0.0-rc.1` release asset ("TODO remove when v2.0.0 is published"). |
| `geo["primary_column"] missing` / `geo["columns"] missing` | FM-2, FM-4 | |
| `primary_column ... not in listed in geo["columns"]` | FM-3 | |
| `lists a X column which is not found in the Parquet fields` | CM-1 (reverse) | |
| `crs ... cannot be parsed` (PROJ `SetFromUserInput`) | CRS-1 | |
| 2.0.0 only: `_PARQUET_GEO_CRS_` vs geo `crs` (null↔`srid:0`; PROJJSON/`auth:code`/WGS84; absent↔absent) | CRS-4, CRS-5, CRS-10 | enforces the `srid:0` SHOULD as an error |
| bbox sanity: `zmax<zmin`, `|x|>180`, `|y|>90` (geographic), `xmax<xmin` (projected), `ymax<ymin` | BB-1, BB-4 (heuristic), AX-1 (heuristic) | `assert False` on 8-element bbox (BB-2 conflict) |
| `declared several times in geometry_types[]` | GT-2 | only executed when `bbox` present (indentation) |
| `--check-data` WKB path: `Invalid WKB geometry`, `unexpected type for GeoParquet`, `not listed in geometry_types[]`, orientation | ENC-1, ENC-2, GT-4, OR-2 | 25D Point mapped to `Point` (should be `Point Z`); no M/ZM |
| `--check-data` native path (GDAL ≥ 3.9): type vs `geometry_types`, flat type vs declared encoding, orientation | ENC-8, GT-4, OR-2 | |

Not covered by GDAL: GC-2..GC-5 (root, repetition), GC-7/ENC-3 (physical/logical type), GT-5, BB-3 (containment), CRS-3, BB-4 beyond heuristics, COV-3, BBC-*, FE-1, MT-1, VC-*.

### C3. `geoparquet-testing/bad_data` → rows

| File | `expected_failure` | Rows |
| --- | --- | --- |
| bbox-does-not-contain-geometry | bbox_mismatch | BB-3 |
| crs-invalid-projjson | schema_validation_error | CRS-1 |
| crs-mismatch-schema-vs-geo-metadata | crs_mismatch | AX-1 / CRS-3 (data vs declared CRS; *not* the Parquet-property vs geo mismatch of CRS-4) |
| edges-spherical-with-planar-antimeridian-line | edges_mismatch | ED-1 semantics; no spec MUST |
| epoch-on-unsupported-crs | epoch_unsupported | EP-1; no spec MUST |
| geo-invalid-json, geo-invalid-utf8 | metadata_invalid_json / _utf8 | MD-2 |
| geometry-types-mismatch-declared-point-actual-linestring, geometry-types-missing-actual-type | geometry_type_mismatch | GT-4 |
| missing-columns, missing-primary-column, missing-version | schema_validation_error | FM-4, FM-2, FM-1 |
| missing-geo-metadata | metadata_missing | MD-1 |
| orientation-ccw-declared-rings-cw | orientation_mismatch | OR-2 |
| primary-column-not-in-columns | schema_validation_error | FM-3 (mislabelled: schema cannot detect this) |
| version-1-0-with-2-0-features, version-unknown | version_feature_mismatch / version_unknown | FM-1, SCH-4 |
| wkb-truncated, wkb-wrong-type-byte, wkb-with-srid-prefix | wkb_parse_error | ENC-1 |
| zm-declared-xy-actual-xyz, zm-declared-xyz-actual-xy | zm_mismatch | GT-4 |

No negative fixture exists for: GC-2..GC-5, GC-7 (logical type), CM-1, ENC-2, GT-5, CRS-4 (Parquet-property vs geo), BB-2 (8-element), BB-4, COV-*, BBC-*.

## D. Reverse index: OGC draft identifiers → rows

| OGC identifier (source) | Included in `document.adoc`? | Rows | Assessment |
| --- | --- | --- | --- |
| /req/core/geometry-columns R1.A, R1.B (#224) | yes | GC-1, ENC-3 | 1.0 wording; conflicts with 1.1; incomplete for 2.0 |
| /req/core/geometry-columns R1'.A–D (#247) | yes (file included; #247 wording) | CM-2, GC-1, ENC-3, ENC-1 | still "MUST be WKB" → 1.0/2.0 only |
| /req/core/nesting R2.A, R2.B | yes | GC-2, GC-3 | R2.B conflicts with 1.1, obsolete in 2.0 |
| /req/core/repetition R3.A, R3.B | yes | GC-4, GC-5 | aligned |
| /req/core/metadata R4.A, R4.B, R4.C | yes | MD-1, MD-2, MD-3, CM-1 | aligned; R4.C untested in the stated direction |
| /req/core/crs R5.A, R5.B | yes | CRS-1, CRS-3 | aligned for 1.1; 2.0 needs CRS-4..CRS-10 |
| /req/core/epoch R6 | yes | EP-1 | conflicting (invents a SHALL) |
| /req/core/orientation R7.A, R7.B | yes | OR-2 | conflicting (unconditional) |
| /req/core/bbox R8 | yes | BB-1, BB-3 | aligned; no lengths, no CRS statement |
| /rec/core/encoding REC1 | yes | ENC-1 | aligned 1.1; stale codes for 2.0; no conformance test (metanorma MODSPEC_1 warning) |
| /rec/core/orientation-spherical-edges REC2 | yes | OR-4 | aligned; no conformance test |
| /rec/core/feature-identifiers REC3 | yes | FI-1 | aligned; no conformance test |
| /req/core/filemetadata R-fm.A, R-fm.B (#247) | **no (orphan)** | FM-1, FM-2, FM-3 | needed; "appropriate value" is not testable as written |
| /req/core/columnmetadata R-cm (#247) | **no (orphan)** | CM-1 | duplicates R4.C |
| /req/core/geoemtrytypes R9.A–C (#247) | **no (orphan)** | CM-3, GT-3, GT-4 | needed; identifier typo |
| /conf/core/* TEST001–TEST008 | yes | mirror R1–R8 one-to-one | test methods restate the requirement; none references a concrete validator or fixture |

Statements with **no** OGC counterpart on either branch: FM-1/2/3 (in #224), CM-3/GT-* (in #224), GC-7 logical type, ENC-2, ENC-5..ENC-8, AX-1, GT-5, CRS-2, CRS-4..CRS-10, OR-1, ED-1, ED-2, BB-2, BB-4, COV-*, BBC-*, VC-*, FE-1, MT-1, SCH-1..SCH-4.
