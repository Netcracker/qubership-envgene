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
    """Update history.log with new version entry only if file list changed.
    Creates history.log if it doesn't exist."""
    history = []
    
    # Ensure parent directory exists
    history_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing history if it exists
    if history_path.exists():
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = yaml.safe_load(f) or []
        except Exception as e:
            print(f"Warning: Could not read existing history.log: {e}")
            history = []
    else:
        # File doesn't exist - will create it with first entry
        print(f"history.log not found, will create new file with version {version}")
    
    # Helper function to extract clean version (remove (current) marker)
    def clean_version(version_str):
        if isinstance(version_str, str):
            return version_str.replace(' (current)', '')
        return version_str
    
    # Check if there's a delta (change in file list)
    has_delta = True
    last_entry = None
    
    if history:
        # Find the last entry (current or most recent)
        for entry in reversed(history):
            if isinstance(entry, dict) and 'version' in entry:
                last_entry = entry
                break
        
        if last_entry:
            # Get file list from last entry
            last_files = set(last_entry.get('package_content', last_entry.get('content', last_entry.get('files', []))))
            current_files = set(package_files)
            
            # Check if file lists are the same
            if last_files == current_files:
                has_delta = False
                print(f"No changes in package content for version {version}, skipping history update")
            else:
                # Show what changed
                added = current_files - last_files
                removed = last_files - current_files
                if added:
                    print(f"Files added: {sorted(added)}")
                if removed:
                    print(f"Files removed: {sorted(removed)}")
    
    # Only update history if there's a delta or if this is the first entry
    if has_delta:
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
        
        # Write updated history with separators between versions
        with open(history_path, 'w', encoding='utf-8') as f:
            for i, entry in enumerate(history):
                # Add separator before each version (except the first one)
                if i > 0:
                    f.write('\n')
                
                # Write version entry with separator
                clean_ver = clean_version(entry.get('version', ''))
                f.write(f"# --- Version {clean_ver} ---\n")
                # Write entry in YAML format
                f.write(f"- version: {entry.get('version')}\n")
                f.write("  package_content:\n")
                for file_path in entry.get('package_content', []):
                    f.write(f"  - {file_path}\n")
        
        print(f"Updated history.log with version {version}")
        print(f"Added {len(package_files)} files to package_content")
    else:
        # No delta in files - check if version changed
        if last_entry:
            last_version = clean_version(last_entry.get('version'))
            if last_version != version:
                # Version changed but files didn't - update version marker in last entry
                last_entry['version'] = f"{version} (current)"
                # Remove "(current)" from other entries
                for entry in history:
                    if entry != last_entry and isinstance(entry, dict) and 'version' in entry:
                        version_str = str(entry['version'])
                        if version_str.endswith(' (current)'):
                            entry['version'] = version_str[:-10]
                
                # Write updated history with new version marker and separators
                with open(history_path, 'w', encoding='utf-8') as f:
                    for i, entry in enumerate(history):
                        # Add separator before each version (except the first one)
                        if i > 0:
                            f.write('\n')
                        
                        # Write version entry with separator
                        clean_ver = clean_version(entry.get('version', ''))
                        f.write(f"# --- Version {clean_ver} ---\n")
                        # Write entry without list brackets
                        f.write(f"- version: {entry.get('version')}\n")
                        f.write("  package_content:\n")
                        for file_path in entry.get('package_content', []):
                            f.write(f"  - {file_path}\n")
                
                print(f"Updated version marker to {version} in history.log (no content changes)")
            else:
                # Neither version nor files changed - no update needed
                print(f"Version {version} already in history.log with same content, no update needed")


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

