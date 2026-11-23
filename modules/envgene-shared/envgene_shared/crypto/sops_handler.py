import base64
import os
import shlex
import subprocess
import tempfile
import sys

from envgene_shared.utils.business_utils import getenv_with_error
from envgene_shared.utils.crypt_utils import get_crypt
from envgene_shared.utils.yaml_utils import openYaml, readYaml, get_or_create_nested_yaml_attribute
from envgene_shared.utils.logger import logger

from envgene_shared.utils.constants import *

ENVGENE_AGE_PRIVATE_KEY = None
PUBLIC_AGE_KEYS = None

DCL2ARGO_AGE_PUBLIC_KEY_PARAM = "DCL_CONFIG_SOPS_DCL2ARGO_AGE_PUBLIC_KEY"
NON_AGE_SOPS_KEY_GROUP_PROVIDERS = ("pgp", "kms", "gcp_kms", "azure_kv", "hc_vault")


def _normalize_age_keys(public_keys):
    return list(dict.fromkeys([key.strip() for key in public_keys.split(",") if key.strip()]))


def _collect_sops_age_recipients(items):
    if not isinstance(items, list):
        return
    for item in items:
        if isinstance(item, dict) and item.get("recipient"):
            yield str(item["recipient"])


def _sops_age_recipients(encrypted_data):
    doc = readYaml(encrypted_data.decode("utf-8"))
    if not isinstance(doc, dict):
        return set(), False
    metadata = doc.get("sops")
    if not isinstance(metadata, dict):
        return set(), False

    recipients = set()
    key_groups = metadata.get("key_groups")
    if isinstance(key_groups, list):
        for group in key_groups:
            if not isinstance(group, dict):
                continue
            recipients.update(_collect_sops_age_recipients(group.get("age")))
            if any(group.get(provider) for provider in NON_AGE_SOPS_KEY_GROUP_PROVIDERS):
                return recipients, True
        return recipients, False

    recipients.update(_collect_sops_age_recipients(metadata.get("age")))
    if any(metadata.get(provider) for provider in NON_AGE_SOPS_KEY_GROUP_PROVIDERS):
        return recipients, True
    return recipients, False


def _read_file_bytes(file_path):
    with open(file_path, "rb") as f:
        return f.read()


def _write_sops_update_keys_config(public_keys):
    age_keys = ",".join(_normalize_age_keys(public_keys))
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sops.yaml", mode="w", encoding="utf-8") as config:
        config.write("creation_rules:\n")
        config.write("  - path_regex: '.*'\n")
        config.write(f'    age: "{age_keys}"\n')
        return config.name


def _update_sops_age_keys(file_path, public_keys):
    desired_recipients = set(_normalize_age_keys(public_keys))
    current_recipients, has_non_age_groups = _sops_age_recipients(_read_file_bytes(file_path))
    if not desired_recipients or not current_recipients or current_recipients == desired_recipients:
        return
    if has_non_age_groups:
        logger.warning(f"Skipping SOPS key update for a file with non-age key groups: {file_path}")
        return

    config_path = _write_sops_update_keys_config(public_keys)
    try:
        _run_SOPS(["--config", config_path, "updatekeys", "--yes", str(file_path)])
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)

    updated_recipients, _ = _sops_age_recipients(_read_file_bytes(file_path))
    if updated_recipients != desired_recipients:
        raise subprocess.SubprocessError(
            f"sops updatekeys did not set expected age recipients for {file_path}: {sorted(updated_recipients)}"
        )


def _sops_subprocess_env(secret_key=None, **extra):
    global ENVGENE_AGE_PRIVATE_KEY
    env = os.environ.copy()
    if secret_key:
        env['SOPS_AGE_KEY'] = secret_key
    elif not env.get('SOPS_AGE_KEY'):
        if ENVGENE_AGE_PRIVATE_KEY is None:
            ENVGENE_AGE_PRIVATE_KEY = getenv_with_error("ENVGENE_AGE_PRIVATE_KEY", no_log=True)
        env['SOPS_AGE_KEY'] = ENVGENE_AGE_PRIVATE_KEY
    env.update(extra)
    return env


