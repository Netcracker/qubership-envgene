import os
import shutil
import yaml
from pathlib import Path
from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.cicd_variables import CICDVariable, create_variable
from git_system_follower.develop.api.templates import create_template, update_template, get_template_names

# Protected files that should never be deleted during package updates
PROTECTED_FILES = {'history.log'}


def _cleanup_old_package_files(parameters: Parameters, old_version_data: dict):
    """Remove files and directories from old package version that are not in new version.
    Uses old_version_data from history.log (read before template update) 
    instead of .structure.yaml to avoid storing it in the repository."""
    # Get package directory (parent of scripts directory)
    script_dir = Path(__file__).parent
    package_dir = script_dir.parent
    
    # Read package.yaml to get version
    package_yaml_path = package_dir / 'package.yaml'
    if not package_yaml_path.exists():
        raise FileNotFoundError(f'package.yaml not found at {package_yaml_path}')
    
    with open(package_yaml_path, 'r') as f:
        package_data = yaml.safe_load(f)
    
    version = package_data.get('version', 'unknown')
    
    # Find the cookiecutter template directory
    templates_dir = script_dir / 'templates' / 'default'
    cookiecutter_template_dir = templates_dir / '{{ cookiecutter.gsf_repository_name }}'
    
    if not cookiecutter_template_dir.exists():
        raise FileNotFoundError(f'Cookiecutter template directory not found at {cookiecutter_template_dir}')
    
    # Collect all files and directories from the cookiecutter template
    files = []
    directories = set()
    
    for root, dirs, filenames in os.walk(cookiecutter_template_dir):
        # Skip only .git directory, but include other hidden files/directories
        dirs[:] = [d for d in dirs if d != '.git']
        
        rel_root = Path(root).relative_to(cookiecutter_template_dir)
        
        # Skip .git directory itself
        if '.git' in rel_root.parts:
            continue
        
        # Skip protected files (they're part of the template but should never be deleted)
        # Check if any protected file is in the path or if we're at root and filename matches
        if rel_root == Path('.') and any(filename in PROTECTED_FILES for filename in filenames):
            continue
        # Check if any protected file name appears in the path parts
        if any(protected_file in str(rel_root) for protected_file in PROTECTED_FILES):
            continue
        
        # Add directories (including intermediate directories)
        if rel_root != Path('.'):
            # Add all parent directories
            parts = rel_root.parts
            for i in range(1, len(parts) + 1):
                dir_path = Path(*parts[:i])
                directories.add(str(dir_path))
        
        # Add all files (including hidden files like .gitlab-ci.yml)
        for filename in filenames:
            # Skip internal package files that shouldn't be in user repository
            if filename in PROTECTED_FILES or filename in ('history.yaml', '.cookiecutterignore'):
                continue
            file_path = rel_root / filename if rel_root != Path('.') else Path(filename)
            files.append(str(file_path))
    
    # Convert set to sorted list
    directories = sorted(list(directories))
    files.sort()
    
    # Debug: Verify .gitlab-ci.yml is in the list
    if '.gitlab-ci.yml' not in files:
        print(f'Warning: .gitlab-ci.yml not found in template files list. Files found: {files[:10]}...')
    
    # Find the remote repository path
    repo_root = _get_repository_root(parameters)
    
    # Helper function to extract clean version (remove (current) marker)
    def clean_version(version_str):
        if isinstance(version_str, str):
            return version_str.replace(' (current)', '')
        return version_str
    
    # If version changed, remove files and directories from old version that are not in new version
    if old_version_data and clean_version(old_version_data.get('version')) != version:
        # Support 'files', 'content' (old) and 'package_content' (new) for backward compatibility
        old_files = set(old_version_data.get('package_content', old_version_data.get('content', old_version_data.get('files', []))))
        # Get directories from old version if available, otherwise compute from file paths
        old_directories = set()
        if 'directories' in old_version_data:
            old_directories = set(old_version_data.get('directories', []))
        else:
            # Compute directories from file paths
            for file_path in old_files:
                file_path_obj = Path(file_path)
                if file_path_obj.parent != Path('.'):
                    # Add all parent directories
                    parts = file_path_obj.parent.parts
                    for i in range(1, len(parts) + 1):
                        dir_path = '/'.join(parts[:i])
                        old_directories.add(dir_path)
        
        new_files = set(files)
        new_directories = set(directories)
        
        # CRITICAL: Always exclude protected files from deletion - they're essential for package management
        # Remove them from both old and new file sets to ensure they're never deleted
        for protected_file in PROTECTED_FILES:
            old_files.discard(protected_file)
            new_files.discard(protected_file)
        
        # Also protect old history.yaml during migration (backward compatibility)
        old_files.discard('history.yaml')
        new_files.discard('history.yaml')
        
        # Find files to delete (in old but not in new)
        files_to_delete = old_files - new_files
        
        # Find directories to delete (in old but not in new)
        directories_to_delete = old_directories - new_directories
        
        # Delete files first
        for file_path in files_to_delete:
            # Double-check: Never delete protected files, even if they somehow got into the deletion list
            if file_path in PROTECTED_FILES or file_path == 'history.yaml':
                print(f'Warning: Skipping deletion of {file_path} (protected file)')
                continue
            
            # Never delete .gitlab-ci.yml - it's a critical CI/CD file
            if file_path == '.gitlab-ci.yml':
                print(f'Warning: Skipping deletion of {file_path} (critical CI/CD file)')
                continue
                
            file_full_path = repo_root / file_path
            if file_full_path.exists() and file_full_path.is_file():
                try:
                    file_full_path.unlink()
                    print(f'Deleted old package file: {file_path}')
                except Exception as e:
                    # Log error but continue
                    print(f'Warning: Could not delete file {file_path}: {e}')
        
        # Delete directories (in reverse order to delete nested directories first)
        # Sort directories by depth (longest paths first)
        directories_to_delete_sorted = sorted(directories_to_delete, key=lambda x: x.count('/'), reverse=True)
        
        for dir_path in directories_to_delete_sorted:
            dir_full_path = repo_root / dir_path
            if dir_full_path.exists() and dir_full_path.is_dir():
                try:
                    # Only delete directory if it's empty (after files were deleted)
                    # This ensures we don't delete directories with user-created files
                    # Also check that directory doesn't contain protected files
                    dir_contents = list(dir_full_path.iterdir())
                    if not dir_contents:
                        dir_full_path.rmdir()
                    else:
                        # Check if directory contains only protected files (shouldn't happen, but be safe)
                        non_protected = [item for item in dir_contents 
                                        if not (item.is_file() and item.name in PROTECTED_FILES)]
                        if not non_protected:
                            # Directory contains only protected files, don't delete
                            print(f'Info: Skipping deletion of directory {dir_path} (contains protected files)')
                except Exception as e:
                    # Log error but continue
                    print(f'Warning: Could not delete directory {dir_path}: {e}')

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

