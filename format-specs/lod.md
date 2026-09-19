# [Proposal] Level of Detail (LoD) extension

This document proposes an optional GeoParquet Level of Detail (LoD) extension for progressive feature access.

## Motivation

Spatial ordering and bounding box statistics help readers find features within a viewport. They do not tell a reader how much of that viewport's data is useful at a given display scale. A world view may intersect almost every row group even though only a small subset of features can be distinguished on screen.

This proposal adds a second selection dimension: rendering resolution. Features useful at coarse resolutions are stored in earlier row groups; later row groups add finer detail. Small metadata describes cumulative row group prefixes, allowing readers to fetch a coarse view first and progressively add features as needed.

## Scope

The extension describes the physical layout of one GeoParquet file with respect to its primary geometry column. It preserves the table's features, geometries, and attributes, while permitting their order to change. Each input row occurs exactly once in the output, including when the input itself contains duplicate-valued rows.

The extension does not define a new geometry encoding, tile matrix, spatial index, or query language. It does not require a per-row level column, sidecar index, or duplicated rows for each resolution.

The key words "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", and "MAY" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Physical layout

A file using this extension MUST conform to the [GeoParquet specification](geoparquet.md).

Features MUST be assigned to ordered detail levels, from coarse to fine. A level represents the features selected for display at a nominal rendering resolution. Earlier levels should provide a useful view of the dataset; later levels may add features that the producer has deferred at coarser resolutions.

Each input row MUST be stored exactly once. Applying this layout MUST NOT simplify, aggregate, or otherwise change its geometry or attribute values. Derived rendering representations may be defined separately, but are not selected by this extension.

Rows introduced by each level MUST occupy consecutive whole Parquet row groups. A row group MUST NOT straddle a level boundary. Row groups MUST occur in coarse-to-fine order in the Parquet footer. Readers use the footer's column chunk offsets for access.

A level selects **all row groups from zero through its boundary**, inclusive. Later levels may add rows to that prefix; they do not replace the earlier rows. The last level includes the entire table.

For example, a file with eight row groups could have this layout:

```text
Row group:          0 | 1  2 | 3  4  5  6  7
New features:   coarse | medium | fine

Coarse selection: [0]
Medium selection: [0, 1, 2]
Fine selection:   [0, 1, 2, 3, 4, 5, 6, 7]
```

Within each level's newly introduced rows, producers SHOULD spatially cluster features to improve spatial pruning. The clustering method is not prescribed: Hilbert ordering, quadtree ordering, and STR packing are possible choices. A global spatial sort that interleaves detail levels would invalidate the declared layout.

## Metadata

The extension adds an OPTIONAL `lod` (level of detail) object to the GeoParquet file metadata stored under the `geo` key. When present, this object MUST contain the fields below. Its levels apply to the primary geometry column identified by `geo.primary_column`.

| Field | Type | Description |
| --- | --- | --- |
| `levels` | array of objects | **REQUIRED.** Non-empty list of levels, ordered from coarse to fine. |
| `levels[].row_group_end` | integer | **REQUIRED.** Zero-based, inclusive end of the selected row group prefix. |
| `levels[].resolution` | number | **REQUIRED.** Positive, finite nominal rendering resolution in the primary geometry column's CRS units. |

Example of the `geo.lod` object for the eight-row-group file above:

```json
{
  "levels": [
    { "row_group_end": 0, "resolution": 1000 },
    { "row_group_end": 2, "resolution": 100 },
    { "row_group_end": 7, "resolution": 10 }
  ]
}
```

### Boundaries

For a file containing `N` row groups:

* Each `row_group_end` MUST satisfy `0 <= row_group_end < N`.
* Boundaries MUST be non-decreasing.
* The final boundary MUST equal `N - 1`.
* Empty files MUST omit this extension. A non-empty file MAY declare a single level covering all its row groups.

Boundaries refer to this file's footer, not to row numbers, byte offsets, or row groups in another file. Partitioned datasets apply the extension independently to each file; this draft does not define a dataset-wide level index.

### Resolution

`resolution` is the nominal rendering resolution for which a feature prefix is intended to be rendered.

`resolution` MUST be expressed in the horizontal coordinate units of the primary geometry column's CRS. For example, a CRS using meters expresses resolution in meters, while a geographic CRS using degrees expresses it in degrees. Values MUST strictly decrease from coarse to fine.

