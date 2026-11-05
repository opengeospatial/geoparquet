# Audit of the OGC-formatted GeoParquet document (PR #224 / PR #247)

**Status: PROPOSAL for SWG review (Phase 1 of the OGC alignment work). Nothing here changes the
community specification. Read-only audit; no PR branch was modified.**

> **Phase 2 decisions (chair, 2026-09-03) and outputs.** Target version **2.0.0**; a single
> standardization target (the file), so reader expectations are informative; the covering class is
> drafted from PR #302 and marked conditional. The 2.0 metanorma document is in
> [`../../ogc/`](../../ogc/) (two requirements classes: Core with 20 requirements, 6
> recommendations, 3 permissions; Bounding Box Covering with 6 requirements; plus, at Chris Holmes's suggestion, a proposed
> Cloud-Optimized Distribution class with 5 requirements and 4 recommendations drawn from the
> distribution best-practices guide and `geoparquet-io`; 31 abstract tests, each naming the `gpio` check that implements it).
> Companion files: [`CHANGES.md`](CHANGES.md) (wording differences), [`spec-issues.md`](spec-issues.md)
> (defects in the community spec to raise as issues), [`gaps.md`](gaps.md) (validator coverage per
> test). Section 7 below describes the five-class structure proposed before that decision; the
> drafted document folds CRS and geometry properties into Core, as section 7.1 allowed.

Companion file: [`crosswalk.md`](crosswalk.md) (one row per normative statement, with the row IDs
`GC-*`, `MD-*`, `FM-*`, `CM-*`, `ENC-*`, `GT-*`, `CRS-*`, `EP-*`, `OR-*`, `ED-*`, `BB-*`, `COV-*`,
`BBC-*`, `VC-*`, `FE-*`, `MT-*`, `SCH-*` used below).

## 1. Summary

* PR #224 is a complete, **buildable** metanorma skeleton (Metanorma 2.5.3 in the current
  `metanorma/metanorma` Docker image builds it to HTML/XML in about 100 s with warnings, no errors).
  It describes **GeoParquet 1.0.0**, not 1.1: the preface, external-id, edition and every
  requirement are 1.0 wording. Chris confirmed this target in the PR thread (2024-06-08).
* PR #247 adds three requirement files and rewrites requirement 1, but the three new files are
  **never included** in `document.adoc`, so they do not render (confirmed by building the branch).
  It also predates the last merge of `main` into #224 and uses an ATS attribute (`subject::`) that
  Gobe later corrected to `target::` on #224.
* Coverage: the crosswalk has about 70 rows for the community spec, roughly **60 of them carrying
  a requirement, recommendation or permission**; #224 captures 8 requirements (15 `part::`
  statements) and 3 recommendations. Of those, 3 are wrong for 1.1 and later (R1, R2.B, R7) and 1
  invents a SHALL the spec does not make (R6).
  About **40 statements have no OGC counterpart on either branch**, including everything about `version`,
  `primary_column`, `geometry_types`, `edges`, covering/bounding-box columns, the whole 2.0 CRS
  model, and all reader-side requirements.
* The two community validators disagree with the current spec in several places (GPQ is 1.0-only;
  GDAL crashes on a valid 2.0 8-element bbox and mislabels 3D points), so "map every OGC requirement
  to an existing validator check" will leave a real gaps list either way.
