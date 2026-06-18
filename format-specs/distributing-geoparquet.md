# Best Practices for Distributing GeoParquet

This guide aims to encapsulate a number of best practices that the community has
started to align on for making 'good' GeoParquet files, especially for distribution
of data. Parquet gives users lots of different options, and the defaults of various
libraries are different and usually not optimized for geospatial data.

## tl;dr Recommendations

Later sections will go deep into the reasoning and nuances behind these options, but if you're
just looking to be sure you get the basics right then this section may be sufficient.
And if you're building a tool or library then consider these as good defaults.

 * Use zstd for compression, and set the compression level to 15.
 * Use GeoParquet 2.0, which stores geometries in the native Parquet `GEOMETRY`/`GEOGRAPHY` types. These carry built-in geospatial statistics (a bounding box per column chunk), giving efficient spatial access without the extra `bbox` column that 1.1 required.
 * Spatially order the data within the file.
 * Set the maximum row group size between 50,000 and 150,000 per row.
 * If the data is larger than ~2 gigabytes consider spatially partitioning the files.
 * Use [STAC Metadata](https://stacspec.org/) metadata to describe the data.


### Compression

Parquet has built in compression, enabling users to directly use files that are similar in size to the zipped versions
of other formats. You can easily change the compression algorithm, and new ones continue to be added.
The default for most Parquet libraries is `snappy`, which excels at speed and gets good compression. More recently the
`zstd` library has been added to the Parquet ecosystem, and it achieves a better compression ratio with similar speeds
to snappy. So it is recommended to use `zstd`, since at this point most all Parquet libraries support `zstd` and because
better compression makes for faster downloads.

`zstd` does have a nice ability to control compression, with options ranging up to 22. The cool thing is that
decompression times are pretty constant with `zstd`, so if you're distributing data then it makes a lot of sense to spend
a bit more time up to do a higher compression level. Then downloads will go faster, but it won't take clients longer
to decompress. Many tools default to one of the lowest compression levels, indeed the core Apache Arrow library that
many tools use defaults to 1. So our recommendation is generally to increase the compression level, particularly if you're
making data for distribution. But don't bother to go all the way to 22 - the consensus seems to be that the levels 17 and
above take _way_ longer, but the size gains are less than one percent. There is more research needed on this topic, but
the current recommendation is to aim for something between 11 and 16.

### Efficient spatial access

In GeoParquet 2.0 the geometry column is stored using the native Parquet
[`GEOMETRY`/`GEOGRAPHY`](https://github.com/apache/parquet-format/blob/master/Geospatial.md) logical types. Parquet writes
[geospatial statistics](https://github.com/apache/parquet-format/blob/master/Geospatial.md#geospatial-statistics) for these
columns — most importantly a bounding box for each column chunk (row group). Readers use these statistics to quickly skip any
row group whose bounding box does not intersect a query's area of interest, which greatly increases the performance of spatial
queries. This is the same kind of speedup that the GeoParquet 1.1 `bbox` covering provided, but it comes built in to the
geometry column, so **you no longer need to add a separate `bbox` column**.

Dropping the `bbox` column also makes files smaller. The 1.1 covering added a Parquet `struct` of four values to every row; for
point datasets that overhead is especially large, since the four-value box is bigger than the point it describes. With the native
geospatial statistics you get efficient spatial filtering and a smaller file.

As with the `bbox` column, these statistics only help if the data is spatially ordered and the row groups are sized sensibly —
see the next two sections. Statistics are per row group, so the row group is the unit at which a reader can skip data spatially;
see [Further Discussion: page-level spatial statistics](#page-level-spatial-statistics) for ongoing exploration of finer-grained pruning.

> [!NOTE]
> The earlier [`bbox` covering](https://github.com/opengeospatial/geoparquet/blob/v1.1.0/format-specs/geoparquet.md#bbox-covering-encoding)
> from GeoParquet 1.1 remains a valid way to enable spatial filtering, and may still be worth including if you need to reach
> readers that do not yet understand the native Parquet geospatial statistics. If you go that route, distribute the files as
> GeoParquet 1.1 so that all tools know they can use the `bbox` column.

### Spatial Ordering

It is essential to make sure that the data is spatially ordered in some way within the file, in order for the row group
statistics to be used effectively. If the GeoParquet data was converted from a GIS format like GeoPackage or Shapefile then often
it will already by spatially ordered. One way to check this is to open the file in a GIS tool and see if the data loads
all the spatial data for an area in chunks, or if data for the whole are appears and continues to load everywhere.

<img alt="non-indexed load" height="300" src="https://miro.medium.com/v2/resize:fit:1400/format:webp/1*yugDd1ZjLG4lEwUZucRdmA.gif"> vs <img alt="indexed load" height="300" src="https://miro.medium.com/v2/resize:fit:1400/format:webp/1*-4wyoKgwFXpUnkLeziv5KA.gif"/>

GeoParquet itself does not have a specific spatial index like other formats (R-tree in GeoPackage, Packed Hilbert R-tree in
FlatGeobuf). Instead data can be ordered in any way, and then Parquet's Row Group statistics will be used to speed up spatial
queries (using the native geometry statistics, or a `bbox` covering column). Most tools that provide GeoParquet writers have some ability to apply a spatial ordering. The examples below will show how to do this for a few common tools.

### Row Group Size

A row group in Parquet is 'a logical horizontal partitioning of the data into rows', and there's some good explanation
in [this article](https://medium.com/data-engineering-with-dremio/all-about-parquet-part-03-parquet-file-structure-pages-row-groups-and-columns-d7c7e54a8311). It ends up being important to
get this right, since it will impact the performance of spatial queries. If the row group size is too big then the GeoParquet
reader will not be able to 'skip' over large chunks of data and if it's too small then the file metadata can get large,
which can slow things down if there are a lot of files.

Unfortunately there's no single 'best' size for row groups, and it will depend on the size of the data and the access patterns.
The community is still learning what works best, so there are no solid recommendations at this point - hopefully we'll learn
more and update this section in the future. As of this writing there are several larger global datasets that are being distributed with
row group sizes of 50,000 to 200,000 rows, so that's what we recommend as a starting point.

Most geospatial tools give you the ability to set the maximum number of rows per row group, but some tools may let you set
the byte size for the row group. The core thing that really matters is the byte size for the row group, as that will be
the amount of data that needs to be read (and moved over the network in cloud-native geo access patterns). So if your data
rows are large then you'll want to set a smaller row group size, and if your rows are small it could make sense to go to the
larger end of the spectrum. If you can set the byte size for row groups a common recommendation is to aim for 128MB - 256MB
per row group.

### Spatial Partitioning

One of the useful features of Parquet is the ability to partition a large dataset into multiple files, as most readers
can be pointed at a folder of files and it will read them as a single dataset. The reader will use the row group statistics
to quickly figure out if a given file needs to be read, and multiple files can be read in parallel. So with spatial data,
where most every query contains a spatial filter, partioning the data spatially can greatly accelerate the performance.

Similar to the row group size, the community is still figuring out the best way to spatially partition the data, and the
overall query performance will depend on both row group size and the size of the partitioned files, along with the nature of
the data. Hopefully someone will do a set of robust testing to help inform more definitive recommendations.

For now the recommendation is to spatially partition your data 'in some way', at least if the dataset is larger than a couple
gigabytes. If it's smaller than that then the additional overhead of splitting it up is likely not worth it. There was some
[great discussion](https://github.com/opengeospatial/geoparquet/discussions/251) on the topic, and an nice
[blog post](https://dewey.dunnington.ca/post/2024/partitioning-strategies-for-bigger-than-memory-spatial-data/) with some
further experimentation. The leading approach at the moment is to use a K-dimensional tree (KD-tree), which will enable
balancing of the file sizes and spatial separation; however, sorts based on S2, GeoHash or R-tree can all work. Partitioning [based on admin
boundaries](https://medium.com/radiant-earth-insights/the-admin-partitioned-geoparquet-distribution-59f0ca1c6d96) is another
approach that works and is used in the [Google-Microsoft-OSM Buildings - combined by VIDA](https://source.coop/repositories/vida/google-microsoft-osm-open-buildings/description)
dataset.

### Use STAC metadata

If you're publishing GeoParquet files publicly or internally then it's a good idea to describe the data in a standard way.
The [STAC specification](https://stacspec.org/en)'s [Collection](https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md#provider-object%20PROVIDERS%20=%20[) level metadata to describe what's in it. For single
GeoParquet files this should be very simple, just create a collection.json file in the same folder as the GeoParquet file and
use `application/vnd.apache.parquet` as the media type. If the GeoParquet is partitioned then you can create individual
STAC Items linked to from the collection, with each item describing the bounding box of the data in the file.

## Usage in Frontend Applications

While GeoParquet excels in analytics use cases, it can also be accessed directly from an object store within frontend applications. This can be a convenient way to losslessly access large geospatial datasets in a way that has more query flexibility than other cloud native geospatial formats like FlatGeobuf. For example, FlatGeobuf only provides an index on the geometry column, whereas GeoParquet has row group statistics on other columns.

When creating a GeoParquet file for use in a frontend application you will need to decide your row group sizes, presenting a tradeoff between frontend query latency and analytics performance. Many frontend applications only wish to display a subset of geospatial data within a bounding box. The native [geospatial statistics](#efficient-spatial-access) on the geometry column let a reader skip any row group that does not intersect the requested bounding box. Because those statistics are per row group, the row group is the unit at which irrelevant data can be skipped, so for this access pattern you should significantly reduce [row group size](#row-group-size). This is since large row groups increase the amount of irrelevant data (such as points outside the bounding box) that will be fetched when running geospatial queries and in doing so, add additional latency from network transfer.

However, small row groups come at a tradeoff. Each row group contains metadata and the more groups the file has, the slower the speed of a full scan of all rows. In other words, small row groups decrease the performance of analytical queries like averages or sums. As such, if you wish to use the same GeoParquet file for both frontend display and analytics, you need to optimize the row group size to strike a balance between the two depending on which use case is most important.

## Exemplar Datasets

At the time of writing there are several datasets that are fully following the recommendations above. They are provided
here as reference and as a way to see what it looks like when all the recommendations are followed.

### Overture

[Overture Maps](https://overturemaps.org/) provides a number of different 'themes' of data in well-organized GeoParquet files, with larger datasets. See [their documentation](https://docs.overturemaps.org/getting-data/) for instructions on how to get
the data. Their buildings data is more than 2.2 billion rows. It is distributed as GeoParquet 1.1 and follows the core
recommendations for that version. The row group
size seems to be around 150,000, and it's zstd compressed with the bbox column, ordered by a GeoHash. The data is partitioned
spatially, see [this discussion comment](https://github.com/opengeospatial/geoparquet/discussions/251#discussioncomment-11478379)
for more details.

### Almost Exemplar

These datasets are all 'good enough' to use, but don't quite follow all the recommendations above. Once they are updated we'll
move them up.

* The [Google-Microsoft-OSM Buildings - combined by VIDA](https://source.coop/repositories/vida/google-microsoft-osm-open-buildings/description) is a great example of a dataset that is almost following all the recommendations above. They did use snappy, and
their row group sizes are around 5,000 (which still gets reasonable performance). They distribute the data in 2 different
partition schemes. One is just by admin boundary, which leads to a few really large files (India, USA, etc). The other further
splits larger countries into smaller files, using S2 cells.

* [US Structures from Oak Ridge National Laboratory](https://source.coop/wherobots/usa-structures/geoparquet) formatted by
Wherobots.

* [Planet Ag Field Boundaries over EU](https://source.coop/repositories/planet/eu-field-boundaries/description) - needs to be
spatially partitioned, row group size is 25,000.

## Examples in common tools

This section will discuss what each tool does by default, and show any additional options
needed to follow the recommendations above. STAC metadata and spatial partitioning will
have their own sections, since there are fewer tools that can do it, but most any of
the other tools can be used to prep the data.

### GDAL/OGR

Out of the box:

```
ogr2ogr out.parquet in.geojson
```

Out of the box GDAL/OGR defaults to snappy compression, with max row group size of 65536.
Version 3.9 and later will write out the `bbox` column by default, producing GeoParquet 1.1. And there is a built-in
option to spatially order the data that works by creating a temporary GeoPackage file and
using its r-tree spatial index. It defaults to false since it can be an intensive operation,
and GDAL is usually translating from formats that already have spatial indexes.

### GDAL/OGR with recommended settings

These examples are done with the `ogr2ogr command-line tool, but the layer creation options
will be the same calling from C or Python.

You can easily control the compression and the max row group size, and the following command is sufficient
if your source data is already spatially ordered in a file format with a spatial index (like FlatGeobuf or GeoPackage):
```
ogr2ogr out.parquet -lco "COMPRESSION=ZSTD" -lco "MAX_ROW_GROUP_SIZE=100000" in.fgb
```

GDAL 3.12 and above introduces `COMPRESSION_LEVEL` as a [Parquet layer creation option](https://gdal.org/en/latest/drivers/vector/parquet.html#layer-creation-options). So if you're working with that then you should definitely use it (along with the new
[gdal CLI](https://gdal.org/en/latest/programs/index.html#general), which is used here.

```
gdal vector convert vegetation.fgb vegetation.parquet --lco compression=zstd --lco compression_level=15
```

If you want to be sure that the output is spatially ordered then you can add `SORT_BY_BBOX=YES`, like in the following example:
```
ogr2ogr out.parquet -lco SORT_BY_BBOX=YES -lco "COMPRESSION=ZSTD" in.geojson
```

This operation writes the data to a GeoPackage as an interim step, so it can take additional storage and computation, especially
with large files, so it's not enabled by default.

#### Writing native geometry types

As of this writing GDAL does not yet write GeoParquet 2.0 metadata — by default it produces GeoParquet 1.1 with a `bbox`
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

```
ogr2ogr out.parquet -lco USE_PARQUET_GEO_TYPES=ONLY -lco "COMPRESSION=ZSTD" -lco "MAX_ROW_GROUP_SIZE=100000" in.fgb
```

> [!NOTE]
> A file written with `ONLY` is **not conformant GeoParquet 2.0**, because it has no `geo` metadata block (no `version`, and the
> CRS is only on the native Parquet type rather than restated as PROJJSON in the `geo` metadata). It is plain Parquet with native
> geospatial types — readable by GeoParquet 2.0 readers, but not a self-described GeoParquet file. Switch to a dedicated 2.0 mode
> once GDAL adds one.

### DuckDB

Out of the box:
```
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

```
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet', GEOPARQUET_VERSION 'V2');
```

The spatial *functions* are not in core, however — anything using an `ST_*` function needs `LOAD spatial` first. That includes
reprojection (`ST_Transform`) and, importantly for distribution, spatially ordering your data (`ST_Hilbert`, shown below). So in
practice you will still load the extension whenever you spatially order or reproject, even though the GeoParquet writer itself
does not require it.

#### DuckDB with recommended settings

You can control the [compression](https://duckdb.org/docs/sql/statements/copy.html#parquet-options), compression level and [row group size](https://duckdb.org/docs/data/parquet/tips.html#selecting-a-row_group_size), and write GeoParquet 2.0 with `GEOPARQUET_VERSION 'V2'`:

```
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet', GEOPARQUET_VERSION 'V2', COMPRESSION 'zstd', COMPRESSION_LEVEL 15, ROW_GROUP_SIZE '100000');
```

Interestingly you can also set the row group size in bytes, which would likely be a better way to handle geospatial data since the
row size can vary so much.

```
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet', GEOPARQUET_VERSION 'V2', COMPRESSION 'zstd', ROW_GROUP_SIZE_BYTES '128mb');

```

But you can only use that when [`SET preserve_insertion_order = false;`](https://duckdb.org/docs/stable/guides/performance/how_to_tune_workloads#the-preserve_insertion_order-option) is enabled, which can help when working with large files, but it's not
clear if it can mess up spatial ordering.

DuckDB also has functionality to spatially order your data, with the `[ST_Hilbert](https://duckdb.org/docs/extensions/spatial/functions#st_hilbert)`
function. Because this uses `ST_*` functions you need to `LOAD spatial` first. It is strongly recommended to pass in the bounds of
your entire dataset to the function call or the hilbert curve won't be built right. The following call will dynamically get the
bounds of your dataset, pass that into the ST_Hilbert function, and write the result as GeoParquet 2.0.

```
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

### gpio (geoparquet-io)

[gpio](https://geoparquet.io) is a command-line tool, built on DuckDB, that is designed to apply the recommendations in this
guide by default — it exists specifically to make 'good' GeoParquet without having to remember all the options. Install it from
PyPI (the package is `geoparquet-io`):

```
pipx install geoparquet-io   # or: pip install geoparquet-io
```

A plain conversion applies ZSTD compression at level 15, Hilbert spatial ordering, a `bbox` covering column, and 100,000-row
row groups, then validates the result:

```
gpio convert geoparquet input.gpkg output.parquet
```

By default it writes GeoParquet 1.1 (it auto-detects from the input, preserving the input's version and upgrading native geo
types to 2.0). Pass `--geoparquet-version 2.0` to write GeoParquet 2.0, which stores the geometry in the native Parquet types
with geospatial statistics and omits the `bbox` column:

```
gpio convert geoparquet input.gpkg output.parquet --geoparquet-version 2.0
```

gpio also handles other steps covered in this guide, including spatial partitioning (`gpio partition kdtree`), adding
partitioning columns such as H3 or admin divisions (`gpio add`), generating STAC metadata and uploading
(`gpio publish`), and validating existing files (`gpio check all`).

### Additional Tools

We hope to get more discussion of additional tools that follow the same format as DuckDB and OGR/GDAL, especially Sedona, GPQ,
GeoPandas, QGIS and Esri. But we'll aim to add those later as their own PR's - contributions are very welcome.

## STAC Metadata

None of the tools to write GeoParquet currently write out STAC Metadata, but that makes sense, as they don't write out other
metadata formats either. To write STAC metadata you can write it by hand if you've just got one or two GeoParquet files. If you've
got more then the best option is to use something like [rustac](https://github.com/stac-utils/rustac) or
[pystac](https://pystac.readthedocs.io/en/stable/) to do it a bit more programmatically. You should be able to populate some
of the STAC fields like bbox from the GeoParquet files directly.

## Spatial Partitioning

Most tools don't yet provide any way to do automatic spatial partitioning across files, when you have larger datasets.
Many people are finding success using DuckDB, since it's a very flexible tool for manipulating data. For some pointers see
[this gist using kdtree](https://gist.github.com/jwass/8e9b6c16902a05ae66b9688f1a5bb4ff) and
[this blog post](https://dewey.dunnington.ca/post/2024/partitioning-strategies-for-bigger-than-memory-spatial-data/) that
discusses the kdtree, along with some other options (r-tree, s2 cells).

The [gpio](https://geoparquet.io) tool (see its section above) can add columns to partition on and then perform the partitions,
supporting KD-tree, quadkey, S2, H3, A5, and [admin](https://medium.com/radiant-earth-insights/the-admin-partitioned-geoparquet-distribution-59f0ca1c6d96)
partitioning (e.g. `gpio partition kdtree`).

The solution that is currently one of the most 'out of the box' option is Sedona, with its
[Spatial RDD's](https://sedona.apache.org/latest/tutorial/rdd/). The following code takes you through using it to write out partitions by kdtree.

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
df_partitioned.write.format("geoparquet").mode("overwrite").save(
    "buildings_partitioned"
)

# The output files have funny names because Spark writes them this way
files = glob.glob("buildings_partitioned/*.parquet")
len(files)
```

## Further Discussion

This section captures topics the community is still actively exploring. They are not part of the recommendations above, but
are written up here both to explain known limitations and to invite others to help move them forward.

### Page-level spatial statistics

As noted under [Efficient spatial access](#efficient-spatial-access), the native Parquet `GEOMETRY`/`GEOGRAPHY` types carry
geospatial statistics — a bounding box — at the **column chunk (row group)** level only. A reader can therefore skip an entire
row group whose bounding box does not intersect the query, but once a row group is selected it must read all of that row group's
pages, even if many of those pages fall entirely outside the area of interest.

This is actually a step back from what the GeoParquet 1.1 `bbox` covering column could do. Because that covering is an ordinary
Parquet `struct` column, it gets a normal Parquet page index (`ColumnIndex`), so its per-page min/max values let a reader prune
individual **pages** within a row group, not just whole row groups. So while the native geometry statistics remove the need for
an extra column and make files smaller, the 1.1 `bbox` covering column can still offer finer-grained spatial pruning.

How much does page-level pruning matter? [Issue #279](https://github.com/opengeospatial/geoparquet/issues/279) collects some
early benchmarks. On a ~10 million row Overture buildings file with a selective `intersects` query, page-level pruning roughly
halved query time (~93 ms using the built-in row-group statistics vs. ~48 ms when pruning to the page level). The benefit grows
the more selective the query is, and — like the row-group statistics — it depends on the data being spatially ordered so that
individual pages stay spatially compact.

A notable result from the same exploration is that a *specialized* embedded spatial index (an R-tree) gave no measurable
improvement over a simple "flat" list of per-page bounding boxes. With only a few hundred to a few thousand pages in a typical
file, brute-force checking each page's bounding box is effectively as fast as querying an index. That suggests the simplest
possible mechanism — a per-page bounding box — is likely enough, and that a more complex embedded index may not be worth the
added serialization complexity (every reader and writer would have to agree on its exact binary layout).

#### How page-level geometry statistics could be added

Two broad approaches have come up:

1. **Add geospatial statistics to Parquet at the page level.** The cleanest long-term solution is to extend the Parquet format
   itself so that geometry/geography columns can carry a per-page bounding box, mirroring the existing per-row-group geospatial
   statistics. This could be done either by encoding the bounding box into the existing page `min`/`max` statistics fields (with
   some care needed around Z and M bounds), or by adding a `GeoStatistics` structure alongside the existing `Statistics` in the
   page metadata (the Thrift definition). The main concern raised when geospatial statistics were first added to Parquet was the
   increase in metadata/file size — but this can be designed so that there is no effect unless a writer actually chooses to emit
   geometry page statistics. The practical path is a note to the [Apache Parquet mailing list](https://parquet.apache.org/community/)
   with a reproducible benchmark, then a pull request against [parquet-format](https://github.com/apache/parquet-format) editing
   the Thrift definition, followed by at least two implementations.

2. **A user-defined index embedded in the file.** Independent of any Parquet spec change, it is possible to pack a custom spatial
   index into the bytes of a Parquet file that the footer does not reference (for example, just before the footer), as described
   in [this DataFusion blog post on user-defined Parquet indexes](https://datafusion.apache.org/blog/2025/07/14/user-defined-parquet-indexes/).
   A reader that knows where to look can use the index, while other readers ignore it and read the file normally. This keeps the
   file a valid Parquet file, but requires readers and writers to agree on the index format and how to locate it — and, per the
   benchmark above, a full index does not appear to beat simple page-level bounding boxes.

None of this is currently on anyone's immediate roadmap, and the native row-group statistics are a good default for most
distribution use cases today. It is written up here so that anyone interested in finer-grained spatial pruning has a starting
point — if this is something you would use, the discussion in [issue #279](https://github.com/opengeospatial/geoparquet/issues/279)
is the place to weigh in.
