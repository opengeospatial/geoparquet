"""
Test cases (valid and invalid ones) to test the JSON schema.

Run tests with `pytest test_json_schema.py`

Test cases are generated on the fly, but if you want to have them written
as .json files to inspect, run `python test_json_schema.py`

"""

import copy
import json
import pathlib
import urllib.request

import pytest
from jsonschema.validators import Draft7Validator
from referencing import Registry, Resource

HERE = pathlib.Path(__file__).parent
SCHEMA_SRC = HERE / ".." / "format-specs" / "schema.json"
SCHEMA = json.loads(SCHEMA_SRC.read_text())


def fetch_remote_schema(uri: str) -> dict:
    """Fetch a remote schema and return its contents."""
    req = urllib.request.Request(uri, headers={"User-Agent": "geoparquet-tests"})
    with urllib.request.urlopen(req) as response:
        return json.load(response)


# Pre-fetch the projjson schema and create a registry with it
PROJJSON_URI = "https://proj.org/schemas/v0.7/projjson.schema.json"
projjson_schema = fetch_remote_schema(PROJJSON_URI)
REGISTRY = Registry().with_resources(
    [(PROJJSON_URI, Resource.from_contents(projjson_schema))]
)


# # Define test cases

valid_cases = {}
invalid_cases = {}


def get_version() -> str:
    """Read the version const from the schema.json file"""
    with open(HERE / "../format-specs/schema.json") as f:
        spec_schema = json.load(f)
        return spec_schema["properties"]["version"]["const"]


metadata_template = {
    "version": get_version(),
    "primary_column": "geometry",
    "columns": {"geometry": {"encoding": "WKB", "geometry_types": []}},
}


# Minimum required metadata

