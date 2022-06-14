import sys
from pathlib import Path

import click
import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from encoder import AVAILABLE_COMPRESSIONS, PathType, geopandas_to_arrow

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
