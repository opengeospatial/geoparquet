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


### Compression

### bbox covering
  - geoarrow native encoding will be much better for points, but the tool support isn't yet extensive enough to recommend it.

### Spatial Ordering

### Row Group Size

### Spatial Partitioning