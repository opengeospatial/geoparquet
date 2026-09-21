# Parquet Geospatial Compatibility

As of version 2.11 of the Parquet format, released in March 2025, Parquet itself defines native
[geospatial types and statistics](https://github.com/apache/parquet-format/blob/apache-parquet-format-2.12.0/Geospatial.md):
the `GEOMETRY` and `GEOGRAPHY` logical types. Any Parquet file that stores its geometries using these
types is completely compatible with the GeoParquet ecosystem. Every GeoParquet 2.0 reader is required
to read such files, whether or not they contain any GeoParquet metadata — see the
[reader rules](./geoparquet.md#crs-parquet-property) in the specification.

This means that if the tools you use write the native Parquet geospatial types, you generally do not
need to do anything more: there is no need to fully implement GeoParquet 2.0 to participate in the
ecosystem. Adding the full GeoParquet metadata on top is worthwhile in some situations, described
[below](#when-to-add-full-geoparquet-20-metadata).

Not every tool can write the native geospatial types yet, however. The types are relatively new, and
support has been rolling out across Parquet libraries and engines at different speeds. The
[compatibility guidelines](#compatibility-guidelines-for-tools-that-pre-date-the-parquet-geospatial-types)
in the second half of this document are for data producers who are stuck on a tool or library version
that pre-dates the Parquet geospatial types. They describe how to write plain Parquet files that
GeoParquet readers can still interpret correctly, so that data can flow into the ecosystem even from
older tools. See [when you need the compatibility guidelines](#when-you-need-the-compatibility-guidelines)
for the library versions where this applies.

## Native Parquet geospatial types

The foundation of GeoParquet 2.0 is simply using Parquet's native `GEOMETRY` or `GEOGRAPHY` logical
type for the geometry column. A writer that does this gets, with no additional effort:

* An unambiguous, self-describing declaration that the column contains geospatial data (no guessing
  from column names or sniffing binary blobs).
* The coordinate reference system carried on the column itself, via the logical type's `crs` property.
* [Geospatial statistics](https://github.com/apache/parquet-format/blob/apache-parquet-format-2.12.0/Geospatial.md#geospatial-statistics)
  — per-row-group bounding boxes and geometry type lists — that let readers efficiently skip data
  that does not match a spatial query.

If you are producing data this way, GeoParquet readers will read it. The one recommendation that goes
beyond what the core Parquet specification requires: if your tool lets you control the `crs` property,
use inline [PROJJSON](https://proj.org/specifications/projjson.html) or an `<authority>:<code>` string
(e.g. `EPSG:4326`), and use `srid:0` when the CRS is unknown, as described in the
[`crs` Parquet property](./geoparquet.md#crs-parquet-property) section of the specification.

### When to add full GeoParquet 2.0 metadata

Full GeoParquet 2.0 conformance additionally means writing the `geo` file metadata described in the
[specification](./geoparquet.md). It is a small amount of extra work for a writer, and it is worth
doing when:

* **Your users' CRS handling needs to be robust.** The GeoParquet metadata restates the CRS as
  guaranteed inline PROJJSON, so readers always get a complete CRS definition without resolving an
  authority code against an external registry (important for offline use and for readers without a
  full CRS database).
* **You know things about the data that Parquet cannot express.** The GeoParquet column metadata can
  declare the exact [geometry types](./geoparquet.md#geometry_types) present, the polygon
  [winding order](./geoparquet.md#orientation), the coordinate [epoch](./geoparquet.md#epoch) for
  dynamic CRS's, and non-planar [edge interpretations](./geoparquet.md#edges) beyond spherical.
* **The file has multiple geometry columns.** The `primary_column` field tells readers which one to
  use by default.
* **You want a [bbox covering](./geoparquet.md#covering) column.** The covering metadata points
  readers at a per-row bounding box column, which enables page-level spatial pruning and spatial
  filtering in readers that pre-date the native geospatial statistics — see
  [when to add a bbox covering column](./distributing-geoparquet.md#when-to-add-a-bbox-covering-column).
* **You are writing a general-purpose geospatial tool or library.** Emitting the full metadata costs
  little and maximizes what downstream readers can do with the data, so it is the recommended default
  for tools whose job is producing geospatial output.

## When you need the compatibility guidelines

Whether the compatibility guidelines apply comes down to what the tool writing your Parquet can do:

1. **It can write the native Parquet geospatial types.** You are done — the file is fully compatible
   with the GeoParquet ecosystem, and you can optionally add the full GeoParquet metadata as described
   above. See the table below for the library versions where this became available.
2. **It cannot write the native types, but it is a geospatial tool that writes GeoParquet 1.x
   metadata** (for example GeoPandas or Apache Sedona today). That output is valid GeoParquet, which
   every GeoParquet reader also understands — you do not need these compatibility guidelines either.
3. **It is a general-purpose Parquet tool with no geospatial support at all** — it can write neither
   the native types nor GeoParquet metadata. This is the case the compatibility guidelines below are
   for.

### Library support for the native geospatial types

The native geospatial types were introduced in version 2.11 of the Parquet format in March 2025, and
support has been rolling out across the ecosystem since then. The table below shows the first released
version of common Parquet libraries and engines that can read and write the native types, as of
September 2026. If you are on an older version, that library cannot write them:

| Library / engine | First version with native geospatial types | Notes |
| --- | --- | --- |
| Apache Arrow C++ / PyArrow | 21.0.0 (July 2025) | Reads/writes via [GeoArrow](https://geoarrow.org) extension types; in Python, register them with the `geoarrow-pyarrow` package |
| parquet-java | 1.16.0 (September 2025) | Logical types plus geospatial statistics |
| DuckDB | 1.4.0 (September 2025) | Since 1.4.1, writing the native types is opt-in with the `GEOPARQUET_VERSION 'V2'` COPY option; the default writes GeoParquet 1.0 |
| arrow-rs (Rust `parquet` crate) | 57.0.0 (October 2025) | Opt-in via the `geospatial` feature flag |
| GDAL/OGR | 3.12.0 (November 2025) | Opt-in with the `USE_PARQUET_GEO_TYPES` layer creation option; requires Arrow ≥ 21 |
| parquet-go | 0.27.0 (January 2026) | Geospatial statistics added in 0.30.0 |
| SedonaDB | 0.3.0 (read) / 0.4.0 (write) (2026) | Write with `geoparquet_version="2.0"` |
| Apache Spark | 4.2.0 (July 2026) | `GEOMETRY`/`GEOGRAPHY` SQL types, enabled by default |
| Apache Arrow Go | 18.8.0 (September 2026) | Reads to GeoArrow extension types |

Note that in most of these libraries writing the native types is currently *opt-in*: the default
output is still GeoParquet 1.x (which is also fine — that is valid GeoParquet, case 2 above). Check
your tool's documentation for how to enable it.

Some commonly used Parquet writers still have no support for the native geospatial types (or
GeoParquet metadata) as of September 2026. Data written with these falls under the compatibility
guidelines:

* **fastparquet** — no geospatial support.
* **Polars** — no geospatial support (tracked in
  [polars#20978](https://github.com/pola-rs/polars/issues/20978)); the `polars-st` community plugin
  provides spatial operations, but writes plain WKB.
* **cuDF (RAPIDS)** — no geospatial support in its Parquet reader/writer.
* **Amazon Athena** — geospatial functions operate on WKT/WKB, and Parquet output has no geospatial
  types or metadata.
* **Snowflake** — loading and unloading plain Parquet still goes through WKB/WKT transforms with no
  geospatial types (though Iceberg v3 tables, which store the native Parquet types in their data
  files, are supported).

Geospatial libraries that write GeoParquet 1.x but not yet the native types (case 2 above, no
compatibility guidelines needed) include **GeoPandas** (native type support tracked in
[geopandas#3632](https://github.com/geopandas/geopandas/issues/3632)) and **Apache Sedona** for Spark.
BigQuery exports `GEOGRAPHY` columns with the native Parquet `GEOGRAPHY` logical type and GeoParquet
metadata.

Support is evolving quickly, so check your tool's current documentation — and if a tool you rely on
is missing, we encourage advocating for native geospatial type support. Feel free to
[start a discussion](https://github.com/opengeospatial/geoparquet/discussions) so the community can
help encourage an implementation.

## Compatibility guidelines for tools that pre-date the Parquet geospatial types

These guidelines are for data producers using tools that cannot write the native Parquet geospatial
types (or GeoParquet metadata). They are *only* recommended in that situation: if your tool can write
the native types, do that instead. The core idea is that tools and libraries that read GeoParquet will
be able to parse these geospatial compatible Parquet files, to make it easy to get data into the
GeoParquet ecosystem. But it is only recommended for those tools and libraries to produce valid
GeoParquet, following [Postel's Law](https://en.wikipedia.org/wiki/Robustness_principle) of being
liberal in what you accept but conservative in what you send - if you are authoring a tool to write
GeoParquet please do not give users the option to create these parquet files.

The compatibility guidelines have the output match the defaults of the official spec as closely as
possible, so it is very easy for tools to simply add the appropriate Parquet metadata and create valid
GeoParquet. The guidelines are as follows:

* The geometry column should be named either `"geometry"` or `"geography"`.

* The geometry column should be a `BYTE_ARRAY` with Well Known Binary (WKB) used to define the geometries, as defined in the [encoding](./geoparquet.md#encoding) section of the GeoParquet spec. Alternatively, the geometry column can be stored according to the Point, MultiPoint, MultiLineString, or MultiPolygon memory layouts with separated (struct) coordinates as specified in the [GeoArrow format](https://geoarrow.org/format).

* All data is stored in longitude, latitude based on the WGS84 datum, as defined as the default in the [crs](./geoparquet.md#crs) section of the GeoParquet spec.

* If the column is named `"geometry"` then the [edges](./geoparquet.md#edges) must be `"planar"`. If the column is named `"geography"` then the edges must be `"spherical"`.

### Data Reader Assumptions

The above are the key recommendations a data producer should follow. Any implemented reader will need to make the following assumptions when reading one of these columns, unless the user supplies additional information that they are aware of:

* The geometry_types values is an empty array, signaling the geometry type is not known and the reader should make no assumptions about the types, as defined in the [geometry_types](./geoparquet.md#geometry_types) section of the spec.

* Any CRS-aware reader should assume that the CRS is OGC:CRS84 as explained in the [crs](./geoparquet.md#crs) section of the spec. (Or it could assume it is EPSG:4326 but overriding the axis order to assume longitude latitude as explained in the [Coordinate axis order](./geoparquet.md#coordinate-axis-order) section).

* No assertions are made on the winding order, the default of the [orientation](./geoparquet.md#orientation) section of the spec.

* The edge definition is based on whether the column is named `"geometry"` or `"geography"`.

### Data Reader Implementation Considerations

Reading this non-compliant geospatial data from Parquet should ideally work with no user intervention if the producer followed all the guidelines and named their geometry column 'geometry'. Readers can optionally support user input (in whatever manner works for the tool / library) to provide hints for metadata that is not inline with the lowest common denominator compatibility. This would include things like letting the user supply a geometry column name (i.e., something other than 'geometry' or 'geography'), using Well Known Text (WKT) in a `STRING` column instead of WKB, providing a more specific geometry_type value, or providing other enhanced metadata (specifying the CRS, the winding order, the edges, the bbox or the epoch).

We strongly advise against creating a reader that can only understand these geospatial compatible files - all readers should start by looking at the native Parquet geospatial types and the metadata specified by GeoParquet, and only fall back on these compatibility techniques if neither is present. A reader that could not read GeoParquet but would read compatible geodata would have no idea if there was in fact metadata, and thus could easily decrease interoperability.

### Data Producer Considerations

As mentioned above, we strongly recommend trying to find tools that will produce the native Parquet geospatial types or valid GeoParquet. If the tool you are working with does not support either directly then there are [many tools](https://geoparquet.org) that can help you. We only recommend this route if there is no way to create the native types or valid GeoParquet metadata. This will enable those who have readers that understand GeoParquet and these compatible files to turn it into valid GeoParquet themselves.

We recommend sticking to the core recommendations as much as possible - naming the geometry column 'geometry', using WKB, and storing data as long, lat. If your data must be formatted differently, fewer readers will be able to work with it. If you do go that route, be sure to make it clear in all your documentation where things are different.
