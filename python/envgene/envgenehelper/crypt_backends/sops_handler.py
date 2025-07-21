import logging
import os
from pathlib import Path
import subprocess
import tempfile
import shutil

from ..business_helper import getenv_with_error
from ..yaml_helper import openYaml, readYaml, get_or_create_nested_yaml_attribute, writeYamlToFile, dumpYamlToStr
from ..logger import logger

from .constants import SOPS_MODES, ENCRYPTED_REGEX_STR


def _run_SOPS(arg_str, return_codes_to_ignore=None):
    return_codes_to_ignore = return_codes_to_ignore if return_codes_to_ignore else []
    sops_command = f'sops {arg_str}'
    result = subprocess.run(sops_command, shell=True,
                            capture_output=True, text=True, timeout=10)
    if "metadata not found" in result.stderr:
        raise ValueError('File was already decrypted')
    if "The file you have provided contains a top-level entry called 'sops'" in result.stderr:
        raise ValueError('File was already encrypted')
    if result.returncode != 0 and result.returncode not in return_codes_to_ignore:
        logger.error(f"command: {sops_command}")
        logger.error(f"Error: {result.stderr} {result.stdout}")
        raise subprocess.SubprocessError()
    return result


def _create_replace_content_sh(content):
    delimiter = 'ENVGENE_SOPS_EDIT_CUSTOM_EOF'

    script_content = f"""#!/bin/sh
if [ -z "$1" ]; then
    echo "No target file specified."
    exit 1
fi
cat > "$1" << '{delimiter}'
{content}
{delimiter}
"""
    script = tempfile.NamedTemporaryFile(delete=False, suffix=".sh")

    script.write(script_content.encode('utf-8'))
    script.close()

    return script.name


def _sops_edit(file_path, new_content, public_key):
    # expects that SOPS age key is set in environment variables
    new_content_str = dumpYamlToStr(new_content)
    editor_path = _create_replace_content_sh(new_content_str)
    try:
        os.chmod(editor_path, 0o777)
        os.environ['EDITOR'] = editor_path
        sops_args = f'edit --age {public_key} {file_path}'
        _run_SOPS(sops_args, [200])  # 200 is FileHasNotBeenModified error code
    finally:
        if os.path.exists(editor_path):
            os.remove(editor_path)


def _get_minimized_diff(file_path, old_file_path, public_key):
    new_content = openYaml(file_path)

    tmp_file_obj = tempfile.NamedTemporaryFile(delete=False, suffix=".yml")
    tmp_file_obj.close()

    shutil.copy(old_file_path, tmp_file_obj.name)

    _sops_edit(tmp_file_obj.name, new_content, public_key)
    content_with_minimized_diff = openYaml(tmp_file_obj.name)
    os.remove(tmp_file_obj.name)

    return content_with_minimized_diff


def crypt_SOPS(file_path, secret_key, in_place, public_key, mode, minimize_diff=False, old_file_path=None, *args, **kwargs):
    if not secret_key and mode == 'decrypt':
        secret_key = getenv_with_error("ENVGENE_AGE_PRIVATE_KEY")
    if not public_key and mode == 'encrypt':
        public_key = getenv_with_error("PUBLIC_AGE_KEYS")

    if secret_key:
        os.environ['SOPS_AGE_KEY'] = secret_key

    is_encrypted, empty = is_encrypted_SOPS(file_path)
    if empty:
        logger.info(f'Skipped encryption of {file_path}. File is empty. ')
        return readYaml(file_path)
    if is_encrypted and mode == "encrypt":
        logger.warning(f'File is already encrypted. Path: {file_path}')
        return openYaml(file_path)
    if not is_encrypted and mode == "decrypt":
        logger.warning(f'File is not encrypted. Path: {file_path}')
        return openYaml(file_path)

    if minimize_diff and mode != "decrypt":
        result = _get_minimized_diff(file_path, old_file_path, public_key)
        if in_place:
            writeYamlToFile(file_path, result)
    else:
        sops_args = f' --{SOPS_MODES[mode]} '
        if mode != "decrypt":
            sops_args += f' --encrypted-regex "{ENCRYPTED_REGEX_STR}"'
        if in_place:
            sops_args += ' --in-place'
        sops_args += f' -age {public_key} "{file_path}"'

        sops_cmd = (
            f'find {file_path} -name "*.y*ml" -print0 | '
            f'xargs - 0 - I{{}} sops {sops_args} "{{}}"'
        )
        try:
            if Path(file_path).is_file():
                result = _run_SOPS(f'sops {sops_args}').stdout
            if Path(file_path).is_dir():
                result = _run_SOPS(sops_cmd).stdout
        except ValueError as e:
            logger.warning(f'{str(e)}. Path: {file_path}')
            return openYaml(file_path)

    logger.debug(f'The file has been {mode}ed. Path: {file_path}')
    if not in_place:
        return readYaml(result)
    return openYaml(file_path)


def extract_value_SOPS(file_path, attribute_str):
    attribute_list = attribute_str.split('.')
    attribute_param = ''.join(f'["{item}"]' for item in attribute_list)
    sops_args = f'--extract {attribute_param} {file_path}'
    try:
        result = _run_SOPS(sops_args).stdout
    except ValueError:
        logger.warning(f'The {file_path} file is already not encrypted')
        result = get_or_create_nested_yaml_attribute(
            openYaml(file_path), attribute_str)
    return result


def _dict_has_value(d, target):
    stack = [d]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
        elif current == target:
            return True
    return False


def is_encrypted_SOPS(file_path):
    content = openYaml(file_path)
    if not content:
        return False, True
    if 'sops' in content.keys() or _dict_has_value(content, "valueIsSet"):
        return True, False
    return False, False
