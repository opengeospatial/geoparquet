#!/usr/bin/python3

import sys
import json
import pyarrow.parquet as pq

from pathlib import Path
from jsonschema.validators import Draft7Validator


def validate_geoparquet(input_file):
    here = Path(sys.path[0])
    schema_path = here / "schema.json"
    with open(schema_path) as f:
        schema = json.load(f)

    metadata = json.loads(pq.read_schema(input_file).metadata[b"geo"])

    errors = Draft7Validator(schema).iter_errors(metadata)

    valid = True
    print("Validating file...")

    for error in errors:
        valid = False
        print(f"- [ERROR] {error.json_path}: {error.message}")
        if "description" in error.schema:
            print(f"          INFO: {error.schema['description']}")

    # Extra errors
    if (metadata["primary_column"] not in metadata["columns"]):
        valid = False
        print("- [ERROR] $.primary_column: must be in $.columns")

    if valid:
        print("This is a valid GeoParquet file.")
    else:
        print("This is an invalid GeoParquet file.")


if __name__ == '__main__':
    validate_geoparquet(sys.argv[1])
