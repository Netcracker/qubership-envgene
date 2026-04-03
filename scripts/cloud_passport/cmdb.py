from pathlib import Path

from yaml import safe_load, safe_dump
from envgenehelper.yaml_helper import beautifyYaml


def map_creds_to_cmdb_format(sensitive_data: dict) -> dict:
    for key, value in sensitive_data.items():
        if value["type"] == "usernamePassword":
            sensitive_data[key] = {
                "type": value["type"],
                "data": {
                    "username": value["username"],
                    "password": value["password"]
                }
            }

        elif value["type"] == "secret":
            for k, v in value.items():
                if k != "type":
                    sensitive_data[key] = {
                        "type": value["type"],
                        "data": {
                            "secret": v
                        }
                    }
    return sensitive_data


def update_creds_to_cmdb_format(creds_path: str, schema_path: str = "/build_env/schemas/credential.schema.json"):
    creds_path = Path(creds_path)
    data = safe_load(creds_path.read_text(encoding="utf-8"))
    cmdb_mapped = map_creds_to_cmdb_format(data)
    creds_path.write_text(safe_dump(cmdb_mapped), encoding="utf-8")
    beautifyYaml(str(creds_path), schema_path)
