import os
import shutil
import yaml
from pathlib import Path
from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.cicd_variables import CICDVariable, create_variable
from git_system_follower.develop.api.templates import create_template, update_template, get_template_names


def _create_structure_yaml(parameters: Parameters):
    """Create .structure.yaml file with package version and list of files/directories created by the cookiecutter template."""
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
        
        # Add directories (including intermediate directories)
        if rel_root != Path('.'):
            # Add all parent directories
            parts = rel_root.parts
            for i in range(1, len(parts) + 1):
                dir_path = Path(*parts[:i])
                directories.add(str(dir_path))
        
        # Add all files (including hidden files like .gitlab-ci.yml)
        for filename in filenames:
            file_path = rel_root / filename if rel_root != Path('.') else Path(filename)
            files.append(str(file_path))
    
    # Convert set to sorted list
    directories = sorted(list(directories))
    files.sort()
    
    # Find the remote repository path to write .structure.yaml
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
    
    # Read existing .structure.yaml if it exists to compare versions
    structure_yaml_path = repo_root / '.structure.yaml'
    versions_list = []
    last_version_data = None
    last_version_directories = None
    
    if structure_yaml_path.exists():
        try:
            with open(structure_yaml_path, 'r') as f:
                existing_data = yaml.safe_load(f)
                
                # Helper function to extract clean version (remove (current) marker)
                def clean_version(version_str):
                    if isinstance(version_str, str):
                        return version_str.replace(' (current)', '')
                    return version_str
                
                # Check if it's old format (single version) or new format (list of versions)
                if existing_data and 'version' in existing_data:
                    # Old format - convert to new format
                    # Support 'files', 'content' (old) and 'package_content' (new) for backward compatibility
                    content_list = existing_data.get('package_content', existing_data.get('content', existing_data.get('files', [])))
                    version_str = existing_data['version']
                    old_version_entry = {
                        'version': clean_version(version_str),
                        'package_content': content_list
                    }
                    versions_list = [old_version_entry]
                    # Extract directories if they exist in old format for deletion logic
                    if 'directories' in existing_data:
                        last_version_directories = existing_data.get('directories', [])
                elif isinstance(existing_data, list):
                    # New format - list of versions, remove directories from each entry
                    versions_list = []
                    for entry in existing_data:
                        # Support 'files', 'content' (old) and 'package_content' (new) for backward compatibility
                        content_list = entry.get('package_content', entry.get('content', entry.get('files', [])))
                        version_str = entry.get('version')
                        version_entry = {
                            'version': clean_version(version_str),
                            'package_content': content_list
                        }
                        versions_list.append(version_entry)
                    # Extract directories from last version if they exist (for backward compatibility)
                    if existing_data and len(existing_data) > 0:
                        last_entry = existing_data[-1]
                        if 'directories' in last_entry:
                            last_version_directories = last_entry.get('directories', [])
                elif isinstance(existing_data, dict) and 'versions' in existing_data:
                    # Alternative format with 'versions' key
                    versions_list = []
                    for entry in existing_data['versions']:
                        # Support 'files', 'content' (old) and 'package_content' (new) for backward compatibility
                        content_list = entry.get('package_content', entry.get('content', entry.get('files', [])))
                        version_str = entry.get('version')
                        version_entry = {
                            'version': clean_version(version_str),
                            'package_content': content_list
                        }
                        versions_list.append(version_entry)
                
                # Get last version data for comparison
                if versions_list:
                    last_version_data = versions_list[-1]
                    # Add directories to last_version_data if we extracted them
                    if last_version_directories is not None:
                        last_version_data['directories'] = last_version_directories
        except Exception:
            # If we can't read the old file, continue without it
            pass
    
    # If version changed, remove files and directories from old version that are not in new version
    if last_version_data and last_version_data.get('version') != version:
        # Support 'files', 'content' (old) and 'package_content' (new) for backward compatibility
        old_files = set(last_version_data.get('package_content', last_version_data.get('content', last_version_data.get('files', []))))
        # Get directories from old version if available, otherwise compute from file paths
        old_directories = set()
        if 'directories' in last_version_data:
            old_directories = set(last_version_data.get('directories', []))
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
        
        # Exclude .structure.yaml from deletion
        old_files.discard('.structure.yaml')
        
        # Find files to delete (in old but not in new)
        files_to_delete = old_files - new_files
        
        # Find directories to delete (in old but not in new)
        directories_to_delete = old_directories - new_directories
        
        # Delete files first
        for file_path in files_to_delete:
            file_full_path = repo_root / file_path
            if file_full_path.exists() and file_full_path.is_file():
                try:
                    file_full_path.unlink()
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
                    if not any(dir_full_path.iterdir()):
                        dir_full_path.rmdir()
                except Exception as e:
                    # Log error but continue
                    print(f'Warning: Could not delete directory {dir_path}: {e}')
    
    # Add new version to the list (or create new list if first time)
    # Save only version and package_content, NOT directories
    new_version_data = {
        'version': version,
        'package_content': files
    }
    
    # Check if this version already exists in the list
    version_exists = any(v.get('version') == version for v in versions_list)
    
    if version_exists:
        # Update existing version entry
        for i, v in enumerate(versions_list):
            if v.get('version') == version:
                versions_list[i] = new_version_data
                break
    else:
        # Add new version to the list
        versions_list.append(new_version_data)
    
    # Remove 'current' marker from all versions, then add it to the last one
    for v in versions_list:
        v.pop('current', None)
        # Also clean up version string if it has (current) marker
        if isinstance(v.get('version'), str) and ' (current)' in v['version']:
            v['version'] = v['version'].replace(' (current)', '')
    
    # Mark the last version as current
    if versions_list:
        versions_list[-1]['version'] = f"{versions_list[-1]['version']} (current)"
    
    # Write .structure.yaml to remote repository root (without directories)
    with open(structure_yaml_path, 'w') as f:
        yaml.dump(versions_list, f, default_flow_style=False, sort_keys=False)

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
    
    if parameters.used_template:
        update_template(parameters, variables, is_force=True)
    else:
        create_template(parameters, template, variables)
    
    # Create .structure.yaml file
    _create_structure_yaml(parameters)
