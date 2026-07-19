# Tools for Distributing GeoParquet

This page shows how to produce 'good' GeoParquet with common tools, applying the recommendations in
[Best Practices for Distributing GeoParquet](distributing-geoparquet.md). See that guide for the reasoning behind these
recommendations — compression, spatial ordering, row group size, spatial partitioning, native geometry types, and so on.

## Examples in common tools

This section discusses what each tool does by default, and shows the additional options needed to follow the
[distribution recommendations](distributing-geoparquet.md), including spatial partitioning and STAC metadata where the tool
supports them.

### GDAL/OGR

Out of the box:

```bash
ogr2ogr out.parquet in.geojson
```

Out of the box GDAL/OGR defaults to snappy compression, with max row group size of 65536.
Version 3.9 and later will write out the `bbox` column by default, producing GeoParquet 1.1. There is a built-in
option (`SORT_BY_BBOX=YES`) to spatially order the data that works by creating a temporary GeoPackage file and
using its r-tree spatial index. It defaults to false since it can be an intensive operation,
and GDAL is usually translating from formats that already have spatial indexes.

#### GDAL/OGR with recommended settings

These examples are done with the `ogr2ogr` command-line tool, but the layer creation options
will be the same calling from C or Python.

You can control the compression and the max row group size, and the following command is sufficient
if your source data is already spatially ordered in a file format with a spatial index (like FlatGeobuf or GeoPackage):

```bash
ogr2ogr out.parquet -lco "COMPRESSION=ZSTD" -lco "MAX_ROW_GROUP_SIZE=100000" in.fgb
```

