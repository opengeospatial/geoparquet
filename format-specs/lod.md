# [Work in Progress] Levels of Detail

*This spec should currently be considered of "alpha" quality. There is much more to work out. We welcome early implementations and feedback, but please do not expect anywhere near the robustness of the main GeoParquet specification. You can track progress and contribute through the [GeoParquet issues](https://github.com/opengeospatial/geoparquet/issues).*

## Overview

This proposal defines optional metadata and multi-scale columns for storing lower-detail representations feature geometries. These additional columns allow readers to select lower-detail geometries appropriate for a given display scale without loading the full-resolution geometry.

This proposal applies to `LineString`, `MultiLineString`, `Polygon`, and `MultiPolygon` geometry columns. It is RECOMMENDED that writers also include ordering metadata. A file MAY implement this proposal independently from any ordering proposal.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## LOD metadata

The GeoParquet file metadata MAY contain a top-level `lod` object:

| Field Name | Type | Description |
| --- | --- | --- |
| `geometry_column` | string | **REQUIRED.** Name of the authoritative full-resolution line or polygon geometry column. The name MUST exist in the GeoParquet `columns` metadata. |
| `encoding` | string | **REQUIRED.** Encoding shared by every LOD column. MUST currently be `"pbf"`. |
| `orientation` | string | **REQUIRED.** Winding order of polygon exterior rings in every LOD column. MUST be `"clockwise"`. Interior rings use the opposite winding order. MUST be omitted for line geometry. |
| `levels` | \[[Level](#level)] | **REQUIRED.** One or more LOD levels. |


### Geometry column requirements

The column identified by `lod.geometry_column` is the authoritative full-resolution geometry for each feature. Its `geometry_types` metadata MUST contain exactly one value whose base geometry type is `LineString`, `MultiLineString`, `Polygon`, or `MultiPolygon`. The value MAY include the `Z`, `M`, or `ZM` dimensional suffix defined by the GeoParquet specification.

The CRS MUST be equivalent to WGS 84 longitude-latitude or Web Mercator. The conventional EPSG identifiers are EPSG:4326 and EPSG:3857, respectively.

### `geolod` column group

The `geolod` group column MUST exist at the root of the Parquet schema and MUST NOT be nested in another group. Every column referenced by `lod.levels` MUST be a direct child of this group.

LOD column names are encoded as two-element Parquet schema paths. The first item MUST be `"geolod"`, and the second item names a child field. For example, `["geolod", "level_1"]` identifies the `level_1` field in the `geolod` group.

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

