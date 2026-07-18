# GeoParquet Specification

## Overview

The [Apache Parquet](https://parquet.apache.org/) provides a standardized open-source columnar storage format. The GeoParquet specification originally defined how geospatial data should be stored in Parquet format, including the representation of geometries and the required additional metadata. As of Parquet version 2.11, released in March 2025, the Parquet format specifies [geospatial types and statistics](https://github.com/apache/parquet-format/blob/apache-parquet-format-2.12.0/Geospatial.md). The 2.0 version of the GeoParquet specification provides guidance for geospatial tools to implement Parquet Geometry and Geography types, along with some optional metadata not covered in the core Parquet specification.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Version and schema

This is version 2.1.0 of the GeoParquet specification.  See the [JSON Schema](schema.json) to validate metadata for this version. See [Version Compatibility](#version-compatibility) for details on version compatibility guarantees.

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

|   Field Name   |  Type  |                             Description                              |
| -------------- | ------ | -------------------------------------------------------------------- |
| version        | string | **REQUIRED.** The version identifier for the GeoParquet specification. |
| primary_column | string | **REQUIRED.** The name of the "primary" geometry column. In cases where a GeoParquet file contains multiple geometry columns, the primary geometry may be used by default in geospatial operations. |
| columns        | object\<string, [Column Metadata](#column-metadata)> | **REQUIRED.** Metadata about geometry columns. Each key is the name of a geometry column in the table. |
| display        | [Display Metadata](#display-optimization) | Optional metadata describing spatial row ordering and other optimizations for display streaming. |

At this level, additional implementation-specific fields (e.g. library name) MAY be present, and readers should be robust in ignoring those.

### Column metadata

Each geometry column in the dataset MUST be included in the `columns` field above with the following content, keyed by the column name:

| Field Name     | Type         | Description |
| -------------- | ------------ | ----------- |
| encoding       | string       | **REQUIRED.** Name of the geometry encoding format. Only `"WKB"` is supported. |
| geometry_types | \[string]    | **REQUIRED.** The geometry types of all geometries, or an empty array if they are not known. |
| crs            | object\|null | [PROJJSON](https://proj.org/specifications/projjson.html) object representing the Coordinate Reference System (CRS) of the geometry, or `null` if the CRS is undefined or unknown. It MUST describe the same CRS as the Parquet logical-type `crs` property on the geometry column (see [`crs` Parquet property](#crs-parquet-property)). If the field is not provided, the default CRS is [OGC:CRS84](https://www.opengis.net/def/crs/OGC/1.3/CRS84), which means the data in this column must be stored in longitude, latitude based on the WGS84 datum. |
| orientation    | string       | Winding order of exterior ring of polygons. If present must be `"counterclockwise"`; interior rings are wound in opposite order. If absent, no assertions are made regarding the winding order. |
| edges          | string       | Describes how to interpret the edges of the geometries. Must be one of `planar`, `spherical`, `vincenty`, `thomas`, `andoyer`, `karney`. The default value is `planar`.
| bbox           | \[number]    | Bounding Box of the geometries in the file, formatted according to [RFC 7946, section 5](https://tools.ietf.org/html/rfc7946#section-5). |
| epoch          | number       | Coordinate epoch in case of a dynamic CRS, expressed as a decimal year. |

#### crs

The Coordinate Reference System (CRS) is an optional parameter for each geometry column defined in GeoParquet format.

Since GeoParquet 2 the CRS travels with the geometry column on the Parquet `GEOMETRY`/`GEOGRAPHY` logical type's `crs` property, which is the source of truth (see [`crs` Parquet property](#crs-parquet-property)). That Parquet property is flexible and MAY identify the CRS in several forms. The GeoParquet column-metadata `crs` field described here restates that same CRS for files that carry GeoParquet `geo` metadata. (Writing that metadata is itself optional — a writer MAY emit only the native Parquet geospatial types — but a file that does carry GeoParquet metadata describes its CRS here.) Unlike the Parquet property, the GeoParquet `crs` field MUST be inline PROJJSON (or `null`), so that a reader of the GeoParquet metadata can always obtain a complete CRS definition directly, without resolving an authority code against an external registry.

The CRS, when given in the GeoParquet column-metadata `crs` field, MUST be provided in [PROJJSON](https://proj.org/specifications/projjson.html) format, which is a JSON encoding of [WKT2:2019 / ISO-19162:2019](https://docs.opengeospatial.org/is/18-010r7/18-010r7.html), which itself implements the model of [OGC Topic 2: Referencing by coordinates abstract specification / ISO-19111:2019](http://docs.opengeospatial.org/as/18-005r4/18-005r4.html). Apart from the difference of encodings, the semantics are intended to match WKT2:2019, and a CRS in one encoding can generally be represented in the other.

If the `crs` key does not exist, all coordinates in the geometries MUST use longitude, latitude based on the WGS84 datum, and the default value is [OGC:CRS84](https://www.opengis.net/def/crs/OGC/1.3/CRS84) for CRS-aware implementations. Note that a missing `crs` key has different meaning than a `crs` key set to `null` (see below).

[OGC:CRS84](https://www.opengis.net/def/crs/OGC/1.3/CRS84) is equivalent to the well-known [EPSG:4326](https://epsg.org/crs_4326/WGS-84.html) but changes the axis from latitude-longitude to longitude-latitude.

See below for additional details about representing or identifying OGC:CRS84.

The value of this key may be explicitly set to `null` to indicate that there is no CRS assigned to this column (CRS is undefined or unknown). When the GeoParquet column-metadata `crs` is `null`, the Parquet logical-type `crs` property SHOULD be set to the string `srid:0` (see [`crs` Parquet property](#crs-parquet-property)).

The GeoParquet column-metadata `crs` field, when present, MUST describe the same CRS as the Parquet `crs` property on the `GEOMETRY` or `GEOGRAPHY` logical type. Because the GeoParquet field is always inline PROJJSON (or `null`) while the Parquet property MAY use other forms, the two need not be byte-for-byte identical, but they MUST NOT describe different coordinate reference systems.

##### `crs` Parquet property

In GeoParquet 2.0 the geometry columns are stored using the native Parquet `GEOMETRY`/`GEOGRAPHY` logical types, and the CRS travels with the column on the logical type's `crs` property. Producing these native geospatial Parquet types is the foundation of GeoParquet 2.0 and is what every writer should do; the GeoParquet `geo` metadata layers additional, more explicit information on top — including a restatement of the CRS that is guaranteed to be inline PROJJSON.

The Parquet Geospatial definitions have a [crs customization](https://github.com/apache/parquet-format/blob/apache-parquet-format-2.12.0/Geospatial.md#crs-customization) section that permits several forms for the `crs` property: inline PROJJSON, an `<authority>:<code>` string (e.g. `EPSG:4326`), `srid:<identifier>`, and `projjson:<key_name>`.

The rules in the rest of this subsection govern the **native Parquet `crs` property** on the `GEOMETRY`/`GEOGRAPHY` logical type. They do not relax the requirement on the GeoParquet column-metadata `crs` field, which is always inline PROJJSON or `null` (see [crs](#crs)).

GeoParquet 2.0 does not restrict which of these forms a writer uses for the Parquet `crs` property. A writer SHOULD use one of:

- **inline PROJJSON** — self-describing and requiring no external CRS registry, or
- **an `<authority>:<code>` string** — compact and convenient. This is the RECOMMENDED form for writers that cannot readily generate PROJJSON (e.g. pure-SQL pipelines or lightweight browser-side writers).

A writer that cannot generate PROJJSON is encouraged to simply write the native Parquet geospatial types with an `<authority>:<code>` `crs` and omit the GeoParquet `geo` metadata. Such a file is not conformant GeoParquet 2.0, but any GeoParquet 2.0 reader should still be able to read it (see the reader rules below). Conversely, any file that does carry GeoParquet `geo` metadata MUST express its CRS as inline PROJJSON there.

When the CRS is undefined or unknown, the writer SHOULD set the Parquet `crs` property to the string `srid:0`. The Parquet core specification mentions the `srid:<identifier>` form but does not assign a meaning to a value of `0`; GeoParquet 2.0 adopts `srid:0` to mean an undefined or unknown CRS, following the convention used by [GeoPackage](https://www.geopackage.org/spec/), where an SRID of `0` denotes an undefined CRS.

A GeoParquet 2.0 reader MUST be able to interpret the Parquet `crs` property in both inline PROJJSON and `<authority>:<code>` form. Readers SHOULD additionally try to parse the other Parquet-core representations (`srid:<identifier>` and `projjson:<key_name>`) when encountered, to improve interoperability with the broader Parquet geospatial ecosystem.

If a writer also carries GeoParquet `geo` metadata for the column, its `crs` field MUST contain the resolved CRS as inline PROJJSON (or `null` when the Parquet `crs` is `srid:0`). This guarantees that any reader of the GeoParquet metadata can obtain a complete CRS definition directly, without resolving an authority code. The GeoParquet column-metadata `crs` and the Parquet `crs` property MUST NOT describe different coordinate reference systems.

| Parquet logical-type `crs`              | GeoParquet column-metadata `crs`           | Meaning                                       |
| --------------------------------------- | ------------------------------------------ | --------------------------------------------- |
| absent (Parquet default)                | absent                                     | OGC:CRS84                                     |
| inline PROJJSON object                  | the same CRS as inline PROJJSON            | CRS fully described in metadata               |
| `<authority>:<code>` string             | the resolved CRS as inline PROJJSON        | CRS identified by an authority code           |
| `srid:0`                                | `null`                                     | CRS undefined or unknown                      |

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

It is RECOMMENDED to always set the orientation to counterclockwise if `edges` is `"spherical"` (see below).

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
  the formula in Thomas, Paul D. Spheroidal geodesics, reference systems, & local geometry.
  US Naval Oceanographic Office, 1970 using the ellipsoid specified by the `"crs"`.
- `"andoyer"`: Edges in the longitude-latitude dimensions follow a path calculated by
  the formula in Thomas, Paul D. Mathematical models for navigation systems. US Naval
  Oceanographic Office, 1965 using the ellipsoid specified by the `"crs"`.
- `"karney"`: Edges in the longitude-latitude dimensions follow a path calculated by
  the formula in
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

## Display optimization

The optional `display` metadata indicates which spatial optimizations, such as spatial ordering or levels of detail, have been applied to the file to enable streaming for display.


| Field Name | Type | Description |
| --- | --- | --- |
| `geometry_column` | string | **REQUIRED.** Name of the geometry column used for display ordering and LOD generation. The name MUST exist in `columns`. |
| `ordering` | [Z Ordering](#z-order-point-ordering) \| [XZ Ordering](#xz-order-geometry-ordering) | **REQUIRED.** The spatial ordering of the file. |
| `lods` | [Levels of Detail](#levels-of-detail) | These levels describe the geometry columns that provide lower-detail representations of the `geometry_column` at different scales. MUST be present when `ordering` type is `"xz"`.|

### Geometry column requirements

The geometry identified by `display.geometry_column` is the authoritative full-resolution geometry for each displayed feature. It MUST satisfy the following requirements:

- `geometry_types` MUST contain exactly one value:
  - For `"z"` ordering it MUST be `Point`.
  - For `"xz"` ordering it MUST be one of `MultiPoint`, `LineString`, `MultiLineString`, `Polygon`, or `MultiPolygon`.
- The CRS MUST be equivalent to WGS 84 longitude-latitude or Web Mercator. The conventional EPSG identifiers are EPSG:4326 and EPSG:3857, respectively.

### Geodisplay column

The `geodisplay` group column MUST exist at the root of the schema. It MUST NOT be nested in another group. Every ordering and LOD field referenced by `display` MUST be a direct child of this group.

The `geodisplay` group MAY be required or optional. Every referenced child field MUST be required whenever the group exists.

Display column names are encoded as two-element Parquet schema paths. The first item in every path MUST be `"geodisplay"`, and the second item names a child field. For example, `["geodisplay", "ordering_code"]` identifies the `ordering_code` field in the `geodisplay` group.

### Ordering extent

`geodisplay` ordering types contain an `extent` defined as `[xmin, ymin, xmax, ymax]`. The values MUST be finite, MUST satisfy `xmin < xmax` and `ymin < ymax`, and MUST use the CRS of `display.geometry_column`. If every geometry is either NULL or non-finite, `geodisplay` MUST be null or undefined.

### Z-order point ordering

Z-ordering spatially orders points by interleaving X and Y coordinate bits.

| Field Name | Type | Description |
| --- | --- | --- |
| `type` | string | **REQUIRED.** MUST be `"z"`. |
| `extent` | \[number] | **REQUIRED.** Four-element ordered normalization extent for the point coordinates. |
| `column` | \[string] | **REQUIRED.** Path of the Morton-code column, stored as Parquet `INT64` annotated as unsigned 64-bit. |
| `bit_width` | integer | **REQUIRED.** Number of bits used to quantize each coordinate axis before Morton-code interleaving. MUST be between `1` and `32`. |

To generate a Z code, a writer MUST:

1. Normalize X and Y independently into the range from `0` through `1` using `extent`.
2. Multiply each normalized coordinate by `2^bit_width`.
3. Truncate each result to an integer and clamp it to the range from `0` through `2^bit_width - 1`.
4. Interleave X bits into even bit positions and Y bits into odd bit positions, starting with the least-significant bit.
5. Sort rows by the resulting unsigned code.

### XZ-order geometry ordering

XZ ordering spatially orders non-point geometries using feature extents.

| Field Name | Type | Description |
| --- | --- | --- |
| `type` | string | **REQUIRED.** MUST be `"xz"`. |
| `extent` | \[number] | **REQUIRED.** Four-element ordered normalization extent used for XZ-code generation. |
| `column` | \[string] | **REQUIRED.** Path of the XZ-code column, stored as Parquet `INT64` annotated as unsigned 64-bit. |
| `max_level` | integer | **REQUIRED.** Maximum XZ hierarchy depth. MUST currently be `20`. |

XZ-code generation MUST follow the [XZ-ordering algorithm described by Böhm et al.](http://dx.doi.org/10.1007/3-540-48482-5_7):

1. Compare the feature extent width and height with the corresponding normalization extent.
2. Select the deepest level at which the feature fits within the enlarged two-cell XZ region, capped by `max_level`.
3. Recursively subdivide the normalization extent into four quadrants.
4. Encode the quadrant sequence containing the feature extent's lower-left corner.
5. Sort rows by the resulting unsigned code.

Clients can compute the XZ covering of a query extent and compare it with page-level code statistics to skip unrelated byte ranges.

### Levels of detail

The optional `lods` object describes derived geometry columns at one or more scales. It MUST be present when `ordering.type` is `"xz"`.

| Field Name | Type | Description |
| --- | --- | --- |
| `encoding` | string | **REQUIRED.** Encoding shared by all LOD columns. MUST currently be `"pbf"`, the PBF Geometry format defined below. |
| `orientation` | string | **REQUIRED.** Winding order of polygon exterior rings in every LOD column. MUST be `"clockwise"`; interior rings use the opposite winding order. |
| `levels` | \[[Level](#level)] | **REQUIRED.** One or more unique LOD levels. |

#### Level

A `Level` object describes one derived geometry column and its display resolution:

| Field Name | Type | Description |
| --- | --- | --- |
| `column` | \[string] | **REQUIRED.** Path of the LOD column, stored as Parquet `BYTE_ARRAY` type. |
| `scale` | number | **REQUIRED.** Map scale associated with the level.
| `transform` | [Transform](#transform) | **REQUIRED.** Scale and translation used to quantize and unquantize X, Y, Z, and M values. |

##### Transform

A `Transform` object contains the scale and translation for each coordinate dimension:

| Field Name | Type | Description |
| --- | --- | --- |
| `scale` | \[number] | **REQUIRED.** Four scale values ordered as X, Y, Z, and M. |
| `translate` | \[number] | **REQUIRED.** Four translation values ordered as X, Y, Z, and M. |

`scale` and `translate` are both tuples ordered as X, Y, Z, and M and MUST contain four finite numbers. Scale values MUST be positive. Writers MUST use scale `1` and translation `0` for dimensions absent from the source geometry.

#### LOD generation

Feature geometries are quantized for each level, reducing the number of vertices needed at each scale.

```text
quantized = round((coordinate - translate) / scale)
```

The way that writers quantize geometries is implementation dependent, but the following steps are RECOMMENDED:
- For 2D geometries with only XY, snap vertices to the level grid and merge consecutive collinear vertices.
- For geometry containing Z or M, pixel snapping is not ideal as it does not preserve original vertices, making Z and M values ambiguous. First generalize with [Douglas-Peucker](https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm), using the XY resolution associated with the `scale` as the tolerance. Then snap the retained XY coordinates to the level grid and encode them as deltas, while preserving the Z and M values attached to those source vertices.

#### PBF Geometry format

The `"pbf"` format encodes flattened geometries in a Protocol Buffers message:

```proto
message Geometry {
  repeated uint32 lengths = 2 [packed = true];
  repeated sint64 coords = 3 [packed = true];
}
```

Each `lengths` value contains the vertex count of one path or ring. The coordinate stride is two for XY, three when the dimensional suffix contains Z or M, and four when it contains ZM. Coordinates are interleaved per vertex as XY, XYZ, XYM, or XYZM.

The first X and Y values of each part are absolute quantized coordinates. Later X and Y values are deltas from the preceding vertex. Z and M values are absolute quantized coordinates for every vertex and MUST NOT use delta encoding. Missing, non-finite Z or M ordinates MUST encode as `0`.

##### Polygon winding

Polygon exterior rings MUST be clockwise and interior rings MUST be counterclockwise. This rule is independent of the full-resolution GeoParquet `orientation`. Writers MUST therefore reorient derived rings when required. Quantization may collapse a ring to a single coordinate or otherwise remove a stable orientation.

##### Polygon example

Consider the following polygon in WGS 84 longitude-latitude coordinates. It contains one clockwise exterior ring and one counterclockwise interior ring:

```text
Polygon {
  rings: [
    [
      [-122.50, 37.70], [-122.50, 37.80], [-122.40, 37.80],
      [-122.40, 37.70], [-122.50, 37.70]
    ],
    [
      [-122.48, 37.72], [-122.42, 37.72], [-122.42, 37.78],
      [-122.48, 37.78], [-122.48, 37.72]
    ]
  ]
}
```

With `scale` set to `[0.01, 0.01, 1, 1]` and `translate` set to `[-132.50, 17.70, 0, 0]`, the coordinate `[-122.40, 37.80]` quantizes to `[1010, 2010]`:

```text
x = round((-122.40 - -132.50) / 0.01) = 1010
y = round((  37.80 -   17.70) / 0.01) = 2010
```

The complete rings quantize to:

```text
[
  [[1000, 2000], [1000, 2010], [1010, 2010], [1010, 2000], [1000, 2000]],
  [[1002, 2002], [1008, 2002], [1008, 2008], [1002, 2008], [1002, 2002]]
]
```

Each ring contains five coordinates, including its closing coordinate:

```text
lengths: [5, 5]
```

The first X and Y values of each ring remain absolute. Every later X and Y value stores the delta from the preceding coordinate:

```text
coords: [
  1000, 2000,   0, 10,  10,  0,   0, -10, -10,  0,
  1002, 2002,   6,  0,   0,  6,  -6,   0,   0, -6
]
```

This produces the following Geometry message:

```text
Geometry {
  lengths: [5, 5],
  coords: [1000, 2000, 0, 10, 10, 0, 0, -10, -10, 0, 1002, 2002, 6, 0, 0, 6, -6, 0, 0, -6]
}
```

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

For implementations that operate entirely with longitude, latitude coordinates and are not CRS-aware or do not have easy access to CRS-aware libraries that can fully parse PROJJSON, it may be possible to infer that coordinates conform to the OGC:CRS84 CRS based on properties of the `crs` field. For simplicity, JavaScript object dot notation is used to refer to nested properties below.

The CRS is likely equivalent to OGC:CRS84 for a GeoParquet file if the `id` property is present:

- `id.authority` = `"OGC"` and `id.code` = `"CRS84"`
- `id.authority` = `"EPSG"` and `id.code` = `4326` (due to longitude, latitude ordering in this specification)

It is reasonable for implementations to require that one of the above `id` combinations are present and skip further tests to determine if the CRS is functionally equivalent with OGC:CRS84.

> [!NOTE]
>
> EPSG:4326 and OGC:CRS84 are equivalent with respect to this specification because this specification specifically overrides the coordinate axis order in the `crs` to be longitude-latitude.

When the Parquet `crs` property identifies the CRS by an `<authority>:<code>` string, the values `"OGC:CRS84"` and `"EPSG:4326"` are likewise equivalent to OGC:CRS84 for the purposes of this specification.

## Version Compatibility

GeoParquet version numbers follow [SemVer](https://semver.org), meaning patch releases are for bugfixes, minor releases represent backwards compatible changes, and major releases represent breaking changes. For this specification, a backwards compatible change means that a file written with the older specification will always be compatible with the newer specification. Minor releases are also guaranteed to be forward compatible up to the next major release. Forward compatibility means that an implementation that is only aware of the older specification MUST be able to correctly interpret data written according to the newer specification, OR recognize that it cannot correctly interpret that data.

Examples of a forward compatible change include:

- Adding a new field in File or Column Metadata that can be ignored without changing the interpretation of the data (e.g. an index that can improve query performance).
- Adding a new option to an existing field.

Examples of a breaking change include:

- Adding a new field that cannot be ignored without changing the interpretation of the data.
- Changing the default value in an existing field.
- Changing the meaning of an existing field value.

In order to support data written according to future minor releases, implementations of this specification:

- SHOULD NOT reject metadata with unknown fields.
- SHOULD explicitly validate all field values they rely on (e.g. an implementation of the 1.0.0 specification should validate encoding = "WKB" even though it is the only allowed value, as new options might be added).

## File Extension

It is RECOMMENDED to use `.parquet` as the file extension for a GeoParquet file. This provides the best interoperability with existing Parquet tools. The file extension `.geoparquet` SHOULD NOT be used.

## Media Type

If a [media type](https://en.wikipedia.org/wiki/Media_type) (formerly: MIME type) is used, a GeoParquet file MUST use [application/vnd.apache.parquet](https://www.iana.org/assignments/media-types/application/vnd.apache.parquet) as the media type.
