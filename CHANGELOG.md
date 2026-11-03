# Changelog

This changelog records the changes in each release, focused on the key things implementors need
to know when moving to a new version. For the complete list of every change see
the [GitHub releases](https://github.com/opengeospatial/geoparquet/releases).

## 2.0.0 (2026-11-05)

GeoParquet 2.0 re-centers the specification on the
[Parquet Geospatial Logical Types](https://github.com/apache/parquet-format/blob/master/Geospatial.md)
that became part of the core Parquet format in version 2.11 (March 2025). Where GeoParquet 1.x
layered geospatial metadata on top of plain binary columns, 2.0 makes the native Parquet `GEOMETRY`
and `GEOGRAPHY` types the foundation: the geometry column is typed by the format itself, the CRS
travels on the column, and per–row-group geospatial statistics enable efficient spatial filtering
with no extra columns. The GeoParquet `geo` metadata remains for tool compatibility, and it provides some small things
beyond what the Parquet core does, including a guaranteed inline CRS definition, polygon winding
order, epoch and the primary geometry column.

The overall goal of 2.0 is to align the geospatial world with mainstream Parquet tooling: any tool
that writes the native Parquet geospatial types correctly produces a file the GeoParquet 2.0
ecosystem can read, whether or not it carries GeoParquet metadata, and the spec supplies that
metadata in the same way previous GeoParquet versions did. See the
[Parquet Geospatial Compatibility guide](format-specs/compatible-parquet.md) for how the pieces fit
together.

### Native Parquet geospatial types ([#278](https://github.com/opengeospatial/geoparquet/pull/278))

Geometry columns must be stored with the native Parquet `GEOMETRY` or `GEOGRAPHY` logical types —
still WKB-encoded underneath — rather than the plain `BYTE_ARRAY` columns of 1.x, and the
GeoParquet metadata must agree with what the Parquet-level metadata says.

* The GeoArrow-based native encodings introduced in 1.1 were removed, so `"WKB"` is once again the
  only `encoding` value. They were added to let Parquet's own statistics see coordinates directly,
  which is exactly what the native types now do, so a second encoding was no longer worth the
  implementation cost to writers and readers.
* New `edges` values `vincenty`, `thomas`, `andoyer` and `karney`, aligning with the `algorithm`
  field of the Parquet `GEOGRAPHY` type for non-planar edge interpolation.

### Spatial filtering and the `bbox` covering ([#302](https://github.com/opengeospatial/geoparquet/pull/302))

The native types carry geospatial statistics for every row group, which is most of what the 1.1
`bbox` covering column was introduced to provide: readers can skip row groups that do not intersect
a query without reading any extra column, and files — point data especially — get smaller.

The covering was therefore removed in the 2.0 drafts, then brought back as an option before the
final release. It is still worth adding when you want page-level pruning within a row group, or
when you need the file to remain usable by 1.1 readers. See
[when to add a bbox covering column](format-specs/distributing-geoparquet.md#when-to-add-a-bbox-covering-column)
for the tradeoff.

### CRS handling ([#286](https://github.com/opengeospatial/geoparquet/pull/286))

2.0 cleanly separates the two places a CRS can now live:

* The **native Parquet `crs` property** is the source of truth, and may use any Parquet-core form:
  inline PROJJSON, `<authority>:<code>`, `srid:<identifier>` or `projjson:<key_name>`. Writers that
  cannot readily generate PROJJSON (pure-SQL pipelines, lightweight browser-side writers) are
  encouraged to write plain native Parquet with an `<authority>:<code>` CRS.
* The **GeoParquet `geo` metadata `crs`** must be inline PROJJSON (or `null`), so a reader can
  always obtain a complete CRS definition without resolving an authority code against an external
  registry. The two must not describe different coordinate reference systems.
* `crs: null` for an unknown or undefined CRS is kept for 1.x compatibility, and maps to `srid:0`
  on the Parquet side, following the GeoPackage convention.
* Readers must accept files that carry only the native Parquet geospatial types, with no GeoParquet
  metadata at all.

### Distribution best practices ([#254](https://github.com/opengeospatial/geoparquet/pull/254), [#281](https://github.com/opengeospatial/geoparquet/pull/281), [#288](https://github.com/opengeospatial/geoparquet/pull/288))

A new best-practices guide for creating and distributing good GeoParquet files, introduced in
[#254](https://github.com/opengeospatial/geoparquet/pull/254) and expanded with a section on
powering frontend and web applications ([#281](https://github.com/opengeospatial/geoparquet/pull/281)).
For 2.0 it was reworked and split in two ([#288](https://github.com/opengeospatial/geoparquet/pull/288)):
a focused [recommendations page](format-specs/distributing-geoparquet.md) covering spatial ordering,
zstd compression at level 15+, row-group sizing and efficient spatial access via native statistics,
and a companion [tools guide](format-specs/distributing-geoparquet-tools.md) with verified how-tos
for GDAL/OGR, DuckDB, geoparquet-io and Sedona — including how to get native 2.0 output from each.

### Other changes

* Example files updated to GeoParquet 2.0 output [#280](https://github.com/opengeospatial/geoparquet/pull/280)
* The [Parquet Geospatial Compatibility guide](format-specs/compatible-parquet.md) was rewritten for 2.0 [#306](https://github.com/opengeospatial/geoparquet/pull/306)

## 1.1.0 (2024-06-19)

The second stable release, fully backwards compatible with 1.0. Its two major additions are both
aimed at making spatial queries faster by leveraging more of Parquet's native capabilities: a
per-row bounding box column that works with the existing WKB encoding, and an alternative
GeoArrow-based encoding that exposes coordinates directly to Parquet's statistics. Both are
completely optional, and only one is needed in practice — the bbox covering is easy to add to any
1.0-style file, while the GeoArrow encodings take more implementation work but are more aligned
with the Parquet way of doing things.

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
