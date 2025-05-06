# Helper scripts

## Usage

The scripts in this directory use [uv](https://docs.astral.sh/uv/) for describing dependencies and keeping a consistent lockfile. This lockfile is useful because it ensures every contributor is able to use the exact same dependencies.

To install uv, follow the [installation guide](https://docs.astral.sh/uv/getting-started/installation/).

To install from the lockfile:

```
uv sync
```

To run a script, prefix it with `uv run`. For example:

```
uv run python generate_example.py
```

### Tests

To run the tests, change into the `scripts` directory and run the following:

```
uv run pytest test_json_schema.py -v
```

### example.parquet

The `example.parquet` file in the `examples` directory is generated with the `generate_example.py` script.  This script needs to be updated and run any time there are changes to the "geo" file metadata or to the version constant in `schema.json`.

To update the `../examples/example.parquet` file, run this from the `scripts` directory:

```
uv run python generate_example.py
```

### nz-building-outlines to Parquet

```bash
uv run python write_nz_building_outline.py \
    --input nz-building-outlines.gpkg \
    --output nz-building-outlines.parquet \
    --compression SNAPPY
```
