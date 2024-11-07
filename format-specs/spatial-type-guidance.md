# Spatial Type Implementation Review

The GeoParquet specification is an example of a **Spatial Type** implementation
that attempts to combine principles from both well established existing geospatial libraries
and cutting edge data engineering

### Spatial Types

By **Spatial Type**, we are referring to a library, specification, or file format
that intend to represent points, lines, polygons, or combinations thereof and relate
them to a position on the surface of the earth[^1]. Essentially, if you intend for your
data to be on a map, that data comes from a spatial type implementation.

[^1]: Technically this also applies if you are on the surface of another planet or
celestial body. We'll discuss this later.

A non-exhaustive list of well-established Spatial type implementations include:

- [PostGIS](https://postgis.net/)
- [GeoPandas](https://geopandas.org)
- [Esri Shapefile](https://doc.arcgis.com/en/arcgis-online/reference/shapefiles.htm)
- [R/sf](https://r-spatial.org/sf)
- [GeoJSON](https://geojson.org/)
- [GeoPackage](https://www.geopackage.org/)
- [Apache Calcite Spatial](https://calcite.apache.org/docs/spatial.html)
- [BigQuery Geography](https://cloud.google.com/bigquery/docs/reference/standard-sql/geography_functions)
- [Snowflake Geospatial](https://docs.snowflake.com/en/sql-reference/data-types-geospatial)
- [Redshift Geospatial](https://docs.aws.amazon.com/redshift/latest/dg/geospatial-functions.html)
- [GeoParquet](https://geoparquet.org)
- [FlatGeoBuf](http://flatgeobuf.org/)

In addition to well-established examples of geospatial type implementations,

- [GeoArrow](https://geoarrow.org)
- [DuckDB Spatial](https://github.com/duckdb/duckdb_spatial)
- [Ibis](https://ibis-project.org/)


Some examples of projects that are not considered Geospatial type implementations for
the purposes of this document include:

- [Shapely](https://github.com/shapely/shapely)
- [GEOS](https://libgeos.org)
- [JTS](https://locationtech.github.io/jts/)
- [s2geometry](http://s2geometry.io)
- [Boost Geometry](https://www.boost.org/doc/libs/1_86_0/libs/geometry/doc/html/index.html)

These libraries are used by Geospatial type implementations to handle the details of
computational geometry; however, thier scope does not include relating those geometries
to the surface of the earth.


