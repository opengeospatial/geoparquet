# Helper scripts

## Usage

The scripts in this directory use [Poetry](https://github.com/python-poetry/poetry) for describing dependencies and keeping a consistent lockfile. This lockfile is useful because it ensures every contributor is able to use the exact same dependencies.

To install Poetry, follow the Poetry [installation guide](https://python-poetry.org/docs/#installation).

To install from the lockfile, run `poetry install`. To update the lockfile (such as when you add a new dependency) run `poetry update`.

To run a script, prefix it with `poetry run`. For example:

```
poetry run python update_example_schemas.py
```

Using `poetry run` ensures that you're running the python script using _this_ local environment, not your global environment.

### nz-building-outlines to Parquet

```bash
poetry run python write_nz_building_outline.py \
    -i nz-building-outlines.gpkg \
    -o nz-building-outlines.parquet \
    --compression SNAPPY
```

#### Recompile pygeos

Poetry doesn't currently have a way to force installing a package from source.
To make the script run faster, you can reinstall pygeos manually in the
virtualenv:

```
poetry run pip install -U --force-reinstall pygeos --no-binary pygeos
```
