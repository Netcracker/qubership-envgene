# GitHub Folder Sync Workflow

## Overview

The `sync-github-folder.yml` workflow is a powerful tool designed to synchronize the `.github` folder across multiple branches in a repository. This workflow ensures that GitHub Actions, workflows, and other GitHub-specific configurations are consistent across all branches by copying the `.github` folder from the main branch to target branches.

## Purpose

This workflow serves several important purposes:

- **Consistency**: Ensures all branches have the same GitHub Actions workflows and configurations
- **Maintenance**: Reduces manual effort in keeping multiple branches synchronized
- **Quality Assurance**: Prevents issues caused by outdated or missing GitHub configurations
- **Automation**: Automates the process of propagating GitHub folder changes across branches

## Workflow Features

### Input Parameters

> **Important Note**: The `include_files` parameter is only used in Sync Mode. In Check Mode, this parameter is ignored and all files are analyzed for differences.

The workflow accepts the following input parameters:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `target_branches` | string | No | '' | Comma-separated list of target branches or "ALL" for all branches |
| `exclude_branch` | string | No | '' | Comma-separated list of branches to exclude from sync |
| `check_only` | choice | No | 'false' | Check mode - show differences without syncing (true/false) |
| `include_files` | string | No | '' | Specific files/folders to sync (comma-separated, e.g., "actions,workflows/perform_tests.yml"), "ALL" for all .github files, or empty (only when target_branches is empty or "ALL") |

### Modes of Operation

#### 1. Sync Mode (Default)
- **Purpose**: Actually synchronizes the `.github` folder to target branches
- **Behavior**: Creates commits and pushes changes to target branches
- **Use Case**: When you want to update branches with the latest GitHub configurations

#### 2. Check Mode
- **Purpose**: Analyzes differences without making any changes
- **Behavior**: Shows what would be changed without actually syncing
- **Use Case**: When you want to preview what changes would be made before syncing

## How It Works

### Branch Discovery
1. **Automatic Detection**: The workflow automatically discovers all remote branches (excluding main)
2. **Manual Specification**: You can specify specific branches or use "ALL" for all branches
3. **Exclusion Support**: You can exclude specific branches from the sync process

### Sync Process

#### For Existing .github Folders
1. **Timestamp Comparison**: Compares the last modification time of `.github` files between main and target branches
2. **Conditional Sync**: Only syncs if main branch has newer `.github` files
3. **File Operations**:
   - Copies `.github` folder from main branch (or specific files if `include_files` is specified in sync mode)
   - Excludes `sync-github-folder.yml` from target branches (keeps it only in main)
   - Removes workflow files that don't exist in main
   - Creates a temporary branch for changes
   - Commits and pushes changes

#### Selective File Sync
When `include_files` parameter is provided (only in Sync Mode):
- **Specific Files**: Syncs only the specified files and folders
- **Path Support**: Supports both individual files (e.g., `workflows/perform_tests.yml`) and folders (e.g., `actions`)
- **Flexible Paths**: Can specify paths with or without `.github/` prefix:
  - `actions/build-effective-set-python/action.yml` (recommended)
  - `.github/actions/build-effective-set-python/action.yml` (also supported)
- **ALL Mode**: Use `"ALL"` to sync all `.github` files (equivalent to empty `include_files` when `target_branches` is empty or "ALL")
- **Multiple Items**: Can specify multiple files/folders separated by commas
- **Recursive Copy**: When specifying a folder, all files and subfolders within it are copied

#### include_files Logic Rules
- **When `target_branches` is specified**: `include_files` is **required** in sync mode
- **When `target_branches` is empty or "ALL"**: `include_files` can be empty (syncs all files)
- **"ALL" in include_files**: Syncs all `.github` files regardless of `target_branches` value
- **Check Mode**: `include_files` is ignored (always analyzes all files)
- **Flexible Paths**: Can specify paths with or without `.github/` prefix:
  - `actions/build-effective-set-python/action.yml` (recommended)
  - `.github/actions/build-effective-set-python/action.yml` (also supported)

