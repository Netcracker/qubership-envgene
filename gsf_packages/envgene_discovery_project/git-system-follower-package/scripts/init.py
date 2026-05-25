from pathlib import Path
from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.templates import create_template, get_template_names

# Protected files that should never be deleted
PROTECTED_FILES = {
    'history.log',
    '.gitlab-ci.yml',
    '.gitignore',
    'gitlab-ci/pipeline_vars.yaml',
    'gitlab-ci/pipeline_vars.yml',
}


def _migrate_pipeline_vars_format(content: bytes) -> bytes:
    """Migrate old .pipeline_vars: wrapper format to new format."""
    text = content.decode('utf-8')
    lines = text.splitlines()

    if not lines:
        return content

    # Find .pipeline_vars: - can be anywhere in file (after ---, comments, etc.)
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip() == '.pipeline_vars:':
            start_idx = i
            break
    if start_idx is None:
        return content  # Not old format

    rest = lines[start_idx + 1:]
    non_empty = [line for line in rest if line.strip()]
    if not non_empty:
        return b'---\n'

    min_indent = min(len(line) - len(line.lstrip()) for line in non_empty)
    dedented = []
    for line in rest:
        if line.strip() and len(line) - len(line.lstrip()) >= min_indent:
            dedented.append(line[min_indent:])
        else:
            dedented.append(line)

    result = '\n'.join(dedented)
    if not result.strip().startswith('---'):
        result = '---\n' + result
    return result.encode('utf-8')


def _delete_files_from_history(parameters: Parameters):
    """Delete files listed in history.log from the user repository."""
    script_dir = Path(__file__).parent
    templates_dir = script_dir / 'templates' / 'default'
    cookiecutter_template_dir = templates_dir / '{{ cookiecutter.gsf_repository_name }}'
    history_log_path = cookiecutter_template_dir / 'history.log'
    
    if not history_log_path.exists():
        print(f'\t\tWarning: history.log not found at {history_log_path}')
        return

    try:
        with open(history_log_path, 'r', encoding='utf-8') as f:
            files_to_delete = {line.strip() for line in f if line.strip()}
    except Exception as e:
        print(f'\t\tWarning: Could not read history.log: {e}')
        return
    
    if not files_to_delete:
        return
    
    # Use current working directory as repository root
    repo_root = Path.cwd()
    directories_to_check = set()
    deleted_count = 0
    
    # Delete files listed in history.log
    for file_path_str in files_to_delete:
        if file_path_str in PROTECTED_FILES:
            continue
        
        file_path = Path(file_path_str)
        file_full_path = repo_root / file_path
        
        if file_full_path.exists() and file_full_path.is_file():
            try:
                if file_path.parent != Path('.'):
                    directories_to_check.add(file_path.parent)
                file_full_path.unlink()
                deleted_count += 1
                print(f'\t\tDeleted file: {file_path_str}')
            except Exception as e:
                print(f'\t\tWarning: Could not delete file {file_path_str}: {e}')
    
    # Delete empty directories
    for dir_path in sorted(directories_to_check, key=lambda p: len(p.parts), reverse=True):
        dir_full_path = repo_root / dir_path
        if dir_full_path.exists() and dir_full_path.is_dir():
            try:
                if not any(dir_full_path.iterdir()):
                    dir_full_path.rmdir()
                    print(f'\t\tDeleted empty directory: {dir_path}')
            except Exception:
                pass
    
    if deleted_count > 0:
        print(f'\t\tDeleted {deleted_count} file(s) from repository')


def main(parameters: Parameters):
    """Main function: delete files listed in history.log from user repository."""
    _delete_files_from_history(parameters)

    templates = get_template_names(parameters)
    if not templates:
        raise ValueError('There are no templates in the package')

    if len(templates) > 1:
        template = parameters.extras.get('TEMPLATE')
        if template is None:
            raise ValueError('There are more than 1 template in the package, '
                             'specify which one you want to use with the TEMPLATE variable')
    else:
        template = templates[0]

    variables = parameters.extras.copy()
    variables.pop('TEMPLATE', None)

    # Backup pipeline_vars before create_template - never overwrite user's file
    repo_root = Path.cwd()
    pipeline_vars_paths = ['gitlab-ci/pipeline_vars.yaml', 'gitlab-ci/pipeline_vars.yml']
    pipeline_vars_backup = {}
    for f in pipeline_vars_paths:
        path = repo_root / f
        if path.exists() and path.is_file():
            pipeline_vars_backup[f] = path.read_bytes()
            print(f'\t\tFile {f} exists. Backed up for preserve')

    create_template(parameters, template, variables)

    # Restore pipeline_vars if it existed - never overwrite, keep only user's format
    if pipeline_vars_backup:
        for f in pipeline_vars_paths:
            if f in pipeline_vars_backup:
                path = repo_root / f
                content = pipeline_vars_backup[f]
                migrated = _migrate_pipeline_vars_format(content)
                if migrated != content:
                    print(f'\t\tFile {f} migrated to new format. Preserved')
                else:
                    print(f'\t\tFile {f} preserved. Skip overwrite')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(migrated)
        # Remove the other format - template creates yaml, user may have yml
        for f in pipeline_vars_paths:
            if f not in pipeline_vars_backup:
                path = repo_root / f
                if path.exists():
                    path.unlink()
                    print(f'\t\tRemoved {f} (user uses different format)')

    internal_files_to_remove = ['history.log']
    for file_name in internal_files_to_remove:
        file_path = repo_root / file_name
        if file_path.exists():
            try:
                file_path.unlink()
                print(f'\t\tRemoved internal file: {file_name}')
            except Exception as e:
                print(f'\t\tWarning: Could not remove {file_name}: {e}')
