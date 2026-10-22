# Draft PR description (for the chair to edit and paste)

Suggested title: **OGC Standard document for GeoParquet 2.0 (metanorma), aligned with the 2.0.0 release**

Suggested settings: open as a **draft**; base `main`; label `ogc`. Mention that it supersedes
#224 and #247 and ask the authors whether to close those once this is merged.

---

## Why

The OGC GeoParquet SWG needs an OGC-formatted version of the specification (metanorma, OGC
Standard template) to take to the OGC Architecture Board and to a membership vote. That work
stalled in December 2024 with #224 (@m-mohr, based on @ghobona's migration) and #247 (@cholmes),
both written for GeoParquet 1.0. With 2.0.0 about to be released, the SWG (with OGC staff)
agreed to target **2.0** directly: 1.x got the community to implement, 2.x is what implementers
should adopt, and it is far less likely to need another major revision. OGC membership will be
notified separately with a short note explaining this.

**This PR is not on the 2.0.0 release path and needs no action before the tag.** It changes
nothing under `format-specs/`.

## What is in the PR

Everything lives in a new `ogc/` directory plus `docs/ogc/`:

* `ogc/` — the metanorma document for GeoParquet **2.0.0**. Two requirements classes, both
  targeting the file:
  * **Core**: 20 requirements, 6 recommendations, 3 permissions;
  * **Bounding Box Covering**: 6 requirements, taken from the #302 text and marked conditional
    on that PR merging.
  * One abstract test per requirement (26). Every requirement file starts with a `// Source:`
    comment pointing at the line of `geoparquet.md` it restates.
  * Normative references pin Apache Parquet 2.12.0 (`LogicalTypes.md`, `Geospatial.md`) instead
    of restating the encoding.
  * The community spec's expectations on *readers* (interpret PROJJSON and authority:code
    `crs`, don't reject unknown fields, forward compatibility) are informative (Clause 8). The
    SWG chose a single standardization target, the file, to keep approval simple.
* `docs/ogc/CHANGES.md` — **start here if you review.** Every place where the OGC wording
  differs from `geoparquet.md`, with the reason. The intent is that the OGC text is purely
  derivative; where the markdown implies something without stating it, the OGC text has a NOTE,
  not a requirement.
* `docs/ogc/spec-issues.md` — things in the community spec that the drafting surfaced. Two are
  one-line edits worth making before the 2.0.0 tag (a Parquet link that points at a version
  without the text it cites; "spherical" vs "not planar" for the orientation recommendation).
  The rest are for after the release. Nothing was changed in `format-specs/`; I'll open issues
  for whichever of these the maintainers think are real.
* `docs/ogc/gaps.md` — for each abstract test, which existing validator (GPQ, GDAL
  `validate_geoparquet.py`, `geoparquet-testing`) covers it. Eight of the 26 tests have no
  implementation anywhere (four of them in the covering class); nine are fully covered.
* `docs/ogc/AUDIT.md`, `docs/ogc/crosswalk.md` — the audit of #224/#247 against 1.1 and 2.0
  that this work started from.
* `.github/workflows/ogc-document.yml` — builds the document with the `metanorma/metanorma`
  Docker image on pushes/PRs touching `ogc/**`; fails on metanorma errors or a requirement
  without a test; uploads the HTML. The old `docs.ogc.org/DRAFTS/24-013` cron build is gone
  (#277), so this replaces it.

The #224 and #247 branches are merged into this branch so the original authorship is preserved
in history; the files were then moved from `format-specs/` to `ogc/` and rewritten for 2.0.

## Questions for reviewers

1. **Editors and contributors.** `document.adoc` lists Chris Holmes, Tim Schaub, Joris Van den
   Bossche, Kyle Barron and Javier de la Torre as editors (carried over from #224). Who else
   should be there, and who should be in the Contributors table? @cholmes, your view first.
2. **Location.** `ogc/` rather than `format-specs/` (where #224 had it), so the community spec
   directory stays as it is and CI can be scoped. Happy to move it back.
3. **#302.** If the covering does not come back, Clause 7 and its conformance class are removed
   as a unit.
4. **Document number 24-013** was assigned for the 1.0 draft; I'll confirm with OGC staff that
   it carries over.
5. **CI.** The workflow pulls the metanorma image (~2 GB) on each run touching `ogc/`. Fine, or
   should it be manual-only?

## How to build locally

```sh
cd ogc
docker run --rm -v "$PWD":/metanorma metanorma/metanorma \
  metanorma compile --agree-to-terms -t ogc -x xml,html document.adoc
open document.html
```

Supersedes #224 and #247. Refs #277, #302.
