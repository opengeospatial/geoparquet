# [Work in Progress] Spatial Ordering

*This spec should currently be considered of "alpha" quality. There is much more to work out. We welcome early implementations and feedback, but please do not expect anywhere near the robustness of the main GeoParquet specification. You can track progress and contribute through the [GeoParquet issues](https://github.com/opengeospatial/geoparquet/issues).*

## Overview

This proposal defines metadata and a physical cluster key for spatially ordered GeoParquet files. Spatial ordering places nearby features near one another in the row sequence, allowing Parquet readers to use row-group and page statistics to skip unrelated byte ranges.

Two ordering methods are supported:

- **Z ordering** for point geometries.
- **XZ ordering** for geometries represented by two-dimensional extents.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## Ordering metadata

Spatial ordering is described by an optional `ordering` field in the GeoParquet file metadata. Its value MUST be either a [Z ordering](#z-ordering) object or an [XZ ordering](#xz-ordering) object.

The geometry column's CRS MUST be equivalent to WGS 84 longitude-latitude or Web Mercator. The conventional EPSG identifiers are EPSG:4326 and EPSG:3857, respectively.

### `geokey` column

A spatially ordered file MUST contain a root column named `geokey`. It MUST NOT be nested in a group or another column.

`geokey` MUST use either the Parquet physical type `INT32` with the unsigned 32-bit integer logical type or `INT64` with the unsigned 64-bit integer logical type. Every generated key MUST fit within the selected unsigned integer type. Rows MUST be sorted by `geokey` in ascending unsigned order.

### Ordering extent

The `extent` values MUST be finite, MUST satisfy `xmin < xmax` and `ymin < ymax`, and MUST use the CRS of `geometry_column`. The extent establishes the normalization domain for every cluster key in the file.

## Z ordering

Z ordering spatially orders points by interleaving quantized X and Y coordinate bits. The geometry column's `geometry_types` metadata MUST contain exactly one value, and that value MUST be `Point` with any valid dimensional suffix.

| Field Name | Type | Description |
| --- | --- | --- |
| `type` | string | **REQUIRED.** MUST be `"z"`. |
| `geometry_column` | string | **REQUIRED.** Name of the point geometry column used to calculate the cluster key. The name MUST exist in the GeoParquet `columns` metadata. |
| `extent` | \[number] | **REQUIRED.** Four-element normalization extent formatted as `[xmin, ymin, xmax, ymax]`. |
| `bit_width` | integer | **REQUIRED.** Number of bits used to quantize each coordinate axis. MUST be between `1` and `32`. |


To generate a Z cluster key, a writer MUST:

1. Normalize X and Y independently to the range from `0` through `1` using `extent`.
2. Multiply each normalized coordinate by `2^bit_width`.
3. Truncate each result to an integer and clamp it to the range from `0` through `2^bit_width - 1`.
4. Interleave X bits into even bit positions and Y bits into odd bit positions, starting with the least-significant bit.
5. Store the resulting unsigned Morton code in `geokey`.

## XZ ordering

XZ ordering spatially orders geometries using their two-dimensional feature extents. The geometry column's `geometry_types` metadata MUST contain one or more of `MultiPoint`, `LineString`, `MultiLineString`, `Polygon`, or `MultiPolygon`, with any valid dimensional suffix.

| Field Name | Type | Description |
| --- | --- | --- |
| `type` | string | **REQUIRED.** MUST be `"xz"`. |
| `geometry_column` | string | **REQUIRED.** Name of the geometry column used to calculate the cluster key. The name MUST exist in the GeoParquet `columns` metadata. |
| `extent` | \[number] | **REQUIRED.** Four-element normalization extent formatted as `[xmin, ymin, xmax, ymax]`. |
| `max_level` | integer | **REQUIRED.** Maximum XZ hierarchy depth. MUST currently be `20`. |


XZ cluster key generation MUST follow the [XZ-ordering algorithm described by Böhm et al.](https://doi.org/10.1007/3-540-48482-5_7):

1. Calculate the feature's finite two-dimensional extent.
2. Compare the feature extent's width and height with the corresponding normalization extent.
3. Select the deepest level at which the feature fits within the enlarged two-cell XZ region, capped by `max_level`.
4. Recursively subdivide the normalization extent into four quadrants.
5. Encode the quadrant sequence containing the feature extent's lower-left corner.
6. Store the resulting unsigned XZ code in `geokey`.
