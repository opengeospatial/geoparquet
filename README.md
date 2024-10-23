# GeoParquet

## About

This repository defines a [specification](https://geoparquet.org/releases/) for how to store geospatial [vector data](https://gisgeography.com/spatial-data-types-vector-raster/) (point, lines, polygons) in [Apache Parquet](https://parquet.apache.org/), a popular columnar storage format for tabular data - see [this vendor explanation](https://databricks.com/glossary/what-is-parquet) for more on what that means. Our goal is to standardize how geospatial data is represented in Parquet to further geospatial interoperability among tools using Parquet today, and hopefully help push forward what's possible with 'cloud-native geospatial' workflows. There are now more than 20 different tools and libraries in 6 different languages that support GeoParquet, you can learn more at [geoparquet.org](https://geoparquet.org).

Early contributors include developers from GeoPandas, GeoTrellis, OpenLayers, Vis.gl, Voltron Data, Microsoft, CARTO, Azavea, Planet & Unfolded.
Anyone is welcome to join the project, by building implementations, trying it out, giving feedback through issues and contributing to the spec via pull requests.
Initial work started in the [geo-arrow-spec](https://github.com/geoarrow/geoarrow) GeoPandas repository, and that will continue on
Arrow work in a compatible way, with this specification focused solely on Parquet. We are in the process of becoming an [OGC](https://ogc.org) official
[Standards Working Group](https://portal.ogc.org/files/103450) and are on the path to be a full OGC standard.

**The latest [stable specification](https://geoparquet.org/releases/v1.1.0/) and [JSON schema](https://geoparquet.org/releases/v1.1.0/schema.json) are published at [geoparquet.org/releases/](https://geoparquet.org/releases/).**

**The community has agreed on this release, but it is still pending OGC approval.** We are currently working on the process to get it officially OGC approved as soon as possible. The OGC candidate Standard is at [https://docs.ogc.org/DRAFTS/24-013.html](https://docs.ogc.org/DRAFTS/24-013.html). The candidate Standard remains in draft form until it is approved as a Standard by the OGC Membership. Released versions of GeoParquet will not be changed, so if changes are needed for OGC approval, it will be released with a new version number.

The 'dev' versions of the spec are available in this repo:

- [**Specification**](format-specs/geoparquet.md) (dev version - not stable, go to the [stable specification](https://geoparquet.org/releases/v1.1.0/) instead)
- [JSON Schema](format-specs/schema.json)
- [Examples](examples/)

## Validating GeoParquet

There are two tools that validate the metadata and the actual data. It is recommended to use one of them to ensure any GeoParquet you produce or are given is completely valid according to the specification:

* **[GPQ](https://github.com/planetlabs/gpq)** - the `validate` command generates a report with `gpq validate example.parquet`.
* **[GDAL/OGR Validation Script](https://gdal.org/drivers/vector/parquet.html#validation-script)** - a Python script that can check compliance with `python3 validate_geoparquet.py --check-data my_geo.parquet`

## Goals

There are a few core goals driving the initial development.

* **Establish a great geospatial format for workflows that excel with columnar data** - Most data science and 'business intelligence' workflows have been moving
 towards columnar data, but current geospatial formats can not be as efficiently loaded as other data. So we aim to bring geospatial data best practices to one
 of the most popular formats, and hopefully establish a good pattern for how to do so.
* **Introduce columnar data formats to the geospatial world** - And most of the geospatial world is not yet benefitting from all the breakthroughs in data analysis
 in the broader IT world, so we are excited to enable interesting geospatial analysis with a wider range of tools.
* **Enable interoperability among cloud data warehouses** - BigQuery, Snowflake, Redshift and others all support spatial operations but importing and exporting data
 with existing formats can be problematic. All support and often recommend Parquet, so defining a solid GeoParquet can help enable interoperability.
* **Persist geospatial data from Apache Arrow** - GeoParquet is developed in parallel with a [GeoArrow spec](https://github.com/geoarrow/geoarrow), to
 enable cross-language in-memory analytics of geospatial information with Arrow. Parquet is already well-supported by Arrow as the key on disk persistance format.

And our broader goal is to innovate with 'cloud-native vector' providing a stable base to try out new ideas for cloud-native & streaming workflows.

## Features

A quick overview of what GeoParquet supports (or at least plans to support).

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
will work much better if it is backing a system that is constantly updating the data and adding new data.

## Versioning

As of version 1.0 the specification follows [Semantic Versioning](https://semver.org/), so at that point any breaking change will require the spec to go to 2.0.0.

## Current Implementations & Examples

Examples of GeoParquet files following the current spec can be found in the [examples/](examples/) folder. For information on all the tools and libraries implementing GeoParquet, as well as sample data, see the [implementations section](https://geoparquet.org/#implementations) of the website.
