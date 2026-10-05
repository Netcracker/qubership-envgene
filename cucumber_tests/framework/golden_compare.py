import os
import shutil
import json
import yaml
from pathlib import Path

def compare_directories(expected_dir: Path, actual_dir: Path, ignore_patterns: list = None):
    """
    Recursively compares actual_dir to expected_dir.
    If UPDATE_GOLDEN=1 is set, overwrites expected_dir with actual_dir instead.
    """
    if os.environ.get('UPDATE_GOLDEN') == '1':
        if expected_dir.exists():
            shutil.rmtree(expected_dir)
        shutil.copytree(actual_dir, expected_dir)
        print(f"Updated golden directory at {expected_dir}")
        return

    assert expected_dir.exists(), f"Golden directory {expected_dir} does not exist. Run with UPDATE_GOLDEN=1 to create it."
    assert actual_dir.exists(), f"Actual directory {actual_dir} does not exist."

    ignore_patterns = ignore_patterns or []

    def is_ignored(f_path):
        for pat in ignore_patterns:
            if f_path.match(pat) or str(f_path).startswith(pat):
                return True
        return False

    expected_files = set(f.relative_to(expected_dir) for f in expected_dir.rglob('*') if f.is_file() and f.name != 'README.md' and not is_ignored(f.relative_to(expected_dir)))
    actual_files = set(f.relative_to(actual_dir) for f in actual_dir.rglob('*') if f.is_file() and f.name != 'README.md' and not is_ignored(f.relative_to(actual_dir)))

    # Check for missing and extra files
    missing_files = expected_files - actual_files
    extra_files = actual_files - expected_files

    assert not missing_files, f"Files missing from generated output: {missing_files}"
    assert not extra_files, f"Extra files generated that are not in golden: {extra_files}"

    for rel_file in expected_files:
        expected_file = expected_dir / rel_file
        actual_file = actual_dir / rel_file

        ext = expected_file.suffix.lower()

        if ext in ['.yml', '.yaml']:
            try:
                with open(expected_file, 'r', encoding='utf-8') as ef:
                    expected_data = list(yaml.safe_load_all(ef))
                with open(actual_file, 'r', encoding='utf-8') as af:
                    actual_data = list(yaml.safe_load_all(af))
                assert expected_data == actual_data, f"YAML content mismatch in file: {rel_file}"
            except yaml.YAMLError:
                # Fallback to string comparison if not valid YAML
                _compare_text(expected_file, actual_file, rel_file)
        elif ext == '.json':
            try:
                with open(expected_file, 'r', encoding='utf-8') as ef:
                    expected_data = json.load(ef)
                with open(actual_file, 'r', encoding='utf-8') as af:
                    actual_data = json.load(af)
                assert expected_data == actual_data, f"JSON content mismatch in file: {rel_file}"
            except json.JSONDecodeError:
                _compare_text(expected_file, actual_file, rel_file)
        else:
            _compare_text(expected_file, actual_file, rel_file)

def _compare_text(expected_file: Path, actual_file: Path, rel_file: Path):
    with open(expected_file, 'r', encoding='utf-8', errors='replace') as ef:
        expected_text = ef.read()
    with open(actual_file, 'r', encoding='utf-8', errors='replace') as af:
        actual_text = af.read()
    
    # Normalize line endings
    expected_text = expected_text.replace('\r\n', '\n')
    actual_text = actual_text.replace('\r\n', '\n')

    assert expected_text == actual_text, f"Text content mismatch in file: {rel_file}"