#### Check Mode vs Sync Mode Behavior

**Check Mode:**
- **Ignores `include_files` parameter** - always analyzes all files in `.github` folder
- **Shows complete picture** of differences between branches
- **No file filtering** - reports all missing, extra, and different files
- **Purpose**: To understand the full scope of differences before syncing

**Sync Mode:**
- **Respects `include_files` parameter** - only syncs specified files/folders
- **Selective synchronization** based on `include_files` value
- **File filtering** - only processes files specified in `include_files`
- **Purpose**: To apply specific changes to target branches

#### For Missing .github Folders
1. **Creation**: Creates the `.github` folder in target branches
2. **Initial Setup**: Copies all necessary files from main branch
3. **Cleanup**: Ensures only files that exist in main are included

### Safety Features

- **Temporary Branches**: Uses temporary branches (`sync-github-{branch}`) for changes
- **Cleanup**: Automatically removes temporary branches after sync
- **Error Handling**: Comprehensive error handling and reporting
- **Dry Run**: Check mode allows previewing changes without applying them

## Usage Examples

### Sync All Branches
```yaml
# Trigger workflow with default settings
# This will sync all branches except main
```

### Sync Specific Branches
```yaml
# Target specific branches
target_branches: "feature/new-ui, bugfix/login-issue, develop"
```

### Exclude Branches
```yaml
# Sync all branches except specific ones
target_branches: "ALL"
exclude_branch: "experimental, deprecated-feature"
```

### Check Mode (Recommended First Step)
```yaml
# Preview all differences without applying changes
check_only: "true"
target_branches: "ALL"
```

### Sync All Files
```yaml
# Sync entire .github folder (default behavior)
target_branches: "feature/new-ui, develop"
```

### Sync Specific Files
```yaml
# Sync only specific files/folders
include_files: "actions,workflows/perform_tests.yml"
target_branches: "feature/new-ui, develop"
```

### Sync Actions Folder Only
```yaml
# Sync only the actions folder
include_files: "actions"
target_branches: "ALL"
```

### Sync Multiple Specific Files
```yaml
# Sync multiple specific files and folders
include_files: "actions,workflows/perform_tests.yml,workflows/dev-build-docker-images.yml"
target_branches: "feature/bugfix, develop"
```

### Sync with Flexible Paths
```yaml
# Both formats work - with or without .github/ prefix
include_files: "actions/build-effective-set-python/action.yml,.github/workflows/perform_tests.yml"
target_branches: "feature/new-ui, develop"
```

### Sync All Files to Specific Branches
```yaml
# Sync all .github files to specific branches
include_files: "ALL"
target_branches: "feature/new-ui, develop"
```

### Sync Specific Files to All Branches
```yaml
# Sync specific files to all branches
include_files: "actions,workflows/perform_tests.yml"
target_branches: "ALL"
```

### Check Mode with Specific Branches
```yaml
# Check specific branches for differences
check_only: "true"
target_branches: "feature/new-ui, develop"
```

## Output and Reporting

### Console Output
The workflow provides detailed console output including:
- Branch processing status
- File operations performed
- Timestamps and commit information
- Error messages and warnings

### GitHub Step Summary
The workflow creates a comprehensive summary in the GitHub Actions interface:
- **Sync Mode**: Lists files updated for each branch
- **Check Mode**: Shows differences, missing files, and extra files for each branch
- **Statistics**: Provides summary statistics for processed branches

### Summary Statistics (Check Mode)
- Total branches processed
- Branches up to date
- Branches with differences
- Branches without .github folder

## File Handling

### Included Files
- All files in `.github/` directory from main branch
- Workflows, actions, and configurations
- Templates and reusable components

### Excluded Files
- `sync-github-folder.yml` (kept only in main branch)
- Workflow files that don't exist in main branch
- Files specified in exclusion patterns