Resolution is a display hint. It is not a bound on geometric error, positional accuracy, feature spacing, or analytical precision. The extension does not prescribe a projection, a zoom-to-resolution formula, or a pixel size. A renderer decides how its current display scale maps to a target resolution.

The target resolution is interpreted in the same CRS units as `resolution`. If the CRS is unknown, `resolution` uses the primary geometry's coordinate units without assigning them a physical unit.

### Metadata handling

Readers that do not support this extension can ignore `lod` and read the file as ordinary GeoParquet. Extension-aware readers MUST validate the required fields and boundary constraints before using the levels to exclude row groups. If the metadata is invalid, readers MUST NOT use it for prefix selection and SHOULD report the problem. They MAY fall back to ordinary GeoParquet access.

Readers MUST ignore unrecognized fields within `lod`. This proposal does not introduce an independent extension version field.

## Reader behavior

A typical rendering reader:

1. Reads the Parquet footer and validates the extension metadata against the row group count.
2. Chooses a level for its target resolution or rendering budget.
3. Applies row group spatial pruning within the selected prefix, from `0` through `row_group_end`.
4. Can further prune pages within the retained row groups when page indexes are available.
5. Fetches the required geometry and attribute data and evaluates the per-feature predicate.
6. Fetches additional data when finer detail or a different viewport is requested, reusing cached data where possible.

One possible level-selection policy is to choose the finest level whose `resolution` is greater than or equal to the target. Clamp to the first level when the target is coarser than every level, and to the last when it is finer than every level. With the example above, a target of 250 CRS units selects the level with `resolution: 1000`; a target of 100 CRS units selects the level with `resolution: 100`. Applications may choose a finer level when visual completeness matters more than transfer cost.

A prefix is a partial feature selection. Readers MUST NOT treat it as a complete query result unless the selected prefix includes every row group that could contribute to that query. Analytical operations such as counts, sums, and spatial joins must consider all potentially matching row groups, independently of display resolution. Coarse prefixes are not statistically representative samples.

Reading a prefix of row groups does not mean downloading a standalone prefix of the file's bytes. The complete Parquet footer is still needed, and column projection and spatial pruning may produce multiple range requests. An ordinary reader can ignore the extension and read the complete table; the extension does not guarantee that such a reader will visit row groups in order.

## Producer guidance

The assignment of features to levels is intentionally producer-defined. Point data can use spatial thinning; lines and polygons can use geometric size or visibility criteria; thematic datasets can use application-specific importance. These choices affect rendering quality but do not change the reader interface.

Producers SHOULD distribute coarse-level features across the dataset's spatial extent where that is meaningful. Merely moving one spatial corner of a globally sorted dataset into the first level rarely provides a useful overview. Features that cannot be assigned a meaningful display scale, such as null or empty geometries, MUST still be preserved and can be assigned to the final level.

Producers SHOULD keep early row groups small enough for responsive initial access and provide spatial statistics appropriate to the GeoParquet version. GeoParquet 1.1 bbox covering statistics and GeoParquet 2.0 native geospatial statistics can support spatial pruning. Page indexes can refine access further. Readers must use conservative pruning and handle unavailable statistics without discarding potential matches.

No compression codec, row group size, page size, thinning algorithm, or spatial ordering algorithm is required. These choices depend on the dataset and expected access pattern. Coarse-to-fine ordering can reduce locality across levels compared with a single global spatial sort, so producers should measure both progressive rendering and full-resolution spatial queries.

This layout reduces the number of features fetched at coarse scales. It does not reduce the vertex count of a selected feature: a large detailed polygon can still dominate transfer and decoding cost. Geometry overviews are complementary and should be specified separately.

Any operation that changes row order, row group boundaries, feature membership, or the primary geometry MUST remove or regenerate the extension metadata. Copying it unchanged through a generic rewrite can silently produce incomplete rendering results.

## Validation

A structural validator can check the metadata types, non-empty levels, positive finite and strictly decreasing resolutions, and non-decreasing row group boundaries. It can verify that each boundary is within the footer's row group count and that the final boundary includes the last row group. It can also validate the underlying GeoParquet file.

Structural validation confirms only that the metadata is consistent with the file's row groups. It does not verify that every source row was preserved, nor that early levels form a useful coarse view; both require comparison with the source data or dataset-specific evaluation.
