import os

def get_schemas_dir() -> str:
    return os.getenv('JSON_SCHEMAS_DIR', '/module/schemas')