GDAL 3.12 and above introduces `COMPRESSION_LEVEL` as a [Parquet layer creation option](https://gdal.org/en/latest/drivers/vector/parquet.html#layer-creation-options) and a new
[CLI](https://gdal.org/en/latest/programs/index.html#general), which is used here.

```bash
gdal vector convert vegetation.fgb vegetation.parquet --lco compression=zstd --lco compression_level=15
```

If you want to be sure that the output is spatially ordered then you can add `SORT_BY_BBOX=YES`, like in the following example:

```bash
ogr2ogr out.parquet -lco SORT_BY_BBOX=YES -lco "COMPRESSION=ZSTD" in.geojson
```

This operation writes the data to a GeoPackage as an interim step, so it can take additional storage and computation, especially
with large files, so it's not enabled by default.

#### Writing native geometry types

As of this writing GDAL does not yet write GeoParquet 2.0 metadata: by default it produces GeoParquet 1.1 with a `bbox`
covering column. GDAL 3.12 and above (built against libarrow 21 or later) does, however, let you write the native Parquet
`GEOMETRY`/`GEOGRAPHY` logical types via the `USE_PARQUET_GEO_TYPES` layer creation option, which takes `NO` (the default),
`YES`, or `ONLY`:

* `YES` adds the native geometry logical types **but still** writes GeoParquet 1.1 metadata and the redundant `bbox` covering
  column, so the file is larger than it needs to be and still advertises itself as 1.1.
* `ONLY` writes **only** the native geometry types — no `bbox` column and no `geo` metadata block. The native column carries the
  Parquet geospatial statistics (the per–row-group bounding box) that give efficient spatial access, and the CRS is written as
  PROJJSON on the logical type's `crs` property.

Until GDAL can emit GeoParquet 2.0 directly, `USE_PARQUET_GEO_TYPES=ONLY` is the closest you can get: it produces the native,
statistics-bearing geometry column that GeoParquet 2.0 is built on, and any GeoParquet 2.0 reader can read it.

```bash
ogr2ogr out.parquet -lco USE_PARQUET_GEO_TYPES=ONLY -lco "COMPRESSION=ZSTD" -lco "MAX_ROW_GROUP_SIZE=100000" in.fgb
```

> [!NOTE]
> A file written with `ONLY` is **not conformant GeoParquet 2.0**, because it has no `geo` metadata block (no `version`, and the
> CRS is only on the native Parquet type rather than restated as PROJJSON in the `geo` metadata). It is plain Parquet with native
> geospatial types — readable by GeoParquet 2.0 readers, but not a self-described GeoParquet file. Switch to a dedicated 2.0 mode
> once GDAL adds one.

#### Spatial partitioning

GDAL is a flexible tool that can split a dataset into multiple files with `gdal vector partition`. It partitions on the values of
one or more fields (`--field`), writing a `hive` or `flat` directory layout, and can bound the output with `--max-file-size` or
`--feature-limit`:

```bash
gdal vector partition in.parquet out_dir --field region --max-file-size 1GB
```

GDAL does not compute a spatial partitioning scheme on its own, but you can partition spatially by first adding a column that
encodes a spatial grouping — an admin region, geohash, or grid cell — and partitioning on that field. `gdal vector sort` can
spatially order the features beforehand so each partition stays compact.

GDAL does not write STAC metadata.

### DuckDB

Out of the box:

```sql
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet');
```

In DuckDB 1.5 the `GEOMETRY` type and GeoParquet reading and writing are part of core DuckDB — you do **not** need the
[spatial extension](https://duckdb.org/docs/stable/core_extensions/spatial/overview.html) just to read a GeoParquet file,
write one, or convert/recompress/repartition it. CRS information is carried through a read/write round-trip in core as well.
DuckDB automatically writes GeoParquet metadata for any output containing a geometry column. The default compression is snappy,
the max row group size is 122,880, by default it writes GeoParquet 1.0.0, and the data is not spatially ordered.

You can choose the GeoParquet version written with the `GEOPARQUET_VERSION` copy option. Pass `GEOPARQUET_VERSION 'V2'` to write
GeoParquet 2.0: the geometry column is stored using the native Parquet `GEOMETRY`/`GEOGRAPHY` logical types (with the geospatial
statistics that give efficient spatial access), the CRS is written as PROJJSON, and no `bbox` covering column is added.

```sql
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet', GEOPARQUET_VERSION 'V2');
```

The spatial *functions* are not in core, however — anything using an `ST_*` function needs `LOAD spatial` first. That includes
reprojection (`ST_Transform`) and, importantly for distribution, spatially ordering your data (`ST_Hilbert`, shown below). So in
practice you will still load the extension whenever you spatially order or reproject, even though the GeoParquet writer itself
does not require it.

#### DuckDB with recommended settings

You can control the [compression](https://duckdb.org/docs/sql/statements/copy.html#parquet-options), compression level and [row group size](https://duckdb.org/docs/data/parquet/tips.html#selecting-a-row_group_size), and write GeoParquet 2.0 with `GEOPARQUET_VERSION 'V2'`:

```sql
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet', GEOPARQUET_VERSION 'V2', COMPRESSION 'zstd', COMPRESSION_LEVEL 15, ROW_GROUP_SIZE '100000');
```

Interestingly you can also set the row group size in bytes, which would likely be a better way to handle geospatial data since the
row size can vary so much.

```sql
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet', GEOPARQUET_VERSION 'V2', COMPRESSION 'zstd', ROW_GROUP_SIZE_BYTES '128mb');
```

The `ROW_GROUP_SIZE_BYTES` option may only be used when [`SET preserve_insertion_order = false;`](https://duckdb.org/docs/stable/guides/performance/how_to_tune_workloads#the-preserve_insertion_order-option) is enabled, which can help when working with large files, but it's not
clear if it can preserve spatial ordering.

DuckDB also has functionality to spatially order your data, with the [`ST_Hilbert`](https://duckdb.org/docs/extensions/spatial/functions#st_hilbert)
function. Because this uses `ST_*` functions you need to `LOAD spatial` first. It is strongly recommended to pass in the bounds of
your entire dataset to the function call or the hilbert curve won't be built right. The following call will dynamically get the
bounds of your dataset, pass that into the `ST_Hilbert` function, and write the result as GeoParquet 2.0.

```sql
LOAD spatial;
COPY (
    WITH bbox AS (
        SELECT ST_Extent(ST_Extent_Agg(geometry))::BOX_2D AS b
        FROM   geo_table
    )
    SELECT   t.*
    FROM     geo_table AS t
            CROSS JOIN bbox
    ORDER BY ST_Hilbert(t.geometry, bbox.b)
) TO 'out.parquet' (FORMAT 'parquet', GEOPARQUET_VERSION 'V2', COMPRESSION 'zstd', ROW_GROUP_SIZE '100000');
```

DuckDB 1.5 and later preserves CRS information when you read GeoParquet in and write it back out. Earlier versions dropped the
CRS metadata on write, so if you are on an older DuckDB you may need to add the CRS back in with tools like GDAL or QGIS.

#### Spatial partitioning

DuckDB can write a hive-partitioned dataset with `COPY ... PARTITION_BY`. To partition *spatially*, compute a spatial grid cell
for each row and partition on it. The [a5](https://github.com/Query-farm/a5) DuckDB community extension provides a global,
equal-area cell grid that works well for this:

```sql
INSTALL a5 FROM community; LOAD a5;
INSTALL spatial; LOAD spatial;
COPY (
    SELECT *, a5_u64_to_hex(a5_lonlat_to_cell(ST_X(geometry), ST_Y(geometry), 3)) AS a5_cell
    FROM   geo_table
) TO 'partitioned' (FORMAT 'parquet', PARTITION_BY a5_cell, GEOPARQUET_VERSION 'V2', COMPRESSION 'zstd');
```

Choose the a5 resolution to target a reasonable number of features per partition for your data. For non-point geometries, derive
the cell from a representative point such as `ST_Centroid(geometry)`. You can also sort within each partition by `ST_Hilbert` for
tighter row-group bounds. For other approaches, see [this gist using a KD-tree](https://gist.github.com/jwass/8e9b6c16902a05ae66b9688f1a5bb4ff)
and [this blog post](https://dewey.dunnington.ca/post/2024/partitioning-strategies-for-bigger-than-memory-spatial-data/) that
discusses the KD-tree along with other options (r-tree, s2 cells).

DuckDB does not write STAC metadata.

### geoparquet-io

[geoparquet-io](https://geoparquet.io) is a command-line tool, built on DuckDB, that is designed to apply the
[distribution recommendations](distributing-geoparquet.md) by default — it exists specifically to make 'good' GeoParquet without
having to remember all the options. It produces fully compliant GeoParquet that follows every recommendation in that guide; the
one area still being finalized is 2.0 output, so by default it writes GeoParquet 1.1. Install it from PyPI (the package is
`geoparquet-io`):

```bash
pipx install geoparquet-io   # or: pip install geoparquet-io
```

A plain conversion applies ZSTD compression at level 15, Hilbert spatial ordering, a `bbox` covering column, and 100,000-row
row groups, then validates the result:

```bash
gpio convert geoparquet input.gpkg output.parquet
```

It defaults to writing GeoParquet 1.1 (it auto-detects from the input, preserving the input's version and upgrading native geo
types to 2.0). Pass `--geoparquet-version 2.0` to write GeoParquet 2.0, which stores the geometry in the native Parquet types
with geospatial statistics and omits the `bbox` column:

```bash
gpio convert geoparquet input.gpkg output.parquet --geoparquet-version 2.0
```

#### Spatial partitioning

gpio partitions large datasets with `gpio partition`, which supports KD-tree, quadkey, S2, H3, A5, and
[admin](https://medium.com/radiant-earth-insights/the-admin-partitioned-geoparquet-distribution-59f0ca1c6d96) schemes. The
KD-tree scheme auto-selects a partition count targeting ~120,000 rows per file, and adds the partition column for you if it is
missing:

```bash
gpio partition kdtree input.parquet output/
gpio partition kdtree input.parquet output/ --partitions 32
```

The `gpio add` commands can also add just the partitioning column (for example `gpio add h3` or `gpio add admin-divisions`) if
you want to partition or sort on it yourself.

#### STAC metadata

gpio generates STAC with `gpio publish stac`. A single file produces a STAC Item; a partitioned directory produces a STAC
Collection plus per-file Items written alongside the data, following STAC best practices:

```bash
# Single file -> STAC Item
gpio publish stac input.parquet item.json --bucket s3://my-bucket/roads/

# Partitioned dataset -> Collection + per-file Items
gpio publish stac partitions/ . --bucket s3://my-bucket/roads/
```

You can upload the data (and its STAC) to object storage with `gpio publish upload`, and validate any file with `gpio check all`.

### Sedona

[Apache Sedona](https://sedona.apache.org/) is one of the most 'out of the box' options for spatially partitioning large
datasets, using its [Spatial RDDs](https://sedona.apache.org/latest/tutorial/rdd/). The following code writes out partitions by
KD-tree:

```python
import glob

from sedona.spark import SedonaContext, GridType
from sedona.utils.structured_adapter import StructuredAdapter
from sedona.sql.st_functions import ST_GeoHash

# Configuring this line to do the right thing can be tricky
# https://sedona.apache.org/latest/setup/install-python/?h=python#prepare-sedona-spark-jar
config = (
    SedonaContext.builder()
    .config("spark.executor.memory", "6G")
    .config("spark.driver.memory", "6G")
    .getOrCreate()
)

sedona = SedonaContext.create(config)

# Read from GeoParquet or some other datasource + do any spatial ops/transformations
# using Sedona pyspark or SQL
df = sedona.read.format("geoparquet").load(
    "/Users/dewey/gh/geoarrow-data/microsoft-buildings/files/microsoft-buildings_point_geo.parquet"
)

# Create the partitioning. KDBTREE provides a nice balance providing
# tight (but well-separated) partitions with approximately equal numbers of
# features in each file. Note that num_partitions is only a suggestion
# (actual value may differ)
rdd = StructuredAdapter.toSpatialRdd(df, "geometry")
rdd.analyze()

# UseWithoutDuplicates() variant to ensure that we don't introduce
# duplicate features
rdd.spatialPartitioningWithoutDuplicates(GridType.KDBTREE, num_partitions=8)
rdd.getPartitioner().getGrids()
df_partitioned = StructuredAdapter.toSpatialPartitionedDf(rdd, sedona)

# Optional: sort within partitions for tighter rowgroup bounding boxes within files
df_partitioned = (
    df_partitioned.withColumn("geohash", ST_GeoHash(df_partitioned.geometry, 12))
    .sortWithinPartitions("geohash")
    .drop("geohash")
)

# Write in parallel directly from each executor node.
# There are several options for geoparquet writing:
# https://sedona.apache.org/latest/tutorial/files/geoparquet-sedona-spark/
df_partitioned.write.format("geoparquet").mode("overwrite").option("compression", "zstd").save(
    "buildings_partitioned"
)

# The output files have funny names because Spark writes them this way
files = glob.glob("buildings_partitioned/*.parquet")
len(files)
```

Only spatial partitioning is documented here for now. Sedona can do much more for producing distribution-ready GeoParquet
(compression, row group size, GeoParquet version, etc.) — documenting those settings still needs a PR, and contributions are
very welcome.

### Additional Tools

We hope to get more discussion of additional tools that follow the same format as the ones above, especially GPQ,
GeoPandas, QGIS and Esri. But we'll aim to add those later as their own PR's - contributions are very welcome.
