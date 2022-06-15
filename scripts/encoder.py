import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

import click
import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pygeos
from numpy.typing import NDArray

GEOPARQUET_VERSION = "0.4.0"
AVAILABLE_COMPRESSIONS = ["NONE", "SNAPPY", "GZIP", "BROTLI", "LZ4", "ZSTD"]

PygeosGeometryArray = NDArray[pygeos.Geometry]

class Edges(Enum):
    PLANAR = 'planar'
    SPHERICAL = 'spherical'

class PathType(click.Path):
    """A Click path argument that returns a pathlib Path, not a string"""

    def convert(self, value, param, ctx):
        return Path(super().convert(value, param, ctx))

class GeometryType(int, Enum):
    """Pygeos (GEOS) geometry type mapping
    From https://pygeos.readthedocs.io/en/latest/geometry.html?highlight=type#pygeos.geometry.get_type_id
    """

    Missing = -1
    Point = 0
    LineString = 1
    LinearRing = 2
    Polygon = 3
    MultiPoint = 4
    MultiLinestring = 5
    MultiPolygon = 6
    GeometryCollection = 7


def _parse_to_pygeos(df: gpd.GeoDataFrame) -> Dict[str, PygeosGeometryArray]:
    """Parse to pygeos geometry array

    This is split out from _create_metadata so that we don't have to create the pygeos
    array twice: once for converting to wkb and another time for metadata handling.
    """
    geometry_columns: Dict[str, PygeosGeometryArray] = {}
    for col in df.columns[df.dtypes == "geometry"]:
        geometry_columns[col] = df[col].array.data

    return geometry_columns


def _create_metadata(
    df: gpd.GeoDataFrame, geometry_columns: Dict[str, PygeosGeometryArray], edges: Edges
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
        geometry_type = _get_geometry_type(geometry_array)
        bbox = list(pygeos.total_bounds(geometry_array))

        series = df[col]
        column_metadata[col] = {
            "encoding": "WKB",
            "geometry_type": geometry_type,
            "crs": series.crs.to_json_dict() if series.crs else None,
            # We don't specify orientation for now
            # "orientation"
            "edges": edges.value,
            "bbox": bbox,
            # I don't know how to get the epoch from a pyproj CRS, and if it's relevant
            # here
            # "epoch":
        }

    return {
        "version": GEOPARQUET_VERSION,
        "primary_column": df._geometry_column_name,
        "columns": column_metadata,
        # "creator": {"library": "geopandas", "version": geopandas.__version__},
    }


def _get_geometry_type(pygeos_geoms: PygeosGeometryArray) -> List[str]:
    type_ids = pygeos.get_type_id(pygeos_geoms)
    unique_type_ids = set(type_ids)

    geom_type_names: List[str] = []
    for type_id in unique_type_ids:
        geom_type_names.append(GeometryType(type_id).name)

    return geom_type_names


def _encode_metadata(metadata: Dict) -> bytes:
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
    return json.dumps(metadata, separators=(',', ':')).encode("utf-8")


def geopandas_to_arrow(df: gpd.GeoDataFrame, edges:Edges = Edges.PLANAR) -> pa.Table:
    geometry_columns = _parse_to_pygeos(df)
    geo_metadata = _create_metadata(df, geometry_columns, edges)

    df = pd.DataFrame(df)
    for col, geometry_array in geometry_columns.items():
        df[col] = pygeos.to_wkb(geometry_array)

    table = pa.Table.from_pandas(df, preserve_index=False)

    metadata = table.schema.metadata
    metadata.update({b"geo": _encode_metadata(geo_metadata)})
    return table.replace_schema_metadata(metadata)
