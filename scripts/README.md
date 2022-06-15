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
poetry run python update_example_schemas.py
```

Using `poetry run` ensures that you're running the python script using _this_ local environment, not your global environment.

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

### BigQuery

Convert a SQL query to parquet:

```bash
poetry run python bigquery_to_parquet.py \
    --input-query "SELECT * FROM carto-do-public-data.carto.geography_usa_blockgroup_2019" \
    --primary-column geom \
    --output geography_usa_blockgroup_2019
```

Upload a parquet file or folder to BigQuery:
```bash
poetry run python parquet_to_bigquery.py \
    --input geography_usa_blockgroup_2019 \
    --output "cartodb-gcp-backend-data-team.alasarr.geography_usa_blockgroup_2019"
```

Instead of using folders, you can also work with a single file, but it might hit [bigquery limits](https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-parquet) when you upload it to BigQuery. For large parquet files you might get `UDF out of memory` errors.

Convert a SQL query to single parquet file:

```bash
poetry run python bigquery_to_parquet.py \
    --input-query "SELECT * FROM carto-do-public-data.carto.geography_usa_blockgroup_2019" \
    --primary-column geom \
    --mode file \
    --output geography_usa_blockgroup_2019.parquet
```
