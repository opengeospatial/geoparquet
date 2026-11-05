# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "geoarrow-pyarrow>=0.2.0",
#   "pyarrow>=22.0.0",
#   "shapely>=2.1.0",
# ]
# ///
"""
Generate GeoParquet files for testing the levels-of-detail proposal.

Run this script to regenerate and validate the LOD-only test data:

    uv run generate_test_data.py
"""

import json
from pathlib import Path

import geoarrow.pyarrow as ga
import pyarrow as pa
import pyarrow.parquet as pq
import shapely
from shapely.geometry import LineString, MultiLineString, MultiPolygon, Polygon

HERE = Path(__file__).parent

START_LONGITUDE = -117.1956458
START_LATITUDE = 34.0559533
LOD_LEVELS = (
    {
        "column": "geometry_lod_0",
        "field": "level_0",
        "resolution": 0.004,
    },
    {
        "column": "geometry_lod_1",
        "field": "level_1",
        "resolution": 0.002,
    },
    {
        "column": "geometry_lod_2",
        "field": "level_2",
        "resolution": 0.001,
    },
)

EPSG_4326 = {
    "$schema": "https://proj.org/schemas/v0.7/projjson.schema.json",
    "type": "GeographicCRS",
    "name": "WGS 84",
    "datum_ensemble": {
        "name": "World Geodetic System 1984 ensemble",
        "members": [
            {
                "name": "World Geodetic System 1984 (Transit)",
                "id": {"authority": "EPSG", "code": 1166},
            },
            {
                "name": "World Geodetic System 1984 (G730)",
                "id": {"authority": "EPSG", "code": 1152},
            },
            {
                "name": "World Geodetic System 1984 (G873)",
                "id": {"authority": "EPSG", "code": 1153},
            },
            {
                "name": "World Geodetic System 1984 (G1150)",
                "id": {"authority": "EPSG", "code": 1154},
            },
            {
                "name": "World Geodetic System 1984 (G1674)",
                "id": {"authority": "EPSG", "code": 1155},
            },
            {
                "name": "World Geodetic System 1984 (G1762)",
                "id": {"authority": "EPSG", "code": 1156},
            },
            {
                "name": "World Geodetic System 1984 (G2139)",
                "id": {"authority": "EPSG", "code": 1309},
            },
            {
                "name": "World Geodetic System 1984 (G2296)",
                "id": {"authority": "EPSG", "code": 1383},
            },
        ],
        "ellipsoid": {
            "name": "WGS 84",
            "semi_major_axis": 6378137,
            "inverse_flattening": 298.257223563,
        },
        "accuracy": "2.0",
        "id": {"authority": "EPSG", "code": 6326},
    },
    "coordinate_system": {
        "subtype": "ellipsoidal",
        "axis": [
            {
                "name": "Geodetic latitude",
                "abbreviation": "Lat",
                "direction": "north",
                "unit": "degree",
            },
            {
                "name": "Geodetic longitude",
                "abbreviation": "Lon",
                "direction": "east",
                "unit": "degree",
            },
        ],
    },
    "scope": "Horizontal component of 3D system.",
    "area": "World.",
    "bbox": {
        "south_latitude": -90,
        "west_longitude": -180,
        "north_latitude": 90,
        "east_longitude": 180,
    },
    "id": {"authority": "EPSG", "code": 4326},
}


def generate_example_files():
    for name, geometry in example_geometries().items():
        path = HERE / f"{name}.parquet"
        write_geometry_file(path, geometry)
        validate_geometry_file(path)


def example_geometries():
    line = [
        coordinate(0.000, 0.000),
        coordinate(0.002, 0.002),
        coordinate(0.004, -0.001),
        coordinate(0.006, 0.003),
        coordinate(0.008, 0.000),
        coordinate(0.010, 0.002),
    ]
    first_polygon = Polygon(
        [
            coordinate(0.000, -0.002),
            coordinate(0.000, 0.001),
            coordinate(0.001, 0.004),
            coordinate(0.004, 0.004),
            coordinate(0.005, 0.003),
            coordinate(0.008, 0.004),
            coordinate(0.008, 0.001),
            coordinate(0.008, -0.002),
            coordinate(0.004, -0.001),
            coordinate(0.000, -0.002),
        ],
        [
            [
                coordinate(0.002, 0.000),
                coordinate(0.004, 0.0002),
                coordinate(0.006, 0.000),
                coordinate(0.006, 0.001),
                coordinate(0.006, 0.002),
                coordinate(0.004, 0.0018),
                coordinate(0.002, 0.002),
                coordinate(0.002, 0.001),
                coordinate(0.002, 0.000),
            ]
        ],
    )
    second_polygon = Polygon(
        [
            coordinate(0.012, -0.001),
            coordinate(0.012, 0.003),
            coordinate(0.018, 0.003),
            coordinate(0.018, -0.001),
            coordinate(0.012, -0.001),
        ]
    )
    return {
        "linestring": LineString(line),
        "multilinestring": MultiLineString([line[:3], line[3:]]),
        "polygon": first_polygon,
        "multipolygon": MultiPolygon([first_polygon, second_polygon]),
    }


