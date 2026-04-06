"""
Generates example data using pyarrow by running `python generate_test_data.py`.

You can print the metadata with:

.. code-block:: python

   >>> import json, pprint, pyarrow.parquet as pq
   >>> pprint.pprint(json.loads(pq.read_schema("example.parquet").metadata[b"geo"]))
"""

import json
import pathlib
import copy

import geoarrow.pyarrow as ga
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow.csv import write_csv


HERE = pathlib.Path(__file__).parent


metadata_template = {
    "version": "2.0-dev",
    "primary_column": "geometry",
    "columns": {
        "geometry": {
            "encoding": "WKB",
            "geometry_types": [],
        },
    },
}


## Various geometry types


def write_encoding_files(geometries_wkt, geometry_type):

    table = pa.table({"col": range(len(geometries_wkt)), "geometry": geometries_wkt})
    write_csv(table, HERE / f"data-{geometry_type.lower()}-wkt.csv")

    # WKB encoding
    table = pa.table(
        {
            "col": range(len(geometries_wkt)),
            "geometry": ga.as_wkb(geometries_wkt),
        }
    )
    metadata = copy.deepcopy(metadata_template)
    metadata["columns"]["geometry"]["geometry_types"] = [geometry_type]
    table = table.replace_schema_metadata({"geo": json.dumps(metadata)})
    out_file = HERE / f"data-{geometry_type.lower()}-encoding_wkb.parquet"
    pq.write_table(table, out_file)

    # Check geometry logical type output
    f = pq.ParquetFile(out_file)
    geom_col_schema = f.schema.column(1)
    logical_type = geom_col_schema.logical_type

    assert logical_type is not None, "geometry column has no logical type"
    logical_type_json = json.loads(logical_type.to_json())
    assert logical_type_json["Type"] == "Geometry"


# point

geometries_wkt = [
    "POINT (30 10)",
    "POINT EMPTY",
    None,
    "POINT (40 40)",
]

write_encoding_files(geometries_wkt, geometry_type="Point")

# linestring

geometries_wkt = ["LINESTRING (30 10, 10 30, 40 40)", "LINESTRING EMPTY", None]

write_encoding_files(geometries_wkt, geometry_type="LineString")

# polygon

geometries_wkt = [
    "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))",
    "POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10), (20 30, 35 35, 30 20, 20 30))",
    "POLYGON EMPTY",
    None,
]

write_encoding_files(geometries_wkt, geometry_type="Polygon")

# multipoint

geometries_wkt = [
    "MULTIPOINT ((30 10))",
    "MULTIPOINT ((10 40), (40 30), (20 20), (30 10))",
    "MULTIPOINT EMPTY",
    None,
]

write_encoding_files(geometries_wkt, geometry_type="MultiPoint")

# multilinestring

geometries_wkt = [
    "MULTILINESTRING ((30 10, 10 30, 40 40))",
    "MULTILINESTRING ((10 10, 20 20, 10 40), (40 40, 30 30, 40 20, 30 10))",
    "MULTILINESTRING EMPTY",
    None,
]

write_encoding_files(geometries_wkt, geometry_type="MultiLineString")

# multipolygon

geometries_wkt = [
    "MULTIPOLYGON (((30 10, 40 40, 20 40, 10 20, 30 10)))",
    "MULTIPOLYGON (((30 20, 45 40, 10 40, 30 20)), ((15 5, 40 10, 10 20, 5 10, 15 5)))",
    "MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))",
    "MULTIPOLYGON EMPTY",
    None,
]

write_encoding_files(geometries_wkt, geometry_type="MultiPolygon")
