"""
Test cases (valid and invalid ones) to test the JSON schema.

Run tests with `pytest test_json_schema.py`

Test cases are generated on the fly, but if you want to have them written
as .json files to inspect, run `python test_json_schema.py`

"""
import copy
import json
import pathlib

from jsonschema.validators import Draft7Validator

import pytest


HERE = pathlib.Path(__file__).parent
SCHEMA_SRC = HERE / ".." / "format-specs" / "schema.json"
SCHEMA = json.loads(SCHEMA_SRC.read_text())


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
    "columns": {
        "geometry": {
            "encoding": "WKB",
            "geometry_types": [],
            "covering": {
                "bbox": {
                    "xmin": "bbox.xmin",
                    "ymin": "bbox.ymin",
                    "xmax": "bbox.xmax",
                    "ymax": "bbox.ymax",
                },
            },
        },
    },
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
metadata["columns"]["geometry"]["edges"] = "ellipsoid"
invalid_cases["edges"] = metadata

# Epoch

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["epoch"] = 2015.1
valid_cases["epoch"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["epoch"] = "2015.1"
invalid_cases["epoch_string"] = metadata

# Geometry Bbox

# Allow "any_column.xmin" etc.
metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["covering"]["bbox"] = {
    "xmin": "any_column.xmin",
    "ymin": "any_column.ymin",
    "xmax": "any_column.xmax",
    "ymax": "any_column.ymax",
}
valid_cases["valid_but_not_bbox_struct_name"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["covering"].pop("bbox")
invalid_cases["empty_geometry_bbox"] = metadata


metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["covering"]["bbox"] = {}
invalid_cases["empty_geometry_bbox_missing_fields"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["covering"]["bbox"].pop("xmin")
invalid_cases["covering_bbox_missing_xmin"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["covering"]["bbox"].pop("ymin")
invalid_cases["covering_bbox_missing_ymin"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["covering"]["bbox"].pop("xmax")
invalid_cases["covering_bbox_missing_xmax"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["covering"]["bbox"].pop("ymax")
invalid_cases["covering_bbox_missing_ymax"] = metadata

## Invalid bbox xmin/xmax/ymin/ymax values
metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["covering"]["bbox"]["xmin"] = "not_bbox_dot_xmin"
invalid_cases["covering_bbox_invalid_xmin"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["covering"]["bbox"]["xmax"] = "not_bbox_dot_xmax"
invalid_cases["covering_bbox_invalid_xmax"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["covering"]["bbox"]["ymin"] = "not_bbox_dot_ymin"
invalid_cases["covering_bbox_invalid_ymin"] = metadata

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["covering"]["bbox"]["ymax"] = "not_bbox_dot_ymax"
invalid_cases["covering_bbox_invalid_ymax"] = metadata

# # Tests

@pytest.mark.parametrize(
    "metadata", valid_cases.values(), ids=valid_cases.keys()
)
def test_valid_schema(request, metadata):
    errors = Draft7Validator(SCHEMA).iter_errors(metadata)

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
            + "\n\nErrors:\n" + "\n".join(msgs)
        )


@pytest.mark.parametrize(
    "metadata", invalid_cases.values(), ids=invalid_cases.keys()
)
def test_invalid_schema(request, metadata):
    errors = Draft7Validator(SCHEMA).iter_errors(metadata)

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
