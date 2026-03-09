from dataclasses import dataclass, field
from os import path

from .business_helper import getEnvDefinitionPath, getEnvCredentialsPath, INV_GEN_CREDS_PATH
from .creds_helper import mask_sensitive
from .crypt import decrypt_file
from .logger import logger
from .yaml_helper import openYaml


@dataclass
class Environment:
    base_dir: str
    cluster: str
    name: str
    env_path: str = field(init=False)
    inventory: dict = field(init=False)
    inventory_path: str = field(init=False)
    creds: dict = field(init=False)
    creds_path: str = field(init=False)

    def __post_init__(self):
        self.env_path = path.join(self.base_dir, "environments", self.cluster, self.name)
        logger.info(f"env_path: {self.env_path}")

        self.inventory_path = getEnvDefinitionPath(self.env_path)
        logger.info(f"inventory_path: {self.inventory_path}")

        self.creds_path = getEnvCredentialsPath(self.env_path)
        logger.info(f"creds_path: {self.creds_path}")

        self.inv_gen_creds_path = path.join(self.env_path, INV_GEN_CREDS_PATH)
        logger.info(f"inv_gen_creds_path: {self.inv_gen_creds_path}")

        self.inventory = openYaml(self.inventory_path, allow_default=True)
        logger.info(f"inventory: {self.inventory}")

        self.creds = decrypt_file(self.creds_path, in_place=False, allow_default=True)
        logger.info(f"creds: {mask_sensitive(self.creds)}")

        self.inv_gen_creds = decrypt_file(self.inv_gen_creds_path, in_place=False, allow_default=True)
        logger.info(f"inv_gen_creds: {mask_sensitive(self.inv_gen_creds)}")
