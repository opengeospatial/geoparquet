# [Work in Progress] Parquet Raster Specification

## Overview

The [Apache Parquet](https://parquet.apache.org/) provides a standardized open-source columnar storage format and it also natively supports geo types (i.e., Geometry and Geography types). The Parquet Raster specification defines how geo-referenced raster imagery data (abbr., raster) should be stored in parquet format, including the representation of raster and the required additional metadata.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Raster columns

A raster column MUST be stored as a `struct` type column in parquet files. The `struct` type MUST contain the fields defined in the following table. The `raster` column MUST be stored in the root level of the parquet file.

Each raster column must also have a corresponding `Geometry` or `Geography` type column, stored in the top level of the parquet file. The name of the geometry column MUST be specified in the `geometry` field of the raster column metadata.

## Raster Representation

The raster data model is largely inspired by the WKB raster encoding of PostGIS but extracts the raster metadata out of the binary encoding. It always uses the little-endian byte order for the raster data.

### Raster value

A raster value is composed by the following components:

| Field        | Parquet Physical Type | Parquet Logical Type | Description                                                             |
|--------------|-----------------------|----------------------|-------------------------------------------------------------------------|
| `crs`        | `BYTE_ARRAY`          | UTF8                 | **OPTIONAL.** The coordinate reference system of the raster             |
| `scale_x`    | `DOUBLE`              |                      | **REQUIRED.** The scale factor of the raster in X direction             |
| `scale_y`    | `DOUBLE`              |                      | **REQUIRED.** The scale factor of the raster in Y direction             |
| `ip_x`       | `DOUBLE`              |                      | **REQUIRED.** The X coordinate of the upper left corner of the raster   |
| `ip_y`       | `DOUBLE`              |                      | **REQUIRED.** The Y coordinate of the upper left corner of the raster   |
| `skew_x`     | `DOUBLE`              |                      | **REQUIRED.** The skew factor of the raster in X direction              |
| `skew_y`     | `DOUBLE`              |                      | **REQUIRED.** The skew factor of the raster in Y direction              |
| `width`      | `INT32`               |                      | **REQUIRED.** The width of the raster in pixels                         |
| `height`     | `INT32`               |                      | **REQUIRED.** The height of the raster in pixels                        |
| `bands`      | `BYTE_ARRAY`          | List<BYTE_ARRAY>     | **REQUIRED.** The bands of the raster. See the band data encoding below |

A raster is one or more grids of cells. All the grids should have `width` rows and `height` columns. The grid cells are represented by the `band` field. The grids are geo-referenced using an affine transformation that maps the grid coordinates to world coordinates. The coordinate reference system (CRS) of the world coordinates is specified by the `crs` field. For more details, please refer to the [CRS Customization](#crs-customization) section.

The geo-referencing information is represented by the parameters of an affine transformation (`ip_x`, `ip_y`, `scale_x`, `scale_y`, `skew_x`, `skew_y`). This specification only supports affine transformation as geo-referencing transformation, other transformations such as polynomial transformation are not supported.

The affine transformation is defined as follows:

```
world_x = ip_x + (col + 0.5) * scale_x + (row + 0.5) * skew_x
world_y = ip_y + (col + 0.5) * skew_y + (row + 0.5) * scale_y
```

col = the column number (pixel index) from the left (0 is the first/leftmost column)
row = the row number (pixel index) from the top (0 is the first/topmost row)

The grid coordinates of a raster is always anchored at the center of grid cells. The translation factor of the affine transformation `ip_x` and `ip_y` also designates the world coordinate of the center of the upper left grid cell.

This specification supports persisting raster band values in two different ways specified by the `isOffline` flag in the band data encoding. The two options are:

* **in-db**: The band values are stored in the same Parquet file as the geo-referencing information.
* **out-db**: The band values are stored in files external to the Parquet file.

### Band data encoding

| Name              | Type                                      | Meaning                                                                                                                                                                                                                                                                                                        |
|-------------------|-------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `isOffline`       | 1 bit                                     | If true, data is found on external storage, through the path specified in `RASTERDATA`.                                                                                                                                                                                                                        |
| `hasNodataValue`  | 1 bit                                     | If true, the stored nodata value is a true nodata value. Otherwise, the nodata value should be ignored.                                                                                                                                                                                                        |
| `isAllNodata`     | 1 bit                                     | If true, all values of the band are expected to be nodata values. This is a dirty flag; to set it properly, the function `st_bandisnodata` must be called with `TRUE` as the last argument.                                                                                                                    |
| `isGZIPPed`       | 1 bit                                     | If true, the data is compressed using GZIP before being passed to the Parquet compression process.                                                                                                                                                                                                             |
| `pixtype`         | 4 bits                                    | Pixel type: <br>0: 1-bit boolean<br>1: 2-bit unsigned integer<br>2: 4-bit unsigned integer<br>3: 8-bit signed integer<br>4: 8-bit unsigned integer<br>5: 16-bit signed integer<br>6: 16-bit unsigned integer<br>7: 32-bit signed integer<br>8: 32-bit unsigned integer<br>10: 32-bit float<br>11: 64-bit float |
| `nodata`          | 1 to 8 bytes (depending on `pixtype` [1]) | Nodata value.                                                                                                                                                                                                                                                                                                  |
| `length`          | int64                                     | Length of the `data` byte_array in bytes.                                                                                                                                                                                                                                                                      |
| `data`            | byte_array                                | Raster band pixel data (see below).                                                                                                                                                                                                                                                                            |

### In-DB pixel data encoding

This encoding is used when `isOffline` flag is false.

| Name         | Type            | Meaning |
|--------------|-----------------|---------|
| `pix[w*h]`   | 1 to 8 bytes (depending on `pixtype` [1]) | Pixel values, row after row. `pix[0]` is the upper-left, `pix[w-1]` is the upper-right. <br><br>Endianness is specified at the start of WKB. It is implicit up to 8 bits (bit-order is most significant first). |

### Out-DB pixel data encoding

This encoding is used when `isOffline` flag is true.

| Name         | Type   | Meaning                                                                 |
|--------------|--------|-------------------------------------------------------------------------|
| `bandNumber` | int8   | 0-based band number to use from the set available in the external file. |
| `length`     | int16  | Length of the `url` string in bytes.                                    |
| `url`        | string | The URI of the out-db raster file (e.g., GeoTIFF files).                |

The allowed URI schemes are:
* `file://`: Local file system
* `http://`: HTTP
* `https://`: HTTPS

---

[1] Note: 1, 2, and 4 bit `pixtype`s are still encoded as 1 byte per value.

### CRS Customization

CRS is represented as a string value. Writer and reader implementations are
responsible for serializing and deserializing the CRS, respectively.

As a convention to maximize the interoperability, custom CRS values can be
specified by a string of the format `type:value`, where `type` is one of
the following values:

* `srid`: [Spatial reference identifier](https://en.wikipedia.org/wiki/Spatial_reference_system#Identifier), `value` is the SRID itself.
* `projjson`: [PROJJSON](https://proj.org/en/stable/specifications/projjson.html), `value` is the PROJJSON string.


## Metadata

Parquet Raster files include additional metadata at two levels:

1. File metadata indicating things like the version of this specification used
2. Column metadata with additional metadata for each raster column

### File metadata

|     Field Name     |  Type  | Description                                                                                                                                                                            |
| ------------------ | ------ |----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| version     		 | string | **REQUIRED.** The version identifier for the Parquet Raster specification.                                                                                                             |
| primary_column     | string | **REQUIRED.** The name of the "primary" raster column. In cases where a Parquet file contains multiple raster columns, the primary raster may be used by default in raster operations. |
| columns            | object\<string, [Column Metadata](#column-metadata)> | **REQUIRED.** Metadata about raster columns. Each key is the name of a raster column in the table.                                                                                     |

At this level, additional implementation-specific fields (e.g. library name) MAY be present, and readers should be robust in ignoring those.

### Column metadata

Each raster column in the dataset, although annotated with Parquet `strcut` type, MUST be included in the `columns` field above with the following content, keyed by the column name:

| Field Name | Type         | Description                                                                              |
|------------| ------------ |------------------------------------------------------------------------------------------|
| geometry   | string       | **REQUIRED.** Name of the geo-reference column to help accelerate spatial data retrieval |
