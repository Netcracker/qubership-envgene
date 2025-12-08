from pathlib import Path
from git_system_follower.develop.api.types import Parameters

# Protected files that should never be deleted
PROTECTED_FILES = {'history.log', '.gitlab-ci.yml', '.gitignore'}


def _get_repository_root(parameters: Parameters):
    """Find the repository root directory."""
    repo_root = None
    
    # Try to get repository name from parameters.extras (from cookiecutter variables)
    repo_name = parameters.extras.get('gsf_repository_name')
    
    # Look for .git-system-follower/repositories directory
    current = Path.cwd()
    gsf_repos_dir = current / '.git-system-follower' / 'repositories'
    
    if gsf_repos_dir.exists() and gsf_repos_dir.is_dir():
        if repo_name:
            # Use the repository name from cookiecutter
            repo_root = gsf_repos_dir / repo_name
        else:
            # Try to find any repository directory
            repos = [d for d in gsf_repos_dir.iterdir() if d.is_dir()]
            if repos:
                # Use the first one found (most likely the one just created)
                repo_root = repos[0]
    
    # If still not found, try to get from parameters attributes
    if (repo_root is None or not repo_root.exists()) and hasattr(parameters, 'repository_path') and parameters.repository_path:
        repo_root = Path(parameters.repository_path)
    
    # Last resort: try to find repository by looking for .git directory
    if repo_root is None or not repo_root.exists():
        # Check current directory first (might be the target repository)
        if (Path.cwd() / '.git').exists():
            repo_root = Path.cwd()
        else:
            # Walk up to find .git directory
            current = Path.cwd()
            while current != current.parent:
                if (current / '.git').exists() and (current / '.git').is_dir():
                    repo_root = current
                    break
                current = current.parent
    
    if repo_root is None or not repo_root.exists():
        raise FileNotFoundError(f'Could not find remote repository. Checked parameters.repository_path and .git-system-follower/repositories')
    
    return repo_root


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
    
    repo_root = _get_repository_root(parameters)
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
