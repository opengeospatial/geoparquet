"""
Test cases for validating the example.parquet file.

Run tests with `pytest test_example.py`
"""

import json
import pathlib

import pyarrow.parquet as pq
import pytest
from jsonschema.validators import Draft7Validator
from referencing import Registry, Resource

from test_json_schema import fetch_remote_schema, SCHEMA, PROJJSON_URI

HERE = pathlib.Path(__file__).parent
EXAMPLE_PARQUET = HERE / ".." / "examples" / "example.parquet"

# Pre-fetch the projjson schema and create a registry with it
projjson_schema = fetch_remote_schema(PROJJSON_URI)
REGISTRY = Registry().with_resources(
    [(PROJJSON_URI, Resource.from_contents(projjson_schema))]
)


def get_geo_metadata(parquet_file: pq.ParquetFile) -> dict:
    """Read geo metadata from a ParquetFile."""
    metadata = parquet_file.metadata.metadata
    geo_bytes = metadata.get(b"geo")
    if geo_bytes is None:
        raise ValueError("No 'geo' metadata found in parquet file")
    return json.loads(geo_bytes)


class TestExampleParquet:
    """Tests for the example.parquet file

    This is a test to make sure the example file we generated in generate_example.py
    matches the expectations of what we thought we wrote.
    """

    @pytest.fixture(scope="class")
    def parquet_file(self):
        return pq.ParquetFile(EXAMPLE_PARQUET)

    @pytest.fixture(scope="class")
    def geo_metadata(self, parquet_file):
        return get_geo_metadata(parquet_file)

    def test_file_exists(self):
        assert EXAMPLE_PARQUET.exists()

    def test_has_geo_metadata(self, geo_metadata):
        assert geo_metadata is not None

    def test_schema_valid(self, geo_metadata):
        errors = list(
            Draft7Validator(SCHEMA, registry=REGISTRY).iter_errors(geo_metadata)
        )
        assert errors == []

    def test_has_version(self, geo_metadata):
        assert "version" in geo_metadata
        # Version should match the const in schema.json
        expected_version = SCHEMA["properties"]["version"]["const"]
        assert geo_metadata["version"] == expected_version, (
            f"Version mismatch: {geo_metadata['version']} != {expected_version}"
        )

    def test_has_primary_column(self, geo_metadata):
        assert "primary_column" in geo_metadata
        assert geo_metadata["primary_column"] == "geometry"

    def test_has_columns(self, geo_metadata):
        assert "columns" in geo_metadata
        primary = geo_metadata["primary_column"]
        assert primary in geo_metadata["columns"], (
            f"Primary column '{primary}' not found in columns"
        )

    def test_geometry_column_has_encoding(self, geo_metadata):
        geom_col = geo_metadata["columns"]["geometry"]
        assert "encoding" in geom_col
        assert geom_col["encoding"] == "WKB"

    def test_geometry_column_has_geometry_types(self, geo_metadata):
        geom_col = geo_metadata["columns"]["geometry"]
        assert geom_col["geometry_types"] == ["Polygon", "MultiPolygon"]

    def test_can_read_parquet_file(self):
        table = pq.read_table(EXAMPLE_PARQUET)
        assert table is not None
        assert len(table) == 5

    def test_geometry_column_in_parquet(self):
        table = pq.read_table(EXAMPLE_PARQUET)
        assert "geometry" in table.column_names


class TestParquetSchema:
    """Tests for Parquet schema and statistics using ParquetFile

    This is designed as a test to make sure the example file has the corect Parquet
    schema that matches the expectation of what we thought we wrote.
    """

    @pytest.fixture(scope="class")
    def parquet_file(self):
        return pq.ParquetFile(EXAMPLE_PARQUET)

    @pytest.fixture(scope="class")
    def geo_metadata(self, parquet_file):
        return get_geo_metadata(parquet_file)

    def test_geometry_has_geometry_logical_type(self, parquet_file):
        # Find geometry column index
        column_names = parquet_file.schema.names
        assert "geometry" in column_names, "geometry column not found in schema"
        geom_idx = column_names.index("geometry")

        # Check logical type
        geom_col_schema = parquet_file.schema.column(geom_idx)
        logical_type = geom_col_schema.logical_type

        assert logical_type is not None, "geometry column has no logical type"
        logical_type_json = json.loads(logical_type.to_json())
        assert logical_type_json["Type"] == "Geometry"

    def test_has_one_row_group(self, parquet_file):
        assert parquet_file.metadata.num_row_groups == 1

    def test_geometry_has_geo_statistics(self, parquet_file):
        column_names = parquet_file.schema.names
        geom_idx = column_names.index("geometry")

        rg = parquet_file.metadata.row_group(0)
        geom_col = rg.column(geom_idx)

        assert geom_col.is_geo_stats_set, "Geometry column has no geo statistics"
        assert geom_col.geo_statistics is not None

    def test_geo_statistics_match_metadata_bbox(self, parquet_file, geo_metadata):
        column_names = parquet_file.schema.names
        geom_idx = column_names.index("geometry")

        rg = parquet_file.metadata.row_group(0)
        geom_col = rg.column(geom_idx)
        geo_stats = geom_col.geo_statistics

        # Get bbox from metadata (xmin, ymin, xmax, ymax for 2D)
        metadata_bbox = geo_metadata["columns"]["geometry"]["bbox"]
        assert len(metadata_bbox) == 4, "Expected 2D bbox with 4 elements"

        xmin, ymin, xmax, ymax = metadata_bbox

        # Compare with geo statistics
        assert geo_stats.xmin == pytest.approx(xmin), (
            f"xmin mismatch: {geo_stats.xmin} != {xmin}"
        )
        assert geo_stats.ymin == pytest.approx(ymin), (
            f"ymin mismatch: {geo_stats.ymin} != {ymin}"
        )
        assert geo_stats.xmax == pytest.approx(xmax), (
            f"xmax mismatch: {geo_stats.xmax} != {xmax}"
        )
        assert geo_stats.ymax == pytest.approx(ymax), (
            f"ymax mismatch: {geo_stats.ymax} != {ymax}"
        )

    def test_geo_statistics_geometry_types(self, parquet_file):
        column_names = parquet_file.schema.names
        geom_idx = column_names.index("geometry")

        rg = parquet_file.metadata.row_group(0)
        geom_col = rg.column(geom_idx)
        geo_stats = geom_col.geo_statistics

        # Geometry type codes: 3 = Polygon, 6 = MultiPolygon (WKB type codes)
        assert geo_stats.geospatial_types == [3, 6]
