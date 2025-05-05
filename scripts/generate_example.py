"""
Generates `example.parquet` using pyarrow by running `python example.py`.

You can print the metadata with:

.. code-block:: python

   >>> import json, pprint, pyarrow.parquet as pq
   >>> pprint.pprint(json.loads(pq.read_schema("example.parquet").metadata[b"geo"]))
"""

from collections import OrderedDict
import json
import pathlib

import geopandas
import pyarrow as pa
import pyarrow.parquet as pq

HERE = pathlib.Path(__file__).parent

df = geopandas.read_file(HERE.parent / "examples" / "example.csv")
df = geopandas.GeoDataFrame(
    df, geometry=geopandas.GeoSeries.from_wkt(df.geometry, crs="OGC:CRS84")
)

geometry_bbox = df.bounds.rename(
    OrderedDict(
        [("minx", "xmin"), ("miny", "ymin"), ("maxx", "xmax"), ("maxy", "ymax")]
    ),
    axis=1,
)
df["bbox"] = geometry_bbox.to_dict("records")
table = pa.Table.from_pandas(df.head().to_wkb())


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
            "bbox": [round(x, 4) for x in df.total_bounds],
            "covering": {
                "bbox": {
                    "xmin": ["bbox", "xmin"],
                    "ymin": ["bbox", "ymin"],
                    "xmax": ["bbox", "xmax"],
                    "ymax": ["bbox", "ymax"],
                },
            },
        },
    },
}

schema = table.schema.with_metadata({"geo": json.dumps(metadata)})
table = table.cast(schema)

pq.write_table(table, HERE / "../examples/example.parquet")
