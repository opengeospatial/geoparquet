# Changelog

This changelog tracks the meaningful changes in each GeoParquet release — the things an
implementor needs to know when moving between versions. For the complete list of every change see
the [GitHub releases](https://github.com/opengeospatial/geoparquet/releases).

## 2.0.0 (2026-07-19, pending final OGC approval)

GeoParquet 2.0 re-centers the specification on the
[Parquet Geospatial Logical Types](https://github.com/apache/parquet-format/blob/master/Geospatial.md)
that became part of the core Parquet format in version 2.11 (March 2025). Where GeoParquet 1.x
layered geospatial metadata on top of plain binary columns, 2.0 makes the native Parquet `GEOMETRY`
and `GEOGRAPHY` types the foundation: the geometry column is typed by the format itself, the CRS
travels on the column, and per–row-group geospatial statistics enable efficient spatial filtering
with no extra columns. The GeoParquet `geo` metadata remains as a layer on top, providing things
Parquet core doesn't — like a guaranteed inline CRS definition and polygon winding order.

The overall goal of 2.0 is to align the geospatial world with mainstream Parquet tooling: any
Parquet file that uses the native geospatial types is compatible with the GeoParquet 2.0 ecosystem,
whether or not it carries GeoParquet metadata. See the
[Parquet Geospatial Compatibility guide](format-specs/compatible-parquet.md) for how the pieces fit
together.

### Changes from 1.1

* Geometry columns must be stored with the native Parquet `GEOMETRY`/`GEOGRAPHY` logical types (still WKB-encoded) instead of plain `BYTE_ARRAY` [#278](https://github.com/opengeospatial/geoparquet/pull/278)
* The GeoArrow-based native encodings introduced in 1.1 were removed — `"WKB"` is again the only `encoding` value [#278](https://github.com/opengeospatial/geoparquet/pull/278)
* New `edges` values `vincenty`, `thomas`, `andoyer` and `karney`, matching the edge interpolation algorithms of the Parquet `GEOGRAPHY` type [#278](https://github.com/opengeospatial/geoparquet/pull/278)
* The CRS now lives on the Parquet logical type's `crs` property as the source of truth, in any Parquet-core form (inline PROJJSON or `<authority>:<code>` recommended); the GeoParquet metadata `crs` restates it as guaranteed inline PROJJSON (or `null`) [#286](https://github.com/opengeospatial/geoparquet/pull/286)
* `srid:0` on the Parquet `crs` property denotes an undefined or unknown CRS, matching `crs: null` in the GeoParquet metadata [#286](https://github.com/opengeospatial/geoparquet/pull/286)
* Readers must accept files that carry only the native Parquet geospatial types, with no GeoParquet metadata [#286](https://github.com/opengeospatial/geoparquet/pull/286)
* The 1.1 `bbox` covering remains available as an option, but most files no longer need it — the native types' row-group statistics provide spatial filtering built in [#302](https://github.com/opengeospatial/geoparquet/pull/302)
* New best-practices guides for [distributing GeoParquet](format-specs/distributing-geoparquet.md) and the [tools to do it with](format-specs/distributing-geoparquet-tools.md) [#254](https://github.com/opengeospatial/geoparquet/pull/254), [#288](https://github.com/opengeospatial/geoparquet/pull/288)
* Example files updated to GeoParquet 2.0 output [#280](https://github.com/opengeospatial/geoparquet/pull/280)

## 1.1.0 (2024-06-19)

The second stable release, fully backwards compatible with 1.0. Its two major additions were both
aimed at making spatial queries faster by leveraging more of Parquet's native capabilities: a
per-row bounding box column that works with the existing WKB encoding, and an alternative
GeoArrow-based encoding that exposes coordinates directly to Parquet's statistics. Both were
optional; in practice the bbox covering saw wide adoption, and in GeoParquet 2.0 the native Parquet
geospatial types took over the role the GeoArrow encodings were exploring.

### Changes from 1.0

* Added the `bbox` covering: an optional per-row bounding box struct column, declared in metadata, that lets readers prune row groups and pages using standard Parquet statistics [#191](https://github.com/opengeospatial/geoparquet/pull/191)
* Added optional GeoArrow-based native encodings (`point`, `linestring`, etc.) as an alternative to WKB [#189](https://github.com/opengeospatial/geoparquet/pull/189)
* Defined the version compatibility policy for future releases [#229](https://github.com/opengeospatial/geoparquet/pull/229)
* Clarified that a `null` `crs` (unknown CRS) is distinct from an absent one (OGC:CRS84 default) [#225](https://github.com/opengeospatial/geoparquet/pull/225)
* Recommended `.parquet` as the file extension [#212](https://github.com/opengeospatial/geoparquet/pull/212) and `application/vnd.apache.parquet` as the media type [#213](https://github.com/opengeospatial/geoparquet/pull/213)

## 1.0.0 (2023-09-18)

The first stable release of GeoParquet, establishing the core specification: geometry columns
stored as WKB in `BYTE_ARRAY` columns, identified by a `geo` metadata key holding file-level
metadata (spec version, primary geometry column) and per-column metadata — the CRS as inline
PROJJSON (defaulting to OGC:CRS84, with axis order always longitude/latitude), the geometry types
present, planar or spherical edges, polygon orientation, the column's bounding box, and the
coordinate epoch for dynamic CRS's. Multiple geometry columns are supported, with one designated
primary. The release also committed the specification to [SemVer](https://semver.org/) and added
the first version of the compatibility guide for geospatial data in plain Parquet.
