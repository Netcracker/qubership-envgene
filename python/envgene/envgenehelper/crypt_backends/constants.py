import re

UNENCRYPTED_REGEX_STR = "^type$"
UNENCRYPTED_REGEX = re.compile(UNENCRYPTED_REGEX_STR)

SOPS_MODES = {"encrypt": "encrypt", "decrypt": "decrypt"}
FERNET_STR = '[encrypted:AES256_Fernet]'