* The daily OGC DRAFTS build referenced everywhere (`docs.ogc.org/DRAFTS/24-013.html`) returns 404
  and 24-013 is not on the DRAFTS index (also reported in issue #277). Whatever cron existed is gone;
  the repo has no metanorma CI of its own.

## 2. What is in PR #224 (`ogc-template`, head `a3a9fa3`)

Twelve commits: Gobe Hobona's migration (`de9a021`, originally #206), Kyle's pre-commit fix, Chris's
README rewrite (May 31 2024), three merges of `main` (June 7, June 10, Oct 23 2024), and Gobe's
one-line ATS fix (Dec 17 2024). Everything lives under `format-specs/` next to the markdown spec.

### 2.1 Document structure

```
format-specs/document.adoc                  entry file (metanorma attributes + include list)
  sections/clause_0_front_material.adoc     preface ("This is version 1.0.0"), abstract, submitters, contributors
  sections/clause_1_scope.adoc              one paragraph
  sections/clause_2_conformance.adoc        boilerplate; single "Core" conformance class
  sections/clause_3_references.adoc         Apache Parquet, PROJJSON, OGC 06-103r3, ISO 19111:2019
  sections/clause_4_terms_and_definitions.adoc   epoch, coordinate reference system (+ RFC 2119 note)
  sections/clause_5_conventions.adoc        identifier base http://www.opengis.net/spec/geoparquet/1.0
  sections/clause_6_normative_text.adoc     the 1.0 spec prose, with include:: of 8 req + 3 rec files
  sections/annex-a.adoc                     includes abstract_tests/ATS_class_core.adoc
  sections/annex-history.adoc               one row (0.1, 2022-04-18)
  sections/annex-bibliography.adoc          ISO/IEC 13249-3:2016
  requirements/requirements_class.adoc      /req/core listing the 8 requirements
  requirements/requirement001..008.adoc     /req/core/{geometry-columns,nesting,repetition,metadata,crs,epoch,orientation,bbox}
  recommendations/recommendation001..003.adoc   /rec/core/{encoding,orientation-spherical-edges,feature-identifiers}
  abstract_tests/ATS_class_core.adoc        /conf/core, target /req/core, includes TEST001..008
  abstract_tests/TEST001..008.adoc          /conf/core/<same names>, one per requirement, no tests for recommendations
  Gemfile (metanorma-cli, relaton-cli), notes.txt, README.md, empty code/ figures/ images/ folders
```

All requirement/recommendation includes in clause 6 use a leading slash
(`include::/requirements/requirement001.adoc[]`). Asciidoctor warns "include file is outside of
jail; recovering automatically" twelve times and then resolves them relative to the document, so
they do render, but the paths should be made relative (`include::../requirements/...`).

### 2.2 Document metadata problems (all in `document.adoc`)

| Attribute | Value on branch | Problem |
| --- | --- | --- |
| `:external-id:` | `http://www.opengis.net/doc/IS/geoparquet/1.0` | must follow the target version |
| `:edition:` | `1.0.0` | idem |
| `:docnumber:` | `24-013` | number was assigned by OGC in 2024; confirm with OGC staff that it is still reserved for GeoParquet before reuse |
| `:status:` | `draft` | metanorma OGC: "draft is not an allowed status for standard" (use `swg-draft`, `oab-review`, `public-rfc`, `tc-vote`, `approved`, `published`, ...) |
| `:docsubtype:` | `Interface` | "not a permitted subtype of Standard: reverting to 'implementation'"; for a data format the intended value is `encoding` |
| `:received-date:` etc. | `2029-03-30` | placeholder dates in the future |
| `:fullname..fullname_5:` | Chris Holmes, Tim Schaub, Joris Van den Bossche, Kyle Barron, Javier de la Torre | editors list is Chris's guess (`notes.txt`: "Confirm the editors, submitters and contributors"); Contributors table is empty |
| `:submitting-organizations:` | Planet; CARTO | needs SWG confirmation |
| `:draft:` | `3.0` | meaningless as is |

### 2.3 Normative content

Eight requirements, three recommendations, eight abstract tests. The abstract tests are
one-to-one restatements of the requirement parts ("Verify that ...") and reference no fixture or
tool. Metanorma warns that the three recommendations have no conformance test (`MODSPEC_1`).
See crosswalk section D for the per-identifier assessment.

## 3. What is in PR #247 (`ogc-requirements-updates`, head `fe68d22`, draft)

Four commits by Chris (June 16–17 2024), based on #224 at `91b412e` (June 10). It touches only:

| File | Change | Rendered? |
| --- | --- | --- |
| `requirements/requirement001.adoc` | rewritten into four parts: encoding string valid; value MUST be `WKB`; BYTE_ARRAY for WKB; WKB encoding | yes (file is already included) |
| `requirements/requirement-fm.adoc` (new) | `/req/core/filemetadata`: `version` present with "appropriate value"; `primary_column` present and matches a column key | **no** — not included anywhere |
| `requirements/requirement-cm.adoc` (new) | `/req/core/columnmetadata`: each geometry column has an entry keyed by its name | **no** |
| `requirements/requirements009.adoc` (new) | `/req/core/geoemtrytypes` (typo): list required; all present types listed; empty if unknown | **no** |
| `abstract_tests/ATS_class_core.adoc` | uses `subject:: <<rc_table-core>>`; #224 later changed this line to `target:: /req/core` | builds, but metanorma reports the requirements class and conformance class as unlinked |

The GitHub diff of #247 against #224 also shows `geoparquet.md`, `schema.json`, `README.md` and
the examples changing, but that is only because #224 merged `main` after #247 branched; against its
own merge base #247 does not touch those files. None of the new requirements has an abstract test,
and `requirements_class.adoc` was not updated to list them. Chris's wiki crosswalk stops at the
same point ("TODO: Fix this, its not right" on R7; REC2 "doesn't quite match").

## 4. What is stale

### 4.1 Relative to 1.1.0

The whole document is 1.0. Concretely, against `v1.1.0`:

* R1 (BYTE_ARRAY + WKB only) and #247's R1' ("MUST be WKB") reject the six native GeoArrow
  encodings that 1.1 allows (GC-1, CM-2).
* R2.B ("MUST NOT be a group field") contradicts 1.1's native `point` encoding, which is a group.
  1.1.0 itself carries this contradiction; PR #234 removed the sentence from `main` in June 2024
  (GC-3, spec issue SI-1).
* Missing entirely: native-encoding rules ENC-5..ENC-8, `covering` and bounding-box columns
  (COV-1..3, BBC-1..6 — eleven MUST statements), `bbox` same-CRS rule (BB-4), Version
  Compatibility (VC-1..3), File Extension (FE-1), Media Type (MT-1).
* The column-metadata table in clause 6 lacks the `covering` row; the preface and the JSON Schema
  link point at `v1.0.0`.

### 4.2 Relative to 2.0.0-rc.1

Everything in 4.1 that survives into 2.0, plus:

* Geometry columns must carry the Parquet `GEOMETRY`/`GEOGRAPHY` logical type (GC-7); nothing in
  the OGC text mentions logical types, `GeospatialStatistics`, or Parquet 2.11+/2.12.
* The CRS model changed: the Parquet logical-type `crs` property is the source of truth, geo `crs`
  restates it as inline PROJJSON, `srid:0` ↔ `null`, `<authority>:<code>` forms, and two reader
  requirements (CRS-4..CRS-10). None of this exists in #224.
* `geometry_types` gains ` M`/` ZM` and must match Parquet `geospatial_types` (GT-1, GT-5).
* `edges` gains four geodesic values (ED-1); REC1's "[1001,1007]" is stale.
* `bbox` may have 8 elements (BB-2).
* `covering`/bounding-box columns were dropped in rc.1 and are being restored by PR #302 (open,
  not draft, 2026-08-28). The OGC document must follow that decision.
