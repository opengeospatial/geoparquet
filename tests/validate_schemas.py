import json
import pathlib

from jsonschema.validators import Draft7Validator


HERE = pathlib.Path(__file__).parent
SCHEMA_SRC = HERE / ".." / "format-specs" / "schema.json"
SCHEMA = json.loads(SCHEMA_SRC.read_text())

# use pytest?

def test_valid_schema(path):

    with open(path, "r") as f:
        metadata = json.load(f)["geo"]

    print(f"Validating {path}")

    errors = Draft7Validator(SCHEMA).iter_errors(metadata)

    valid = True
    for error in errors:
        valid = False
        print(f"  - {error.json_path}: {error.message}", "warning")
        if "description" in error.schema:
            print(f"    \"{error.schema['description']}\"", "warning")

    if valid:
        print("This is a valid GeoParquet file.\n", "success")
    else:
        print("This is an invalid GeoParquet file.\n", "error")
        exit(1)


def test_invalid_schema(path):

    with open(path, "r") as f:
        metadata = json.load(f)["geo"]

    print(f"Validating {path}")

    errors = Draft7Validator(SCHEMA).iter_errors(metadata)

    if len(list(errors)):
        print("Validation error occurred.\n", "success")
    else:
        print("This is an invalid GeoParquet file, but no validation error occurred.\n", "error")
        exit(1)


if __name__ == "__main__":
    for path in (HERE / "valid").iterdir():
        test_valid_schema(path)

    for path in (HERE / "invalid").iterdir():
        if "missing_columns_entry" in path.name:
            print(f"Skipping {path}")
            continue
        test_invalid_schema(path)
