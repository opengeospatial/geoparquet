# [Work in Progress] PBF Geometry Encoding

*This spec should currently be considered of "alpha" quality. There is much more to work out. We welcome early implementations and feedback, but please do not expect anywhere near the robustness of the main GeoParquet specification. You can track progress and contribute through the [GeoParquet issues](https://github.com/opengeospatial/geoparquet/issues).*

## Overview

The PBF geometry encoding stores quantized geometry coordinates in a compact Protocol Buffers message. It can encode any supported GeoParquet geometry column independently from level-of-detail, spatial-ordering, or display metadata.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Column metadata

A PBF geometry column declares its encoding and coordinate transform in the GeoParquet column metadata:

```json
{
  "encoding": {
    "pbf": {
      "transform": {
        "scale": [0.01, 0.01, 1, 1],
        "translate": [-132.5, 17.7, 0, 0]
      }
    }
  },
  "geometry_types": ["Polygon"],
  "orientation": "clockwise"
}
```

The `pbf` object MUST contain one `transform` object:

| Field Name | Type | Description |
| --- | --- | --- |
| `scale` | \[number] | **REQUIRED.** Four positive scale values ordered as X, Y, Z, and M. |
| `translate` | \[number] | **REQUIRED.** Four translation values ordered as X, Y, Z, and M. |

Both arrays MUST contain exactly four finite numbers. Writers MUST use scale `1` and translation `0` for dimensions absent from the geometry column.

PBF geometry columns MUST have non-empty `geometry_types` metadata. Every listed type MUST belong to one geometry family: Point and MultiPoint, LineString and MultiLineString, or Polygon and MultiPolygon. Every listed type MUST use the same dimensional suffix: no suffix, `Z`, `M`, or `ZM`. GeometryCollection is not supported.

Polygon-family PBF columns MUST set the GeoParquet `orientation` field to `"clockwise"` so the column metadata matches this encoding's required exterior-ring winding convention. Point- and line-family PBF columns MUST omit `orientation`.

PBF values MUST be stored as Parquet `BYTE_ARRAY` values.

## Coordinate transform

Writers quantize every coordinate ordinate to a signed 64-bit integer:

```text
quantized = round((coordinate - translate) / scale)
```

Readers restore an ordinate to the coordinate space:

```text
coordinate = quantized * scale + translate
```

Implementations MUST round ties away from zero. The transform applies independently to X, Y, Z, and M.

## Geometry message

Each non-null Parquet value contains one serialized `Geometry` message:

```proto
message Geometry {
  repeated uint32 lengths = 2 [packed = true];
  repeated sint64 coords = 3 [packed = true];
}
```

The message derives from the geometry representation in the [ArcGIS FeatureCollection PBF specification](https://github.com/Esri/arcgis-pbf/tree/main/proto/FeatureCollection), while omitting fields supplied by GeoParquet column metadata.

Each `lengths` value contains the vertex count of one point, path, or ring. Point has one length of `1`. MultiPoint has one length of `1` per point. LineString has one path length. MultiLineString has one length per path. Polygon and MultiPolygon have one length per ring.

An empty geometry MUST encode empty `lengths` and `coords` arrays. A null geometry MUST use a null Parquet value rather than a serialized message.

The coordinate stride is two for XY, three for XYZ or XYM, and four for XYZM. Coordinates are interleaved per vertex as XY, XYZ, XYM, or XYZM. The dimensional suffix in `geometry_types` determines the stride and whether the third ordinate represents Z or M.

The first X and Y values of each part are absolute quantized coordinates. Later X and Y values are deltas from the preceding vertex in that part. Z and M values are absolute quantized coordinates for every vertex and MUST NOT use delta encoding. Missing or non-finite Z or M ordinates MUST encode as `0`.

The sum of `lengths`, multiplied by the coordinate stride, MUST equal the number of values in `coords`.

## Polygon rings

Polygon rings MUST be closed. Exterior rings MUST be clockwise and interior rings MUST be counterclockwise in quantized coordinate space.

Rings for each polygon MUST place the exterior ring first, followed immediately by its interior rings. In a MultiPolygon, each clockwise ring begins a new polygon and subsequent counterclockwise rings belong to that polygon until the next clockwise ring.

## Example

Consider a polygon with one exterior ring and one interior ring:

```text
[
  [[-122.50, 37.70], [-122.50, 37.80], [-122.40, 37.80],
   [-122.40, 37.70], [-122.50, 37.70]],
  [[-122.48, 37.72], [-122.42, 37.72], [-122.42, 37.78],
   [-122.48, 37.78], [-122.48, 37.72]]
]
```

With scale `[0.01, 0.01, 1, 1]` and translate `[-132.50, 17.70, 0, 0]`, the rings quantize to:

```text
[
  [[1000, 2000], [1000, 2010], [1010, 2010], [1010, 2000], [1000, 2000]],
  [[1002, 2002], [1008, 2002], [1008, 2008], [1002, 2008], [1002, 2002]]
]
```

The resulting message contains:

```text
lengths: [5, 5]
coords: [
  1000, 2000, 0, 10, 10, 0, 0, -10, -10, 0,
  1002, 2002, 6, 0, 0, 6, -6, 0, 0, -6
]
```