def main(parameters: Parameters):
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
    
    # Read history.log from installed package (not from user repository)
    # history.log is part of the package template but not copied to user repository
    script_dir = Path(__file__).parent
    package_dir = script_dir.parent
    
    # Read package.yaml to get current version
    package_yaml_path = package_dir / 'package.yaml'
    current_version = 'unknown'
    if package_yaml_path.exists():
        with open(package_yaml_path, 'r') as pf:
            package_data = yaml.safe_load(pf)
        current_version = package_data.get('version', 'unknown')
    
    # Read history.log from package template directory
    templates_dir = script_dir / 'templates' / 'default'
    cookiecutter_template_dir = templates_dir / '{{ cookiecutter.gsf_repository_name }}'
    history_log_path = cookiecutter_template_dir / 'history.log'
    
    # Fallback to old history.yaml for backward compatibility
    if not history_log_path.exists():
        history_log_path = cookiecutter_template_dir / 'history.yaml'
    
    old_version_data = None
    
    if history_log_path.exists():
        try:
            with open(history_log_path, 'r') as f:
                history_data = yaml.safe_load(f)
                
                # Helper function to extract clean version (remove (current) marker)
                def clean_version(version_str):
                    if isinstance(version_str, str):
                        return version_str.replace(' (current)', '')
                    return version_str
                
                # Find the last version entry that is not the current version
                # This will be the previous installed version
                if isinstance(history_data, list) and len(history_data) > 0:
                    for entry in reversed(history_data):
                        if isinstance(entry, dict) and 'version' in entry:
                            entry_version = clean_version(entry.get('version'))
                            if entry_version != current_version:
                                old_version_data = entry
                                break
        except Exception as e:
            # If we can't read the file, continue without it
            print(f'Warning: Could not read history.log from package: {e}')
    
    # Now update the template (this will also update history.log)
    if parameters.used_template:
        update_template(parameters, variables, is_force=True)
    else:
        create_template(parameters, template, variables)
    
    # Remove internal package files that shouldn't be in user repository
    # These files are part of the package but should not be copied to user repo
    repo_root = _get_repository_root(parameters)
    internal_files_to_remove = ['history.log', 'history.yaml', '.cookiecutterignore']
    
    for file_name in internal_files_to_remove:
        file_path = repo_root / file_name
        if file_path.exists():
            try:
                file_path.unlink()
                print(f'Removed internal package file: {file_name}')
            except Exception as e:
                print(f'Warning: Could not remove {file_name}: {e}')
    
    # Clean up old package files using the old version data we read earlier
    if old_version_data:
        _cleanup_old_package_files(parameters, old_version_data)
