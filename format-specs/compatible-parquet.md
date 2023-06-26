# Parquet Geospatial Compatibility

The goal of GeoParquet is that every tool producing Parquet and includes geospatial data uses official [metadata defined in the GeoParquet spec](./geoparquet_spec) to achieve true interoperability. Thid document represents a set of guidelines for those would like to produce geospatial Parquet data but are using tools that are not yet fully implementing GeoParquet metadata. It is meant to be used just for the interim time when only some tools properly produce GeoParquet, to data producer support the growing ecosystem.

To be clear, this is *only* recommended for those who are using tools that don't yet produce valid GeoParquet, and we encourage advocating to the creaters of tools you are using to implement the GeoParquet spec. Feel free to [start a discussion](https://github.com/opengeospatial/geoparquet/discussions) to raise awareness of tools that ideally support Geoparquet - the community can likely help in encouraging an implementation.

The core idea behind these compatibility guidelines is that tools and libraries that read GeoParquet will be able to parse these geospatial compatible Parquet files, to make it easy to get data into the GeoParquet ecosystem. But it is only recommended for those tools and libraries to produce valid GeoParquet, following [Postel's Law](https://en.wikipedia.org/wiki/Robustness_principle) of being liberal in what you accept but conservative in what you send - if you are authoring a tool to write GeoParquet please do not give users the option to create these parquet files.

## Compatibility Guidelines

The core idea of the compatibility guidelines is to have the output match the defaults of the official spec as closely as possible, so it is very easy for tools to simply add the appropriate Parquet metadata and create valid GeoParquet. The guidelines are as follows:

* The geometry column should be named 'geometry'.

* The geometry column should be a `BYTE_ARRAY` with Well Known Binary (WKB) used to define the geometries, as defined in the [encoding](./geoparquet.md#encoding) section of the GeoParquet spec.

* All data is stored in longitude, latitude based on the WGS84 datum, as defined as the default in the [crs](./geoparquet.md#crs) section of the GeoParquet spec.

### Data Reader Assumptions

The above are the key recommendations a data producer should follow. Any implemented reader will need to make the following assumptions when reading one of these columns, unless the user supplies additional information that they are aware of:

* The geometry_types values is an empty array, signaling the geometry type is not known and the reader should make no assumptions about the types, as defined in the [geometry_types](./geoparquet.md#geometry_types) section of the spec.

* Any CRS-aware reader should assume that the CRS is OGC:CRS84 as explained in the [crs](./geoparquet.md#crs) section of the spec. (Or it could assume it is EPSG:4326 but overriding the axis order to assume longitude latitude as explained in the [Coordinate axis order](./geoparquet.md#coordinate-axis-order)) section.

* No assertions are made on the winding order, the default of the [orientation](./geoparquet.md#orientation) section of the spec.

* Edges are planar, as explained to be the default in the [edges](./geoparquet.md#edges) section of the spec.

## Data Reader Implementation Considerations

Reading this non-compliant geospatial data from Parquet should ideally work with no user intervention if the producer followed all the guidelines and named their geometry column 'geometry'. Readers can optionally support user input (in whatever manner works for the tool / library) to provide hints for metadata that is not inline with the lowest common denominator compatibility. This would include things like letting the user supply a geometry column name (ie something other than 'geometry'), using Well Known Text (WKT) in a `STRING` column instead of WKB, providing a more specific geometry_type value, or providing other enhanced metadata (specifying the CRS, the winding order, the edges, the bbox or the epoch).

We strongly advise against creating a reader that can only understand these geospatial compatible files - all readers should start by looking at the metadata specified by GeoParquet and only fall back on these compatibility techniques if the metadata is not present. A reader that could not read GeoParquet but would read compatible geodata would have no idea if there was in fact metadata, and thus could easily decrease interoperability.

## Data Producer Considerations

As mentioned above, we strongly recommend trying to find tools that will produce valid GeoParquet. If the tool you are working with does not support it directdly then there are [many tools](geoparquet.org) that can help you. Only if there is no way to create valid GeoParquet metadata do we recommend this route. This will enable those who have readers that understand GeoParquet and these compatible files to turn it into valid GeoParquet themselves.

We recommend sticking to the core recommendations as much as possible - naming the geometry column 'geometry', using WKB, and storing data as long, lat. If your data must be formatted differently then less readers will be able to work with it. If you do go that route be sure to make it clear in all your documentation where things are different.
