# Spatial Type Implementation Review

The GeoParquet specification is an example of a **Spatial Type** implementation
that attempts to combine principles from both well established existing geospatial libraries
and cutting edge data engineering components like [Apache Parquet](https://parquet.apache.org),
[Apache Arrow](https://arrow.apache.org), [Apache Iceberg](https://iceberg.apache.org).
These components are used by major data warehouse vendors like
[BigQuery](https://cloud.google.com/bigquery),
[Snowflake](https://snowflake.com), [Databricks](https://databricks.com). Broadly,
GeoParquet was

## Spatial Types?

By **Spatial Type**, we are referring to a library, specification, or file format
that intends to represent points, lines, polygons, or combinations thereof and relate
them to a position on the surface of the earth[^1]. We will also constrain this
definition to only include attempts to *formalize* the representation of this
data within an existing type system or format that is otherwise *not* a dedicated
spatial type. Essentially, if you are storing data in a non-spatial format that you
intend to be put on a map, and you expect somebody else to interpret it in the same
way that you did, that data comes from a spatial type implementation.

[^1]: Technically this also applies if you are on the surface of another planet or
celestial body. We'll discuss this later.

## If you don't read anything else

- **Capture producer intent**: Users of your Spatial Type should not have to discard
  information when converting spatial data from elsewhere. The main thing this means
  if your Spatial Type intends to interoperate with any other Spatial Type, you need
  to provide a mechanism to locate a full Coordinate Reference System definition.
  For example, [GeoPandas](https://geopandas.org) stores a coordinate reference system
  at the type level of each array of geometries.
- **Defer to existing standards**: Spatial data can be complicated and there is a lot
  of prior art to draw from. Deferring to existing standards for well-worn topics like
  Coordinate Reference System representation and serialized representation of geometry
  increases the probability that other tools will be able to easily interact with your
  convention. For example, [GeoParquet](https://geoparquet.org) stores the coordinate
  reference system as [PROJJSON](#projjson).
  and stores geometries as [well-known binary](#well-known-binary).
- **Leverage the capabilities of the format**: Every format has a unique set of
  features and limitations and there is sometimes a tension between deferring to existing
  standards and ensuring that users of the format can leverage existing tools that work with
  the format. For example, [GeoJSON](https://geojson.org) encodes geometries as JavaScript
  objects instead of a previously existing

## Prior art

GeoParquet is far from the first attempt to formalize the representation of spatial
data to an existing type system/storage format. A non-exhaustive list of established
Spatial Type implementations (in no particular order) we will refer to in this document
include:

- [PostGIS](https://postgis.net/) (PostgreSQL)
- [GeoParquet](https://geoparquet.org) (Parquet)
- [GeoPandas](https://geopandas.org) (pandas)
- [Apache Sedona](https://sedona.apache.org) (Apache Spark)
- [Esri Shapefile](https://doc.arcgis.com/en/arcgis-online/reference/shapefiles.htm)
  (DBase).
- [R/sf](https://r-spatial.org/sf) (R)
- [GeoJSON](https://geojson.org/) (JSON)
- [GeoPackage](https://www.geopackage.org/) (SQLite)
- [SpatiaLite](https://www.gaia-gis.it/fossil/libspatialite/index) (SQLite)
- [Apache Calcite Spatial](https://calcite.apache.org/docs/spatial.html) (Apache Calcite)
- [BigQuery Geography](https://cloud.google.com/bigquery/docs/reference/standard-sql/geography_functions) (BigQuery)
- [Snowflake Geospatial](https://docs.snowflake.com/en/sql-reference/data-types-geospatial) (Snowfake)
- [Redshift Geospatial](https://docs.aws.amazon.com/redshift/latest/dg/geospatial-functions.html) (Redshift)
- [FlatGeoBuf](http://flatgeobuf.org/) (Flatbuffers)
- [GeoProtobuf](https://github.com/geo-grpc/api) (gRPC/Protocol buffers)
- [cuspatial](https://docs.rapids.ai/api/cuspatial/stable/) (RAPIDS/cudf)
- [GeoZarr](https://github.com/zarr-developers/geozarr-spec) (Zarr)
- [Climate and Forecasting (CF) Conventions for Geometries](https://cfconventions.org/cf-conventions/cf-conventions.html#geometries)

In addition to established examples of spatial types, several newer libraries are
in the process of adding spatial type support that we will also refer to in this document:

- [GeoArrow](https://geoarrow.org) (Apache Arrow)
- [DuckDB Spatial](https://github.com/duckdb/duckdb_spatial) (DuckDB)
- [Ibis Spatial](https://ibis-project.org/reference/expression-geospatial) (Ibis)
- [Substrait](https://github.com/substrait-io/substrait/blob/67f93b654e4cc60340a214ba90fe15c5e9de941b/extensions/functions_geometry.yaml)

Some examples of projects that are not considered Geospatial type implementations for
the purposes of this document include:

- [Shapely](https://github.com/shapely/shapely)
- [GEOS](https://libgeos.org)
- [JTS](https://locationtech.github.io/jts/)
- [s2geometry](http://s2geometry.io)
- [Boost Geometry](https://www.boost.org/doc/libs/1_86_0/libs/geometry/doc/html/index.html)

These libraries are used by Geospatial type implementations to handle the details of
computational geometry; however, thier scope does not include relating those geometries
to the surface of the earth[^2].

[^2]: Or another celestial body. Again, details forthcoming.

## Components of a data type

Data types describe the user-facing meaning of each element in some collection of
objects (e.g., a column in a table or element in an array). For example,
a [pandas dtype](https://pandas.pydata.org/docs/user_guide/basics.html#basics-dtypes),
a [Parquet LogicalType](https://parquet.apache.org/docs/file-format/types/logicaltypes/),
or an [Arrow Data Type](https://arrow.apache.org/docs/format/Columnar.html#data-types).
Formats use the concept of a data type to separate the arrangement of physical bytes
from the meaning of those bytes. For example, many formats encode dates as the number
of days since January 1, 1970, storing only the type name at the top level and using it
to interpret some sequence of integers.

Most modern type systems allow types to have parameters (e.g., Arrow/Parquet/DuckDB
decimals can be parameterized with a precision and scale at the type level instead
of storing those values alongside each element); however, many older type systems
(e.g., PostgreSQL, SQLite) only have the opportunity to store a type name or identifier.
This requires that all information required to interpret a type lives with each element
(which, depending on the type, can involve a lot of repetition).

If the format allows, spatial data types should be parameterized with a Coordinate
Reference System to avoid unnecessarily repeating this information. This also allows
better interopearability with other spatial data types that store the Coordinate
Reference System in this way (e.g.,
[GeoPandas](#),
[R/sf](https://r-spatial.github.io/sf/reference/st_crs.html),
[GeoArrow](https://geoarrow.org/extension-types.html#extension-metadata),
[GeoParquet](https://github.com/opengeospatial/geoparquet/blob/v1.1.0/format-specs/geoparquet.md#crs)
).

There are cases where a format does not allow a type to be parameterized (i.e., a name
or identifier is all that is possible). PostgreSQL is an example where this is the case:
as a consumer of PostgreSQL using a non-spatial client, all the information you have
is the name or ID of the type ("geometry" or "geography"). The Spatial Type implementation
for PostgreSQL, PostGIS, uses two mechanisms to make the CRS of a column known:

- It stores a CRS identifier (an integer) with every element that refers to a
  `spatial_ref_sys` table that contains an extended string definition of that CRS.
- It keeps a record of all
  [geometry columns as a VIEW](https://postgis.net/docs/using_postgis_dbmanagement.html#geometry_columns) and includes CRS identifier (an integer) that refers to the
  `spatial_ref_sys` table.

For clients reading a table directly, it is possible to look up the type-level CRS
by querying the `geometry_columns` and `spatial_ref_sys` tables; however, for clients
executing a complex query, it is necessary to inspect the integer that is sent alongside
each encoded geometry in the result (which is almost always the exact same value for
every element in the result). An important consequence of this workaround is that
once the context of the original database connection is lost, there is no mechanism
to obtain the full CRS definition to pass on to another Spatial Type[^3].

[^3]: To mitigate this problem, PostGIS does use generally consistent identifiers
for common CRSes such that it is usually possible to guess the CRS based on the
integer identifier.

## Coordinate Reference Systems



https://macwright.com/lonlat/



### PROJJSON


## Geometries

## WKB


