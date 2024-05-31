# GeoParquet Standard

The GeoParquet specification is detailed in this directory. For the clearest explanation of what is in the standard see [`geoparquet.md`](geoparquet.md). It is the 'latest' version of the specification, and you can see its version in the [Version and Schema](geoparquet.md#version-and-schema) section of the document. If it has `-dev` in the suffix then it is an unreleased version of the standard. For the stable versions view the `geoparquet.md` file in the git tree tagged in  [the releases](https://github.com/opengeospatial/geoparquet/releases), for example [v1.0.0/format-specs/geoparquet.md](https://github.com/opengeospatial/geoparquet/blob/v1.0.0/format-specs/geoparquet.md)

The official OGC standard will often lag behind the markdown document, and the target version can be found in the Preface of the [front material document](sections/clause_0_front_material.adoc). The OGC standard is built from the various other documents in this directory. They are `.adoc` files, in the [asciidoc](https://asciidoc.org/) format. They all automatically get built into a single pdf and published at [docs.ogc.org/DRAFTS/24-013.html](https://docs.ogc.org/DRAFTS/24-013.html) by a cron job running on OGC's infrastructure. The 'official' OGC version will be proposed from that draft, and when accepted by the OGC Technical Committee (TC) will become the official 1.0.0 version of the specification.

[Released versions](https://github.com/opengeospatial/geoparquet/releases) of GeoParquet (from the markdown file in this repository) will not be changed when OGC officially releases GeoParquet 1.0.0, so if changes are needed for OGC approval, then the  will be released with a new version number. There will continue to be releases from this repository, which will technically remain 'draft' standards until the OGC TC has officially accepted the next version.

## In this directory

* [`geoparquet.md`](geoparquet.md) - The latest specification overview, which may run ahead of the standard.
* [`document.adoc`](document.adoc) - The main standard document which sets the order of the other sections.
* [sections/](sections/) - Each section of the standard document is a separate document in this folder.
* `figures` - figures go here
* `images` - Image files for graphics go here. Image files for figures go in the `figures` directory. Only place in here images not used in figures (e.g., as parts of tables, as logos, etc.)
* `requirements` - directory for requirements and requirement classes to be referenced in `clause_7_normative_text.adoc`
* `code` - sample code to accompany the standard, if desired
* `abstract_tests` - the Abstract Test Suite comprising one test for every requirement, optional
* `UML` - UML diagrams, if applicable

More information about the document template is https://github.com/opengeospatial/templates/tree/master/standard#readme[here].

An authoring guide is available at https://www.metanorma.org/author/ogc/authoring-guide/[metanorma.org].

== Authoring the Specification

== Building

Run `docker run -v "$(pwd)":/metanorma -v ${HOME}/.fontist/fonts/:/config/fonts  metanorma/metanorma  metanorma compile --agree-to-terms -t ogc -x html document.adoc`.

== Auto built document

A daily built document is available at https://docs.ogc.org/DRAFTS/[OGC Document DRAFTS].