def _run_SOPS(cmd_arg, secret_key=None, return_codes_to_ignore=None, stdin_text=None, **env_extra):
    return_codes_to_ignore = return_codes_to_ignore if return_codes_to_ignore else []
    cmd = ['sops'] + cmd_arg
    env = _sops_subprocess_env(secret_key, **env_extra)
    result = subprocess.run(
        cmd, shell=False, capture_output=True, text=True, timeout=25, env=env, input=stdin_text
    )
    if "metadata not found" in result.stderr:
        raise ValueError('File was already decrypted')
    if "The file you have provided contains a top-level entry called 'sops'" in result.stderr:
        raise ValueError('File was already encrypted')
    if result.returncode != 0 and result.returncode not in return_codes_to_ignore:
        file_path = cmd[-1] if len(cmd) > 1 else 'unknown'
        stderr = (result.stderr or '').strip()
        stdout = (result.stdout or '').strip()
        detail = stderr or stdout or f'exit code {result.returncode}'
        logger.error(f"command: {' '.join(cmd)}")
        logger.error(f"Error: {result.stderr} {result.stdout}")
        raise subprocess.SubprocessError(
            f'sops command failed for {file_path}: {detail}'
        )
    return result


def _create_replace_content_sh(content_bytes):
    """Build an executable SOPS EDITOR script that writes plaintext bytes exactly."""
    payload = base64.b64encode(content_bytes).decode('ascii')
    script_content = f"""import base64
import sys

from ruyaml import YAML

if len(sys.argv) < 2:
    raise SystemExit("No target file specified.")
yaml = YAML(typ="safe")
new_bytes = base64.b64decode({payload!r})
with open(sys.argv[1], "rb") as f:
    old_content = yaml.load(f)
if old_content != yaml.load(new_bytes):
    with open(sys.argv[1], "wb") as out:
        out.write(new_bytes)
"""
    script = tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode='w', encoding='utf-8')
    script.write(script_content)
    script.close()

    return script.name


def _sops_edit(encrypted_path, plaintext_path, public_key, secret_key=None):
    with open(plaintext_path, 'rb') as f:
        plaintext_bytes = f.read()
    editor_path = _create_replace_content_sh(plaintext_bytes)
    try:
        sops_args = ["edit", "--age", public_key, str(encrypted_path)]
        editor = f"{shlex.quote(sys.executable)} {shlex.quote(editor_path)}"
        _run_SOPS(sops_args, secret_key=secret_key, return_codes_to_ignore=[200], EDITOR=editor)
    finally:
        if os.path.exists(editor_path):
            os.remove(editor_path)


def _return_sops_result(file_path, mode, in_place, load_result, result=None):
    logger.debug(f'The file has been {mode}ed. Path: {file_path}')
    if not in_place:
        if isinstance(result, str):
            return readYaml(result)
        return result
    return openYaml(file_path) if load_result else None


def crypt_SOPS(file_path, secret_key, in_place, public_key, mode, load_result=True,
               encrypted_regex=None, *args, **kwargs):
    global ENVGENE_AGE_PRIVATE_KEY, PUBLIC_AGE_KEYS
    if not secret_key or not public_key:
        if ENVGENE_AGE_PRIVATE_KEY is None:
            ENVGENE_AGE_PRIVATE_KEY = getenv_with_error("ENVGENE_AGE_PRIVATE_KEY", no_log=True)
            PUBLIC_AGE_KEYS = getenv_with_error("PUBLIC_AGE_KEYS", no_log=True)
    if not secret_key:
        secret_key = ENVGENE_AGE_PRIVATE_KEY
    if not public_key:
        public_key = PUBLIC_AGE_KEYS

    sops_args = [f"--{SOPS_MODES[mode]}"]
    if mode != "decrypt" and encrypted_regex is not None:
        sops_args.extend(["--encrypted-regex", encrypted_regex])
    if in_place:
        sops_args.append("--in-place")
    sops_args.extend(["-age", public_key, str(file_path)])
    try:
        run_result = _run_SOPS(sops_args, secret_key=secret_key)
        stdout = run_result.stdout if not in_place else None
    except ValueError as e:
        logger.warning(f'{str(e)}. Path: {file_path}')
        return openYaml(file_path) if load_result else None

    return _return_sops_result(file_path, mode, in_place, load_result, stdout)


