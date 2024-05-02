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

import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow.csv import write_csv

from shapely import from_wkt, to_wkb


HERE = pathlib.Path(__file__).parent


metadata_template = {
    "version": "1.1.0",
    "primary_column": "geometry",
    "columns": {
        "geometry": {
            "encoding": "WKB",
            "geometry_types": [],
        },
    },
}


## Various geometry types with WKB and native (GeoArrow-based) encodings

def write_encoding_files(geometries_wkt, geometries_geoarrow, geometry_type):

    table = pa.table({"col": range(len(geometries_wkt)), "geometry": geometries_wkt})
    write_csv(table, HERE / f"data-{geometry_type.lower()}.wkt")

    # WKB encoding
    table = pa.table(
        {"col": range(len(geometries_wkt)), "geometry": to_wkb(from_wkt(geometries_wkt))}
    )
    metadata = copy.deepcopy(metadata_template)
    metadata["columns"]["geometry"]["geometry_type"] = [geometry_type]
    table = table.replace_schema_metadata({"geo": json.dumps(metadata)})
    pq.write_table(table, HERE / f"data-{geometry_type.lower()}-encoding_wkb.parquet")

    # native (geoarrow) encoding
    table = pa.table(
        {"col": range(len(geometries_wkt)), "geometry": geometries_geoarrow}
    )
    metadata["columns"]["geometry"]["encoding"] = geometry_type.lower()
    table = table.replace_schema_metadata({"geo": json.dumps(metadata)})
    pq.write_table(table, HERE / f"data-{geometry_type.lower()}-encoding_native.parquet")


# point

geometries_wkt = [
    "POINT (30 10)",
    "POINT EMPTY",
]

point_type = pa.struct(
    [
        pa.field("x", pa.float64(), nullable=False),
        pa.field("y", pa.float64(), nullable=False)
    ]
)
geometries = pa.array([(30, 10), (float("nan"), float("nan"))], type=point_type)

write_encoding_files(
    geometries_wkt, geometries, geometry_type="Point"
)

# linestring

geometries_wkt = [
    "LINESTRING (30 10, 10 30, 40 40)",
    "LINESTRING EMPTY",
]

linestring_type = pa.list_(pa.field("vertices", point_type, nullable=False))
geometries = pa.array(
    [[(30, 10), (10, 30), (40, 40)], []], type=linestring_type)

write_encoding_files(
    geometries_wkt, geometries, geometry_type="LineString"
)

# polygon

geometries_wkt = [
    "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))",
    "POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10), (20 30, 35 35, 30 20, 20 30))",
    "POLYGON EMPTY",
]

polygon_type = pa.list_(
    pa.field("rings", pa.list_(
        pa.field("vertices", point_type, nullable=False)
    ), nullable=False)
)
geometries = pa.array(
    [
        [[(30.0, 10.0), (40.0, 40.0), (20.0, 40.0), (10.0, 20.0), (30.0, 10.0)]],
        [[(35.0, 10.0), (45.0, 45.0), (15.0, 40.0), (10.0, 20.0), (35.0, 10.0)],
         [(20.0, 30.0), (35.0, 35.0), (30.0, 20.0), (20.0, 30.0)]],
        [],
    ],
    type=polygon_type
)

write_encoding_files(
    geometries_wkt, geometries, geometry_type="Polygon"
)

# multipoint

geometries_wkt = [
    "MULTIPOINT ((30 10))",
    "MULTIPOINT ((10 40), (40 30), (20 20), (30 10))",
    "MULTIPOINT EMPTY",
]

multipoint_type = pa.list_(pa.field("points", point_type, nullable=False))
geometries = pa.array(
    [
        [(30.0, 10.0)],
        [(10.0, 40.0), (40.0, 30.0), (20.0, 20.0), (30.0, 10.0)],
        []
    ],
    type=multipoint_type
)

write_encoding_files(
    geometries_wkt, geometries, geometry_type="MultiPoint"
)

# multilinestring

geometries_wkt = [
    "MULTILINESTRING ((30 10, 10 30, 40 40))",
    "MULTILINESTRING ((10 10, 20 20, 10 40), (40 40, 30 30, 40 20, 30 10))",
    "MULTILINESTRING EMPTY",
]

multilinestring_type = pa.list_(
    pa.field("linestrings", linestring_type, nullable=False)
)
geometries = pa.array(
    [
        [[(30.0, 10.0), (10.0, 30.0), (40.0, 40.0)]],
        [[(10.0, 10.0), (20.0, 20.0), (10.0, 40.0)],
         [(40.0, 40.0), (30.0, 30.0), (40.0, 20.0), (30.0, 10.0)]],
        [],
    ],
    type=multilinestring_type
)

write_encoding_files(
    geometries_wkt, geometries, geometry_type="MultiLineString"
)

# multipolygon

geometries_wkt = [
    "MULTIPOLYGON (((30 10, 40 40, 20 40, 10 20, 30 10)))",
    "MULTIPOLYGON (((30 20, 45 40, 10 40, 30 20)), ((15 5, 40 10, 10 20, 5 10, 15 5)))",
    "MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))",
    "MULTIPOLYGON EMPTY",
]

multipolygon_type = pa.list_(pa.field("polygons", polygon_type, nullable=False))
geometries = pa.array(
    [
        [[[(30.0, 10.0), (40.0, 40.0), (20.0, 40.0), (10.0, 20.0), (30.0, 10.0)]]],
        [[[(30.0, 20.0), (45.0, 40.0), (10.0, 40.0), (30.0, 20.0)]],
         [[(15.0, 5.0), (40.0, 10.0), (10.0, 20.0), (5.0, 10.0), (15.0, 5.0)]]],
        [[[(40.0, 40.0), (20.0, 45.0), (45.0, 30.0), (40.0, 40.0)]],
         [[(20.0, 35.0), (10.0, 30.0), (10.0, 10.0), (30.0, 5.0), (45.0, 20.0), (20.0, 35.0)],
          [(30.0, 20.0), (20.0, 15.0), (20.0, 25.0), (30.0, 20.0)]]],
        [],
    ],
    type=multipolygon_type
)

write_encoding_files(
    geometries_wkt, geometries, geometry_type="MultiPolygon"
)
