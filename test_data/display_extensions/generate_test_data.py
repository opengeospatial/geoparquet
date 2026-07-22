# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "geoarrow-pyarrow>=0.2.0",
#   "pyarrow>=22.0.0",
#   "shapely>=2.1.0",
#   "proto-plus>=1.28.1",
# ]
# ///
"""
Generates example data using pyarrow, shapely, and proto-plus by running:

    uv run test_data/display_extensions/generate_test_data.py

"""

import json
import math
from pathlib import Path

import geoarrow.pyarrow as ga
import proto
import pyarrow as pa
import pyarrow.parquet as pq
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

HERE = Path(__file__).parent

START_LONGITUDE = -117.1956458
START_LATITUDE = 34.0559533
ORDERING_EXTENT = [-180.0, -90.0, 180.0, 90.0]
POINT_Z_BIT_WIDTH = 20
XZ_MAX_LEVEL = 20

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


class PbfGeometry(proto.Message):
    lengths = proto.RepeatedField(proto.UINT32, number=2)
    coords = proto.RepeatedField(proto.SINT64, number=3)


def generate_example_files():
    for name, geometry in example_geometries().items():
        write_geometry_file(HERE / f"{name}.parquet", geometry)


def create_lod_levels():
    resolution = 0.703125
    scale = 295_829_355.4545656
    levels = []

    for level in range(17):
        if level % 2 == 0:
            levels.append(
                {
                    "column": f"level_{level}",
                    "resolution": resolution,
                    "scale": scale,
                }
            )
        resolution /= 2
        scale /= 2

    return levels


