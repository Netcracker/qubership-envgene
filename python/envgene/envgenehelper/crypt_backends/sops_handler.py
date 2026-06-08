import base64
import os
import shlex
import subprocess
import tempfile
import shutil

from ..business_helper import getenv_with_error
from ..yaml_helper import openYaml, readYaml, get_or_create_nested_yaml_attribute
from ..logger import logger

from .constants import *


def _sops_subprocess_env(secret_key=None, **extra):
    env = os.environ.copy()
    if secret_key:
        env['SOPS_AGE_KEY'] = secret_key
    elif not env.get('SOPS_AGE_KEY'):
        env['SOPS_AGE_KEY'] = getenv_with_error("ENVGENE_AGE_PRIVATE_KEY")
    env.update(extra)
    return env


def _run_SOPS(arg_str, secret_key=None, return_codes_to_ignore=None, **env_extra):
    return_codes_to_ignore = return_codes_to_ignore if return_codes_to_ignore else []
    cmd = ['sops'] + shlex.split(arg_str)
    env = _sops_subprocess_env(secret_key, **env_extra)
    result = subprocess.run(
        cmd, shell=False, capture_output=True, text=True, timeout=5, env=env
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
    script_content = f"""#!/usr/bin/env python3
import base64
import sys

if len(sys.argv) < 2:
    raise SystemExit("No target file specified.")
with open(sys.argv[1], "wb") as out:
    out.write(base64.b64decode({payload!r}))
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
        os.chmod(editor_path, 0o777)
        sops_args = f'edit --age {public_key} {encrypted_path}'
        _run_SOPS(sops_args, secret_key=secret_key, return_codes_to_ignore=[200], EDITOR=editor_path)
    finally:
        if os.path.exists(editor_path):
            os.remove(editor_path)


def _get_minimized_diff(file_path, old_file_path, public_key, secret_key=None):
    tmp_file_obj = tempfile.NamedTemporaryFile(delete=False, suffix=".yml")
    tmp_file_obj.close()
    tmp_path = tmp_file_obj.name

    shutil.copy(old_file_path, tmp_path)

    _sops_edit(tmp_path, file_path, public_key, secret_key=secret_key)
    return tmp_path


def _return_sops_result(file_path, mode, in_place, load_result, result=None):
    logger.info(f'The file has been {mode}ed. Path: {file_path}')
    if not in_place:
        if isinstance(result, str):
            return readYaml(result)
        return result
    return openYaml(file_path) if load_result else None


def crypt_SOPS(file_path, secret_key, in_place, public_key, mode, minimize_diff=False, old_file_path=None,
               load_result=True, *args, **kwargs):
    if not secret_key:
        secret_key = getenv_with_error("ENVGENE_AGE_PRIVATE_KEY")
    if not public_key:
        public_key = getenv_with_error("PUBLIC_AGE_KEYS")

    file_content = openYaml(file_path)
    if file_content == {}:
        logger.info(f'File is empty, skipping de/encryption. Path: {file_path}')
        return file_content if load_result else None

    encrypted = is_encrypted_SOPS(file_path)
    if encrypted and mode == "encrypt":
        logger.warning(f'File is already encrypted. Path: {file_path}')
        return openYaml(file_path) if load_result else None
    if not encrypted and mode == "decrypt":
        logger.warning(f'File is not encrypted. Path: {file_path}')
        return openYaml(file_path) if load_result else None

    if minimize_diff and mode != "decrypt":
        tmp_path = _get_minimized_diff(file_path, old_file_path, public_key, secret_key=secret_key)
        try:
            if in_place:
                shutil.copy2(tmp_path, file_path)
                if load_result:
                    return openYaml(file_path)
                return None
            result = openYaml(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        logger.info(f'The file has been {mode}ed. Path: {file_path}')
        return result

    sops_args = f' --{SOPS_MODES[mode]} '
    if mode != "decrypt":
        sops_args += f' --unencrypted-regex "{UNENCRYPTED_REGEX_STR}"'
    if in_place:
        sops_args += ' --in-place'
    sops_args += f' -age {public_key} {file_path}'
    try:
        run_result = _run_SOPS(sops_args, secret_key=secret_key)
        stdout = run_result.stdout if not in_place else None
    except ValueError as e:
        logger.warning(f'{str(e)}. Path: {file_path}')
        return openYaml(file_path) if load_result else None

    return _return_sops_result(file_path, mode, in_place, load_result, stdout)


def extract_value_SOPS(file_path, attribute_str):
    attribute_list = attribute_str.split('.')
    attribute_param = ''.join(f'["{item}"]' for item in attribute_list)
    sops_args = f'--extract {attribute_param} {file_path}'
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
    if not text:
        return False
    for line in reversed(text.splitlines()):
        if line.startswith('sops:'):
            return True
    return False
