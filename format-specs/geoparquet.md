# GeoParquet Specification

## Overview

The [Apache Parquet](https://parquet.apache.org/) provides a standardized open-source columnar storage format. The GeoParquet specification originally defined how geospatial data should be stored in Parquet format, including the representation of geometries and the required additional metadata. As of Parquet version 2.11, released in March 2025, the Parquet format specifies [geospatial types and statistics](https://github.com/apache/parquet-format/blob/apache-parquet-format-2.12.0/Geospatial.md). The 2.0 version of the GeoParquet specification provides guidance for geospatial tools to implement Parquet Geometry and Geography types, along with some optional metadata not covered in the core Parquet specification.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Version and schema

This is version 2.0-dev of the GeoParquet specification.  See the [JSON Schema](schema.json) to validate metadata for this version. See [Version Compatibility](#version-compatibility) for details on version compatibility guarantees.

## Geometry columns

Geometry columns MUST be encoded as either [`GEOMETRY`](https://github.com/apache/parquet-format/blob/apache-parquet-format-2.12.0/LogicalTypes.md#geometry) or [`GEOGRAPHY`](https://github.com/apache/parquet-format/blob/apache-parquet-format-2.12.0/LogicalTypes.md#geography) logical types in Parquet, which both annotate a BYTE_ARRAY that encodes geospatial features in the [WKB](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry#Well-known_binary) format.

### Nesting

Geometry columns MUST be at the root of the schema. In practice, this means that when writing to GeoParquet from another format, geometries cannot be contained in complex or nested types such as structs, lists, arrays, or map types.

### Repetition

The repetition for all geometry columns MUST be "required" (exactly one) or "optional" (zero or one). A geometry column MUST NOT be repeated. A GeoParquet file MAY have multiple geometry columns with different names, but those geometry columns cannot be repeated.

## Metadata

GeoParquet files include additional metadata at two levels:

1. File metadata indicating things like the version of this specification used
2. Column metadata with additional metadata for each geometry column

A GeoParquet file MUST include a `geo` key in the Parquet metadata (see [`FileMetaData::key_value_metadata`](https://github.com/apache/parquet-format/blob/apache-parquet-format-2.12.0/README.md#metadata).  The value of this key MUST be a JSON-encoded UTF-8 string representing the file and column metadata that validates against the [GeoParquet metadata schema](schema.json). The file and column metadata fields are described below.

## File metadata

|     Field Name     |  Type  |                             Description                              |
| ------------------ | ------ | -------------------------------------------------------------------- |
| version     		 | string | **REQUIRED.** The version identifier for the GeoParquet specification. |
| primary_column     | string | **REQUIRED.** The name of the "primary" geometry column. In cases where a GeoParquet file contains multiple geometry columns, the primary geometry may be used by default in geospatial operations. |
| columns            | object\<string, [Column Metadata](#column-metadata)> | **REQUIRED.** Metadata about geometry columns. Each key is the name of a geometry column in the table. |

At this level, additional implementation-specific fields (e.g. library name) MAY be present, and readers should be robust in ignoring those.

### Column metadata

Each geometry column in the dataset MUST be included in the `columns` field above with the following content, keyed by the column name:

| Field Name     | Type         | Description |
| -------------- | ------------ | ----------- |
| encoding       | string       | **REQUIRED.** Name of the geometry encoding format. Only `"WKB"` is supported. |
| geometry_types | \[string]    | **REQUIRED.** The geometry types of all geometries, or an empty array if they are not known. |
| crs            | object\|null | [PROJJSON](https://proj.org/specifications/projjson.html) object representing the Coordinate Reference System (CRS) of the geometry. If the field is not provided, the default CRS is [OGC:CRS84](https://www.opengis.net/def/crs/OGC/1.3/CRS84), which means the data in this column must be stored in longitude, latitude based on the WGS84 datum. |
| orientation    | string       | Winding order of exterior ring of polygons. If present must be `"counterclockwise"`; interior rings are wound in opposite order. If absent, no assertions are made regarding the winding order. |
| edges          | string       | Describes how to interpret the edges of the geometries. Must be one of `planar`, `spherical`, `vincenty`, `thomas`, `andoyer`, `karney`. The default value is `planar`.
| bbox           | \[number]    | Bounding Box of the geometries in the file, formatted according to [RFC 7946, section 5](https://tools.ietf.org/html/rfc7946#section-5). |
| epoch          | number       | Coordinate epoch in case of a dynamic CRS, expressed as a decimal year. |

#### crs

The Coordinate Reference System (CRS) is an optional parameter for each geometry column defined in GeoParquet format.

The CRS MUST be provided in [PROJJSON](https://proj.org/specifications/projjson.html) format, which is a JSON encoding of [WKT2:2019 / ISO-19162:2019](https://docs.opengeospatial.org/is/18-010r7/18-010r7.html), which itself implements the model of [OGC Topic 2: Referencing by coordinates abstract specification / ISO-19111:2019](http://docs.opengeospatial.org/as/18-005r4/18-005r4.html). Apart from the difference of encodings, the semantics are intended to match WKT2:2019, and a CRS in one encoding can generally be represented in the other.

If the `crs` key does not exist, all coordinates in the geometries MUST use longitude, latitude based on the WGS84 datum, and the default value is [OGC:CRS84](https://www.opengis.net/def/crs/OGC/1.3/CRS84) for CRS-aware implementations. Note that a missing `crs` key has different meaning than a `crs` key set to `null` (see below).

[OGC:CRS84](https://www.opengis.net/def/crs/OGC/1.3/CRS84) is equivalent to the well-known [EPSG:4326](https://epsg.org/crs_4326/WGS-84.html) but changes the axis from latitude-longitude to longitude-latitude.

See below for additional details about representing or identifying OGC:CRS84.

The value of this key may be explicitly set to `null` to indicate that there is no CRS assigned to this column (CRS is undefined or unknown).

The `crs` field of GeoParquet MUST reflect the crs of the Parquet `crs` property on the GEOMETRY or GEOGRAPHY logical type.

##### `crs` Parquet property

The Parquet Geospatial definitions have a [crs customization](https://github.com/apache/parquet-format/blob/apache-parquet-format-2.12.0/Geospatial.md#crs-customization) section
that gives flexibility for how to specify the crs.

The GeoParquet 2.0 specification gives less flexibility. To comply with
GeoParquet 2.0 if there is a non-default crs then the crs field in the Parquet geometry or geography type MUST be an in-line projjson representation of the crs. This is allowed by the Parquet specification, though it is not explicitly articulated.

Readers of geospatial Parquet data SHOULD try to parse other crs representations in the Parquet metadata.

#### epoch

In a dynamic CRS, coordinates of a point on the surface of the Earth may change with time. To be unambiguous, the coordinates must always be qualified with the epoch at which they are valid.

The optional `epoch` field allows to specify this in case the `crs` field defines a dynamic CRS. The coordinate epoch is expressed as a decimal year (e.g. `2021.47`). Currently, this specification only supports an epoch per column (and not per geometry).

#### encoding

This is the memory layout used to encode geometries in the geometry column. The only supported value is `"WKB"`. This SHOULD be the ["OpenGIS® Implementation Specification for Geographic information - Simple feature access - Part 1: Common architecture"](https://portal.ogc.org/files/?artifact_id=18241) WKB representation. The [Parquet Geospatial Definitions](https://github.com/apache/parquet-format/blob/apache-parquet-format-2.12.0/Geospatial.md) provide full details on implementing the encoding and the Parquet logical types.

WKB geometry columns MUST be stored using the `BYTE_ARRAY` parquet type, with either a `GEOMETRY` or `GEOGRAPHY` logical type, as specified by the Parquet format.

#### Coordinate axis order

The axis order of the coordinates in WKB stored in a GeoParquet follows the de facto standard for axis order in WKB and is therefore always (x, y) where x is easting or longitude and y is northing or latitude. This ordering explicitly overrides the axis order as specified in the CRS. This is aligned with [Parquet Coordinate Axis Order](https://github.com/apache/parquet-format/blob/apache-parquet-format-2.12.0/Geospatial.md#coordinate-axis-order).

#### geometry_types

This field captures the geometry types of the geometries in the column, when known. Accepted geometry types are: `"Point"`, `"LineString"`, `"Polygon"`, `"MultiPoint"`, `"MultiLineString"`, `"MultiPolygon"`, `"GeometryCollection"`.

In addition, the following rules are used:

- In case of 3D geometries (XYZ), a `" Z"` suffix gets added (e.g. `["Point Z"]`).
- In case of measured geometries (XYM), a `" M"` suffix gets added (e.g. `["Point M"]`).
- In case of 3D measured geometries (XYZM), a `" ZM"` suffix gets added (e.g. `["Point ZM"]`).
- A list of multiple values indicates that multiple geometry types are present (e.g. `["Polygon", "MultiPolygon"]`).
- An empty array explicitly signals that the geometry types are not known.
- The geometry types in the list must be unique (e.g. `["Point", "Point"]` is not valid).

It is expected that this field is strictly correct. For example, if having both polygons and multipolygons, it is not sufficient to specify `["MultiPolygon"]`, but it is expected to specify `["Polygon", "MultiPolygon"]`. Or if having 3D points, it is not sufficient to specify `["Point"]`, but it is expected to list `["Point Z"]`.

These MUST match the corresponding [Geospatial Types](https://github.com/apache/parquet-format/blob/apache-parquet-format-2.12.0/Geospatial.md#geospatial-types)
in the Parquet statistics.

#### orientation

This attribute indicates the winding order of polygons. The only available value is `"counterclockwise"`. All vertices of exterior polygon rings MUST be ordered in the counterclockwise direction and all interior rings MUST be ordered in the clockwise direction.

If no value is set, no assertions are made about winding order or consistency of such between exterior and interior rings or between individual geometries within a dataset. Readers are responsible for verifying and if necessary re-ordering vertices as required for their analytical representation.

Writers are encouraged but not required to set `orientation="counterclockwise"` for portability of the data within the broader ecosystem.

It is RECOMMENDED to always set the orientation (to counterclockwise) if `edges` is `"spherical"` (see below).

#### edges

This attribute indicates how to interpret the edges of the geometries: whether the line between two points is a straight cartesian line or the shortest line on the sphere (geodesic line). Available values are:
 - `"planar"`: use a flat cartesian coordinate system.
 - `"spherical"`: Edges in the longitude-latitude dimensions follow the
    shortest distance between vertices approximated as the shortest distance
    between the vertices on a perfect sphere. This edge interpretation is used by
    [BigQuery Geography](https://cloud.google.com/bigquery/docs/geospatial-data#coordinate_systems_and_edges),
    and [Snowflake Geography](https://docs.snowflake.com/en/sql-reference/data-types-geospatial).
    A common library for interpreting edges in this way is
    [Google's s2geometry](https://github.com/google/s2geometry); a common formula
    for calculating distances along this trajectory is the
    [Haversine Formula](https://en.wikipedia.org/wiki/Haversine_formula).
  - `"vincenty"`: Edges in the longitude-latitude dimensions follow a path calculated
    using [Vincenty's formula](https://en.wikipedia.org/wiki/Vincenty%27s_formulae) and
    the ellipsoid specified by the `"crs"`.
  - `"thomas"`:  Edges in the longitude-latitude dimensions follow a path calculated by
    the fomula in Thomas, Paul D. Spheroidal geodesics, reference systems, & local geometry.
    US Naval Oceanographic Office, 1970 using the ellipsoid specified by the `"crs"`.
  - `"andoyer"`: Edges in the longitude-latitude dimensions follow a path calculated by
    the fomula in Thomas, Paul D. Mathematical models for navigation systems. US Naval
    Oceanographic Office, 1965 using the ellipsoid specified by the `"crs"`.
  - `"karney"`: Edges in the longitude-latitude dimensions follow a path calculated by
    the fomula in
    [Karney, Charles FF. "Algorithms for geodesics." Journal of Geodesy 87 (2013): 43-55](https://link.springer.com/content/pdf/10.1007/s00190-012-0578-z.pdf)
    and [GeographicLib](https://geographiclib.sourceforge.io/)
    using the ellipsoid specified by the `"crs"`. GeographicLib is available via modern
    versions of PROJ.

If no value is set, the default value to assume is `"planar"`.

Note if `edges` is not `"planar"` then it is RECOMMENDED that `orientation` is always ensured to be `"counterclockwise"`. If it is not set, it is not clear how polygons should be interpreted within spherical coordinate systems, which can lead to major analytical errors if interpreted incorrectly. In this case, software will typically interpret the rings of a polygon such that it encloses at most half of the sphere (i.e. the smallest polygon of both ways it could be interpreted). But the specification itself does not make any guarantee about this.

#### bbox

Bounding boxes are used to help define the spatial extent of each geometry column. Implementations of this schema may choose to use those bounding boxes to filter partitions (files) of a partitioned dataset.

The bbox, if specified, MUST be encoded with an array representing the range of values for each dimension in the geometry coordinates. For geometries in a geographic coordinate reference system, longitude and latitude values are listed for the most southwesterly coordinate followed by values for the most northeasterly coordinate. This follows the GeoJSON specification ([RFC 7946, section 5](https://tools.ietf.org/html/rfc7946#section-5)), which also describes how to represent the bbox for a set of geometries that cross the antimeridian.

For non-geographic coordinate reference systems, the items in the bbox are minimum values for each dimension followed by maximum values for each dimension. For example:
- XY (two dimensions): `[<xmin>, <ymin>, <xmax>, <ymax>]`
- XYZ (three dimensions): `[<xmin>, <ymin>, <zmin>, <xmax>, <ymax>, <zmax>]`
- XYZM (three dimensions with measure): `[<xmin>, <ymin>, <zmin>, <mmin>, <xmax>, <ymax>, <zmax>, <mmax>]`

It is not currently possible to specify M bounds without Z bounds using a GeoParquet metadata bbox: in this case, producers may produce an XY bounding box and omit M bounds. M bounds are typically encoded in Parquet statistics for consumers that benefit from this information.

The bbox values MUST be in the same coordinate reference system as the geometry.

### Additional information

#### Feature identifiers

If you are using GeoParquet to serialize geospatial data with feature identifiers, it is RECOMMENDED that you create your own [file key/value metadata](https://github.com/apache/parquet-format#metadata) to indicate the column that represents this identifier. As an example, GDAL writes additional metadata using the `gdal:schema` key including information about feature identifiers and other information outside the scope of the GeoParquet specification.

### OGC:CRS84 details

The PROJJSON object for OGC:CRS84 is:

```json
{
    "$schema": "https://proj.org/schemas/v0.5/projjson.schema.json",
    "type": "GeographicCRS",
    "name": "WGS 84 longitude-latitude",
    "datum": {
        "type": "GeodeticReferenceFrame",
        "name": "World Geodetic System 1984",
        "ellipsoid": {
            "name": "WGS 84",
            "semi_major_axis": 6378137,
            "inverse_flattening": 298.257223563
        }
    },
    "coordinate_system": {
        "subtype": "ellipsoidal",
        "axis": [
        {
            "name": "Geodetic longitude",
            "abbreviation": "Lon",
            "direction": "east",
            "unit": "degree"
        },
        {
            "name": "Geodetic latitude",
            "abbreviation": "Lat",
            "direction": "north",
            "unit": "degree"
        }
        ]
    },
    "id": {
        "authority": "OGC",
        "code": "CRS84"
    }
}
```

For implementations that operate entirely with longitude, latitude coordinates and are not CRS-aware or do not have easy access to CRS-aware libraries that can fully parse PROJJSON, it may be possible to infer that coordinates conform to the OGC:CRS84 CRS based on elements of the `crs` field.  For simplicity, Javascript object dot notation is used to refer to nested elements.

The CRS is likely equivalent to OGC:CRS84 for a GeoParquet file if the `id` element is present:

* `id.authority` = `"OGC"` and `id.code` = `"CRS84"`
* `id.authority` = `"EPSG"` and `id.code` = `4326` (due to longitude, latitude ordering in this specification)

It is reasonable for implementations to require that one of the above `id` elements are present and skip further tests to determine if the CRS is functionally equivalent with OGC:CRS84.

Note: EPSG:4326 and OGC:CRS84 are equivalent with respect to this specification because this specification specifically overrides the coordinate axis order in the `crs` to be longitude-latitude.

## Version Compatibility

GeoParquet version numbers follow [SemVer](https://semver.org), meaning patch releases are for bugfixes, minor releases represent backwards compatible changes, and major releases represent breaking changes. For this specification, a backwards compatible change means that a file written with the older specification will always be compatible with the newer specification. Minor releases are also guaranteed to be forward compatible up the the next major release. Forward compatiblity means that an implementation that is only aware of the older specification MUST be able to correctly interpret data written according to the newer specification, OR recognize that it cannot correctly interpret that data.

Examples of a forward compatible change include:
- Adding a new field in File or Column Metadata that can be ignored without changing the interpretation of the data (e.g. an index that can improve query performance).
- Adding a new option to an existing field.

Examples of a breaking change include:
- Adding a new field that cannot be ignored without changing the interpretation of the data.
- Changing the default value in an existing field.
- Changing the meaning of an existing field value.

In order to support data written according future minor relases, implementations of this specification:
- SHOULD NOT reject metadata with unknown fields.
- SHOULD explicitly validate all field values they rely on (e.g. an implementation of the 1.0.0 specification should validate enocoding = "WKB" even though it is the only allowed value, as new options might be added).

## File Extension

It is RECOMMENDED to use `.parquet` as the file extension for a GeoParquet file. This provides the best interoperability with existing Parquet tools. The file extension `.geoparquet` SHOULD NOT be used.

## Media Type

If a [media type](https://en.wikipedia.org/wiki/Media_type) (formerly: MIME type) is used, a GeoParquet file MUST use [application/vnd.apache.parquet](https://www.iana.org/assignments/media-types/application/vnd.apache.parquet) as the media type.