### File Operations
- **Copy**: Files from main to target branches
- **Remove**: Files that shouldn't exist in target branches
- **Update**: Files with different content
- **Create**: Missing .github folders

## Best Practices

### When to Use
- After updating GitHub Actions workflows in main branch
- When creating new branches that need GitHub configurations
- During repository maintenance and cleanup
- Before major releases to ensure consistency

### When Not to Use
- During active development on target branches
- When branches have custom GitHub configurations that shouldn't be overwritten
- Immediately after creating pull requests (to avoid conflicts)

### Recommended Workflow
1. **Check Mode First**: Always run in check mode first to preview all differences
2. **Review Changes**: Examine the summary to understand the full scope of differences
3. **Plan Sync Strategy**: Decide whether to sync all files or use `include_files` for selective sync
4. **Sync Mode**: Run in sync mode to apply changes (with or without `include_files`)
5. **Verify**: Check that the changes were applied correctly

## Troubleshooting

### Common Issues

#### Branch Not Found
- **Cause**: Target branch doesn't exist
- **Solution**: Verify branch name and ensure it exists in the repository

#### Permission Errors
- **Cause**: Insufficient permissions to push to branches
- **Solution**: Ensure the workflow has write permissions to the repository

#### Merge Conflicts
- **Cause**: Target branch has conflicting changes
- **Solution**: Resolve conflicts manually or rebase the target branch

#### No Changes Applied
- **Cause**: Target branch already has up-to-date .github folder
- **Solution**: This is normal behavior - the workflow only syncs when needed

### Error Messages

#### "target_branches is required"
- **Solution**: Provide branch names or use "ALL", or enable check_only mode

#### "Branch does not exist"
- **Solution**: Verify the branch name and ensure it exists in the repository

#### "No changes to sync"
- **Solution**: This is informational - the branch is already up to date

#### "include_files is required when target_branches is specified in sync mode"
- **Cause**: You specified target branches but didn't specify which files to sync
- **Solution**: Either:
  - Specify files in `include_files` (e.g., "actions,workflows/perform_tests.yml")
  - Use "ALL" in `include_files` to sync all files
  - Use "ALL" in `target_branches` to sync all branches
  - Enable `check_only` mode to check differences without syncing

## Security Considerations

### Permissions
- **Contents**: Write permission required for pushing changes
- **Actions**: Read permission for accessing workflow information

### Authentication
- Uses `GITHUB_TOKEN` for authentication
- Runs with GitHub Actions bot identity
- Commits are made with `github-actions[bot]` user

### Safety Measures
- Uses temporary branches for changes
- Automatic cleanup of temporary branches
- Comprehensive error handling
- Check mode for previewing changes

## Integration with CI/CD

### Triggering
- **Manual**: Can be triggered manually via GitHub Actions UI
- **Scheduled**: Can be integrated into scheduled workflows
- **Event-based**: Can be triggered by specific events

### Integration Points
- **Pre-deployment**: Run before deploying to ensure consistency
- **Release preparation**: Run before creating releases
- **Branch maintenance**: Regular maintenance task

## Monitoring and Maintenance

### Monitoring
- Check workflow execution logs for errors
- Review step summaries for sync results
- Monitor branch consistency over time

### Maintenance
- Regular review of excluded branches
- Update workflow as needed for new requirements
- Monitor for new GitHub features that might affect the workflow

## Future Enhancements

### Potential Improvements
- **Selective File Sync**: Sync specific files or directories
- **Conflict Resolution**: Automatic conflict resolution strategies
- **Rollback Capability**: Ability to revert sync changes
- **Advanced Filtering**: More sophisticated branch filtering options
- **Integration APIs**: API endpoints for external triggering

### Feature Requests
- **Custom Commit Messages**: Allow custom commit message templates
- **Branch Protection**: Respect branch protection rules
- **Notification Integration**: Slack/Teams notifications for sync results
- **Audit Trail**: Detailed audit trail of sync operations 