# GeoParquet

## About

This repository defines how to store geospatial [vector data](https://gisgeography.com/spatial-data-types-vector-raster/) (point,
lines, polygons) in [Apache Parquet](https://parquet.apache.org/), a popular columnar storage format for tabular data - see
[this vendor explanation](https://databricks.com/glossary/what-is-parquet) for more on what that means. Our goal is to standardize how
geospatial data is represented in Parquet to further geospatial interoperability among tools using Parquet today, and hopefully
help push forward what's possible with 'cloud-native geospatial' workflows.

**Warning:** This is not (yet) a stable specification that can be relied upon. All 0.X releases are made to gather wider feedback, and we anticipate that some things may change. For now we reserve the right to make changes in backwards incompatible
ways (though will try not to), see the [versioning](#versioning) section below for more info. If you are excited about the potential
please collaborate with us by building implementations, sounding in on the issues and contributing PR's!

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
* **Enable spatial indices** - To enable top performance a spatial index is essential. This will be the focus of a future release.

It should be noted what GeoParquet is less good for. The biggest one is that it is not a good choice for write-heavy interactions. A row-based format
will work much better if it is backing a system that is constantly updating the data and adding new data.

## Roadmap

Our aim is to get to a 1.0.0 within 'months', not years. The rough plan is:

* 0.1 - Get the basics established, provide a target for implementations to start building against.
* 0.2 / 0.3 - Feedback from implementations, 3D coordinates support, geometry types, crs optional.
* 0.x - Several iterations based on feedback from implementations, spatial index best practices.
* 1.0.0-RC.1 - Aim for this when there are at least 6 implementations that all work interoperably and all feel good about the spec.
* 1.0.0 - Once there are 12(?) implementations in diverse languages we will lock in for 1.0

Our detailed roadmap is in the [Milestones](https://github.com/opengeospatial/geoparquet/milestones) and we'll aim to keep it up to date.


## Versioning

After we reach version 1.0 we will follow [SemVer](https://semver.org/), so at that point any breaking change will require the spec to go to 2.0.0.
Currently implementors should expect breaking changes, though at some point, hopefully relatively soon (0.4?), we will declare that we don't *think* there
will be any more potential breaking changes. Though the full commitment to that won't be made until 1.0.0.

## Current Implementations & Examples

Examples of GeoParquet files following the current spec can be found in the [examples/](examples/) folder. There is also a
larger sample dataset [nz-building-outlines.parquet](https://storage.googleapis.com/open-geodata/linz-examples/nz-building-outlines.parquet)
available on Google Cloud Storage.

Currently known libraries that can read and write GeoParquet files:

* [GeoPandas](https://geopandas.org/en/stable/docs/user_guide/io.html#apache-parquet-and-feather-file-formats) (Python)
* [geoarrow](https://github.com/paleolimbot/geoarrow) (R)
* [sfarrow](https://wcjochem.github.io/sfarrow/index.html) (R)
* [GDAL/OGR](https://gdal.org/drivers/vector/parquet.html) (C++, bindings in several languages)
* [GeoParquet.jl](https://github.com/JuliaGeo/GeoParquet.jl) (Julia)
* [gpq](https://github.com/tschaub/gpq) (Go, CLI and WASM build for reading/writing GeoParquet)
* [Apache Sedona](https://sedona.apache.org/tutorial/sql/#load-geoparquet) (Scala, bindings in Python and R)
