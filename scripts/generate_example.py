"""
Generates `example.parquet` using pyarrow by running `python example.py`.

You can print the metadata with:

.. code-block:: python

   >>> import json, pprint, pyarrow.parquet as pq
   >>> pprint.pprint(json.loads(pq.read_schema("example.parquet").metadata[b"geo"]))
"""

import json
import pathlib

import pandas as pd
import geoarrow.pyarrow as ga
import geopandas
import pyarrow as pa
import math
import pyarrow.parquet as pq

HERE = pathlib.Path(__file__).parent

df = pd.read_csv(HERE.parent / "examples" / "example.csv")
df = geopandas.GeoDataFrame(
    df, geometry=geopandas.GeoSeries.from_wkt(df.geometry, crs="OGC:CRS84")
)

table = pa.table(df.to_arrow())

def get_version() -> str:
    """Read the version const from the schema.json file"""
    with open(HERE / "../format-specs/schema.json") as f:
        spec_schema = json.load(f)
        return spec_schema["properties"]["version"]["const"]


metadata = {
    "version": get_version(),
    "primary_column": "geometry",
    "columns": {
        "geometry": {
            "encoding": "WKB",
            "geometry_types": ["Polygon", "MultiPolygon"],
            "crs": json.loads(df.crs.to_json()),
            "edges": "planar",
            "bbox": list(df.total_bounds),
        },
    },
}

table = table.replace_schema_metadata({"geo": json.dumps(metadata)})
pq.write_table(table, HERE / "../examples/example.parquet")
