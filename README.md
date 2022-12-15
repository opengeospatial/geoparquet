# GeoParquet

## About

This repository defines a [specification](https://geoparquet.org/releases/v1.0.0-beta.1/) for how to store geospatial [vector data](https://gisgeography.com/spatial-data-types-vector-raster/) (point, lines, polygons) in [Apache Parquet](https://parquet.apache.org/), a popular columnar storage format for tabular data - see [this vendor explanation](https://databricks.com/glossary/what-is-parquet) for more on what that means. Our goal is to standardize how geospatial data is represented in Parquet to further geospatial interoperability among tools using Parquet today, and hopefully help push forward what's possible with 'cloud-native geospatial' workflows. Learn more at [geoparquet.org](https://geoparquet.org)

**Warning:** This specification is currently in 1.0 'beta' releases, which means we don't anticipate anything major will change, but still reserve the right to make changes in backwards incompatible ways. See the [versioning](#versioning) section below for more info. If you are excited about the potential please collaborate with us by building implementations, sounding in on the issues and contributing PR's! Note that the specification in this repository is in flux, we recommend using the [latest published release](https://geoparquet.org/releases/).

Early contributors include developers from GeoPandas, GeoTrellis, OpenLayers, Vis.gl, Voltron Data, Microsoft, Carto, Azavea, Planet & Unfolded.
Anyone is welcome to join us, by building implementations, trying it out, giving feedback through issues and contributing to the spec via pull requests.
Initial work started in the [geo-arrow-spec](https://github.com/geopandas/geo-arrow-spec/) GeoPandas repository, and that will continue on
Arrow work in a compatible way, with this specification focused solely on Parquet.

- [**Specification**](format-specs/geoparquet.md)
- [JSON Schema](format-specs/schema.json)
- [Examples](examples/)
- [Validator](validator/)

## Goals

There are a few core goals driving the initial development.

* **Establish a great geospatial format for workflows that excel with columnar data** - Most data science and 'business intelligence' workflows have been moving
 towards columnar data, but current geospatial formats can not be as efficiently loaded as other data. So we aim to bring geospatial data best practices to one
 of the most popular formats, and hopefully establish a good pattern for how to do so.
* **Introduce columnar data formats to the geospatial world** - And most of the geospatial world is not yet benefitting from all the breakthroughs in data analysis
 in the broader IT world, so we are excited to enable interesting geospatial analysis with a wider range of tools.
* **Enable interoperability among cloud data warehouses** - BigQuery, Snowflake, Redshift and others all support spatial operations but importing and exporting data
 with existing formats can be problematic. All support and often recommend Parquet, so defining a solid GeoParquet can help enable interoperability.
* **Persist geospatial data from Apache Arrow** - GeoParquet is developed in parallel with a [GeoArrow spec](https://github.com/geopandas/geo-arrow-spec), to
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

## Roadmap

Our aim is to get to a 1.0.0 in the next few months. The next steps are to push towards our 1.0.0 acceptance criteria, articulated in this [discussion post], which mostly involves getting great validation tools, more software implementations, and more data providers. This should provide key feedback to feel confident in going to 1.0. The goal of 1.0.0 is to establish a baseline of interoperability for geospatial information in Parquet. We've got some exciting plans to go beyond that, which we'll articulate soon on the website.

## Versioning

After we reach version 1.0 we will follow [SemVer](https://semver.org/), so at that point any breaking change will require the spec to go to 2.0.0.
Currently implementors should expect breaking changes, though at some point, hopefully relatively soon (0.4?), we will declare that we don't *think* there
will be any more potential breaking changes. Though the full commitment to that won't be made until 1.0.0.

## Current Implementations & Examples

Examples of GeoParquet files following the current spec can be found in the [examples/](examples/) folder. For information on all the tools and libraries implementing GeoParquet, as well as sample data, see the [implementations section](https://geoparquet.org/#implementations) of the website.
