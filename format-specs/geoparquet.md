# Geospatial Parquet format

## Overview

The [Apache Parquet][parquet] provides a standardized open-source columnar storage format. This specification defines how geospatial data
should be stored in parquet format, including the representation of geometries and the required additional metadata.

## Geometry columns

Geometry columns are stored using the `BYTE_ARRAY` parquet type. They are encoded as WKB.

## Metadata

geoparquet files include additional metadata at two levels:

1. File metadata indicating things like the version of this specification used
2. Column (chunk) metadata with additional metadata for each geometry column

## File metadata

|     Field Name     |  Type  |                             Description                              |
| ------------------ | ------ | -------------------------------------------------------------------- |
| geoparquet_version | string | **REQUIRED** The version of the metadata standard used when writing. |
| primary_column     | string | The "primary" geometry column.                                       |


## Column metadata

Each geometry column should include additional metadata

| Field Name |                               Type                                      |                                                                   Description                                                                     |
| ---------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| epsg       | integer\| null                                                          | **REQUIRED.** [EPSG code](http://www.epsg-registry.org/) of the datasource                                                                        |
| bbox       | \[number]                                                               | Bounding Box of the asset represented by this Item, formatted according to [RFC 7946, section 5](https://tools.ietf.org/html/rfc7946#section-5).  |                                                                                                                                                                                      |
| wkt2       | string\| null                                                           | [WKT2](http://docs.opengeospatial.org/is/12-063r5/12-063r5.html) string representing the Coordinate Reference System (CRS) used by the geometries |
| projjson   | [PROJJSON Object](https://proj.org/specifications/projjson.html)\| null | PROJJSON object representing the Coordinate Reference System (CRS) that the `proj:geometry` and `proj:bbox` fields represent                      |

### Additional information

## TODO

1. Figure out what parquet allows for metadata. Might be forced to use bytes?
2. Figure out if we want the "primary" column thing.
3. What all is required on the column metadata?


[parquet]: https://parquet.apache.org/