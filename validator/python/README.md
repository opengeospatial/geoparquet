# GeoParquet validator - Python

Command-line tool to validate a GeoParquet file. Written in Python. Using [JSON Schema](https://json-schema.org/).

## Installation

```
pip install wheel
pip install .
```

**Update**

```
pip install -U .
```

**Development**

```
pip install -e .
```

**Uninstall**

```
pip uninstall geoparquet_validator
```

## Usage

```
geoparquet_validator ../../examples/example.parquet
geoparquet_validator https://storage.googleapis.com/open-geodata/linz-examples/nz-buildings-outlines.parquet
```

The validator also supports remote files.

- `http://` or `https://`: no further configuration is needed.
- `s3://`: `s3fs` needs to be installed (run `pip install s3fs`) and you may need to set environment variables. Refer [here](https://s3fs.readthedocs.io/en/latest/#credentials) for how to define credentials.
- `gs://`: `gcsfs` needs to be installed (run `pip install gcsfs`). By default, `gcsfs` will attempt to use your default gcloud credentials or, attempt to get credentials from the google metadata service, or fall back to anonymous access.
