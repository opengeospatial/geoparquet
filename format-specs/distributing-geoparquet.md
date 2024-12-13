# Best Practices for Distributing GeoParquet

This guide aims to encapsulate a number of best practices that the community has
started to align on for making 'good' GeoParquet files, especially for distribution
of data. Parquet gives users lots of different options, and the defaults of various
libraries are different and usually not optimized for geospatial data. 

## tl;dr Recommendations

Later sections will go deep into the reasoning and nuances behind these options, but if you're
just looking to be sure you get the basics right then this section may be sufficient.
And if you're building a tool or library then consider these as good defaults.

 * Use zstd for compression.
 * Be sure to include the [bbox covering](https://github.com/opengeospatial/geoparquet/blob/v1.1.0/format-specs/geoparquet.md#bbox-covering-encoding), and use GeoParquet version 1.1.
 * Spatially order the data within the file.
 * Set the maximum row group size between 100,000 and 200,000 per row.
 * If the data is larger than ~2 gigabytes consider spatially partitioning the files.
 * Use [https://stacspec.org/en] STAC metadata to describe the data.


### Compression

Parquet has built in compression, enabling users to directly use files that are similar in size to the zipped versions
of other formats. The cool thing is you can easily change the compression algorithm, and new ones continue to be added.
The default for most Parquet libraries is `snappy`, which excels at speed and gets good compression. More recently the
`zstd` library has been added to the Parquet ecosystem, and it achieves a better compression ration with similar speeds
to snappy. At this point most all Parquet libraries support `zstd`, and since better compression makes for faster downloads
and streaming it's the current recommendation.

One interesting option is `brotli`, which often compresses 20-30% smaller than `zstd` but is slower. It is reaching wider
adoption, so if you want to have the smallest possible files then it's worth considering. But for many access patterns
it will be slower overall than `zstd`. There is an option to do 'uncompressed' files, but this is not recommended.

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
for a point adds a good bit of overhead. But we do not yet recommend using the native encodings, since the tool support
isn't yet extensive enough to be sure that most clients will understand them. But as the ecosystem matures this will
be a great option.

### Spatial Ordering

### Row Group Size

### Spatial Partitioning