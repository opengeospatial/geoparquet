import json
import click
import pyarrow.parquet as pq

from pprint import pprint
from urllib.parse import urlparse
from pathlib import Path, PurePath
from jsonschema.validators import Draft7Validator
from fsspec import AbstractFileSystem
from fsspec.implementations.http import HTTPFileSystem
from fsspec.implementations.local import LocalFileSystem
from pyarrow.fs import FSSpecHandler, PyFileSystem


class MetadataError(ValueError):
    pass


def choose_fsspec_fs(url_or_path: str) -> AbstractFileSystem:
    """Choose fsspec filesystem by sniffing input url"""
    parsed = urlparse(url_or_path)

    if parsed.scheme.startswith("http"):
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


def log(text: str, color="white"):
    click.echo(click.style(text, fg=color))


@click.command()
@click.argument("input_file")
def main(input_file):
    here = Path(PurePath(__file__).parent)
    schema_path = here / "schema.json"
    with open(schema_path) as f:
        schema = json.load(f)

    parquet_schema = load_parquet_schema(input_file)

    if b"geo" not in parquet_schema.metadata:
        raise MetadataError("Parquet file schema does not have 'geo' key")

    metadata = json.loads(parquet_schema.metadata[b"geo"])
    log("Metadata loaded from file:")
    pprint(metadata)

    valid = True
    log("Validating file...")

    errors = Draft7Validator(schema).iter_errors(metadata)

    for error in errors:
        valid = False
        log(f"  - {error.json_path}: {error.message}", "yellow")
        if "description" in error.schema:
            log(f"    \"{error.schema['description']}\"", "yellow")

    # Extra errors
    if (metadata["primary_column"] not in metadata["columns"]):
        valid = False
        log("- $.primary_column: must be in $.columns", "yellow")

    if valid:
        log("This is a valid GeoParquet file.\n", "green")
    else:
        log("This is an invalid GeoParquet file.\n", "red")
        exit(1)


if __name__ == "__main__":
    main()
