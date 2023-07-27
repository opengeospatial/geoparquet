import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import click
import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import shapely
from numpy.typing import NDArray
from shapely import GeometryType

AVAILABLE_COMPRESSIONS = ["NONE", "SNAPPY", "GZIP", "BROTLI", "LZ4", "ZSTD"]

ShapelyGeometryArray = NDArray[np.object_]


class PathType(click.Path):
    """A Click path argument that returns a pathlib Path, not a string"""

    def convert(self, value, param, ctx):
        return Path(super().convert(value, param, ctx))


def parse_to_shapely(df: gpd.GeoDataFrame) -> Dict[str, ShapelyGeometryArray]:
    """Parse to shapely geometry array

    This is split out from _create_metadata so that we don't have to create the pygeos
    array twice: once for converting to wkb and another time for metadata handling.
    """
    geometry_columns: Dict[str, ShapelyGeometryArray] = {}
    for col in df.columns[df.dtypes == "geometry"]:
        geometry_columns[col] = df[col].values

    return geometry_columns


def _create_metadata(
    df: gpd.GeoDataFrame, geometry_columns: Dict[str, ShapelyGeometryArray]
) -> Dict[str, Any]:
    """Create and encode geo metadata dict.

    Parameters
    ----------
    df : GeoDataFrame

    Returns
    -------
    dict
    """

    # Construct metadata for each geometry
    column_metadata = {}
    for col, geometry_array in geometry_columns.items():
        geometry_types = get_geometry_types(geometry_array)
        bbox = list(shapely.total_bounds(geometry_array))

        series = df[col]
        column_metadata[col] = {
            "encoding": "WKB",
            "geometry_types": geometry_types,
            "crs": series.crs.to_json_dict() if series.crs else None,
            # We don't specify orientation for now
            # "orientation"
            "edges": "planar",
            "bbox": bbox,
            # I don't know how to get the epoch from a pyproj CRS, and if it's relevant
            # here
            # "epoch":
        }

    with open("../format-specs/schema.json") as f:
        spec_schema = json.load(f)
        version = spec_schema["properties"]["version"]["const"]

    return {
        "version": version,
        "primary_column": df._geometry_column_name,
        "columns": column_metadata,
        # "creator": {"library": "geopandas", "version": geopandas.__version__},
    }


def get_geometry_types(shapely_geoms: ShapelyGeometryArray) -> List[str]:
    type_ids = shapely.get_type_id(shapely_geoms)
    unique_type_ids = set(type_ids)

    geom_type_names: List[str] = []
    for type_id in unique_type_ids:
        geom_type_names.append(GeometryType(type_id).name)

    return geom_type_names


def encode_metadata(metadata: Dict) -> bytes:
    """Encode metadata dict to UTF-8 JSON string

    Parameters
    ----------
    metadata : dict

    Returns
    -------
    UTF-8 encoded JSON string
    """
    # Remove unnecessary whitespace in JSON metadata
    # https://stackoverflow.com/a/33233406
    return json.dumps(metadata, separators=(",", ":")).encode("utf-8")


def cast_dtypes(df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Note: This is specific to the nz-building-outlines data
    See reference here:
    https://nz-buildings.readthedocs.io/en/latest/published_data.html#table-nz-building-outlines
    """
    # Double checks
    assert df["building_id"].min() >= np.iinfo(np.int32).min
    assert df["building_id"].max() <= np.iinfo(np.int32).max
    df["building_id"] = df["building_id"].astype(np.int32)

    assert df["capture_source_id"].min() >= np.iinfo(np.int32).min
    assert df["capture_source_id"].max() <= np.iinfo(np.int32).max
    df["capture_source_id"] = df["capture_source_id"].astype(np.int32)

    for date_col in ["capture_source_from", "capture_source_to", "last_modified"]:
        df[date_col] = pd.to_datetime(df[date_col], format="%Y-%m-%d")

    return df


def geopandas_to_arrow(df: gpd.GeoDataFrame) -> pa.Table:
    geometry_columns = parse_to_shapely(df)
    geo_metadata = _create_metadata(df, geometry_columns)

    df = pd.DataFrame(df)
    for col, geometry_array in geometry_columns.items():
        df[col] = shapely.to_wkb(geometry_array)

    table = pa.Table.from_pandas(df, preserve_index=False)

    metadata = table.schema.metadata
    metadata.update({b"geo": encode_metadata(geo_metadata)})
    return table.replace_schema_metadata(metadata)


@click.command()
@click.option(
    "-i",
    "--input",
    type=PathType(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to input nz-building-outlines.gpkg",
    required=True,
)
@click.option(
    "--layer-name",
    type=str,
    required=False,
    help="Name of layer within GeoPackage",
    show_default=True,
    default="nz_building_outlines",
)
@click.option(
    "-o",
    "--output",
    type=PathType(file_okay=True, dir_okay=False, writable=True),
    help="Path to output Parquet file.",
    required=True,
)
@click.option(
    "--compression",
    type=click.Choice(AVAILABLE_COMPRESSIONS, case_sensitive=False),
    default="SNAPPY",
    help="Compression codec to use when writing to Parquet.",
    show_default=True,
)
def main(input: Path, layer_name: str, output: Path, compression: str):
    print("Starting to read geopackage", file=sys.stderr)
    df = gpd.read_file(input, layer=layer_name)
    print("Finished reading geopackage", file=sys.stderr)
    df = cast_dtypes(df)

    print("Starting conversion to Arrow", file=sys.stderr)
    arrow_table = geopandas_to_arrow(df)
    print("Finished conversion to Arrow", file=sys.stderr)
    print("Starting write to Parquet", file=sys.stderr)
    pq.write_table(arrow_table, output, compression=compression)
    print("Finished write to Parquet", file=sys.stderr)


if __name__ == "__main__":
    main()
