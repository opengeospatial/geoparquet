# Helper scripts

## Usage

The scripts in this directory use [Poetry](https://github.com/python-poetry/poetry) for describing dependencies and keeping a consistent lockfile. This lockfile is useful because it ensures every contributor is able to use the exact same dependencies.

To install Poetry, follow the Poetry [installation guide](https://python-poetry.org/docs/#installation).

To install from the lockfile:

```
poetry install
```

To update the lockfile (such as when you add a new dependency):

```
poetry update
```

To run a script, prefix it with `poetry run`. For example:

```
poetry run python generate_example.py
```

Using `poetry run` ensures that you're running the python script using _this_ local environment, not your global environment.

### example.parquet

The `example.parquet` file in the `examples` directory is generated with the `generate_example.py` script.  This script needs to be updated and run any time there are changes to the "geo" file metadata or to the version constant in `schema.json`.

To update the `../examples/example.parquet` file, run this from the `scripts` directory:

```
poetry run python generate_example.py
```

### nz-building-outlines to Parquet

```bash
poetry run python write_nz_building_outline.py \
    --input nz-building-outlines.gpkg \
    --output nz-building-outlines.parquet \
    --compression SNAPPY
```

#### Recompile pygeos

Poetry doesn't currently have a way to force installing a package from source.
To make the script run faster, you can reinstall pygeos manually in the
virtualenv:

```
poetry run pip install -U --force-reinstall pygeos --no-binary pygeos
```
