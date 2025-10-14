# Sync .github Folder Workflow

This workflow synchronizes the contents of the `.github` folder between repository branches, taking into account file modification dates and providing flexible control over what gets synchronized.

## Description

The `sync-github-folder.yml` workflow is designed for:

- Manual synchronization of the `.github` folder from the `main` branch to specified target branches
- Protection against overwriting newer changes in target branches based on file timestamps
- Selective file synchronization with granular control over which files to sync
- Check-only mode for analyzing differences without making changes
- Branch exclusion capabilities to skip specific branches
- Maintaining consistency of GitHub Actions configurations, linters, and other settings

## Triggers

The workflow runs **only manually** through GitHub Actions UI with configurable parameters. It does not run automatically on pushes to any branch.

## Manual Run Parameters

When running the workflow manually, you can specify:

- `check_only` - Check mode to show differences without syncing (options: `false`, `true`, default: `false`)
- `target_branches` - Target branches to sync (comma-separated) or "ALL" for all branches (default: empty)
- `exclude_branch` - Branches to exclude from sync (comma-separated, default: empty)
- `include_files` - Specific files/folders to sync (comma-separated, e.g., "actions,workflows/perform_tests.yml"), "ALL" for all .github files, or empty (only when target_branches is empty or "ALL")

## Workflow Logic

1. **Get branch list**: Retrieves all remote branches, excluding `main`
2. **Parse parameters**: Processes target branches, exclusions, and file filters
3. **Branch filtering**: Applies exclusion rules to create a filtered list of branches to process
4. **For each target branch**:
   - **Existence check**: Verifies the branch exists in the remote repository
   - **Check .github folder**: Determines if `.github` folder exists in the target branch
   - **Timestamp comparison**: Compares last modification dates of `.github` files:
     - If files in `main` are newer → proceed with sync
     - If files in target branch are newer → skip (protection against overwriting)
     - If `.github` folder doesn't exist → create it
   - **File synchronization**:
     - **Check mode**: Analyzes and reports differences without making changes
     - **Sync mode**: Creates temporary branch, copies files, commits, and pushes changes
   - **Cleanup**: Removes temporary branches and cleans up workflow files not present in main
5. **Summary generation**: Creates detailed summary of all operations performed

## Key Features

### Check Mode
- **Purpose**: Analyze differences between branches without making any changes
- **Usage**: Set `check_only: true` to enable
- **Output**: Detailed report showing missing files, extra files, and content differences
- **Benefits**: Safe way to preview what would be synchronized

### Selective File Synchronization
- **Granular control**: Sync specific files or folders instead of entire `.github` directory
- **File patterns**: Use comma-separated paths like `"actions,workflows/perform_tests.yml"`
- **ALL mode**: Use `"ALL"` to sync all `.github` files
- **Flexible**: Different file sets can be synced to different branches

### Branch Exclusion
- **Selective processing**: Exclude specific branches from synchronization
- **Pattern matching**: Use comma-separated branch names
- **Use cases**: Skip experimental branches, feature branches, or branches with custom configurations

### Smart Timestamp Protection
- **Automatic detection**: Compares file modification timestamps between branches
- **Overwrite protection**: Never overwrites newer changes in target branches
- **Safety first**: Ensures no work is lost during synchronization

### Comprehensive Reporting
- **Detailed logs**: Step-by-step progress for each branch
- **Summary statistics**: Count of branches processed, updated, skipped
- **File listings**: Complete list of files added, updated, or removed
- **GitHub integration**: Results displayed in GitHub Actions summary

## Security

- The workflow does not overwrite newer changes in target branches
- Uses temporary branches for synchronization
- Automatically cleans up temporary branches after completion
- Requires write permissions to the repository

## Usage Examples

### Check Mode - Analyze Differences

```bash
# Check all branches for differences without syncing
check_only: true
target_branches: ALL
exclude_branch: 
include_files: 
```

### Sync Specific Branches with All Files

```bash
# Synchronize all .github files to specific branches
check_only: false
target_branches: develop,feature/new-ui
exclude_branch: 
include_files: ALL
```

### Sync Specific Files to All Branches

```bash
# Sync only specific files to all branches except main
check_only: false
target_branches: ALL
exclude_branch: experimental,test-branch
include_files: workflows/super-linter.yaml,actions
```

### Sync Specific Files to Specific Branches

```bash
# Sync only linter configuration to production branches
check_only: false
target_branches: production,staging
exclude_branch: 
include_files: workflows/super-linter.yaml,.github/super-linter.env
```

### Check Mode with File Filtering

```bash
# Check differences for specific files only
check_only: true
target_branches: develop,feature/auth
exclude_branch: 
include_files: workflows,actions
```

## Monitoring

The workflow provides comprehensive monitoring and reporting:

### Real-time Logs
- **Branch discovery**: Lists all available branches and filtering results
- **Per-branch progress**: Detailed status for each branch being processed
- **Timestamp analysis**: Shows file modification dates and comparison results
- **File operations**: Lists files being added, updated, or removed
- **Error handling**: Clear error messages with suggested solutions

### GitHub Actions Summary
- **Check mode**: Statistics on branches analyzed, differences found, files affected
- **Sync mode**: Summary of branches updated, files synchronized, operations completed
- **Branch details**: Per-branch breakdown of changes made
- **Statistics**: Count of branches processed, up-to-date, with differences, without .github folder

### Error Reporting
- **Validation errors**: Clear messages when required parameters are missing
- **Branch errors**: Notifications when target branches don't exist
- **Permission errors**: Warnings when write access is insufficient

## Requirements

- **Write permissions** to the repository (contents: write, actions: read)
- **Main branch** must contain the current version of the `.github` folder
- **Target branches** must exist in the remote repository
- **GitHub Actions** must be enabled for the repository
- **Sufficient storage** for temporary branch operations
