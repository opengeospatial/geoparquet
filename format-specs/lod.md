# [Work in Progress] Levels of Detail

*This spec should currently be considered of "alpha" quality. There is much more to work out. We welcome early implementations and feedback, but please do not expect anywhere near the robustness of the main GeoParquet specification. You can track progress and contribute through the [GeoParquet issues](https://github.com/opengeospatial/geoparquet/issues).*

## Overview

This proposal defines optional metadata that relates an authoritative geometry column to lower-detail geometry columns. Readers can select a representation appropriate for a target display resolution without loading the full-resolution geometry.

Each lower-detail representation is a standard GeoParquet geometry column with its own column metadata and encoding. This proposal defines only the relationship between those columns and does not define a geometry encoding, spatial ordering, covering, or simplification algorithm.

This proposal applies to `LineString`, `MultiLineString`, `Polygon`, and `MultiPolygon` geometry columns.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## LOD metadata

Each geometry column definition in the GeoParquet `columns` metadata MAY contain an `lods` field:

| Field Name | Type | Description |
| --- | --- | --- |
| `lods` | \[[Level](#level)] | One or more lower-detail geometry levels. MUST be undefined if this column is referenced by the `lods` of another column. |

The geometry column containing the `lods` field is the authoritative full-resolution geometry column. It MUST NOT reference itself as an LOD level.

### Geometry column paths

For files implementing this proposal, any geometry column definition in the GeoParquet `columns` metadata MAY contain a `path` field:

| Field Name | Type | Description |
| --- | --- | --- |
| `path` | \[string] | Parquet schema path that identifies the geometry column. |

If `path` is omitted, it defaults to a single path component containing the geometry column name. For example, the `geometry` metadata entry defaults to `["geometry"]`.

Every explicit `path` MUST contain one or more non-empty strings. The path starts at the root of the Parquet schema and contains one component for each field traversed. Every component except the last MUST identify a non-repeated group field. The last component MUST identify the leaf field that stores geometry values using the encoding declared by the column metadata.

Resolved paths MUST be unique among the entries in `columns`. No field in a resolved path may be repeated, so geometry columns cannot be nested within lists, arrays, maps, or other repeated structures.

### Level

A `Level` object identifies one lower-detail geometry column and its display resolution:

| Field Name | Type | Description |
| --- | --- | --- |
| `column` | string | **REQUIRED.** Identifier of the lower-detail geometry column in the GeoParquet `columns` metadata. |
| `resolution` | number | **REQUIRED.** Positive finite size of one logical display pixel in CRS coordinate units. |

Each `column` MUST identify a distinct entry in the GeoParquet `columns` metadata. The referenced entry's resolved path locates the physical Parquet column. LOD column references MUST NOT additionally specify `lods`.

The authoritative and LOD columns MUST use equivalent coordinate reference systems and edge interpretations. Their non-empty `geometry_types` metadata MUST belong to the same geometry family, either `LineString` and `MultiLineString` or `Polygon` and `MultiPolygon`. Every geometry type MUST use the same dimensional suffix: no suffix, `Z`, `M`, or `ZM`.

A `resolution` value describes the nominal spatial resolution of the represented geometry. Writers SHOULD list each geometry column at most once and MUST NOT use the same `resolution` for more than one level of the same authoritative geometry column.

### Selecting a level

Given a target display resolution in CRS coordinate units per logical pixel, readers SHOULD select the level with the largest `resolution` that does not exceed the target resolution. This chooses the least detailed level that still provides at least one source sample per logical display pixel.

If no LOD level has a resolution less than or equal to the target resolution, readers SHOULD use the authoritative full-resolution geometry column.

When a display system starts from a scale denominator, it can derive a target resolution using:

```text
target_resolution =
    scale_denominator
    * physical_pixel_size_in_meters
    / meters_per_crs_unit
```

The physical pixel size depends on the scale convention. ArcGIS uses `96` dots per inch, equivalent to approximately `0.000264583` meters per pixel. OGC standards commonly use `0.00028` meters per pixel.

For a geographic CRS, the conversion between angular CRS units and meters varies by location and direction. Readers SHOULD instead use the display resolution already expressed in that CRS when available.

## LOD generation

The method used to create lower-detail geometries is implementation dependent. Writers MAY simplify, quantize, aggregate, or otherwise derive each level, provided every output geometry represents the same feature as the authoritative geometry at the advertised resolution.

## Metadata example

The following metadata relates one authoritative WKB geometry column to two lower-detail WKB geometry columns:

```json
{
  "version": "2.0.0",
  "primary_column": "geometry",
  "columns": {
    "geometry": {
      "encoding": "WKB",
      "geometry_types": ["Polygon", "MultiPolygon"],
      "lods": [
        {
          "column": "lod_0",
          "resolution": 0.01
        },
        {
          "column": "lod_1",
          "resolution": 0.001
        }
      ]
    },
    "lod_0": {
      "path": ["lods", "level_0"],
      "encoding": "WKB",
      "geometry_types": ["Polygon", "MultiPolygon"]
    },
    "lod_1": {
      "path": ["lods", "level_1"],
      "encoding": "WKB",
      "geometry_types": ["Polygon", "MultiPolygon"]
    }
  }
}
```
