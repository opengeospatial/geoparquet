# GeoParquet

## About

This repository defines how to store geospatial [vector data](https://gisgeography.com/spatial-data-types-vector-raster/) (point, lines, polygons) in 
[Parquet](https://parquet.apache.org/), a popular columnar storage format for tabular data. Our goal is to standardize how geospatial data is represented
in Parquet to further geospatial interoperability among tools using Parquet today, and hopefully help push forward what's possible with 
'cloud-native geospatial' workflows. 

**Warning:** This is a completely unreleased specification, with several outstanding updates to make. If you are excited about the potential 
please sound in on the issues and contribute PR's! But please do not start converting all your data to this format, as it will change 
(and possibly in a backwards incompatible way, see the [versioning](#versioning) section below.

Early contributors include developers from GeoPandas, GeoTrellis, OpenLayers, Voltron Data, Microsoft, Carto, Azavea, Planet & Unfolded. 
Anyone is welcome to join us, by building implementations, trying it out, giving feedback through issues and contributing to the spec via pull requests.

Note that version 0.1 only supports 2d geometries, as we are not supporting [EWKB](https://libgeos.org/specifications/wkb/#extended-wkb) or 
[ISO WKB](https://libgeos.org/specifications/wkb/#iso-wkb). We expect to expand WKB to support 3D in the future, if you have thoughts please 
sound in on #18 and/or follow along there.

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

A quick overview of what geoparquet supports (or at least plans to support

* **Support multiple spatial reference systems** - Many tools will use GeoParquet for high-performance analysis, so it's important to be able to use data in its
 native projection. But we do provide a clear default recommendation to better enable interoperability, giving a clear target for implementations that don't want to
 worry about projections.
* **Multiple geometry columns** - There is a default geometry column, but additional geometry columns can be included.
* **Work with both planar and spherical coordinates** - Most cloud data warehouses support spherical coordinates, and so GeoParquet aims to help persist those 
 and be clear about what is supported.
* **Support for data partitioning** - Parquet has a nice ability to partition data into different files for efficiency, and we aim to enable geospatial partitions.
* **Enable spatial indices** - To enable top performance a spatial index is essential. This will be the focus of the 
 [0.2](https://github.com/opengeospatial/geoparquet/milestone/2) release.

## Roadmap

Our aim is to get to a 1.0.0 within 'months', not years. The rough plan is:

* 0.1 - Get the basics established, provide a target for implementations to start building against.
* 0.2 - Feedback from implementations, add spatial index and potentially 3D coordinates.
* 0.x - Several iterations based on feedback from implementations.
* 1.0.0-RC.1 - Aim for this when there are at least 6 implementations that all work interoperably and all feel good about the spec.
* 1.0.0 - Once there are 12(?) implementations in diverse languages we will lock in for 1.0

Our detailed roadmap is in the [Milestones](https://github.com/opengeospatial/geoparquet/milestones) and we'll aim to keep it up to date.


## Versioning

After we reach version 1.0 we will follow [SemVer](https://semver.org/), so at that point any breaking change will require the spec to go to 2.0.0.
Currently implementors should expect breaking changes, though at some point, hopefully relatively soon (0.3?), we will declare that we don't *think* there
will be any more potential breaking changes. Though the full commitment to that won't be made until 1.0.0. 

## Current Implementations & Examples

TODO: Add explanations and links to implementations.

Examples of geoparquet files following the current spec can be found in the [examples/](examples/) folder.



