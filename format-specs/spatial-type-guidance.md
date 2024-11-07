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
data within an existing type system or format. Essentially, if you are storing data that you
intend to be put on a map, and you expect somebody else to interpret it in the same
way that you did, that data comes from a spatial type implementation.

[^1]: Technically this also applies if you are on the surface of another planet or
celestial body. We'll discuss this later.

## If you don't read anything else

- **Capture producer intent**: Users of your Spatial Type should not have to discard
  information when converting spatial data from elsewhere. The main thing this means
  if your Spatial Type intends to interoperate with any other Spatial Type, you need
  to provide a mechanism to locate a full Coordinate Reference System definition.
- **Defer to existing standards**: Spatial data can be complicated and there is a lot
  of prior art to draw from. Deferring to existing standards for well-worn topics like
  Coordinate Reference System representation and serialized representation of geometry
  increases the probability that other tools will be able to easily interact with your
  convention.
- **Leverage the capabilities of the format**: Every format has a unique set of
  features and limitations. There is sometimes a tension between deferring to existing standards
  and ensuring that users of the format can leverage all the great things that
  can be done.

## Prior art

GeoParquet is far from the first attempt to formalize the representation of spatial
data to an existing type system/storage format. A non-exhaustive list of established
Spatial Type implementations we will refer to in this document include:

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

## Types?



## Coordinate Reference Systems

https://macwright.com/lonlat/


