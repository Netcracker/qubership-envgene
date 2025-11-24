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
    old_structure_data = None
    
    if structure_yaml_path.exists():
        try:
            with open(structure_yaml_path, 'r') as f:
                old_structure_data = yaml.safe_load(f)
        except Exception:
            # If we can't read the old file, continue without it
            pass
    
    # If version changed, remove files and directories from old version that are not in new version
    if old_structure_data and old_structure_data.get('version') != version:
        old_files = set(old_structure_data.get('files', []))
        old_directories = set(old_structure_data.get('directories', []))
        new_files = set(files)
        new_directories = set(directories)
        
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
    
    # Create structure data
    structure_data = {
        'version': version,
        'directories': directories,
        'files': files
    }
    
    # Write .structure.yaml to remote repository root
    with open(structure_yaml_path, 'w') as f:
        yaml.dump(structure_data, f, default_flow_style=False, sort_keys=False)

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

    CICD_VARIABLES = [
        {'name': 'DOCKER_REGISTRY', 'value': 'reg2', 'masked': False},
        {'name': 'SECRET_KEY', 'value': 'initial_value', 'masked': True},
        {'name': 'GITLAB_TOKEN', 'value': 'initial_value', 'masked': True},
        {'name': 'ENVGENE_AGE_PRIVATE_KEY', 'value': 'initial_value', 'masked': True},
        {'name': 'ENVGENE_AGE_PUBLIC_KEY', 'value': 'initial_value', 'masked': True},
        {'name': 'PUBLIC_AGE_KEYS', 'value': 'initial_value', 'masked': True},
        {'name': 'IS_OFFSITE', 'value': 'true', 'masked': False},
        {'name': 'GITLAB_RUNNER_TAG_NAME', 'value': 'initial_value', 'masked': False},
        {'name': 'RUNNER_SCRIPT_TIMEOUT', 'value': 'initial_value', 'masked': False},
    ]
    
    for var_config in CICD_VARIABLES:
        var_name = var_config['name']
        var_data = parameters.extras.get(var_name)
        
        if var_data is not None:
            if isinstance(var_data, (list, tuple)) and len(var_data) >= 2:
                value = var_data[0] if var_data[0] else var_config.get('value')
                masked_flag = var_data[1].lower() if len(var_data) > 1 else None
            elif isinstance(var_data, str):
                parts = var_data.strip().split(None, 1)
                value = parts[0] if parts else var_config.get('value')
                masked_flag = parts[1].lower() if len(parts) > 1 else None
            else:
                value = str(var_data) if var_data else var_config.get('value')
                masked_flag = None
            
            if masked_flag:
                masked_flag_lower = masked_flag.lower()
                if 'no' in masked_flag_lower and 'masked' in masked_flag_lower:
                    masked = False
                elif 'masked' in masked_flag_lower:
                    masked = True
                else:
                    masked = var_config['masked']
            else:
                masked = var_config['masked']
        else:
            value = var_config.get('value')
            masked = var_config['masked']
        
        if not value or (isinstance(value, str) and not value.strip()):
            continue
        
        create_variable(
            parameters,
            CICDVariable(
                name=var_config['name'],
                value=value,
                env='*',
                masked=masked
            ),
            is_force=True
        )
    
    # Create .structure.yaml file
    _create_structure_yaml(parameters)
