
# Parquet Geospatial Compatibility

The goal of GeoParquet is that every tool producing Parquet and includes geospatial data uses our [defined metadata](./geoparquet_spec) to enable maximum compatibility. But in the interim time when only some tools properly produce GeoParquet, we are recommending the following best practices for the distribution of geospatial data as Parquet. 

This is *only* recommended for those who are using tools that don't yet produce valid GeoParquet, and we encourage advocating to the creaters of tools you are using to implement the GeoParquet spec. Feel free to [start a discussion](https://github.com/opengeospatial/geoparquet/discussions) to raise awareness of tools that ideally support Geoparquet - the community can likely help in encouraging an implementation.

Tools and libraries that read GeoParquet are encouraged to be able to parse these files, to make it easy to get data into the GeoParquet ecosystem. But it is only recommended for tools and libraries to produce valid GeoParquet, following [Postel's Law](https://en.wikipedia.org/wiki/Robustness_principle) of being liberal in what you accept but conservative in what you send.

## Compatibility Guidelines

TODO: flesh this out with more narrative.

The geometry column should be named 'geometry'.

The geometry column should be either a binary column with Well Known Binary (WKB) or a text column with Well Known Text (WKT) used to define the geometries.

All data is stored in longitude, latitude based on the WGS84 datum.

Readers should be default make the following assumptions when they read one of these columns:

* The geometry_types values is an empty array - the types are not known.
* The CRS OGC:CRS84
* No assertions are made on the winding order
* Edges are planer

## Data Reader Implementation Considerations

Reading this non-compliant geospatial data from Parquet should ideally work with no user intervention if the producer followed all the guidelines and named their geometry column 'geometry'. Readers can optionally support user input (in whatever manner works for the tool / library) to provide hints for metadata that is not inline with the lowest common denominator compatibility. This would include things like letting the user supply a geometry column name (ie something other than 'geometry'), providing a more specific geometry_type value, or providing other enhanced metadata (specifying the CRS, the winding order, the edges, the bbox or the epoch).

We strongly advise against creating a reader that can only understand these geospatial compatible types, all readers should start by looking at the metadata specified by GeoParquet and only fall back on these compatibility techniques if the metadata is not present. A reader that could not read GeoParquet but would read compatible geodata would have no idea if there was in fact metadata, and thus could easily decrease interoperability.

## Data Producer Considerations

As mentioned above, we strongly recommend trying to find tools that will produce valid GeoParquet. If the tool you are working with does not support it directdly then there are [many tools](geoparquet.org) that can help you. Only if there is no way to create valid GeoParquet metadata do we recommend this route. This will enable those who have readers that understand GeoParquet and these compatible files to turn it into valid GeoParquet themselves.

We recommend sticking to the core recommendations as much as possible - naming the geometry column 'geometry', using WKB, and storing data
as long, lat. If your data must be formatted differently then less readers will be able to work with it. If you do go that route be sure to
make it clear in all your documentation where things are different.



