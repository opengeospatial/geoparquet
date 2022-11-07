"""
Generates `example.parquet` using pyarrow by running `python example.py`.

You can print the metadata with:

.. code-block:: python

   >>> import json, pprint, pyarrow.parquet as pq
   >>> pprint.pprint(json.loads(pq.read_schema("example.parquet").metadata[b"geo"]))
"""
import json
import pathlib
import copy

import pyarrow as pa
import pyarrow.parquet as pq

from shapely import wkt, wkb


HERE = pathlib.Path(__file__).parent


metadata_template = {
    "version": "0.4.0",
    "primary_column": "geometry",
    "columns": {
        "geometry": {
            "encoding": "WKB",
            "geometry_type": "Unknown",
        },
    },
}


def to_wkb(values):
    return [wkb.dumps(wkt.loads(val)) for val in values]


# Minimum required metadata

table = pa.table(
    {"col": [1, 2, 3], "geometry": to_wkb(["POINT (1 1)", "POINT (2 2)", "POINT (3 3)"])}
)
metadata = copy.deepcopy(metadata_template)
table = table.replace_schema_metadata({"geo": json.dumps(metadata)})
pq.write_table(table, HERE / "data_minimal.parquet")


# Geometry type - single string or list

table = pa.table(
    {"col": [1, 2, 3], "geometry": to_wkb(["POINT (1 1)", "POINT (2 2)", "POINT (3 3)"])}
)
metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_type"] = "Point"
table = table.replace_schema_metadata({"geo": json.dumps(metadata)})
pq.write_table(table, HERE / "data_geometry_type_string.parquet")

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_type"] = ["Point"]
table = table.replace_schema_metadata({"geo": json.dumps(metadata)})
pq.write_table(table, HERE / "data_geometry_type_list.parquet")


# Geometry column name

table = pa.table(
    {"col": [1, 2, 3], "geom": to_wkb(["POINT (1 1)", "POINT (2 2)", "POINT (3 3)"])}
)
metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geom"] = metadata["columns"].pop("geometry")
table = table.replace_schema_metadata({"geo": json.dumps(metadata)})
pq.write_table(table, HERE / "data_geometry_column_name.parquet")


# CRS - explicit null

table = pa.table(
    {"col": [1, 2, 3], "geometry": to_wkb(["POINT (1 1)", "POINT (2 2)", "POINT (3 3)"])}
)
metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["crs"] = None
table = table.replace_schema_metadata({"geo": json.dumps(metadata)})
pq.write_table(table, HERE / "data_crs_null.parquet")


# Orientation

table = pa.table(
    {"col": [1, 2, 3], "geometry": to_wkb(["POINT (1 1)", "POINT (2 2)", "POINT (3 3)"])}
)
metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["orientation"] = "counterclockwise"
table = table.replace_schema_metadata({"geo": json.dumps(metadata)})
pq.write_table(table, HERE / "data_orientation.parquet")


