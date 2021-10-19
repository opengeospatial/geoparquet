# Geospatial Parquet format

## Overview

The [Apache Parquet][parquet] provides a standardized open-source columnar storage format. This specification defines how geospatial data
should be stored in parquet format, including the representation of geometries and the required additional metadata.

## Version

This is version 0.1.0 of the geoparquest specification.

## Geometry columns

Geometry columns are stored using the `BYTE_ARRAY` parquet type. They are encoded as [WKB](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry#Well-known_binary).

## Metadata

geoparquet files include additional metadata at two levels:

1. File metadata indicating things like the version of this specification used
2. Column metadata with additional metadata for each geometry column

These are both stored under a "geo" key in the parquet metadata.

## File metadata

All file-level metadata should be included under the "geo" key in the parquet metadata.

|     Field Name     |  Type  |                             Description                              |
| ------------------ | ------ | -------------------------------------------------------------------- |
| schema_version     | string | **REQUIRED** The version of the metadata standard used when writing.   |
| primary_column     | string | **REQUIRED** The name of the "primary" geometry column.                |
| columns            | \[[Column Metadata](#column-metadata)\]  | **REQUIRED** Metadata about geometry columns. |


### Additional file metadata information

#### primary_column

This indicates the "primary" or "active" geometry for systems that can store multiple geometries,
but have a default geometry used for geospatial operations.

#### schema_version

Version of the geoparquet spec used, currently 0.1.0

### Column metadata

Each geometry column in the dataset must be included in the columns field above with the following content, keyed by the column name:

| Field Name |                               Type                                      |                                                                   Description                                                                     |
| ---------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| crs       | string   | **REQUIRED** [WKT2](http://docs.opengeospatial.org/is/12-063r5/12-063r5.html) string representing the Coordinate Reference System (CRS) of the geometry.  |
| encoding | string | **REQUIRED** Name of the geometry encoding format. Currently only 'WKB' is supported. |

#### crs

It is strongly recommended to use [EPSG:4326 (lat, long)](https://spatialreference.org/ref/epsg/4326/) for all data, so in most cases the value of the crs should be:

```
GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0,
        AUTHORITY["EPSG","8901"]],
    UNIT["degree",0.01745329251994328,
        AUTHORITY["EPSG","9122"]],
    AUTHORITY["EPSG","4326"]]
```

Data that is better served in particular projections can choose to use an alternate coordinate reference system.

#### encoding

This is the binary format that the geometry is encoded in. The string 'WKB' to represent 
[Well Known Binary](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry#Well-known_binary) is the only current option, but future versions
of the spec may support alternative encodings.

### Additional information

## TODO

1. Figure out what parquet allows for metadata. Might be forced to use bytes?
2. Do we want to include the [bounding box](https://github.com/geopandas/geo-arrow-spec/blob/dac0d4fe28ad2871ea1042aa72ea8d6b236e2fa8/metadata.md#bounding-boxes) metadata? Should probably explain how it would be used as partitions for individual files.
3. What all is required on the column metadata?


[parquet]: https://parquet.apache.org/
