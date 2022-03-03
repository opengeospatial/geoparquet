# Geospatial Parquet format

## Overview

The [Apache Parquet][parquet] provides a standardized open-source columnar storage format. This specification defines how geospatial data
should be stored in parquet format, including the representation of geometries and the required additional metadata.

## Version

This is version 0.1.0 of the geoparquet specification.

## Geometry columns

Geometry columns are stored using the `BYTE_ARRAY` parquet type. They are encoded as [WKB](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry#Well-known_binary).

## Metadata

geoparquet files include additional metadata at two levels:

1. File metadata indicating things like the version of this specification used
2. Column metadata with additional metadata for each geometry column

These are both stored under a "geo" key in the parquet metadata (the [`FileMetaData::key_value_metadata`](https://github.com/apache/parquet-format#metadata)) as a JSON-encoded UTF-8 string.

## File metadata

All file-level metadata should be included under the "geo" key in the parquet metadata.

|     Field Name     |  Type  |                             Description                              |
| ------------------ | ------ | -------------------------------------------------------------------- |
| version     		 | string | **REQUIRED** The version of the geoparquet metadata standard used when writing.   |
| primary_column     | string | **REQUIRED** The name of the "primary" geometry column.                |
| columns            | Map<key, [Colum Metadata](#column-metadata)> | **REQUIRED** Metadata about geometry columns, with each key is the name of a geometry column in the table. |


### Additional file metadata information

#### primary_column

This indicates the "primary" or "active" geometry for systems that can store multiple geometries,
but have a default geometry used for geospatial operations.

#### version

Version of the geoparquet spec used, currently 0.1.0

### Column metadata

Each geometry column in the dataset must be included in the columns field above with the following content, keyed by the column name:

| Field Name |                               Type                                      |                                                                   Description                                                                     |
| ---------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| crs       | string   | **REQUIRED**  string representing the Coordinate Reference System (CRS) of the geometry.  |
| encoding | string | **REQUIRED** Name of the geometry encoding format. Currently only 'WKB' is supported. |

#### crs

The Coordinate Reference System (CRS) is a mandatory parameter for all the geometries defined in geoparquet format. 

The CRS needs to be provided in [WKT](https://en.wikipedia.org/wiki/Well-known_text_representation_of_coordinate_reference_systems) version 2, also known as **WKT2**. WKT2 has several revisions, this specification supports the revisions from [2015](http://docs.opengeospatial.org/is/12-063r5/12-063r5.html) and [2019](https://docs.opengeospatial.org/is/18-010r7/18-010r7.html): WKT2_2015, WKT2_2015_SIMPLIFIED, WKT2_2019, WKT_2019_SIMPLIFIED. 


As the most common CRS for datasets is latitude/longitude, for the widest interoperability we recommend [EPSG:4326](https://spatialreference.org/ref/epsg/wgs-84) for all data, so in most cases the value of the crs should be:

```
GEOGCRS["WGS 84",
    ENSEMBLE["World Geodetic System 1984 ensemble",
        MEMBER["World Geodetic System 1984 (Transit)"],
        MEMBER["World Geodetic System 1984 (G730)"],
        MEMBER["World Geodetic System 1984 (G873)"],
        MEMBER["World Geodetic System 1984 (G1150)"],
        MEMBER["World Geodetic System 1984 (G1674)"],
        MEMBER["World Geodetic System 1984 (G1762)"],
        MEMBER["World Geodetic System 1984 (G2139)"],
        ELLIPSOID["WGS 84",6378137,298.257223563],
        ENSEMBLEACCURACY[2.0]],
    CS[ellipsoidal,2],
        AXIS["geodetic latitude (Lat)",north],
        AXIS["geodetic longitude (Lon)",east],
        UNIT["degree",0.0174532925199433],
    USAGE[
        SCOPE["Horizontal component of 3D system."],
        AREA["World."],
        BBOX[-90,-180,90,180]],
    ID["EPSG",4326]]
```

Due to the large number of CRSes available and the difficulty of implementing all of them, we strongly encourage the first implementing [EPSG:4326](https://spatialreference.org/ref/epsg/wgs-84).

Data that is better served in particular projections can choose to use an alternate coordinate reference system.

#### encoding

This is the binary format that the geometry is encoded in. The string 'WKB' to represent 
[Well Known Binary](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry#Well-known_binary) is the only current option, but future versions
of the spec may support alternative encodings. This should be the ["standard"](https://libgeos.org/specifications/wkb/#standard-wkb) WKB representation.

#### Coordinated order

The axis order in WKB stored in a geoparquet follows the de facto standard for axis order in WKB and is therefore always (x,y{,z}{,m}) where x is easting or longitude, y is northing or latitude, z is optional elevation, and m is optional measure. This ordering explicitly overrides the axis order as specified in the CRS.

### Additional information

## TODO

1. Do we want to include the [bounding box](https://github.com/geopandas/geo-arrow-spec/blob/dac0d4fe28ad2871ea1042aa72ea8d6b236e2fa8/metadata.md#bounding-boxes) metadata? Should probably explain how it would be used as partitions for individual files.
2. What all is required on the column metadata?


[parquet]: https://parquet.apache.org/
