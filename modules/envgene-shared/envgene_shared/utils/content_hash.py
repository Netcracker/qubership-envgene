import hashlib
import json
from functools import lru_cache
from pathlib import Path


def canonical_form(data):
    if isinstance(data, dict):
        return {str(k): canonical_form(v) for k, v in data.items()}
    if isinstance(data, list):
        return [canonical_form(v) for v in data]
    return data


def canonical_hash(data, salt: str = "") -> str:
    payload = json.dumps(canonical_form(data), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256((payload + salt).encode("utf-8")).hexdigest()


@lru_cache(maxsize=None)
def schema_file_hash(schema_path) -> str:
    return hashlib.sha256(Path(schema_path).read_bytes()).hexdigest()
