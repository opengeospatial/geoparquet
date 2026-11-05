# GeoParquet

## About

This repository defines a [specification](https://geoparquet.org/releases/) for how to store geospatial [vector data](https://gisgeography.com/spatial-data-types-vector-raster/) (point, lines, polygons) in [Apache Parquet](https://parquet.apache.org/), a popular columnar storage format for tabular data - see [this vendor explanation](https://databricks.com/glossary/what-is-parquet) for more on what that means. Our goal is to further standardize how geospatial data is represented in Parquet to enhance geospatial interoperability among tools using Parquet today, and hopefully help push forward what's possible with 'cloud-native geospatial' workflows. There are now more than 20 different tools and libraries in 7 different languages that support GeoParquet, you can learn more at [geoparquet.org](https://geoparquet.org).

Contributors include developers from GeoPandas, GeoTrellis, OpenLayers, Vis.gl, Voltron Data, Microsoft, CARTO, Planet & Unfolded.
Anyone is welcome to join the project, by building implementations, trying it out, giving feedback through issues and contributing to the spec via pull requests.
The [geoarrow](https://github.com/geoarrow/geoarrow) specification is related to GeoParquet and embraces geospatial in
Arrow in a compatible way, with this specification focused solely on Parquet. We are an [OGC](https://ogc.org) official
[Standards Working Group](https://www.ogc.org/standards-working-gr/geoparquet-swg-geoparquet-swg/) and are on the path to be an OGC standard.

**The latest [stable specification](https://geoparquet.org/releases/v2.0.0/) and [JSON schema](https://geoparquet.org/releases/v2.0.0/schema.json) are published at [geoparquet.org/releases/](https://geoparquet.org/releases/).**

**The community has agreed on this release, but it is still pending OGC approval.** We are currently working on the process to get it officially OGC approved as soon as possible by the OGC Membership. Released versions of GeoParquet will not be changed, so if changes are needed for OGC approval, it will be released with a new version number.

The 'dev' versions of the spec are available in this repo:

- [**Specification**](format-specs/geoparquet.md) (dev version - not stable, go to the [stable specification](https://geoparquet.org/releases/v2.0.0/) instead)
- [JSON Schema](format-specs/schema.json)
- [Examples](examples/)

The latest version is 2.0.0, which is based on [Parquet Geospatial Logical Types](https://github.com/apache/parquet-format/blob/master/Geospatial.md). The Parquet format now includes core `geometry` and `geography` types and the GeoParquet 2 specification provides guidance for geospatial tools for these types, along with some optional metadata not covered in the core Parquet specification.

## Validating GeoParquet

Several tools check a file against the specification, and it is worth running one over any GeoParquet you produce or are handed. The two most complete cover every released version of the spec — 1.0, 1.1 and 2.0:

* **[geoparquet-validator](https://github.com/geoparquet/geoparquet-validator)** - `geoparquet-validator check example.parquet` reports conformance by class (core, bbox covering, cloud-optimized distribution), with the 2.0 checks following the OGC abstract tests. It also runs in the browser at [validator.geoparquet.org](https://validator.geoparquet.org/), where files never leave your machine, and reads remote files with range requests. Installable for Python, Rust, Node (WebAssembly) and C, or as a standalone binary.
* **[geoparquet-io](https://geoparquet.io/guide/check/#spec-validation)** - `gpio check spec example.parquet` validates 1.0, 1.1 and 2.0, as well as plain Parquet files using the native geospatial types. It detects the version automatically, or you can pin it with `--geoparquet-version`. The broader `gpio check` also reports on the [distribution best practices](format-specs/distributing-geoparquet.md).

Two other validators are still in use:

* **[GDAL/OGR Validation Script](https://gdal.org/drivers/vector/parquet.html#validation-script)** - a Python script run with `python3 validate_geoparquet.py --check-data my_geo.parquet`. It checks the `geo` metadata against the published JSON Schema for whichever version the file declares, covering 1.0, 1.1 and 2.0.
* **[GPQ](https://github.com/planetlabs/gpq)** - `gpq validate example.parquet` generates a report. Its most recent release predates both the 1.1 GeoArrow encodings and the 2.0 native types, so treat its result as a check against 1.0: files with WKB geometry columns and 1.0-era metadata.

## Test Data for Implementations

[geoparquet-testing](https://github.com/geoparquet/geoparquet-testing) is the official test corpus for the format, modeled on Apache's [parquet-testing](https://github.com/apache/parquet-testing). If you maintain a GeoParquet reader or writer, running against it is the quickest way to find where your implementation disagrees with everyone else's. It targets 2.0.0, and every geometry column in it uses the native Parquet `GEOMETRY`/`GEOGRAPHY` logical type.

The files come in three tiers:

* **`data/`** - small conformance fixtures, each exercising one axis of the spec, so a failure points at a specific requirement.
* **`samples/`** - plausibly-real datasets that combine spec features at non-trivial scale.
* **`bad_data/`** - files that deliberately violate the spec, with a `manifest.json` giving the expected failure for each. A reader can walk the manifest, try to open every file and assert that it fails the way the manifest says, which tests error handling rather than just the happy path.

Each tier has a README indexing every file and what it tests. Most projects pull the corpus in as a git submodule, though tagged tarballs are published for those that would rather not. The fixtures are generated deterministically and CI enforces it, so a given tag is always the same bytes.

## Features

A quick overview of what GeoParquet supports.

* **Multiple spatial reference systems** - Many tools will use GeoParquet for high-performance analysis, so it's important to be able to use data in its
 native projection. But we do provide a clear default recommendation to better enable interoperability, giving a clear target for implementations that don't want to
 worry about projections.
* **Multiple geometry columns** - There is a default geometry column, but additional geometry columns can be included.
* **Great compression / small files** - Parquet is designed to compress very well, so data benefits by taking up less disk space & being more efficient over
 the network.
* **Work with both planar and spherical coordinates** - Most cloud data warehouses support spherical coordinates, and so GeoParquet aims to help persist those
 and be clear about what is supported.
* **Great at read-heavy analytic workflows** - Columnar formats enable cheap reading of a subset of columns, and Parquet in particular enables efficient filtering
 of chunks based on column statistics, so the format will perform well in a variety of modern analytic workflows.
* **Support for data partitioning** - Parquet has a nice ability to partition data into different files for efficiency, and we aim to enable geospatial partitions.

It should be noted what GeoParquet is less good for. The biggest one is that it is not a good choice for write-heavy interactions. A row-based format
will work much better if it is backing a system that is constantly updating the data and adding new data. For data that must be updated in place while
staying cloud-native, [Apache Iceberg](https://iceberg.apache.org/spec/#appendix-g-geospatial-notes) is a promising option: its v3 format adds native
`geometry` and `geography` types built on the same Parquet geospatial types that GeoParquet 2.0 uses, so a table can take appends, updates and deletes
while its underlying data files stay ordinary Parquet that the GeoParquet ecosystem can read.

## Versioning

As of version 1.0 the specification follows [Semantic Versioning](https://semver.org/), so at that point any breaking change will require the spec to go to the next major version number, e.g. 1.0.0 to 2.0.0.

## Current Implementations & Examples

Examples of GeoParquet files following the current spec can be found in the [examples/](examples/) folder. For information on all the tools and libraries implementing GeoParquet, as well as sample data, see the [implementations section](https://geoparquet.org/#implementations) of the website.
