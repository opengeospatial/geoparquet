# Cloud Data Warehouse Geospatial Interoperability

## About

This repository is the main record of a collaboration to better standardize the import and export of geospatial information on 'Cloud Data Warehouses'.
It will likely result in one or more small standards, but we'll incubate them here.

## Background

Most Cloud Data Warehouses (BigQuery, Snowflake, Redshift, etc) have at least some level of geospatial support, but all handle the import and export 
in slightly different ways, requiring users do advanced spatial ETL to take it from one and load it in another. For the most part all support some 
sort of standard (WKT, WKB, EWKT, GeoJSON), but all handle it in slightly different ways. 

OGC is helping to convene a small group of key participants to provide leadership to the industry, aligning on the interoperable formats so that 
geospatial information can flow between the various systems with ease. The initial kick-off meeting happened August 28, 2021, with representatives from
Google (BigQuery), Snowflake, Amazon (Redshift), Microsoft (Planetery Computer), Carto and Planet.

## Goals

The primary goal established by the group was to focus on interoperability of import and export of the geospatial elements of common Cloud Data Warehouse formats. 
As most already support geospatial import and export in several formats the goal is not to necessarily align on a single one, but to fully document how each of
the relevant formats should use geospatial columns in a consistent way. 

Future work may involve finding a format that can be used directly, without having to import, but the group decided to keep that out of scope for the initial 
collaboration, to get a clear win on import and export before tackling the more challenging problem of getting a format that will perform adequetly. 


## Interoperability Notes

TODO: Likely turn these each into their own pages.

### CSV

Every implementation supports import and export of CSV, and all have some mechanism to include geospatial information in it. 

The following table details what each can use for geometries. A 'yes' means that it supports both import and export.

|                           | Snowflake | BigQuery                                                  | Oracle | Redshift   |
|---------------------------|-----------|-----------------------------------------------------------|--------|------------|
| **Default Export Format** | GeoJSON   | WKT in 4326 (geodesic edges, oriented polygons) as STRING |    ?   | Hex EWKB   |
|                           |           |                                                           |        |            |
| GeoJSON Geometries        | Yes       | Yes                                                       | Yes    | Yes        |
| WKT                       | Yes       | Yes                                                       | Yes    | Yes        |
| WKB                       | Yes       | Import Only                                               | Yes    | Yes        |
| EWKT                      | Yes       | ?                                                         | No     | Yes        |
| EWKB                      | Yes       | ?                                                         | No     | Yes        |
| Hex-encoded WKB           | ?         | Yes                                                       | ?      | Yes (?)    |
| Hex-encoded EWKB          | ?         | No(?)                                                     | No     | Yes (EWKB) |

Note EWKT and EWKB are formats defined by PostGIS, that include an inline SRID. Others are starting to support it, but OGC SQL/MM chose not to
include it as there is no guarantee that a given SRID is the same across different spatial databases. PostGIS gets around this by always shipping
a spatial_ref_sys that directly maps EPSG to SRID. But Oracle does not do the same (afaik), so EWKT / EWKT won't work well with it.

TODO: Add links to the docs for each vendor.

### JSON

TODO: Lots of subtleties with new line JSON, etc.

### Parquet

TODO: list support, ideas / issues

### Avro

TODO: flesh out

[CSV](csv.md) - Most widely 
[JSON](json.md)
[Parquet](parquet.md)
[Avro](avro.md)

## Current Support

This table aims captures the current state of play between various implementations.

|                                                                          | Snowflake                                    | BigQuery                                                                                                       | Oracle                                                                                                     | Redshift                                                                                |
|--------------------------------------------------------------------------|----------------------------------------------|----------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
|                                                                          |                                              |                                                                                                                |                                                                                                            |                                                                                         |
| **INTERNAL REPRESENTATION**                                              |                                              |                                                                                                                |                                                                                                            |                                                                                         |
| What is the internal representation of Geo data                          | WGS84 spheroid                               | WGS84 spheroid                                                                                                 | Geodetic/Projects; basically any CS                                                                        | Cartesian 2D, 3DZ, 3DM, 4D                                                              |
|                                                                          |                                              |                                                                                                                |                                                                                                            |                                                                                         |
| **EXPORT**                                                               |                                              |                                                                                                                |                                                                                                            |                                                                                         |
| in CSV, what format is the GEOGRAPHY object encoded in?                  | GeoJSON, WKT, EWKT, WKB, EWKB                | WKT in 4326 (geodesic edges, oriented polygons) as STRING                                                      | WKB/WKT/GeoJSON/GML, etc.                                                                                  | Hexadecimal (E)WKB/(E)WKT/GeoJSON (default is Hex EWKB, the others through projections) |
| in JSON, what format is the GEOGRAPHY object encoded in?                 | non-compliant GeoJSON, not respecting wgs-84 | \-                                                                                                             | GeoJSON                                                                                                    | GeoJSON                                                                                 |
| in NDJSON                                                                | not supported                                | WKT in 4326 as STRING                                                                                          |                                                                                                            | not supported                                                                           |
| in AVRO                                                                  | not supported format yet                     | WKT in 4326 (geodesic edges) {"type":"string", "logicalType":"geography\_wkt"}                                 |                                                                                                            | not supported                                                                           |
| in Parquet                                                               | GeoJSON, WKT, EWKT, WKB, EWKB                | not supported                                                                                                  |                                                                                                            | not supported                                                                           |
| in ORC                                                                   | not supported                                | not supported                                                                                                  |                                                                                                            | not supported                                                                           |
|                                                                          |                                              |                                                                                                                |                                                                                                            |                                                                                         |
| **IMPORT**                                                               |                                              |                                                                                                                |                                                                                                            |                                                                                         |
| If there is an auto-detect mode, does it interpretate geo?               | No                                           | No auto-detect of Geography type. If schema contains Geography type, auto-detect of WKT, WKB, GeoJson formats. | Auto detect if it is GeoJSON; otherwise WKT/WKB etc need to be coverted to geometry after the load is done | No                                                                                      |
| If the target schema indicates GEOGRAPHY on the field will it ingest it? | Yes                                          | Yes                                                                                                            | Yes                                                                                                        | Yes                                                                                     |
| in CSV                                                                   | GeoJSON, WKT, EWKT, WKB, EWKB                | WKT, WKB, hex-encoded WKB, Geojson                                                                             | WKT/WKB/geoJSON                                                                                            | (E)WKT/(E)WKB                                                                           |
| in AVRO                                                                  | Yes                                          | [YES](https://stackoverflow.com/questions/52380937/importing-geography-data-into-bigquery-using-avro-parquet)  |                                                                                                            | Not supported                                                                           |
| in Parquet                                                               | Yes                                          | [YES](https://stackoverflow.com/questions/52380937/importing-geography-data-into-bigquery-using-avro-parquet)  |                                                                                                            | Not supported                                                                           |
| in ORC                                                                   | Yes                                          | not supported                                                                                                  |                                                                                                            | Not supported                                                                           |
|                                                                          |                                              |                                                                                                                |                                                                                                            |                                                                                         |
| **QUERY**                                                                |                                              |                                                                                                                |                                                                                                            |                                                                                         |
| When doing a regular query in what way is GEOGRAPHY encoded              | Possible to specify (WKT,WKB,EWKT...)        | WKT in 4326                                                                                                    | Native geometry type, WKT/WKB/JSON/GeoJSON                                                                 | Native GEOMETRY type                                                                    |