def decrypt_SOPS_bytes(data: bytes, file_path, secret_key=None) -> str:
    sops_args = ["decrypt", "--input-type", "yaml", "--output-type", "yaml", "--filename-override", str(file_path),
                 "/dev/stdin"]
    return _run_SOPS(sops_args, secret_key=secret_key, stdin_text=data.decode("utf-8")).stdout


def encrypt_SOPS_bytes(data: bytes, file_path, encrypted_regex=None, old_data: bytes = None) -> bytes:
    global PUBLIC_AGE_KEYS
    if PUBLIC_AGE_KEYS is None:
        PUBLIC_AGE_KEYS = getenv_with_error("PUBLIC_AGE_KEYS", no_log=True)
    if old_data is not None:
        with tempfile.TemporaryDirectory() as tmp:
            old_path = os.path.join(tmp, "old.yml")
            new_path = os.path.join(tmp, "new.yml")
            with open(old_path, "wb") as f:
                f.write(old_data)
            with open(new_path, "wb") as f:
                f.write(data)
            _sops_edit(old_path, new_path, PUBLIC_AGE_KEYS)
            _update_sops_age_keys(old_path, PUBLIC_AGE_KEYS)
            with open(old_path, "rb") as f:
                return f.read()
    sops_args = ["encrypt", "--input-type", "yaml", "--output-type", "yaml", "--age", PUBLIC_AGE_KEYS]
    if encrypted_regex is not None:
        sops_args.extend(["--encrypted-regex", encrypted_regex])
    sops_args.extend(["--filename-override", str(file_path), "/dev/stdin"])
    return _run_SOPS(sops_args, stdin_text=data.decode("utf-8")).stdout.encode("utf-8")


def merge_pipeline_age_key_into_public_keys(effective_set_dir) -> None:
    global PUBLIC_AGE_KEYS
    if not get_crypt():
        return
    params_path = effective_set_dir / "pipeline" / "parameters.yaml"
    params = openYaml(params_path, allow_default=True) or {}
    age_public_key = str(params.get(DCL2ARGO_AGE_PUBLIC_KEY_PARAM) or "").strip()
    if not age_public_key:
        logger.warning(f"{DCL2ARGO_AGE_PUBLIC_KEY_PARAM} not found in pipeline context {params_path}, "
                       "encrypting with PUBLIC_AGE_KEYS only")
        return
    public_age_keys = getenv_with_error("PUBLIC_AGE_KEYS", no_log=True)
    existing_keys = [key.strip() for key in public_age_keys.split(",") if key.strip()]
    if age_public_key not in existing_keys:
        existing_keys.append(age_public_key)
    combined = ",".join(existing_keys)
    os.environ["PUBLIC_AGE_KEYS"] = combined
    PUBLIC_AGE_KEYS = combined
    logger.info(f"PUBLIC_AGE_KEYS combined recipients: {combined}")


def extract_value_SOPS(file_path, attribute_str):
    attribute_list = attribute_str.split('.')
    attribute_param = ''.join(f'["{item}"]' for item in attribute_list)
    sops_args = ["--extract", attribute_param, str(file_path)]
    try:
        result = _run_SOPS(sops_args).stdout
    except ValueError:
        logger.warning(f'The {file_path} file is already not encrypted')
        result = get_or_create_nested_yaml_attribute(openYaml(file_path), attribute_str)
    return result


def is_encrypted_SOPS(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
    except OSError:
        return False
    return is_encrypted_SOPS_text(text)


def is_encrypted_SOPS_text(text: str) -> bool:
    if not text:
        return False
    for line in reversed(text.splitlines()):
        if line.startswith('sops:'):
            return True
    return False
