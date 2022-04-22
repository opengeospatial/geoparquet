# Geospatial Parquet format

## Overview

The [Apache Parquet][parquet] provides a standardized open-source columnar storage format. This specification defines how geospatial data
should be stored in parquet format, including the representation of geometries and the required additional metadata.

## Version

This is version 0.2.0 of the geoparquet specification.

## Geometry columns

Geometry columns are stored using the `BYTE_ARRAY` parquet type. They are encoded as [WKB](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry#Well-known_binary).
See the [encoding](#encoding) section below for more details.

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

At this level, additional implementation-specific fields (e.g. library name) are allowed, and thus readers should be robust in ignoring those.

### Additional file metadata information

#### primary_column

This indicates the "primary" or "active" geometry for systems that can store multiple geometries,
but have a default geometry used for geospatial operations.

#### version

Version of the geoparquet spec used, currently 0.2.0

### Column metadata

Each geometry column in the dataset must be included in the columns field above with the following content, keyed by the column name:

| Field Name |                               Type                                      |                                                                   Description                                                                     |
| ---------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| encoding | string | **REQUIRED** Name of the geometry encoding format. Currently only 'WKB' is supported. |
| geometry_type | string or \[string] | **REQUIRED** The geometry type(s) of all geometries, or 'Unknown' if they are not known.  |
| orientation | string | **OPTIONAL** Winding order of exterior ring of polygons; interior rings are wound in opposite order. If present must be "counterclockwise". If absent, no assertions are made regarding the winding order.
| crs       | string   | **OPTIONAL** [WKT2](https://docs.opengeospatial.org/is/18-010r7/18-010r7.html) string representing the Coordinate Reference System (CRS) of the geometry. If the crs field is not included then the data in this column must be stored in longitude, latitude. In the case where a crs is not provided, CRS-aware implementations should assume a default value of [OGC:CRS84](https://www.opengis.net/def/crs/OGC/1.3/CRS84) (longitude-latitude coordinates). |
| edges | string | **OPTIONAL** Name of the coordinate system for the edges. Must be one of 'planar' or 'spherical'. The default value is 'planar'.  |
| bbox   | \[number] | **OPTIONAL** Bounding Box of the geometries in the file, formatted according to [RFC 7946, section 5](https://tools.ietf.org/html/rfc7946#section-5). |
| epoch    | double | **OPTIONAL** Coordinate epoch in case of a dynamic CRS, expressed as a decimal year.  |


#### crs

The Coordinate Reference System (CRS) is an optional parameter for each geometry column defined in geoparquet format.

The CRS must be provided in [WKT](https://en.wikipedia.org/wiki/Well-known_text_representation_of_coordinate_reference_systems) version 2, also known as **WKT2**. WKT2 has several revisions, this specification only supports [WKT2_2019](https://docs.opengeospatial.org/is/18-010r7/18-010r7.html).

If CRS is not provided, then all coordinates in the geometry must use longitude, latitude to store their data.
If an implementation is CRS-aware and needs a CRS representation of the data it should assume a default value is [OGC:CRS84](https://www.opengis.net/def/crs/OGC/1.3/CRS84). It's equivalent to the well-known [EPSG:4326](https://epsg.org/crs_4326/WGS-84.html) but changes the axis from latitude-longitude to longitude-latitude. The WKT2:2019 string for OGC:CRS84 is:

```
GEOGCRS["WGS 84 (CRS84)",
    ENSEMBLE["World Geodetic System 1984 ensemble",
        MEMBER["World Geodetic System 1984 (Transit)"],
        MEMBER["World Geodetic System 1984 (G730)"],
        MEMBER["World Geodetic System 1984 (G873)"],
        MEMBER["World Geodetic System 1984 (G1150)"],
        MEMBER["World Geodetic System 1984 (G1674)"],
        MEMBER["World Geodetic System 1984 (G1762)"],
        MEMBER["World Geodetic System 1984 (G2139)"],
        ELLIPSOID["WGS 84",6378137,298.257223563,
            LENGTHUNIT["metre",1]],
        ENSEMBLEACCURACY[2.0]],
    PRIMEM["Greenwich",0,
        ANGLEUNIT["degree",0.0174532925199433]],
    CS[ellipsoidal,2],
        AXIS["geodetic longitude (Lon)",east,
            ORDER[1],
            ANGLEUNIT["degree",0.0174532925199433]],
        AXIS["geodetic latitude (Lat)",north,
            ORDER[2],
            ANGLEUNIT["degree",0.0174532925199433]],
    USAGE[
        SCOPE["Not known."],
        AREA["World."],
        BBOX[-90,-180,90,180]],
    ID["OGC","CRS84"]]
```

Due to the large number of CRSes available and the difficulty of implementing all of them, we expect that a number of implementations will start without support for the optional `crs` field.
Users are recommended to store their data in longitude, latitude (OGC:CRS84 or not including the `crs` field) for it to work with the widest number of tools. But data that is better served in particular projections can choose to use an alternate coordinate reference system. We expect many tools will support alternate CRSes, but encourage users to check to ensure their chosen tool supports their chosen crs.

#### epoch

In a dynamic CRS, coordinates of a point on the surface of the Earth may
change with time. To be unambiguous, the coordinates must always be qualified
with the epoch at which they are valid.

The optional "epoch" field allows to specify this in case the "crs" field
defines a a dynamic CRS. The coordinate epoch is expressed as a decimal year
(e.g. 2021.47). Currently, this specification only supports an epoch per
column (and not per geometry).

#### encoding

This is the binary format that the geometry is encoded in.
The string 'WKB', signifying Well Known Binary is the only current option, but future versions
of the spec may support alternative encodings. This should be the ["OpenGIS® Implementation Specification for Geographic information - Simple feature access - Part 1: Common architecture"](https://portal.ogc.org/files/?artifact_id=18241) WKB representation (using codes for 3D geometry types in the \[1001,1007\] range). This encoding is also consistent with the one defined in the ["ISO/IEC 13249-3:2016 (Information technology - Database languages - SQL multimedia and application packages - Part 3: Spatial)"](https://www.iso.org/standard/60343.html) standard.

Note that the current version of the spec only allows for a subset of WKB: 2D or 3D geometries of the standard geometry types (the Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, and GeometryCollection geometry types). This means that M values or non-linear geometry types are not yet supported.

#### Coordinate axis order

The axis order of the coordinates in WKB stored in a geoparquet follows the de facto standard for axis order in WKB and is therefore always
(x, y) where x is easting or longitude and y is northing or latitude. This ordering explicitly overrides the axis order as specified in the CRS.
This follows the precedent of [GeoPackage](https://geopackage.org), see the [note in their spec](https://www.geopackage.org/spec130/#gpb_spec).

#### geometry_type

This field captures the geometry type(s) of the geometries in the
column, when known. Accepted geometry types are: "Point", "LineString",
"Polygon", "MultiPoint", "MultiLineString", "MultiPolygon",
"GeometryCollection".

In addition, the following rules are used:

- In case of 3D geometries, a " Z" suffix gets added (e.g. "Point Z").
- The value can be a single string or an array of strings in case multiple
  geometry types are present (e.g. ["Polygon", "MultiPolygon"]).
- Additionally the value "Unknown" is accepted to explicitly signal that the
  geometry type is not known.

It is expected that this field is strictly correct. For
example, if having both polygons and multipolygons, it is not sufficient to
specify "MultiPolygon", but it is expected to specify
["Polygon", "MultiPolygon"]. Or if having 3D points, it is not sufficient to
specify "Point", but it is expected to list "Point Z".

#### orientation

This attribute indicates the winding order of polygon. Available values are:

- counterclockwise: the winding order of polygons follows the [GeoJSON spec](https://datatracker.ietf.org/doc/html/rfc7946#section-3.1.6). All vertices of exterior polygon rings MUST be ordered in the counterclockwise direction and all interior rings MUST be ordered in the clockwise direction.

If no value is set, no assertions are made about winding order or consistency of such between exterior and interior rings or between individual geometries within a dataset.  Readers are responsible for verifying and if necessary re-ordering vertices as required for their analytical representation.

Writers are encouraged but not required to set orientation="counterclockwise" for portability of the data within the broader ecosystem.

#### edges

This attribute indicates how to interpret the edges of the geometries: whether the line between two points is a straight cartesian line or the shortest line on the sphere (geodesic line). Available values are:
- planar: use a flat cartesian coordinate system.
- spherical: use a spherical coordinate system and radius derived from the spheroid defined by the coordinate reference system.

If no value is set, the default value to assume is 'planar'.

#### bbox

Bounding boxes are used to help define the spatial extent of each geometry column.
Implementations of this schema may choose to use those bounding boxes to filter
partitions (files) of a partitioned dataset.

The bbox, if specified, must be encoded with an array containing the minimum
and maximum values of each dimension: `[<xmin>, <ymin>, <xmax>, <ymax>]`.
This follows the GeoJSON specification ([RFC 7946, section 5](https://tools.ietf.org/html/rfc7946#section-5)).

### Additional information

You can find an example in the [examples](../examples/) folder.

[parquet]: https://parquet.apache.org/
