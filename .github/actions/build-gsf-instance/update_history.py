#!/usr/bin/env python3
"""
Script to update history.log with package content for the current version.
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
            # Skip internal package files that shouldn't be in user repository
            if filename in ('history.log', 'history.yaml', '.cookiecutterignore'):
                continue
            # Include all files, including hidden ones like .gitlab-ci.yml
            file_path = Path(root) / filename
            # Get relative path from package directory
            rel_path = file_path.relative_to(package_path)
            files.append(str(rel_path))
    
    return sorted(files)


def update_history(history_path, version, package_files):
    """Update history.log by adding new files (preserving existing ones).
    Creates history.log if it doesn't exist."""
    # Ensure parent directory exists
    history_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing files if history.log exists
    existing_files = set()
    if history_path.exists():
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                existing_files = {line.strip() for line in f if line.strip()}
        except Exception as e:
            print(f"Warning: Could not read existing history.log: {e}")
    else:
        print(f"history.log not found, will create new file")
    
    # Merge existing files with current files (add new ones, keep old ones)
    current_files = set(package_files)
    all_files = existing_files | current_files
    new_files = current_files - existing_files
    
    if new_files:
        # Write merged list of files to history.log (preserving old entries)
        sorted_files = sorted(all_files)
        with open(history_path, 'w', encoding='utf-8') as f:
            for file_path in sorted_files:
                f.write(f"{file_path}\n")
        
        print(f"Updated history.log: added {len(new_files)} new files")
        print(f"New files: {sorted(new_files)}")
        print(f"Total files in history.log: {len(sorted_files)}")
    elif not history_path.exists():
        # File doesn't exist - create it with current files
        sorted_files = sorted(package_files)
        with open(history_path, 'w', encoding='utf-8') as f:
            for file_path in sorted_files:
                f.write(f"{file_path}\n")
        print(f"Created history.log with {len(sorted_files)} files")
    else:
        print(f"No new files to add to history.log (total {len(existing_files)} files)")


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