* References must move from Wikipedia/WKB to normative references to the Apache Parquet format
  (`LogicalTypes.md`, `Geospatial.md`) and OGC 06-103r4 (SFA 1.2.1, which is what Parquet cites).

### 4.3 Things that were never right for any version

* R6 turns informative background ("coordinates must always be qualified with the epoch") into a
  SHALL. The spec's actual normative element is an optional `epoch` field (EP-1, SI-10).
* R7 states the orientation rule unconditionally; the spec applies it only when `orientation` is
  set (OR-2).
* No requirement covers `version`, `primary_column`, `primary_column ∈ columns`, `geometry_types`,
  `orientation`/`edges` value constraints, or the schema-only constraints (`minProperties`,
  non-empty names). #247 started to fill the first two groups but never wired the files in.

## 5. Build

### 5.1 How the build is meant to work

Per `format-specs/README.md` on #224: run metanorma from `format-specs/` via Docker,
`metanorma compile --agree-to-terms -t ogc -x html document.adoc`. The README also states the
document "automatically get[s] built ... and published at docs.ogc.org/DRAFTS/24-013.html by a
cron job running on OGC's infrastructure". That cron pulled from the `ogc-template` branch when
Gobe set it up in April 2024 (#206). Today the URL is 404 and 24-013 is absent from the DRAFTS
index (78 entries). The repo itself has no metanorma workflow; `.github/workflows/` contains only
`lint.yml` (pre-commit whitespace), `scripts.yml` (JSON Schema tests) and `release.yml`, on both
`main` and the PR branches. There is no `metanorma.yml` (the current OGC template has one).

### 5.2 What I ran

Both branches were exported to a scratch directory (the branches were not touched) and built with
`metanorma/metanorma:latest` (digest `sha256:9e920fd2…`, image date 2026-08-18; Metanorma 2.5.3,
metanorma-cli 1.17.0, standoc 3.5.0):

```
docker run --rm -v "$PWD":/metanorma metanorma/metanorma \
  metanorma compile --agree-to-terms -t ogc -x html,xml document.adoc
```

| Branch | Exit | Time | Output | Requirements rendered |
| --- | --- | --- | --- | --- |
| #224 `a3a9fa3` | 0 | 1 min 42 s (first run, fetches relaton data) | `document.html` 157 KB, `document.xml`, `document.err.html` | 8 req, 3 rec, 8 conf tests |
| #247 `fe68d22` | 0 | similar | same | same 8/3/8 — the three orphan files do not appear |

Network is required: relaton fetches OGC 06-103r3, ISO 19111:2019 and ISO/IEC 13249-3:2016 from the
relaton GitHub indexes. "Apache Parquet" and "PROJJSON" are not recognised prefixes and stay as
plain bibliographic entries (fine, but they should be given proper `[[[id,...]]]` metadata).

### 5.3 What fails or warns (from `document.err.html` and the console)

* `'Interface' is not a permitted subtype of Standard: reverting to 'implementation'` (OGC_17)
* `draft is not an allowed status for standard` (OGC_2)
* 12 × `include file is outside of jail; recovering automatically` (leading-slash includes)
* `line 379: invalid empty option detected in style attribute` (`[cols=",,",options="header",]`
  trailing comma in the metadata tables)
* 3 × `Requirement /rec/core/... has no corresponding Conformance test` (MODSPEC_1)
* 3 × `Table should have title`, 3 × `Hanging paragraph in clause`, 1 × `Style override set for
  ordered list` (STANDOC_48/14)
* `ID Layer_1 has already been used` (OGC logo SVG; harmless, comes from the metanorma OGC assets)
* #247 additionally: `Requirement class /req/core has no corresponding Conformance class` and
  `Conformance class /conf/core has no corresponding Requirement class` (the `subject::` line).

None of these is fatal. A clean CI build needs: relative include paths, valid `status`/`docsubtype`,
real dates, titled tables, an abstract test per recommendation (or drop recommendations from the
ATS on purpose), and a GitHub Actions job (the OGC template ships one that runs
`metanorma-build` and uploads artifacts; PDF output needs the `--agree-to-terms` fonts step).

## 6. Conflicts found

### 6.1 OGC draft vs community spec

| Row | Conflict |
| --- | --- |
| GC-1 / CM-2 | R1, R1' require WKB only; 1.1 allows native encodings; 2.0 requires the logical type too |
| GC-3 | R2.B "MUST NOT be a group field" contradicts 1.1 native encodings; sentence removed from spec by #234 |
| EP-1 | R6 SHALL has no counterpart in the spec |
| OR-2 | R7 drops the "if `orientation` is present" condition |
| ENC-1 | REC1 cites `[1001,1007]` codes; 2.0 also allows 2001–2007 and 3001–3007 via Parquet |
| OR-4 | REC2 says "spherical"; rc.1 itself says "spherical" in one place and "not planar" in another |

### 6.2 Validators vs community spec (matters for "every requirement maps to a check")

| Tool | Finding | Rows |
| --- | --- | --- |
| GPQ | 1.0-only: rejects native encodings, ` M`/` ZM` types, geodesic `edges`, 8-element `bbox`; writes `version: 1.0.0` | GC-1, GT-1, ED-1, BB-2 |
| GPQ | orientation data rule checks `orb.Polygon` only; MultiPolygon rings are not checked | OR-2 |
| GPQ | `geometry_types` data rule accepts `Point` data against `Point Z` (orb is 2D) | GT-4 |
| GPQ | optional-field rules `return nil` on the first column lacking the field; later columns unchecked | CRS-1, OR-1, ED-1, BB-2, EP-1 |
| GPQ | does not run `schema.json`; `columns: {}` and empty `primary_column` pass | MD-3, SCH-1, SCH-3 |
| GDAL | `assert False, "Unexpected len(bbox)"` on an 8-element bbox → uncaught exception on valid 2.0 files | BB-2 |
| GDAL | `wkbPoint25D` mapped to `"Point"` (others map to `"X Z"`), so a correct `["Point Z"]` file errors in `--check-data`; no XYM/XYZM mapping | GT-4, ENC-2 |
| GDAL | duplicate-`geometry_types` check only runs when `bbox` is present (indentation) | GT-2 |
| GDAL | enforces the `srid:0` SHOULD as an error; downloads the `2.0.0-rc.1` release schema for `version: 2.0.0` | CRS-5, SCH-4 |
| GDAL | accepts EWKB (SRID-prefixed) WKB, so `bad_data/wkb-with-srid-prefix` passes | ENC-1 |
| Corpus | `primary-column-not-in-columns` labelled `schema_validation_error`, which JSON Schema cannot produce | FM-3 |
| Neither | checks the logical type (GC-7), `geometry_types` vs Parquet statistics (GT-5), forward direction of CM-1, `bbox` same CRS (BB-4), any covering / bounding-box-column rule (COV-*, BBC-*), file extension (FE-1) | |

### 6.3 Community spec, internal (recorded for `spec-issues.md` in Phase 2; not fixed here)

| ID | Issue |
| --- | --- |
| SI-1 | 1.1.0 L21 "A geometry MUST NOT be a group field" vs 1.1.0 native `point` encoding (a group). Already fixed on `main` (#234) but the released 1.1.0 text is contradictory. |
| SI-2 | `primary_column` must name a key of `columns` is only implied; validators, #247 and the test corpus treat it as a MUST. |
| SI-3 | Corpus `expected_failure` for `primary-column-not-in-columns` cannot be a schema error. |
| SI-4 | "Each key [of `columns`] is the name of a geometry column in the table" is a description, not a MUST; both validators enforce it. |
| SI-5 | Column-level additional properties: spec silent, schema and `test_json_schema.py` allow them. |
| SI-6 | 1.1 native encodings never state that all values must be of the declared single geometry type. |
| SI-7 | "It is expected that this field is strictly correct" (`geometry_types`) is the only sentence carrying the most-tested data rule; not RFC 2119. |
| SI-8 | PROJJSON schema versions: `schema.json` v0.7, CRS84 example v0.5, GPQ default v0.6. |
| SI-9 | rc.1 L80 attributes inline PROJJSON and `<authority>:<code>` to the Parquet 2.12.0 "CRS customization" section; that tag lists only `srid:` and `projjson:`. The fuller list is on parquet-format `master`. The normative reference should pin the Parquet version that actually says what GeoParquet relies on. |
| SI-10 | Epoch prose "must always be qualified" reads as a requirement but is background. |
| SI-11 | rc.1 L146 "if `edges` is spherical" vs L180 "if `edges` is not planar". |
| SI-12 | No rule ties `edges` to the Parquet `GEOGRAPHY.algorithm` / `GEOMETRY` (planar), unlike `crs` and `geometry_types`. |
| SI-13 | `covering` keys "MUST be a supported encoding" but the schema does not set `additionalProperties: false` on `covering`. |
| SI-14 | `columns` `minProperties: 1` and non-empty names exist only in the schema. |
| SI-15 | `schema.json` at tag `v2.0.0-rc.1` pins `version: "2.0.0"`; GDAL has a workaround. Harmless once 2.0.0 is released, worth a note in the release process. |

## 7. Proposed requirements-class structure for the OGC document

Design goals: describe the spec as it is; one OGC requirement per community MUST/SHOULD, grouped so
that every requirement in a class shares a conformance target; normative references to Apache
Parquet instead of restating it; identifiers stable across 1.1 and 2.0 wherever the statement is
the same, so the two candidate targets differ by adding/removing classes rather than renumbering.

Two **conformance target types** are needed, because the spec contains both file rules and
reader/implementation rules (VC-1..3, CRS-8..9):

* *GeoParquet file* (an Apache Parquet file) — all `/req/core/...`, `/req/covering/...`, and for
  1.1 the encoding classes;
* *GeoParquet reader* (software) — `/req/reader/...`.

### 7.1 Classes (2.0 target)

| Class | Target | Contents (crosswalk rows) | Notes |
| --- | --- | --- | --- |
| `/req/core` | file | `geo` key, JSON/UTF-8, validates against schema (MD-1..3); `version`, `primary_column`, `columns`, primary ∈ columns, ≥1 column, non-empty names (FM-1..4, SCH-1..4); each geometry column listed, listed keys exist (CM-1, SI-4); geometry column at root, repetition (GC-2, GC-4, GC-5); BYTE_ARRAY + `GEOMETRY`/`GEOGRAPHY` logical type by normative reference to Parquet `LogicalTypes.md` (GC-7); `encoding` = `WKB` (CM-2); WKB per OGC 06-103r4 / Parquet `Geospatial.md` (ENC-1, ENC-2); axis order (AX-1); `geometry_types` vocabulary, uniqueness, strictness, match with Parquet `geospatial_types` (CM-3, GT-1..5); media type (MT-1) | Sub-identifiers `/req/core/metadata/...`, `/req/core/geometry-column/...`, `/req/core/geometry-types/...` keep the class small in count but navigable. |
| `/req/crs` | file | geo `crs` PROJJSON or null (CRS-1, CRS-2); default CRS84 when absent (CRS-3); geo `crs` consistent with Parquet `crs` property (CRS-4, CRS-7); `srid:0` ↔ null (CRS-5); writer forms for the Parquet property (CRS-6, recommendations); `epoch` semantics (EP-1, as a conditional requirement on the field, not a SHALL on coordinates); CRS84/EPSG:4326 equivalence (CRS-10) | Could be folded into core; kept separate because every requirement here is conditional on a non-default CRS and because it is where 2.0 differs most from 1.1. |
| `/req/geometry-semantics` | file | `orientation` value and ring rule when present (OR-1, OR-2); `edges` values and default (ED-1); recommendation: counterclockwise when edges not planar (OR-4); `bbox` array, lengths, containment, same CRS (BB-1..4) | Alternatively split `/req/bbox` out; all are optional column-metadata fields with data-level consequences. |
| `/req/covering` | file | `covering` keys, `bbox` covering paths, bounding-box column structure (COV-1..3, BBC-1..6) | **Only if PR #302 merges.** Optional class; a file conforms to it only when it declares a covering. Same text serves 1.1. |
| `/req/reader` | reader | interpret PROJJSON and `<authority>:<code>` Parquet `crs` (CRS-8); should parse `srid:`/`projjson:` (CRS-9); forward compatibility (VC-1); SHOULD NOT reject unknown fields (VC-2); SHOULD validate field values (VC-3) | New in OGC terms; the community spec has had these since 1.1. Abstract tests are implementation tests (feed a newer-minor file; feed a `crs` in each form). |
| Recommendations | file | `.parquet` extension / not `.geoparquet` (FE-1); feature-identifier metadata (FI-1); PROJJSON or `<authority>:<code>` for the Parquet property (CRS-6) | Recommendations without conformance tests trigger a metanorma warning; either give each a trivial abstract test or mark them as such deliberately. |

Conformance classes mirror the requirement classes one-to-one (`/conf/core`, `/conf/crs`,
`/conf/geometry-semantics`, `/conf/covering`, `/conf/reader`).

### 7.2 How 2.0's reliance on native Parquet types changes the document

* **Fewer GeoParquet-owned requirements, more normative references.** In 1.0/1.1 the OGC text
  had to define the byte-level encoding itself (BYTE_ARRAY, WKB subset, native GeoArrow layouts).
  In 2.0 the encoding, the WKB variant, XYZM, the `crs` property syntax, the edge-interpolation
  algorithms, statistics and axis order are all defined by `apache/parquet-format`. The OGC
  document should cite those as **normative references pinned to a version** (2.12.0 for the
  logical types; whichever version first documents inline PROJJSON / `<authority>:<code>` for the
  `crs` text, see SI-9) and reduce GeoParquet's own requirement to "the column SHALL be annotated
  with the `GEOMETRY` or `GEOGRAPHY` logical type as defined in [Parquet]".
* **Consistency requirements replace definition requirements.** The genuinely new 2.0 rules are
  cross-checks: geo `crs` ↔ Parquet `crs` (CRS-4), geo `geometry_types` ↔ Parquet
  `geospatial_types` (GT-5), `null` ↔ `srid:0` (CRS-5), and (a spec gap) `edges` ↔ `algorithm`
  (SI-12). These need abstract tests that read both the Thrift schema and the JSON metadata; no
  current validator does this, so they will head the gaps list.
* **The `geo` metadata becomes a conformance marker.** 2.0 says a writer MAY emit only native
  types, but such a file "is not conformant GeoParquet 2.0". The Scope/Conformance clauses should
  say this explicitly: conformance is claimed for files carrying `geo` metadata; readers are
  expected (reader class) to read native-only files as well.
* **A reader conformance target is now unavoidable** (CRS-8 is a MUST on readers).
* **OGC 06-103r4 (SFA 1.2.1) becomes the WKB reference**, because that is what Parquet cites;
  #224 currently cites 06-103r3 and Wikipedia.

### 7.3 1.1 variant

Same skeleton with these differences: `/req/core` allows `encoding` ∈ {WKB, six native values} and
requires BYTE_ARRAY only for WKB (no logical types); add `/req/encoding-native` (ENC-5..8) as a
conditional class for columns using native encodings; `/req/crs` shrinks to CRS-1..3 and EP-1;
`/req/covering` is unconditional (1.1 has it); `/req/reader` keeps VC-1..3 only. Identifier base
`http://www.opengis.net/spec/geoparquet/1.1`.

## 8. Decisions needed from the chair before Phase 2

1. **Target version** (1.1.0 vs 2.0.0). Practical note: 2.0.0 final is imminent and the test
   corpus is already 2.0-only; 1.1 is what GPQ and most deployed writers produce. A 2.0 document
   with a short informative annex on reading 1.x files is the smaller drafting job (fewer
   GeoParquet-owned encoding requirements) but depends on #302 and the final 2.0.0 tag.
2. **PR #302 (covering) outcome**, which decides whether `/req/covering` exists in the 2.0 document.
3. **Reader conformance class**: include (recommended; the MUSTs are in the spec) or leave reader
   rules informative.
4. **Document identity**: keep `24-013`, confirm `docsubtype: encoding`, status `swg-draft`,
   editors/submitters/contributors list, submitting organisations.
5. **Recommendations in the ATS**: give each a conformance test, or accept the metanorma warning.
6. **Where the document lives**: `format-specs/` (as #224) vs a dedicated `ogc/` directory; and
   whether to add a metanorma GitHub Actions job to this repo (needed since the OGC cron is gone).

## 9. Remaining effort (estimate)

| Work item | Estimate |
| --- | --- |
| Rebase #224 skeleton onto `main` layout, fix metadata/attributes/includes, add metanorma CI job that builds on PRs | 0.5 day |
| Write ~45 requirements/recommendations for the chosen version (from crosswalk rows), each with identifier and abstract test; update requirements classes and conformance classes | 2 days |
| Rewrite clause 6 prose from the target `geoparquet.md` so text and requirements agree; references clause (Parquet pinned versions, OGC 06-103r4, PROJJSON, RFC 7946, RFC 2119), terms | 1 day |
| `CHANGES.md` (wording deltas), `spec-issues.md` (SI-1..15 + anything found while drafting), gaps list mapping each requirement to GPQ/GDAL/corpus or "no test" | 0.5 day |
| SWG review iterations (maintainers named in the brief), OGC staff editorial pass (URIs registered with OGC-NA, template compliance) | 2–4 weeks calendar; ~1 day of edits |
| Optional but likely requested by OAB: an executable test suite or at least fixtures for the gaps list (corpus additions: 8-element bbox, logical-type missing, crs mismatch, covering fixtures) | 1–2 days, in `geoparquet-testing`, outside this repo |

Drafting total: about 4 working days for one editor once decisions 1–3 are made; the calendar time
is dominated by review. If the target is 1.1, add roughly one day for the native-encoding class and
for reconciling GPQ's 1.0-only behaviour in the gaps list.

## Appendix A. Sources and revisions

See the "Sources audited" table in `crosswalk.md`. Local read-only branches created for the audit:
`pr-224-ogc-template` → `origin/ogc-template`, `pr-247-ogc-requirements-updates` →
`origin/ogc-requirements-updates`. Builds were run on copies under the session scratch directory;
no build artefacts are committed.
