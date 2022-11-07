"""
Generates test schema .json files by running `python generate_test_data.py`.

"""
import json
import pathlib
import copy


HERE = pathlib.Path(__file__).parent


metadata_template = {
    "version": "0.4.0",
    "primary_column": "geometry",
    "columns": {
        "geometry": {
            "encoding": "WKB",
            "geometry_type": "Unknown",
        },
    },
}


def write_metadata_json(metadata, name, case="valid"):
    with open(HERE / case / ("metadata_" + name + ".json"), "w") as f:
        json.dump({"geo": metadata}, f, indent=2, sort_keys=True)


# Minimum required metadata

metadata = copy.deepcopy(metadata_template)
write_metadata_json(metadata, "minimal")

metadata = copy.deepcopy(metadata_template)
metadata.pop("version")
write_metadata_json(metadata, "missing_version", case="invalid")

metadata = copy.deepcopy(metadata_template)
metadata.pop("primary_column")
write_metadata_json(metadata, "missing_primary_column", case="invalid")

metadata = copy.deepcopy(metadata_template)
metadata.pop("columns")
write_metadata_json(metadata, "missing_columns", case="invalid")

metadata = copy.deepcopy(metadata_template)
metadata["columns"] = {}
write_metadata_json(metadata, "missing_columns_entry", case="invalid")

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"].pop("encoding")
write_metadata_json(metadata, "missing_geometry_encoding", case="invalid")

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"].pop("geometry_type")
write_metadata_json(metadata, "missing_geometry_type", case="invalid")


# Geometry column name

metadata = copy.deepcopy(metadata_template)
metadata["primary_column"] = "geom"
metadata["columns"]["geom"] = metadata["columns"].pop("geometry")
write_metadata_json(metadata, "geometry_column_name")

metadata = copy.deepcopy(metadata_template)
metadata["primary_column"] = ""
write_metadata_json(metadata, "geometry_column_name")


# Encoding

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["encoding"] = "WKT"
write_metadata_json(metadata, "encoding", case="invalid")


metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_type"] = ["Point"]
write_metadata_json(metadata, "geometry_type_list")


# Geometry type - single string or list

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_type"] = "Point"
write_metadata_json(metadata, "geometry_type_string")

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["geometry_type"] = ["Point"]
write_metadata_json(metadata, "geometry_type_list")



# CRS - explicit null

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["crs"] = None
write_metadata_json(metadata, "crs_null")


# Orientation

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["orientation"] = "counterclockwise"
write_metadata_json(metadata, "orientation")

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["orientation"] = "clockwise"
write_metadata_json(metadata, "orientation", case="invalid")

# Edges

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["edges"] = "planar"
write_metadata_json(metadata, "edges_planar")

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["edges"] = "spherical"
write_metadata_json(metadata, "edges_spherical")

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["edges"] = "ellipsoid"
write_metadata_json(metadata, "edges", case="invalid")

# Epoch

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["epoch"] = 2015.1
write_metadata_json(metadata, "epoch")

metadata = copy.deepcopy(metadata_template)
metadata["columns"]["geometry"]["epoch"] = "2015.1"
write_metadata_json(metadata, "epoch_number", case="invalid")