def coordinate(longitude_offset, latitude_offset):
    return (
        START_LONGITUDE + longitude_offset,
        START_LATITUDE + latitude_offset,
    )


def write_geometry_file(path, geometry):
    assert shapely.is_valid(geometry)

    geometry_array = create_geometry_array(geometry)
    column_arrays = [
        pa.array([1], type=pa.int32()),
        pa.array(["feature"], type=pa.string()),
        geometry_array,
    ]
    column_fields = [
        pa.field("id", pa.int32(), nullable=False),
        pa.field("name", pa.string(), nullable=False),
        pa.field("geometry", geometry_array.type, nullable=False),
    ]
    geometry_columns = {
        "geometry": {
            **geometry_column_metadata(geometry),
            "lods": [
                {
                    "column": level["column"],
                    "resolution": level["resolution"],
                }
                for level in LOD_LEVELS
            ],
        }
    }
    source_coordinate_count = shapely.get_num_coordinates(geometry)
    lod_coordinate_counts = []
    lod_arrays = []
    lod_fields = []

    for level in LOD_LEVELS:
        lod_geometry = create_lod_geometry(geometry, level["resolution"])
        assert shapely.is_valid(lod_geometry)
        lod_coordinate_count = shapely.get_num_coordinates(lod_geometry)
        assert lod_coordinate_count <= source_coordinate_count
        lod_coordinate_counts.append(lod_coordinate_count)
        lod_array = create_geometry_array(lod_geometry)
        lod_arrays.append(lod_array)
        lod_fields.append(pa.field(level["field"], lod_array.type, nullable=False))
        geometry_columns[level["column"]] = geometry_column_metadata(
            lod_geometry, ["lods", level["field"]]
        )

    assert min(lod_coordinate_counts) < source_coordinate_count

    lod_type = pa.struct(lod_fields)
    column_arrays.append(pa.StructArray.from_arrays(lod_arrays, fields=lod_fields))
    column_fields.append(pa.field("lods", lod_type, nullable=False))

    metadata = {
        "version": "2.0.0",
        "primary_column": "geometry",
        "columns": geometry_columns,
    }
    schema = pa.schema(
        column_fields,
        metadata={b"geo": json.dumps(metadata).encode()},
    )
    table = pa.Table.from_arrays(column_arrays, schema=schema)
    pq.write_table(table, path, compression="snappy", write_page_index=True)
    print(path)


def validate_geometry_file(path):
    parquet_file = pq.ParquetFile(path)
    schema = parquet_file.schema_arrow
    metadata = json.loads(schema.metadata[b"geo"])
    levels = metadata["columns"]["geometry"]["lods"]
    expected_levels = [
        {
            "column": level["column"],
            "resolution": level["resolution"],
        }
        for level in LOD_LEVELS
    ]
    expected_paths = {
        "geometry": ["geometry"],
        **{level["column"]: ["lods", level["field"]] for level in LOD_LEVELS},
    }

    assert metadata["primary_column"] == "geometry"
    assert "ordering" not in metadata
    assert parquet_file.metadata.num_rows == 1
    assert schema.names == ["id", "name", "geometry", "lods"]
    assert set(metadata["columns"]) == set(expected_paths)
    assert "lod" not in metadata["columns"]["geometry"]
    assert levels == expected_levels

    for identifier, path in expected_paths.items():
        column_metadata = metadata["columns"][identifier]
        resolved_path = column_metadata.get("path", [identifier])
        field = schema.field(path[0])
        for component in path[1:]:
            field = field.type.field(component)
        storage_type = (
            field.type.storage_type
            if isinstance(field.type, pa.ExtensionType)
            else field.type
        )
        assert pa.types.is_binary(storage_type)
        assert resolved_path == path

    assert "path" not in metadata["columns"]["geometry"]

    for level in levels:
        assert set(level) == {"column", "resolution"}
        level_metadata = metadata["columns"][level["column"]]
        assert level_metadata["encoding"] == "WKB"
        assert "lods" not in level_metadata


def create_geometry_array(geometry):
    return ga.with_crs(ga.as_wkb([geometry.wkb]), "EPSG:4326")


def geometry_column_metadata(geometry, path=None):
    metadata = {
        "encoding": "WKB",
        "geometry_types": [geometry.geom_type],
        "bbox": list(geometry.bounds),
        "crs": EPSG_4326,
    }
    if path is not None:
        metadata["path"] = path
    return metadata


def create_lod_geometry(geometry, resolution):
    return shapely.simplify(
        geometry,
        tolerance=resolution,
        preserve_topology=True,
    )


if __name__ == "__main__":
    generate_example_files()
