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
 * Be sure to include the [bbox covering](https://github.com/opengeospatial/geoparquet/blob/v1.1.0/format-specs/geoparquet.md#bbox-covering-encoding), and use GeoParquet version 1.1.
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

### bbox covering

GeoParquet 1.1 included a couple new features that help with spatial indexing and querying. The easiest one to use is the
bbox covering, which adds a column called `bbox` that contains the bounding box of each geometry as a native Parquet 'struct'
of four values. This enables Parquet readers to quickly filter rows based on the bounding box, and thus greatly increasing
the performance of spatial queries. The bbox column by itself is not sufficient to speed up spatial queries - for that
you'll need to be sure to follow the next two recommendations. But be sure to include it. It is possible for some tools to
make use of the bbox column even if the GeoParquet version is not 1.1, but it's best to actually distribute the files with
GeoParquet 1.1 to ensure all tools know they can use the bbox column.

The other new feature is the Native geometry encodings, based on GeoArrow. Using these will enable the same types of speed
ups as the bbox covering, but will store the data more efficiently. Parquet readers will be able to use the min/max statistics
directly from the geometry column, instead of needing the bbox column. For points this will be a big win, since the bbox
for a point adds some overhead. But we do not yet recommend using the native encodings, since the tool support
isn't yet extensive enough to be sure that most clients will understand them. But as the ecosystem matures this will
be a great option.

### Spatial Ordering

It is essential to make sure that the data is spatially ordered in some way within the file, in order for the bbox column
to be used effectively. If the GeoParquet data was converted from a GIS format like GeoPackage or Shapefile then often
it will already by spatially ordered. One way to check this is to open the file in a GIS tool and see if the data loads
all the spatial data for an area in chunks, or if data for the whole are appears and continues to load everywhere.

<img alt="non-indexed load" height="300" src="https://miro.medium.com/v2/resize:fit:1400/format:webp/1*yugDd1ZjLG4lEwUZucRdmA.gif"> vs <img alt="indexed load" height="300" src="https://miro.medium.com/v2/resize:fit:1400/format:webp/1*-4wyoKgwFXpUnkLeziv5KA.gif"/>

GeoParquet itself does not have a specific spatial index like other formats (R-tree in GeoPackage, Packed Hilbert R-tree in
FlatGeobuf). Instead data can be ordered in any way, and then Parquet's Row Group statistics will be used to speed up spatial
queries (when using bbox covering or native arrow types). Most tools that provide GeoParquet writers have some ability to apply a spatial ordering. The examples below will show how to do this for a few common tools.

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
larger end of the spectrum. If you can set the byte size for row groups a common recommendation is to aim for 128mb - 256mb
per row group.

### Spatial Partitioning

One of the coolest features of Parquet is the ability to partition a large dataset into multiple files, as most every reader
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
nice balancing of the file sizes, but sorts based on S2, GeoHash or R-tree can all work. And partitioning [based on admin
boundaries](https://medium.com/radiant-earth-insights/the-admin-partitioned-geoparquet-distribution-59f0ca1c6d96) is another
approach that works, used in the [Google-Microsoft-OSM Buildings - combined by VIDA](https://source.coop/repositories/vida/google-microsoft-osm-open-buildings/description)
dataset.

### Use STAC metadata

If you're publishing GeoParquet files publicly or internally then it's a good idea to describe the data in a standard way.
The [STAC specification](https://stacspec.org/en)'s [Collection](https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md#provider-object%20PROVIDERS%20=%20[) level metadata to describe what's in it. For single
GeoParquet files this should be very simple, just create a collection.json file in the same folder as the GeoParquet file and
use `application/vnd.apache.parquet` as the media type. If the GeoParquet is partitioned then you can create individual
STAC Items linked to from the collection, with each item describing the bounding box of the data in the file.

## Exemplar Datasets

At the time of writing there are a couple datasets that are fully following the recommendations above. They are provided
here as reference, and as a way to see what it looks like when all the recommendations are followed.

### Overture

[Overture Maps](https://overturemaps.org/) provides a number of different 'themes' of data in well-organized GeoParquet files, with larger datasets. See [their documentation](https://docs.overturemaps.org/getting-data/) for instructions on how to get
the data. Their buildings data is more than 2.2 billion rows, and follows all the core recommendations above. The row group
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
Version 3.9 and later will write out the bbox column by default. And there is a built-in
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

GDAL 3.12 and above introduces `COMPRESSION_LEVEL` as a [parquet layer creation option](https://gdal.org/en/latest/drivers/vector/parquet.html#layer-creation-options). So if you're working with that then you should definitely use it (along with the new
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

### DuckDB

Out of the box:
```
LOAD spatial;
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet');
```

DuckDB will automatically write GeoParquet as long as it's version 1.1 and above, the [spatial extension](https://duckdb.org/docs/extensions/spatial/overview.html)
is enabled and the table has geometries The default compression is snappy, and the max row group size is 122,880. The bbox column is not added by default, and it is not spatially ordered by default.

#### DuckDB with recommended settings

You can control the [compression](https://duckdb.org/docs/sql/statements/copy.html#parquet-options), compression level and [row group size](https://duckdb.org/docs/data/parquet/tips.html#selecting-a-row_group_size):

```
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet', COMPRESSION 'zstd', COMPRESSION_LEVEL 15, ROW_GROUP_SIZE '100000');
```

Interestingly you can also set the row group size in bytes, which would likely be a better way to handle geospatial data since the
row size can vary so much.

```
COPY (SELECT * FROM geo_table) TO 'out.parquet' (FORMAT 'parquet', COMPRESSION 'zstd', ROW_GROUP_SIZE_BYTES '128mb');

```

But you can only use that when [`SET preserve_insertion_order = false;`](https://duckdb.org/docs/stable/guides/performance/how_to_tune_workloads#the-preserve_insertion_order-option) is enabled, which can help when working with large files, but it's not
clear if it can mess up spatial ordering.

DuckDB also has functionality to spatially order your data, with the `[ST_Hilbert](https://duckdb.org/docs/extensions/spatial/functions#st_hilbert)`
function. It is strongly recommended to pass in the bounds of your entire dataset to the function call or the hilbert curve
won't be built right. The following call will dynamically get the bounds of your dataset, and pass that into the ST_Hilbert function.

```
COPY (
    WITH bbox AS (
        SELECT ST_Extent(ST_Extent_Agg(geometry))::BOX_2D AS b
        FROM   geo_table
    )
    SELECT   t.*
    FROM     geo_table AS t
            CROSS JOIN bbox
    ORDER BY ST_Hilbert(t.geometry, bbox.b)
) TO 'out.parquet' (FORMAT 'parquet', COMPRESSION 'zstd', ROW_GROUP_SIZE '100000');
```

One note with DuckDB is that it doesn't (yet) handle reprojection, and also does not maintain CRS information if you read data into
it and then write it out, so watch out for that if you're using it for distribution of GeoParquet data. You can add the CRS info
back in with tools like GDAL and QGIS - it just loses the metadata.

### Additional Tools

We hope to get more discussion of additional tools that follow the same format as DuckDB and OGR/GDAL, especially Sedona, GPQ,
GeoPandas, QGIS and Esri. But we'll aim to add those later as their own PR's - contributions are very welcome. There is also a project
currently called [geoparquet-tools](https://github.com/cholmes/geoparquet-tools) that wraps DuckDB in Python and aims to provide all the
best practices out of the box, along with options to spatially partition. It is still immature (not released to pip, and needs to be
renamed for that), but can be built from source and the code may be useful to others.

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

The [geoparquet-tools](https://github.com/cholmes/geoparquet-tools) python tool provides a way to add columns that can be partitioned
on, and then to perform the partitions. Right now it just supports [admin partitions](https://medium.com/radiant-earth-insights/the-admin-partitioned-geoparquet-distribution-59f0ca1c6d96) but [h3 is in a PR](https://github.com/cholmes/geoparquet-tools/pull/3).

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
