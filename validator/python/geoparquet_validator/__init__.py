import json
import click
import pyarrow.parquet as pq

from urllib.parse import urlparse
from pathlib import Path, PurePath
from jsonschema.validators import Draft7Validator
from pyarrow.fs import PyFileSystem, FSSpecHandler
from fsspec.implementations.http import HTTPFileSystem


def is_url(text):
    result = urlparse(text)
    return all([result.scheme, result.netloc])


def log(text, color="white"):
    click.echo(click.style(text, fg=color))


@click.command()
@click.argument("input_file")
def main(input_file):
    valid = True
    log("Validating file...")

    here = Path(PurePath(__file__).parent)
    schema_path = here / "schema.json"
    with open(schema_path) as f:
        schema = json.load(f)

    if is_url(input_file):
        pa_fs = PyFileSystem(FSSpecHandler(HTTPFileSystem()))
        metadata = pq.read_schema(pa_fs.open_input_file(input_file)).metadata
    else:
        metadata = pq.read_schema(input_file).metadata

    if b"geo" not in metadata:
        log("Metadata has no 'geo' field", "red")
        return

    geo_metadata = json.loads(metadata[b"geo"])

    errors = Draft7Validator(schema).iter_errors(geo_metadata)

    for error in errors:
        valid = False
        log(f"  - {error.json_path}: {error.message}", "yellow")
        if "description" in error.schema:
            log(f"    \"{error.schema['description']}\"", "yellow")

    # Extra errors
    if (geo_metadata["primary_column"] not in geo_metadata["columns"]):
        valid = False
        log("- $.primary_column: must be in $.columns", "yellow")

    if valid:
        log("This is a valid GeoParquet file.\n", "green")
    else:
        log("This is an invalid GeoParquet file.\n", "red")


if __name__ == "__main__":
    main()
