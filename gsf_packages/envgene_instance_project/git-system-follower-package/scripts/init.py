from pathlib import Path
from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.templates import create_template, get_template_names

# Protected files that should never be deleted
PROTECTED_FILES = {'history.log', '.gitlab-ci.yml', '.gitignore'}


def _delete_files_from_history(parameters: Parameters):
    """Delete files listed in history.log from the user repository."""
    script_dir = Path(__file__).parent
    templates_dir = script_dir / 'templates' / 'default'
    cookiecutter_template_dir = templates_dir / '{{ cookiecutter.gsf_repository_name }}'
    history_log_path = cookiecutter_template_dir / 'history.log'
    
    if not history_log_path.exists():
        print(f'Warning: history.log not found at {history_log_path}')
        return
    
    # Read files from history.log
    try:
        with open(history_log_path, 'r', encoding='utf-8') as f:
            files_to_delete = {line.strip() for line in f if line.strip()}
    except Exception as e:
        print(f'Warning: Could not read history.log: {e}')
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
                print(f'Deleted file: {file_path_str}')
            except Exception as e:
                print(f'Warning: Could not delete file {file_path_str}: {e}')
    
    # Delete empty directories
    for dir_path in sorted(directories_to_check, key=lambda p: len(p.parts), reverse=True):
        dir_full_path = repo_root / dir_path
        if dir_full_path.exists() and dir_full_path.is_dir():
            try:
                if not any(dir_full_path.iterdir()):
                    dir_full_path.rmdir()
                    print(f'Deleted empty directory: {dir_path}')
            except Exception:
                pass
    
    if deleted_count > 0:
        print(f'Deleted {deleted_count} file(s) from repository')


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
    create_template(parameters, template, variables)

    # Use current working directory as repository root
    repo_root = Path.cwd()
    internal_files_to_remove = ['history.log', '.cookiecutterignore']
    
    for file_name in internal_files_to_remove:
        file_path = repo_root / file_name
        if file_path.exists():
            try:
                file_path.unlink()
                print(f'Removed internal package file: {file_name}')
            except Exception as e:
                print(f'Warning: Could not remove {file_name}: {e}')
