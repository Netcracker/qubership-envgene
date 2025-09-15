from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import json

@dataclass
class ParameterReference:
    environment: str
    namespace: str
    application: Optional[str]
    context: str
    parameter_key: str
    cred_field: str

@dataclass
class AffectedParameter:
    environment: str
    namespace: Optional[str]
    application: str
    context: str
    parameter_key: str
    environment_cred_filepath: str
    shared_cred_filepath: List[str]
    cred_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class FileUpdateEntry:
    cred_file_content: Dict[str, Any]

@dataclass
class PayloadEntry:
    namespace: str
    parameter_key: str
    context: str
    parameter_value: str
    application: Optional[str] = None
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PayloadEntry":
        required = ['namespace', 'parameter_key', 'context', 'parameter_value']
        missing = [key for key in required if not data.get(key)]
        if missing:
            raise ValueError(f"ERROR: Missing required keys: {', '.join(missing)} in entry: {data}. \n Please check payload")
        return cls(
            namespace=data['namespace'],
            parameter_key=data['parameter_key'],
            context=data['context'],
            parameter_value=data['parameter_value'],
            application=data.get('application')
        )
    def __str__(self):
        exclude_fields = {"parameter_value", "cred_field"}
        filtered_dict = {k: v for k, v in asdict(self).items() if k not in exclude_fields}
        return json.dumps(filtered_dict, indent=4)

@dataclass
class RotationResult:
    target_parameter: ParameterReference
    affected_parameters: List[AffectedParameter]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CredMap:
    cred_id: str
    param_value: str
    cred_field: str
    shared_content: Dict[str, Any]


@dataclass
class EnvConfig:
    env_name: str
    envgene_age_public_key: Optional[str] = None
    creds_rotation_enabled: bool = False
    payload_data: Dict[str, Any] = None
    cluster_name: str = ""
    work_dir: str = ""