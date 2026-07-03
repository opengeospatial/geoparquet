# Best Practices for Distributing GeoParquet

This guide aims to encapsulate a number of best practices that the community has
started to align on for making 'good' GeoParquet files, especially for distribution
of data. Parquet gives users lots of different options, and the defaults of various
libraries are different and usually not optimized for geospatial data.

For step-by-step examples of applying these recommendations in specific tools (GDAL/OGR, DuckDB, gpio, and others), see the
companion [Tools for Distributing GeoParquet](distributing-geoparquet-tools.md) guide.

## tl;dr Recommendations

Later sections will go deep into the reasoning and nuances behind these options, but if you're
just looking to be sure you get the basics right then this section may be sufficient.
And if you're building a tool or library then consider these as good defaults.

- Use zstd for compression, at compression level 15 or higher — go as high as you have time for.
- Use GeoParquet 2.0, which stores geometries in the native Parquet `GEOMETRY`/`GEOGRAPHY` types,
  or GeoParquet 1.1 with the [bbox covering](https://github.com/opengeospatial/geoparquet/blob/v1.1.0/format-specs/geoparquet.md#bbox-covering-encoding) for efficient spatial access.
- Spatially order the data within the file.
- Set the maximum row group size between 50,000 and 150,000 per row.
- If the data is larger than ~2 gigabytes consider spatially partitioning the files.
- Use [STAC Metadata](https://stacspec.org/) metadata to describe the data.

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
many tools use defaults to 1. So our recommendation is to use at least level 15, and generally to go as high as you have time
for, particularly if you're making data for distribution. The one caveat is that the highest levels have steeply diminishing
returns - the consensus is that levels 17 and above take _way_ longer while the size gains are less than one percent - so going
all the way to 22 is rarely worth it. But since clients pay no penalty on decompression, if compression time isn't a concern
it's nice to push it as high as you can.

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
> from GeoParquet 1.1 remains a valid way to enable spatial filtering, and using 1.1 is recommended if you need to support a
> wider range of software/versions to read your data. Many tools (GDAL, DuckDB, Hyparquet, geoparquet-io, SedonaDB, QGIS)
> will work with Parquet native types (and the GeoParquet 2.0 metadata), and eventually 2.0 will be the only recommended way.

### Spatial Ordering

It is essential to make sure that the data is spatially ordered in some way within the file, in order for the row group
statistics to be used effectively. If the GeoParquet data was converted from a GIS format like GeoPackage or Shapefile then often
it will already be spatially ordered. One way to check this is to open the file in a GIS tool and see if the data loads
all the spatial data for an area in chunks, or if data for the whole area appears and continues to load everywhere.

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
where most every query contains a spatial filter, partitioning the data spatially can greatly accelerate the performance.

Similar to the row group size, the community is still figuring out the best way to spatially partition the data, and the
overall query performance will depend on both row group size and the size of the partitioned files, along with the nature of
the data. Hopefully someone will do a set of robust testing to help inform more definitive recommendations.

For now the recommendation is to spatially partition your data 'in some way', at least if the dataset is larger than a couple
gigabytes. If it's smaller than that then the additional overhead of splitting it up is likely not worth it. There was some
[great discussion](https://github.com/opengeospatial/geoparquet/discussions/251) on the topic, and a nice
[blog post](https://dewey.dunnington.ca/post/2024/partitioning-strategies-for-bigger-than-memory-spatial-data/) with some
further experimentation. The leading approach at the moment is to use a K-dimensional tree (KD-tree), which will enable
balancing of the file sizes and spatial separation; however, sorts based on S2, GeoHash or R-tree can all work. Partitioning [based on admin
boundaries](https://medium.com/radiant-earth-insights/the-admin-partitioned-geoparquet-distribution-59f0ca1c6d96) is another
approach that works and is used in the [Google-Microsoft-OSM Buildings - combined by VIDA](https://source.coop/repositories/vida/google-microsoft-osm-open-buildings/description)
dataset.

See the [tools guide](distributing-geoparquet-tools.md#examples-in-common-tools) for how to do this with GDAL, DuckDB, gpio,
and Sedona.

### Use STAC metadata

If you're publishing GeoParquet files publicly or internally then it's a good idea to describe the data in a standard way.
The [STAC specification](https://stacspec.org/en)'s [Collection](https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md) level metadata can describe what's in it. For single
GeoParquet files this should be very simple, just create a collection.json file in the same folder as the GeoParquet file and
use `application/vnd.apache.parquet` as the media type. If the GeoParquet is partitioned then you can create individual
STAC Items linked to from the collection, with each item describing the bounding box of the data in the file.

The [geoparquet-io](distributing-geoparquet-tools.md#geoparquet-io) tool can generate STAC Items and Collections from GeoParquet
files. You can also write STAC by hand for one or two files, or use a library like [rustac](https://github.com/stac-utils/rustac)
or [pystac](https://pystac.readthedocs.io/en/stable/) to do it programmatically, populating fields like the bbox from the
GeoParquet files directly.

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

- The [Google-Microsoft-OSM Buildings - combined by VIDA](https://source.coop/repositories/vida/google-microsoft-osm-open-buildings/description) is a great example of a dataset that is almost following all the recommendations above. They did use snappy, and
their row group sizes are around 5,000 (which still gets reasonable performance). They distribute the data in 2 different
partition schemes. One is just by admin boundary, which leads to a few really large files (India, USA, etc). The other further
splits larger countries into smaller files, using S2 cells.
- [US Structures from Oak Ridge National Laboratory](https://source.coop/wherobots/usa-structures/geoparquet) formatted by
Wherobots.
- [Planet Ag Field Boundaries over EU](https://source.coop/repositories/planet/eu-field-boundaries/description) - needs to be
spatially partitioned, row group size is 25,000.

## Tool Examples

For step-by-step examples of producing GeoParquet that follows these recommendations in GDAL/OGR, DuckDB, gpio and other
tools — along with tool-specific guidance for STAC metadata and spatial partitioning — see
[Tools for Distributing GeoParquet](distributing-geoparquet-tools.md).

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
