"""
Generic helpers for reading and writing JSON data files.
All functions accept a filename (full path) and operate on the JSON content.
"""

import json
import os
from typing import Any


def _ensure_file(filename: str, default: Any) -> None:
    """Create the file with a default value if it does not exist."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if not os.path.exists(filename):
        write_json(filename, default)


def read_json(filename: str, default: Any = None) -> Any:
    """Read and return the full JSON content of a file."""
    if default is None:
        default = {}
    _ensure_file(filename, default)
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(filename: str, data: Any) -> None:
    """Overwrite the file with the given data serialised as JSON."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_value(filename: str, key: str, default: Any = None) -> Any:
    """Return the value for *key* from a JSON object file."""
    data = read_json(filename, default={})
    return data.get(key, default)


def set_value(filename: str, key: str, value: Any) -> None:
    """Set *key* = *value* in a JSON object file."""
    data = read_json(filename, default={})
    data[key] = value
    write_json(filename, data)


def delete_key(filename: str, key: str) -> bool:
    """Remove *key* from a JSON object file. Returns True if the key existed."""
    data = read_json(filename, default={})
    if key in data:
        del data[key]
        write_json(filename, data)
        return True
    return False
