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

Validate a local file:

```
geoparquet_validator ../../examples/example.parquet
```

Validate a remote file:

```
geoparquet_validator https://storage.googleapis.com/open-geodata/linz-examples/nz-buildings-outlines.parquet
```
