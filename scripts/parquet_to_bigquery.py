import click
import json
import glob
import pyarrow.parquet as pq

from encoder import PathType
from pathlib import Path
from google.cloud import bigquery
from encoder import Edges

def upload_parquet_file(client:  bigquery.Client, file: Path, write_disposition: str, dst: str):
    """Upload a parquet file to BigQuery"""
    job_config = bigquery.LoadJobConfig(
        source_format = bigquery.SourceFormat.PARQUET,
        write_disposition = write_disposition,
    )

    with open(file, "rb") as source_file:
        print(f"Uploading file {file}")
        job = client.load_table_from_file(source_file, dst, job_config=job_config)

    job.result()  # Waits for the job to complete.

def validate_metadata(metadata):
    """Validate metadata"""
    if metadata is None or b"geo" not in metadata:
        raise ValueError("Missing geo metadata")

    geo = json.loads(metadata[b"geo"])

    if (geo["primary_column"] not in geo["columns"]):
        raise ValueError("Primary column not found")

    for column_name, column_meta in geo["columns"].items():
        encoding = column_meta["encoding"]
        edges = column_meta["edges"]
        if encoding != 'WKB':
            raise ValueError(f"Not supported encoding {encoding} for column {column_name}")
        if edges != Edges.SPHERICAL.value:
            raise ValueError(f"Only spherical edges are supported")

@click.command()
@click.option(
    "-i",
    "--input",
    type=PathType(exists=True, readable=True),
    help="Path to a parquet file or a folder with multiple parquet files inside (it requires extension *.parquet).",
    required=True,
)
@click.option(
    "-o",
    "--output",
    type=str,
    help="FQN of the destination table (project.dataset.table).",
    required=True,
)
def main(input: Path, output: str):
    primary_column = None
    tmp_output =  f"{output}_tmp"
    metadata = None
    client = bigquery.Client()

    if input.is_dir():
        # A folder is detected
        first_file = True

        for file in glob.glob(f"{input}/**/*.parquet",recursive=True):

            if first_file:
                # First file determines the schema and truncates the table
                metadata = pq.read_schema(file).metadata
                validate_metadata(metadata)
                write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
                first_file = False
            else:
               # other files will append
               write_disposition = bigquery.WriteDisposition.WRITE_APPEND

            upload_parquet_file(client, file, write_disposition, tmp_output)
    else:
        # Single file mode
        metadata = pq.read_schema(input).metadata
        validate_metadata(metadata)
        write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
        upload_parquet_file(client, input, write_disposition, tmp_output)

    metadata_geo = json.loads(metadata[b"geo"])
    primary_column = metadata_geo["primary_column"]
    geo_columns = list(metadata_geo["columns"].keys())
    wkb_columns_expression = map(lambda c: f"ST_GEOGFROMWKB({c}) as {c}", geo_columns)

    ## Convert to geography the file(s) imported
    sql = f"""
        DROP TABLE IF EXISTS {output};
        CREATE TABLE {output} CLUSTER BY {primary_column}
        AS SELECT * EXCEPT({", ".join(geo_columns)}),
            {", ".join(wkb_columns_expression)}
        FROM {tmp_output};
        DROP TABLE IF EXISTS {tmp_output};
    """

    query_job = client.query(sql)
    query_job.result()  # Waits for job to complete.

    table = client.get_table(output)
    print(f"Loaded {table.num_rows} rows and {len(table.schema)} columns to {output}")

if __name__ == "__main__":
    main()
