"""
Generates `example.parquet` using pyarrow.
"""
import json
import pathlib

import pyarrow as pa
import pyarrow.parquet as pq
import geopandas

HERE = pathlib.Path(__file__).parent

df = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
table = pa.Table.from_pandas(df.head().to_wkb())


metadata = {
    "geoparquet_version": "0.1.0",
    "primary_column": "geometry",
}

column_metadata = {
    b"epsg": str(df.crs.to_epsg()).encode(),
}
field = table.schema.field("geometry").with_metadata(column_metadata)
idx = table.schema.get_field_index("geometry")

schema = (
    table.schema.remove(idx)
    .insert(idx, field)
    .with_metadata({"geoparquet": json.dumps(metadata)})
)
table = table.cast(schema)

pq.write_table(table, HERE / "example.parquet")
