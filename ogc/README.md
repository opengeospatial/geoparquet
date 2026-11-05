# GeoParquet OGC Standard (metanorma source)

**Status: draft proposal on the `ogc-spec-alignment` branch, for review by the GeoParquet
maintainers and the OGC GeoParquet SWG. Not final.**

This directory contains the OGC-formatted version of the GeoParquet specification, written in
AsciiDoc for [Metanorma](https://www.metanorma.org/author/ogc/) with the OGC Standard template.
It restates the community specification for **GeoParquet 2.0.0**
([`../format-specs/geoparquet.md`](../format-specs/geoparquet.md) and
[`../format-specs/schema.json`](../format-specs/schema.json)) as OGC requirements with
identifiers and abstract tests. It does not change the community specification; where the two
texts differ in wording, [`../docs/ogc/CHANGES.md`](../docs/ogc/CHANGES.md) explains every
difference so reviewers can check that the meaning is the same.

The community specification is the reference for the GeoParquet community releases. The OGC
document follows it and will lag behind it; it is what the SWG submits to the OGC Architecture
Board and to the OGC membership for a vote.

## Layout

| Path | Content |
| --- | --- |
| `document.adoc` | Entry file: document attributes (number, edition, editors, status) and the list of included sections. |
| `sections/clause_0_front_material.adoc` … `clause_5_conventions.adoc` | Preface, abstract, submitters, scope, conformance, normative references, terms, conventions. |
| `sections/clause_6_core.adoc` | Requirements Class **Core**: prose from `geoparquet.md` with the requirement, recommendation and permission blocks included at the point where the markdown states them. |
| `sections/clause_7_covering.adoc` | Requirements Class **Bounding Box Covering** (the `covering` member and bounding box columns), from PR #302 as merged on 2026-09-07. |
| `sections/clause_8_distribution.adoc` | Requirements Class **Cloud-Optimized Distribution** (proposal): the distribution best practices as an optional class that other specifications can cite. Two requirements (geospatial statistics, spatial ordering) and six recommendations (row group size, ZSTD, bbox covering, declared bbox column, partitioning, STAC). Sourced from the Portolan specification; numbers to be confirmed. |
| `sections/clause_9_implementation_considerations.adoc` | Informative: expectations on readers, version compatibility, GeoParquet 1.x, OGC:CRS84 details. |
| `sections/annex-a.adoc` | Abstract Test Suite (normative), includes `abstract_tests/ATS_class_*.adoc`. |
| `sections/annex-b-example.adoc`, `annex-history.adoc`, `annex-bibliography.adoc` | Example metadata, revision history, bibliography. |
| `requirements/requirements_class_core.adoc`, `requirements_class_covering.adoc`, `requirements_class_distribution.adoc` | The three requirements classes, listing their requirements, recommendations and permissions. |
| `requirements/<class>/req_<name>.adoc` | One file per requirement, identifier `/req/<class>/<name>`. Each starts with a `// Source:` comment pointing at the line of `geoparquet.md` it restates. |
| `recommendations/<class>/rec_<name>.adoc`, `permissions/<class>/per_<name>.adoc` | One file per recommendation (`/rec/...`) and permission (`/per/...`). |
| `abstract_tests/ATS_class_<class>.adoc`, `abstract_tests/<class>/ats_<name>.adoc` | One conformance class per requirements class; one abstract test per requirement, identifier `/conf/<class>/<name>`, targeting `/req/<class>/<name>`. Each test ends with a NOTE naming the `geoparquet-io` check that implements it. |
| `Gemfile` | For a local (non-Docker) Metanorma installation. |

Identifiers are relative to `http://www.opengis.net/spec/geoparquet/2.0`.

## Building

With Docker (recommended; this is what CI runs):

```sh
cd ogc
docker run --rm -v "$PWD":/metanorma metanorma/metanorma \
  metanorma compile --agree-to-terms -t ogc -x xml,html document.adoc
```

This produces `document.html`, `document.xml`, `document.presentation.xml` and an error report
`document.err.html` (all git-ignored). Add `pdf` to `-x` for a PDF; the first PDF build downloads
fonts and takes several minutes. Network access is needed for Metanorma to fetch the OGC, ISO and
IETF references through Relaton.

With a local Ruby installation: `bundle install` then
`metanorma compile --agree-to-terms -t ogc -x xml,html document.adoc`.

CI: `.github/workflows/ogc-document.yml` builds the document on every push and pull request that
touches `ogc/**`, fails on Metanorma errors (severity 0 and 1 in `document.err.html`), and
uploads the HTML, XML and error report as a workflow artifact.

## Editing conventions

* One normative statement of `geoparquet.md` maps to exactly one requirement, recommendation or
  permission here, and every requirement has exactly one abstract test. Keep this one-to-one
  mapping when the community specification changes.
* Requirements use SHALL; the community specification uses MUST. Do not paraphrase beyond what
  is needed to make a statement testable; record any wording change in `docs/ogc/CHANGES.md`.
* Do not fix problems of the community specification here. Record them in
  `docs/ogc/spec-issues.md` and raise them as issues against `format-specs/`.
* Requirements that no existing validator (GPQ, GDAL `validate_geoparquet.py`,
  `geoparquet-testing`) checks are listed in `docs/ogc/gaps.md`.
* The authoring guide for OGC documents in Metanorma is at
  https://www.metanorma.org/author/ogc/authoring-guide/.

## Provenance

The 1.0 version of this document was migrated to the OGC template by Gobe Hobona (OGC) in
PR #206 / #224, with contributions from Matthias Mohr and Chris Holmes, and partially updated
by Chris Holmes in PR #247. Those branches are merged into this one; the present files are a
rewrite for GeoParquet 2.0 on top of that work. The Phase 1 audit of the earlier drafts is in
[`../docs/ogc/AUDIT.md`](../docs/ogc/AUDIT.md) and the statement-by-statement crosswalk in
[`../docs/ogc/crosswalk.md`](../docs/ogc/crosswalk.md).
