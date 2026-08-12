import re

UNENCRYPTED_REGEX_STR = "^type$"
UNENCRYPTED_REGEX = re.compile(UNENCRYPTED_REGEX_STR)
ENCRYPTED_REGEX_STR = "data$"
ENCRYPTED_REGEX = re.compile(ENCRYPTED_REGEX_STR)

SOPS_MODES = {"encrypt": "encrypt", "decrypt": "decrypt"}
FERNET_STR = '[encrypted:AES256_Fernet]'

VALID_EXTENSIONS = re.compile(r'\.ya?ml$')
TARGET_REGEX = re.compile(r'(^credentials$|^creds$|-(credentials|creds)($|-))')
TARGET_PARENT_DIRS = {"configuration", "environments"}
TARGET_DIRS = {"credentials"}

ENVGENE_AGE_PUBLIC_KEY_ID = "ENVGENE_AGE_PUBLIC_KEY"
ENVGENE_AGE_PRIVATE_KEY_ID = "ENVGENE_AGE_PRIVATE_KEY"
PUBLIC_AGE_KEYS_ID = "PUBLIC_AGE_KEYS"
SECRET_KEY_ID = "SECRET_KEY"

FERNET_ID = "Fernet"
SOPS_ID = "SOPS"