metadata = copy.deepcopy(metadata_template)
valid_cases["minimal"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata.pop("version")
invalid_cases["missing_version"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["version"] = "bad-version"
invalid_cases["bad_version"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata.pop("primary_column")
invalid_cases["missing_primary_column"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata.pop("columns")
invalid_cases["missing_columns"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"] = {}
invalid_cases["missing_columns_entry"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"].pop("encoding")
invalid_cases["missing_geometry_encoding"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"].pop("geometry_types")
invalid_cases["missing_geometry_type"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["custom_key"] = "value"
valid_cases["custom_key"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["custom_key"] = "value"
valid_cases["custom_key_column"] = metadata


# Geometry columns

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["other_geom"] = copy.deepcopy(metadata["columns"]["geometry"])
valid_cases["geometry_columns_multiple"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["invalid_column_object"] = "foo"
invalid_cases["geometry_columns_invalid_object"] = metadata


# Geometry column name

metadata = copy.deepcopy(metadata_template)
metadata["primary_column"] = "geom"
metadata["columns"]["geom"] = metadata["columns"].pop("geometry")
valid_cases["geometry_column_name"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["primary_column"] = ""
invalid_cases["geometry_column_name_primary_empty"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"][""] = metadata["columns"]["geometry"]
invalid_cases["geometry_column_name_empty"] = metadata


# Encoding

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["encoding"] = "WKT"
invalid_cases["encoding"] = metadata


# Geometry type - non-empty list

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = ["Point"]
valid_cases["geometry_type_list"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = "Point"
invalid_cases["geometry_type_string"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = ["Curve"]
invalid_cases["geometry_type_nonexistent"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = ["Point", "Point"]
invalid_cases["geometry_type_uniqueness"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = ["PointZ"]
invalid_cases["geometry_type_z_missing_space"] = metadata


# CRS - explicit null

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["crs"] = None
valid_cases["crs_null"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["crs"] = "EPSG:4326"
invalid_cases["crs_string"] = metadata


# Bbox

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["bbox"] = [0, 0, 0, 0]
valid_cases["bbox_4_element"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["bbox"] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
valid_cases["bbox_6_element"] = metadata

for n in [3, 5, 7]:
    metadata = copy.deepcopy(metadata_template)
    metadata["columns"]["geometry"]["bbox"] = [0] * n
    invalid_cases[f"bbox_{str(n)}_element"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["bbox"] = ["0", "0", "0", "0"]
invalid_cases["bbox_invalid_type"] = metadata


# Orientation

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["orientation"] = "counterclockwise"
valid_cases["orientation"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["orientation"] = "clockwise"
invalid_cases["orientation"] = metadata

# Edges

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["edges"] = "planar"
valid_cases["edges_planar"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["edges"] = "spherical"
valid_cases["edges_spherical"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["edges"] = "vincenty"
valid_cases["edges_vincenty"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["edges"] = "thomas"
valid_cases["edges_thomas"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["edges"] = "andoyer"
valid_cases["edges_andoyer"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["edges"] = "karney"
valid_cases["edges_karney"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["edges"] = "ellipsoid"
invalid_cases["edges_ellipsoid"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["edges"] = "SPHERICAL"
invalid_cases["edges_uppercase"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["edges"] = "unknown"
invalid_cases["edges_unknown"] = metadata

# Epoch

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["epoch"] = 2015.1
valid_cases["epoch"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["epoch"] = "2015.1"
invalid_cases["epoch_string"] = metadata

# Geometry type with M dimension

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = ["Point M"]
valid_cases["geometry_type_m"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = ["Point ZM"]
valid_cases["geometry_type_zm"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = ["Polygon M", "MultiPolygon ZM"]
valid_cases["geometry_type_m_zm_mixed"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = ["PointM"]
invalid_cases["geometry_type_m_missing_space"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = ["PointZM"]
invalid_cases["geometry_type_zm_missing_space"] = metadata

# Bbox with 8 elements (XYZM)

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["bbox"] = [0, 0, 0, 0, 0, 0, 0, 0]
valid_cases["bbox_8_element"] = metadata

# Display optimization

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = ["Point"]
metadata["display"] = {
    "geometry_column": "geometry",
    "ordering": {
        "type": "z",
        "extent": [-180, -90, 180, 90],
        "column": ["geodisplay", "ordering_code"],
        "bit_width": 16,
    },
}
valid_cases["display_z"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = ["Point ZM"]
metadata["display"] = {
    "geometry_column": "geometry",
    "ordering": {
        "type": "z",
        "extent": [-180, -90, 180, 90],
        "column": ["geodisplay", "ordering_code"],
        "bit_width": 32,
    },
}
valid_cases["display_z_zm"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_types"] = ["Polygon"]
metadata["display"] = {
    "geometry_column": "geometry",
    "ordering": {
        "type": "xz",
        "extent": [-180, -90, 180, 90],
        "column": ["geodisplay", "ordering_code"],
        "max_level": 20,
    },
    "lods": {
        "encoding": "pbf",
        "orientation": "clockwise",
        "levels": [
            {
                "column": ["geodisplay", "level_0"],
                "scale": 1000000,
                "transform": {
                    "scale": [0.703125, 0.703125, 1, 1],
                    "translate": [0, 0, 0, 0],
                },
            }
        ],
    },
}
valid_cases["display_xz"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["levels"].append(
    {
        "column": ["geodisplay", "level_1"],
        "scale": 500000,
        "transform": {
            "scale": [0.3515625, 0.3515625, 1, 1],
            "translate": [0, 0, 0, 0],
        },
    }
)
valid_cases["display_xz_multiple_levels"] = metadata

metadata = copy.deepcopy(valid_cases["display_z"])
metadata["display"].pop("geometry_column")
invalid_cases["display_missing_geometry_column"] = metadata

metadata = copy.deepcopy(valid_cases["display_z"])
metadata["display"]["ordering"]["bit_width"] = 0
invalid_cases["display_z_bit_width_zero"] = metadata

metadata = copy.deepcopy(valid_cases["display_z"])
metadata["display"]["ordering"]["bit_width"] = 33
invalid_cases["display_z_bit_width_above_maximum"] = metadata

metadata = copy.deepcopy(valid_cases["display_z"])
metadata["display"]["ordering"]["extent"] = [-180, -90, 180]
invalid_cases["display_ordering_extent_too_short"] = metadata

metadata = copy.deepcopy(valid_cases["display_z"])
metadata["display"]["ordering"]["extent"] = [-180, -90, 180, 90, 0]
invalid_cases["display_ordering_extent_too_long"] = metadata

metadata = copy.deepcopy(valid_cases["display_z"])
metadata["display"]["ordering"]["column"] = []
invalid_cases["display_empty_column_path"] = metadata

metadata = copy.deepcopy(valid_cases["display_z"])
metadata["display"]["ordering"]["column"] = ["display", "ordering_code"]
invalid_cases["display_wrong_parent_column"] = metadata

metadata = copy.deepcopy(valid_cases["display_z"])
metadata["display"]["ordering"]["column"] = [
    "geodisplay",
    "nested",
    "ordering_code",
]
invalid_cases["display_nested_column_path"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"].pop("lods")
invalid_cases["display_xz_without_lods"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["ordering"]["max_level"] = 19
invalid_cases["display_xz_max_level"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["levels"] = []
invalid_cases["display_xz_missing_levels"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"].pop("encoding")
invalid_cases["display_xz_missing_encoding"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"].pop("orientation")
invalid_cases["display_xz_missing_orientation"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["orientation"] = "counterclockwise"
invalid_cases["display_xz_invalid_orientation"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["levels"][0]["scale"] = 0
invalid_cases["display_xz_scale_zero"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["levels"][0]["scale"] = -1
invalid_cases["display_xz_scale_negative"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["encoding"] = "delta"
invalid_cases["display_xz_invalid_encoding"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["levels"].append(
    copy.deepcopy(metadata["display"]["lods"]["levels"][0])
)
invalid_cases["display_xz_duplicate_level"] = metadata

for field in ("column", "scale", "transform"):
    metadata = copy.deepcopy(valid_cases["display_xz"])
    metadata["display"]["lods"]["levels"][0].pop(field)
    invalid_cases[f"display_xz_level_missing_{field}"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["levels"][0]["column"] = ["lods", "level_0"]
invalid_cases["display_xz_invalid_level_column"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["levels"][0]["transform"]["scale"] = [1, 1, 1]
invalid_cases["display_xz_transform_width"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["levels"][0]["transform"]["scale"][0] = 0
invalid_cases["display_xz_transform_scale_zero"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["levels"][0]["transform"]["scale"][0] = -1
invalid_cases["display_xz_transform_scale_negative"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["levels"][0]["transform"]["translate"] = [0, 0, 0]
invalid_cases["display_xz_transform_translate_width"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["unexpected"] = True
invalid_cases["display_unexpected_property"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["ordering"]["unexpected"] = True
invalid_cases["display_ordering_unexpected_property"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["unexpected"] = True
invalid_cases["display_xz_lods_unexpected_property"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["levels"][0]["unexpected"] = True
invalid_cases["display_xz_level_unexpected_property"] = metadata

metadata = copy.deepcopy(valid_cases["display_xz"])
metadata["display"]["lods"]["levels"][0]["transform"]["unexpected"] = True
invalid_cases["display_xz_transform_unexpected_property"] = metadata

metadata = copy.deepcopy(valid_cases["display_z"])
metadata["display"]["lods"] = copy.deepcopy(valid_cases["display_xz"]["display"]["lods"])
invalid_cases["display_z_with_lods"] = metadata


# # Tests


@pytest.mark.parametrize("metadata", valid_cases.values(), ids=valid_cases.keys())
def test_valid_schema(request, metadata):
    errors = Draft7Validator(SCHEMA, registry=REGISTRY).iter_errors(metadata)

    msgs = []
    valid = True
    for error in errors:
        valid = False
        msg = f"- {error.json_path}: {error.message}"
        if "description" in error.schema:
            msg += f". {error.schema['description']}"
        msgs.append(msg)

    if not valid:
        raise AssertionError(
            f"Error while validating '{request.node.callspec.id}':\n"
            + json.dumps({"geo": metadata}, indent=2, sort_keys=True)
            + "\n\nErrors:\n"
            + "\n".join(msgs)
        )


@pytest.mark.parametrize("metadata", invalid_cases.values(), ids=invalid_cases.keys())
def test_invalid_schema(request, metadata):
    errors = Draft7Validator(SCHEMA, registry=REGISTRY).iter_errors(metadata)

    if not len(list(errors)):
        raise AssertionError(
            "This is an invalid GeoParquet file, but no validation error "
            f"occurred for '{request.node.callspec.id}':\n"
            + json.dumps({"geo": metadata}, indent=2, sort_keys=True)
        )


if __name__ == "__main__":
    (HERE / "data").mkdir(exist_ok=True)

    def write_metadata_json(metadata, name):
        with open(HERE / "data" / ("metadata_" + name + ".json"), "w") as f:
            json.dump({"geo": metadata}, f, indent=2, sort_keys=True)

    for case, metadata in valid_cases.items():
        write_metadata_json(metadata, "valid_" + case)

    for case, metadata in invalid_cases.items():
        write_metadata_json(metadata, "invalid_" + case)
