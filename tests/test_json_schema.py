import json
import pathlib

from jsonschema.validators import Draft7Validator

import pytest


HERE = pathlib.Path(__file__).parent
SCHEMA_SRC = HERE / ".." / "format-specs" / "schema.json"
SCHEMA = json.loads(SCHEMA_SRC.read_text())


@pytest.mark.parametrize(
    "path", list((HERE / "valid").iterdir()), ids=lambda path: path.name
)
def test_valid_schema(path):

    with open(path, "r") as f:
        metadata = json.load(f)["geo"]

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
        raise AssertionError(f"Error while validation {path.name}:\n" + "\n".join(msgs))


@pytest.mark.parametrize(
    "path", list((HERE / "invalid").iterdir()), ids=lambda path: path.name
)
def test_invalid_schema(request, path):
    if "missing_columns_entry" in path.name or "geometry_column_name_empty" in path.name:
        request.node.add_marker(
                pytest.mark.xfail(reason="Not yet working", strict=True)
            )

    with open(path, "r") as f:
        metadata = json.load(f)["geo"]

    errors = Draft7Validator(SCHEMA).iter_errors(metadata)

    if not len(list(errors)):
        raise AssertionError(
            "This is an invalid GeoParquet file, but no validation error "
            f"occurred for {path.name}."
        )
