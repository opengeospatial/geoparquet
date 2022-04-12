#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from pprint import pprint
from urllib.parse import urlparse

import pyarrow.parquet as pq
from fsspec import AbstractFileSystem
from fsspec.implementations.local import LocalFileSystem
from jsonschema.validators import Draft7Validator
from pyarrow.fs import FSSpecHandler, PyFileSystem


class MetadataError(ValueError):
    pass


def choose_fsspec_fs(url_or_path: str) -> AbstractFileSystem:
    """Choose fsspec filesystem by sniffing input url"""
    parsed = urlparse(url_or_path)

    if parsed.scheme.startswith("http"):
        from fsspec.implementations.http import HTTPFileSystem

        return HTTPFileSystem()

    if parsed.scheme == "s3":
        from s3fs import S3FileSystem

        return S3FileSystem()

    if parsed.scheme == "gs":
        from gcsfs import GCSFileSystem

        return GCSFileSystem()

    # TODO: Add Azure
    return LocalFileSystem()


def load_parquet_schema(url_or_path: str) -> pq.ParquetSchema:
    """Load schema from local or remote Parquet file"""
    fsspec_fs = choose_fsspec_fs(url_or_path)
    pyarrow_fs = PyFileSystem(FSSpecHandler(fsspec_fs))
    return pq.read_schema(pyarrow_fs.open_input_file(url_or_path))


def validate_geoparquet(input_file):
    here = Path(sys.path[0])
    schema_path = here / "schema.json"
    with open(schema_path) as f:
        schema = json.load(f)

    parquet_schema = load_parquet_schema(input_file)
    if b"geo" not in parquet_schema.metadata:
        raise MetadataError("Parquet file schema does not have 'geo' key")

    metadata = json.loads(parquet_schema.metadata[b"geo"])
    print("Metadata loaded from file:")
    pprint(metadata)

    errors = Draft7Validator(schema).iter_errors(metadata)

    valid = True
    print("Validating file...")

    for error in errors:
        valid = False
        print(f"- [ERROR] {error.json_path}: {error.message}")
        if "description" in error.schema:
            print(f"          INFO: {error.schema['description']}")

    # Extra errors
    if metadata["primary_column"] not in metadata["columns"]:
        valid = False
        print("- [ERROR] $.primary_column: must be in $.columns")

    if valid:
        print("This is a valid GeoParquet file.")
    else:
        print("This is an invalid GeoParquet file.")
        exit(1)


if __name__ == "__main__":
    validate_geoparquet(sys.argv[1])