def example_geometries():
    def coordinate(longitude_offset, latitude_offset):
        return (
            START_LONGITUDE + longitude_offset,
            START_LATITUDE + latitude_offset,
        )

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
            coordinate(0.000, 0.004),
            coordinate(0.008, 0.004),
            coordinate(0.008, -0.002),
            coordinate(0.000, -0.002),
        ],
        [
            [
                coordinate(0.002, 0.000),
                coordinate(0.006, 0.000),
                coordinate(0.006, 0.002),
                coordinate(0.002, 0.002),
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
        "point": Point(START_LONGITUDE, START_LATITUDE),
        "multipoint": MultiPoint(
            [
                coordinate(0.000, 0.000),
                coordinate(0.003, 0.002),
                coordinate(0.006, -0.001),
                coordinate(0.009, 0.003),
            ]
        ),
        "linestring": LineString(line),
        "multilinestring": MultiLineString([line[:3], line[3:]]),
        "polygon": first_polygon,
        "multipolygon": MultiPolygon([first_polygon, second_polygon]),
    }


def write_geometry_file(path, geometry):
    bounds = list(geometry.bounds)
    ordering = ordering_metadata(geometry, ORDERING_EXTENT)
    geometry_type = geometry.geom_type
    geometry_array = ga.with_crs(ga.as_wkb([geometry.wkb]), "EPSG:4326")

    columns = [
        pa.array([1], type=pa.int32()),
        pa.array(["feature"], type=pa.string()),
        geometry_array,
        pa.array([ordering_key(geometry, ORDERING_EXTENT)], type=pa.uint64()),
    ]
    fields = [
        pa.field("id", pa.int32(), nullable=False),
        pa.field("name", pa.string(), nullable=False),
        pa.field("geometry", geometry_array.type, nullable=False),
        pa.field("geokey", pa.uint64(), nullable=False),
    ]

    lod_metadata = None
    if geometry_type in {
        "LineString",
        "MultiLineString",
        "Polygon",
        "MultiPolygon",
    }:
        geolod, geolod_field, lod_metadata = create_lod_column(geometry)
        columns.append(geolod)
        fields.append(geolod_field)

    metadata = {
        "version": "2.0.0",
        "primary_column": "geometry",
        "columns": {
            "geometry": {
                "encoding": "WKB",
                "geometry_types": [geometry_type],
                "bbox": bounds,
                "crs": EPSG_4326,
            }
        },
        "ordering": ordering,
    }
    if lod_metadata is not None:
        metadata["lod"] = lod_metadata

    schema = pa.schema(fields, metadata={b"geo": json.dumps(metadata).encode()})
    table = pa.Table.from_arrays(columns, schema=schema)
    pq.write_table(table, path, compression="snappy", write_page_index=True)
    print(path)


def ordering_metadata(geometry, extent):
    if geometry.geom_type == "Point":
        return {
            "type": "z",
            "geometry_column": "geometry",
            "extent": extent,
            "bit_width": POINT_Z_BIT_WIDTH,
        }
    return {
        "type": "xz",
        "geometry_column": "geometry",
        "extent": extent,
        "max_level": XZ_MAX_LEVEL,
    }


def ordering_key(geometry, extent):
    if geometry.geom_type != "Point":
        return xz_code(extent, geometry.bounds, max_level=XZ_MAX_LEVEL)

    x_coordinate = quantize_coordinate(
        geometry.x,
        extent[0],
        extent[2],
        POINT_Z_BIT_WIDTH,
    )
    y_coordinate = quantize_coordinate(
        geometry.y,
        extent[1],
        extent[3],
        POINT_Z_BIT_WIDTH,
    )
    return interleave_bits(x_coordinate, y_coordinate, POINT_Z_BIT_WIDTH)


def quantize_coordinate(value, minimum, maximum, bit_width):
    coordinate_count = 1 << bit_width
    normalized = (value - minimum) / (maximum - minimum)
    coordinate = math.trunc(normalized * coordinate_count)
    return min(max(coordinate, 0), coordinate_count - 1)


def xz_code(full_extent, feature_extent, max_level):
    full_width = full_extent[2] - full_extent[0]
    full_height = full_extent[3] - full_extent[1]
    feature_width = feature_extent[2] - feature_extent[0]
    feature_height = feature_extent[3] - feature_extent[1]

    if feature_width <= 0 or feature_height <= 0:
        level = 0
    else:
        x_level = math.log2(full_width / feature_width)
        y_level = math.log2(full_height / feature_height)
        level = min(math.floor(min(x_level, y_level)) + 1, max_level)

    cell_width = full_width / (1 << level)
    cell_height = full_height / (1 << level)
    cell_x_start = math.floor((feature_extent[0] - full_extent[0]) / cell_width)
    cell_x_end = math.floor((feature_extent[2] - full_extent[0]) / cell_width)
    cell_y_start = math.floor((feature_extent[1] - full_extent[1]) / cell_height)
    cell_y_end = math.floor((feature_extent[3] - full_extent[1]) / cell_height)

    if cell_x_end - cell_x_start + 1 > 2 or cell_y_end - cell_y_start + 1 > 2:
        level = max(level - 1, 0)

    return xz_point_code(
        full_extent,
        feature_extent[0],
        feature_extent[1],
        max_level,
        level,
    )


def xz_point_code(full_extent, point_x, point_y, max_level, insert_level):
    depth = 0
    sequence_code = 0
    xmin, ymin, xmax, ymax = full_extent

    while depth != insert_level:
        center_x = (xmin + xmax) / 2
        if point_x >= center_x:
            xmin = center_x
            quadrant_x = 1
        else:
            xmax = center_x
            quadrant_x = 0

        center_y = (ymin + ymax) / 2
        if point_y >= center_y:
            ymin = center_y
            quadrant_y = 1
        else:
            ymax = center_y
            quadrant_y = 0

        quadrant_code = quadrant_x | (quadrant_y << 1)
        sequence_code += quadrant_code * xz_element_count(max_level, depth) + 1
        depth += 1

    return sequence_code


def xz_element_count(max_level, sequence_index):
    return (4 ** (max_level - sequence_index) - 1) // 3


def interleave_bits(x_value, y_value, bit_width):
    result = 0
    for bit_index in range(bit_width):
        result |= ((x_value >> bit_index) & 1) << (bit_index * 2)
        result |= ((y_value >> bit_index) & 1) << (bit_index * 2 + 1)
    return result


def create_lod_column(geometry):
    arrays = []
    fields = []
    levels_metadata = []

    for level in create_lod_levels():
        encoded = encode_lod_geometry(geometry, level["resolution"])
        arrays.append(pa.array([encoded], type=pa.binary()))
        fields.append(pa.field(level["column"], pa.binary(), nullable=True))
        levels_metadata.append(
            {
                "column": ["geolod", level["column"]],
                "scale": level["scale"],
                "transform": {
                    "scale": [
                        level["resolution"],
                        level["resolution"],
                        1.0,
                        1.0,
                    ],
                    "translate": [0.0, 0.0, 0.0, 0.0],
                },
            }
        )

    geolod_type = pa.struct(fields)
    geolod = pa.StructArray.from_arrays(arrays, fields=fields)
    metadata = {
        "geometry_column": "geometry",
        "encoding": "pbf",
        "levels": levels_metadata,
    }
    if geometry.geom_type in {"Polygon", "MultiPolygon"}:
        metadata["orientation"] = "clockwise"
    return geolod, pa.field("geolod", geolod_type, nullable=False), metadata


def encode_lod_geometry(geometry, resolution):
    minimum_length = (
        3 if geometry.geom_type in {"Polygon", "MultiPolygon"} else 2
    )
    paths = [quantize_path(path, resolution) for path in geometry_paths(geometry)]
    retained_paths = [path for path in paths if len(path) >= minimum_length]
    if not retained_paths:
        # Preserve one coordinate when coarse quantization collapses every part.
        retained_paths = [[paths[0][0]]]

    lengths = [len(path) for path in retained_paths]
    encoded_coordinates = []

    for path in retained_paths:
        previous_x, previous_y = path[0]
        encoded_coordinates.extend([previous_x, previous_y])
        # PBF stores the first XY pair absolutely and the rest as deltas.
        for x_value, y_value in path[1:]:
            encoded_coordinates.extend([x_value - previous_x, y_value - previous_y])
            previous_x = x_value
            previous_y = y_value

    return PbfGeometry.serialize(
        PbfGeometry(
            lengths=lengths,
            coords=encoded_coordinates,
        )
    )


def geometry_paths(geometry):
    if geometry.geom_type == "LineString":
        return [list(geometry.coords)]
    if geometry.geom_type == "MultiLineString":
        return [list(line.coords) for line in geometry.geoms]
    if geometry.geom_type == "Polygon":
        return polygon_paths(geometry)
    if geometry.geom_type == "MultiPolygon":
        return [path for polygon in geometry.geoms for path in polygon_paths(polygon)]
    raise ValueError(f"unsupported LOD geometry type: {geometry.geom_type}")


def polygon_paths(polygon):
    paths = [list(reversed(polygon.exterior.coords))]
    paths.extend(list(reversed(interior.coords)) for interior in polygon.interiors)
    return paths


def quantize_path(coordinates, resolution):
    first_x, first_y = coordinates[0]
    previous_x = round_coordinate(first_x / resolution)
    previous_y = round_coordinate(first_y / resolution)
    quantized = [(previous_x, previous_y)]
    previous_delta_x = 0
    previous_delta_y = 0

    for x_value, y_value in coordinates[1:]:
        x_value = round_coordinate(x_value / resolution)
        y_value = round_coordinate(y_value / resolution)
        if (x_value, y_value) == (previous_x, previous_y):
            continue

        delta_x = x_value - previous_x
        delta_y = y_value - previous_y
        collinear = (
            previous_delta_x * delta_y == delta_x * previous_delta_y
            and previous_delta_x * delta_x + previous_delta_y * delta_y > 0
        )
        if collinear:
            # Replace the previous point to remove collinear grid vertices.
            quantized[-1] = (x_value, y_value)
        else:
            quantized.append((x_value, y_value))
            previous_delta_x = delta_x
            previous_delta_y = delta_y

        previous_x = x_value
        previous_y = y_value

    return quantized


def round_coordinate(value):
    return math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5)


if __name__ == "__main__":
    generate_example_files()
