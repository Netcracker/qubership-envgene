#!/usr/bin/env python3
"""
Script to update history.yaml with package content for the current version.
"""
import os
import sys
import yaml
from pathlib import Path


def get_package_files(package_dir):
    """Get all files in the package directory as relative paths."""
    package_path = Path(package_dir)
    if not package_path.exists():
        print(f"Warning: Package directory {package_dir} does not exist")
        return []
    
    files = []
    for root, dirs, filenames in os.walk(package_path):
        # Skip hidden directories (like .git, .github, etc.)
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in filenames:
            # Skip history.yaml itself
            if filename == 'history.yaml':
                continue
            # Include all files, including hidden ones like .gitlab-ci.yml
            file_path = Path(root) / filename
            # Get relative path from package directory
            rel_path = file_path.relative_to(package_path)
            files.append(str(rel_path))
    
    return sorted(files)


def update_history(history_path, version, package_files):
    """Update history.yaml with new version entry."""
    history = []
    
    # Read existing history if it exists
    if history_path.exists():
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = yaml.safe_load(f) or []
        except Exception as e:
            print(f"Warning: Could not read existing history.yaml: {e}")
            history = []
    
    # Remove "(current)" marker from all previous entries
    for entry in history:
        if isinstance(entry, dict) and 'version' in entry:
            version_str = str(entry['version'])
            if version_str.endswith(' (current)'):
                entry['version'] = version_str[:-10]  # Remove " (current)"
    
    # Create new entry
    new_entry = {
        'version': f"{version} (current)",
        'package_content': package_files
    }
    
    # Append new entry
    history.append(new_entry)
    
    # Write updated history
    with open(history_path, 'w', encoding='utf-8') as f:
        yaml.dump(history, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"Updated history.yaml with version {version}")
    print(f"Added {len(package_files)} files to package_content")


def get_version_from_package_yaml(package_yaml_path):
    """Read version from package.yaml file."""
    package_yaml = Path(package_yaml_path)
    if not package_yaml.exists():
        raise FileNotFoundError(f"package.yaml not found at {package_yaml_path}")
    
    try:
        with open(package_yaml, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            version = data.get('version')
            if not version:
                raise ValueError("Version field not found in package.yaml")
            return str(version)
    except Exception as e:
        raise ValueError(f"Could not read version from package.yaml: {e}")


def main():
    if len(sys.argv) < 4:
        print("Usage: update_history.py <package_dir> <package_yaml_path> <history_path>")
        sys.exit(1)
    
    package_dir = sys.argv[1]
    package_yaml_path = sys.argv[2]
    history_path = Path(sys.argv[3])
    
    # Get version from package.yaml
    try:
        version = get_version_from_package_yaml(package_yaml_path)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Get package files
    package_files = get_package_files(package_dir)
    
    # Update history
    update_history(history_path, version, package_files)


if __name__ == '__main__':
    main()

