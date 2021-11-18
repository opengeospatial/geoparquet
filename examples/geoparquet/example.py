"""
Generates `example.parquet` using pyarrow.

You can print the metadata with:

.. code-block:: python

   >>> import json, pprint, pyarrow.parquet
   >>> pprint.pprint(json.loads(pq.read_schema("example.parquet").metadata[b"geo"]))
   {'columns': {'geometry': {'crs': 'GEOGCRS["WGS 84",ENSEMBLE["World Geodetic '
                                    'System 1984 ensemble",MEMBER["World Geodetic '
                                    'System 1984 (Transit)"],MEMBER["World '
                                    'Geodetic System 1984 (G730)"],MEMBER["World '
                                    'Geodetic System 1984 (G873)"],MEMBER["World '
                                    'Geodetic System 1984 (G1150)"],MEMBER["World '
                                    'Geodetic System 1984 (G1674)"],MEMBER["World '
                                    'Geodetic System 1984 '
                                    '(G1762)"],ELLIPSOID["WGS '
                                    '84",6378137,298.257223563],ENSEMBLEACCURACY[2.0]],CS[ellipsoidal,2],AXIS["geodetic '
                                    'latitude (Lat)",north],AXIS["geodetic '
                                    'longitude '
                                    '(Lon)",east],UNIT["degree",0.0174532925199433],USAGE[SCOPE["Horizontal '
                                    'component of 3D '
                                    'system."],AREA["World."],BBOX[-90,-180,90,180]],ID["EPSG",4326]]',
                             'encoding': 'WKB'}},
    'primary_column': 'geometry',
    'version': '0.1.0'}
"""
import json
import pathlib

import geopandas
import pyarrow as pa
import pyarrow.parquet as pq
import pyproj

HERE = pathlib.Path(__file__).parent

df = geopandas.read_file(geopandas.datasets.get_path("naturalearth_lowres"))
table = pa.Table.from_pandas(df.head().to_wkb())


metadata = {
    "version": "0.1.0",
    "primary_column": "geometry",
    "columns": {
        "geometry": {
            "crs": df.crs.to_wkt(pyproj.enums.WktVersion.WKT2_2019_SIMPLIFIED),
            "encoding": "WKB",
        },
    },
}

schema = (
    table.schema
    .with_metadata({"geo": json.dumps(metadata)})
)
table = table.cast(schema)

pq.write_table(table, HERE / "example.parquet")
