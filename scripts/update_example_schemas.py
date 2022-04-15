import json
from pathlib import Path
from typing import Any, Dict, Union

import pyarrow.parquet as pq


def find_root_dir() -> Path:
    """Find root geoparquet directory

    This is a more robust approach than assuming __file__ refers to a specific place
    """
    folder = Path(__file__).resolve()

    while folder.name != "geoparquet":
        if folder == Path("/"):
            raise ValueError("Could not find geoparquet folder")

        folder = folder.parent

    return folder


def copy_parquet_schema_metadata_to_json(parquet_file: Path) -> None:
    """Copy Parquet schema metadata to a neighboring JSON file"""
    neighboring_json_file = parquet_file.parent / f"{parquet_file.stem}_metadata.json"
    schema = pq.read_schema(parquet_file)
    decoded_meta = decode_dict(schema.metadata)

    with open(neighboring_json_file, "w") as f:
        json.dump(decoded_meta, f, indent=2, sort_keys=True)


def decode_dict(d: Dict[Union[bytes, str], Union[bytes, Any]]) -> Dict[str, Any]:
    """Decode binary keys and values to string and dict objects"""
    new_dict = {}
    for key, val in d.items():
        new_key = key.decode() if isinstance(key, bytes) else key
        new_val = val.decode() if isinstance(val, bytes) else val
        if new_val.lstrip().startswith("{"):
            new_val = json.loads(new_val)

        new_dict[new_key] = new_val

    return new_dict


def main():
    examples_dir = find_root_dir() / 'examples'
    for parquet_file in examples_dir.glob("*.parquet"):
        copy_parquet_schema_metadata_to_json(parquet_file)


if __name__ == "__main__":
    main()
