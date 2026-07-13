from typing import Optional
from pydantic import BaseModel, Field, AliasChoices
from enum import Enum, unique

@unique
class RegistryType(Enum):
    ARTIFACTORY = "artifactory"
    NEXUS = "nexus"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"

class MavenConfig(BaseModel):
    targetRelease : str
    targetStaging : str
    targetSnapshot : str 

class AuthRegistry(BaseModel):
    pass

class AuthSTSSecret(AuthRegistry):
    access_key: str
    secret_key: str
    domain: str = ""
    region_name: str = ""
    repository: str = ""

class AuthSTSAssumeRole(AuthRegistry):
    access_key: str
    secret_key: str
    domain: str = ""
    region_name: str = ""
    repository: str = ""
    role_arn: str= ""
    auth_type: str = ""
    session_prefix: str = ""

class AuthGCPFederation(AuthRegistry):
    project: str = ""  # PUB_REG_PROJECT (project number)
    region_name: str = ""
    repository: str = ""
    auth_type: str = ""
    # Federation parameters
    oidc_url: str = ""  # PUB_REG_OIDC_URL
    oidc_method: str = "secret"  # PUB_REG_OIDC_METHOD (secret|cert)
    provider_id: str = ""  # PUB_REG_PROVIDER_ID
    pool_id: str = ""  # PUB_REG_POOL_ID
    sa_email: str = ""  # PUB_REG_SA_EMAIL
    # External OIDC provider parameters
    oidc_client_id: str = ""  # PUB_REG_OIDC_CLIENT_ID
    oidc_client_secret: str = ""  # PUB_REG_OIDC_CLIENT_SECRET (for secret method)
    oidc_custom_params: str = ""  # PUB_REG_OIDC_CUSTOM_PARAM

class AuthGCPServiceAccount(AuthRegistry):
    service_account_key_content: str = ""
    project: str = ""
    region_name: str = ""
    repository: str = ""

class AuthAzureOAuth2(AuthRegistry):
    client_id: str
    client_secret: str

class AuthManageIdentity(AuthRegistry):
    client_id: str
    client_secret: str

class AuthUserPassword(AuthRegistry):
    registry_url: str
    username: str
    password: str

class RegistryInfo(BaseModel):
    version : str = "1.0"
    url: str
    type: RegistryType = RegistryType.ARTIFACTORY
    maven_config: MavenConfig = Field(alias=AliasChoices("mavenConfig", "maven_config"))
    auth_config: Optional[AuthRegistry] = Field(alias=AliasChoices("authConfig", "auth_config"))
