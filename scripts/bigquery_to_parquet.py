import click
import sys
import pyarrow.parquet as pq
import geopandas as gpd

from encoder import AVAILABLE_COMPRESSIONS, Edges, PathType, geopandas_to_arrow
from pathlib import Path
from google.cloud import bigquery

MODES = ["FILE", "FOLDER"]

def read_gdf(input_query: str, primary_column: str):
    client = bigquery.Client()
    df = client.query(input_query).to_dataframe()
    df[primary_column] = gpd.GeoSeries.from_wkt(df[primary_column])
    return gpd.GeoDataFrame(df, geometry=primary_column, crs="EPSG:4326")

@click.command()
@click.option(
    "-q",
    "--input-query",
    type=str,
    help="SQL query of the data to export",
    required=True,
)
@click.option(
    "--primary-column",
    type=str,
    help="The primary column name with geometry data",
    required=True,
)
@click.option(
    "-o",
    "--output",
    type=PathType(file_okay=True, dir_okay=True, writable=True),
    help="Path to output",
    required=True,
)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(MODES, case_sensitive=False),
    help="Mode to use FILE or FOLDER",
    default="FOLDER",
    show_default=True
)
@click.option(
    "--compression",
    type=click.Choice(AVAILABLE_COMPRESSIONS, case_sensitive=False),
    default="SNAPPY",
    help="Compression codec to use when writing to Parquet.",
    show_default=True,
)
@click.option(
    "--partition-size",
    type=int,
    default=5000,
    help="Number of records per partition. Ignored if --single-file is provided.",
    show_default=True,
)
def main(input_query: str, primary_column: str, output: Path, mode: str, compression: str , partition_size: int):
    print("Reading data from BigQuery", file=sys.stderr)

    if mode.upper() == 'FOLDER':
        gdf = (
            read_gdf(input_query, primary_column)
                .assign(__partition__= lambda x: x.index // partition_size)
        )
    else:
        gdf = read_gdf(input_query, primary_column)

    print("Finished reading", file=sys.stderr)
    print("Starting conversion to Arrow", file=sys.stderr)
    arrow_table = geopandas_to_arrow(gdf, Edges.SPHERICAL)
    print("Finished conversion to Arrow", file=sys.stderr)

    print("Starting write to Parquet", file=sys.stderr)

    if mode.upper() == 'FOLDER':
        # We need to export to multiple files, because a single file might hit bigquery limits (UDF out of memory). https://cloud.google.com/bigquery/docs/loading-data-cloud-storage-parquet
        pq.write_to_dataset(arrow_table, root_path=output, partition_cols=['__partition__'], compression=compression)
    else:
        pq.write_table(arrow_table, output, compression=compression)

    print("Finished write to Parquet", file=sys.stderr)

if __name__ == "__main__":
    main()
