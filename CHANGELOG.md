# Changelog
All notable changes to this project will be documented in this file.

It is mostly auto-generated from GitHub's release notes.

# [v0.2.0] - 2022-04-19

## What's Changed
* Add Apache license by @cholmes in https://github.com/opengeospatial/geoparquet/pull/38
* Expand WKB encoding to ISO WKB to support 3D geometries by @jorisvandenbossche in https://github.com/opengeospatial/geoparquet/pull/45
* CRS field is now optional (with default to OGC:CRS84) by @alasarr in https://github.com/opengeospatial/geoparquet/pull/60
* Add a "geometry_type" field per column by @jorisvandenbossche in https://github.com/opengeospatial/geoparquet/pull/51
* Add "epoch" field to optionally specify the coordinate epoch for a dynamic CRS by @jorisvandenbossche in https://github.com/opengeospatial/geoparquet/pull/49
* Add section on winding order by @felixpalmer in https://github.com/opengeospatial/geoparquet/pull/59
* Add validator script for Python based on JSON Schema by @Jesus89 in https://github.com/opengeospatial/geoparquet/pull/58
* Script to store JSON copy of metadata next to example Parquet files by @kylebarron in https://github.com/opengeospatial/geoparquet/pull/68
* Readme enhancements by @jzb in https://github.com/opengeospatial/geoparquet/pull/53
* geoparquet.md: refer to OGC spec for WKB instead of ISO by @rouault in https://github.com/opengeospatial/geoparquet/pull/54
* Update validator with the latest spec changes by @Jesus89 https://github.com/opengeospatial/geoparquet/pull/70

## New Contributors
* @cayetanobv made their first contribution in https://github.com/opengeospatial/geoparquet/pull/57
* @rouault made their first contribution in https://github.com/opengeospatial/geoparquet/pull/54
* @jzb made their first contribution in https://github.com/opengeospatial/geoparquet/pull/53
* @felixpalmer made their first contribution in https://github.com/opengeospatial/geoparquet/pull/59

**Full Changelog**: https://github.com/opengeospatial/geoparquet/compare/v0.1.0...v0.2.0

# [v0.1.0] - 2022-03-08

## What's Changed
* Update geoparquet spec by @TomAugspurger in https://github.com/opengeospatial/geoparquet/pull/2
* Attempt to align with geoarrow spec by @cholmes in https://github.com/opengeospatial/geoparquet/pull/4
* Align "geo" key in metadata and example by @jorisvandenbossche in https://github.com/opengeospatial/geoparquet/pull/5
* Clarify the Parquet FileMetadata value formatting (UTF8 string, JSON-encoded) by @jorisvandenbossche in https://github.com/opengeospatial/geoparquet/pull/6
* Clarify that WKB means "standard" WKB enconding by @TomAugspurger in https://github.com/opengeospatial/geoparquet/pull/16
* More explicitly mention the metadata is stored in the parquet FileMetaData by @jorisvandenbossche in https://github.com/opengeospatial/geoparquet/pull/20
* Readme enhancements by @cholmes in https://github.com/opengeospatial/geoparquet/pull/19
* Optional column metadata field to store bounding box information by @jorisvandenbossche in https://github.com/opengeospatial/geoparquet/pull/21
* Clarify that additional top-level fields in the JSON metadata are allowed by @jorisvandenbossche in https://github.com/opengeospatial/geoparquet/pull/28
* CRS spec definition for version 0.1 by @alasarr in https://github.com/opengeospatial/geoparquet/pull/25
* Update example parquet file by @TomAugspurger in https://github.com/opengeospatial/geoparquet/pull/24
* Clean up TODOs in geoparquet.md by @TomAugspurger in https://github.com/opengeospatial/geoparquet/pull/31
* "edges" field spec definition for version 0.1 by @Jesus89 in https://github.com/opengeospatial/geoparquet/pull/27
* Add known libraries that support GeoParquet to README by @jorisvandenbossche in https://github.com/opengeospatial/geoparquet/pull/29
* Updated warning in readme by @cholmes in https://github.com/opengeospatial/geoparquet/pull/33

## New Contributors
* @TomAugspurger made their first contribution in https://github.com/opengeospatial/geoparquet/pull/2
* @cholmes made their first contribution in https://github.com/opengeospatial/geoparquet/pull/4
* @jorisvandenbossche made their first contribution in https://github.com/opengeospatial/geoparquet/pull/5
* @alasarr made their first contribution in https://github.com/opengeospatial/geoparquet/pull/25
* @Jesus89 made their first contribution in https://github.com/opengeospatial/geoparquet/pull/27

**Full Changelog**: https://github.com/opengeospatial/geoparquet/commits/v0.1.0