# Geospatial Parquet format

## Overview

The [Apache Parquet][parquet] provides a standardized open-source columnar storage format. This specification defines how geospatial data
should be stored in parquet format, including the representation of geometries and the required additional metadata.

## Geometry columns

Geometry columns are stored using the `BYTE_ARRAY` parquet type. They are encoded as [WKB](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry#Well-known_binary).

## Metadata

geoparquet files include additional metadata at two levels:

1. File metadata indicating things like the version of this specification used
2. Column (chunk) metadata with additional metadata for each geometry column

## File metadata

All file-level metadata should be included under the "geoparquet" key in the parquet metadata.

|     Field Name     |  Type  |                             Description                              |
| ------------------ | ------ | -------------------------------------------------------------------- |
| geoparquet_version | string | **REQUIRED** The version of the metadata standard used when writing. |
| primary_column     | string | The name of the "primary" geometry column.                           |


### Additional file metadata information

**primary_column**: This indicates the "primary" or "active" geometry for systems that can store multiple geometries,
but have a default geometry used for geospatial operations.

## Column metadata

Each geometry column should include additional metadata

| Field Name |                               Type                                      |                                                                   Description                                                                     |
| ---------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| epsg       | integer\| null                                                          | **REQUIRED.** [EPSG code](http://www.epsg-registry.org/) of the datasource. Must be 4326                                                          |

### Additional information

## TODO

1. Figure out what parquet allows for metadata. Might be forced to use bytes?
2. Figure out if we want the "primary" column thing.
3. What all is required on the column metadata?


[parquet]: https://parquet.apache.org/