#!/bin/bash
set -e
trap 'echo "Error occurred at line $LINENO"' ERR

TARGET_BRANCHES="$1"
EXCLUDE_BRANCHES="$2"
CHECK_ONLY="$3"
INCLUDE_FILES="$4"

# Check if target_branches is provided (only fail if not in check_only mode)
if [ -z "$TARGET_BRANCHES" ]; then
  if [ "$CHECK_ONLY" = "true" ]; then
    echo "⚠️  Warning: target_branches is empty, but check_only mode is enabled. Using all branches except main."
    TARGET_BRANCHES="$5"  # All branches from step output
  else
    echo "❌ Error: target_branches is required. Please provide branch names or 'ALL', or enable check_only mode."
    echo "## ❌ Workflow Error" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "**Error:** target_branches is required. Please provide branch names or 'ALL', or enable check_only mode." >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "**Solution:** Please either:" >> $GITHUB_STEP_SUMMARY
    echo "- Specify target branches in the workflow input" >> $GITHUB_STEP_SUMMARY
    echo "- Use 'ALL' to process all branches" >> $GITHUB_STEP_SUMMARY
    echo "- Enable check_only mode to check all branches without syncing" >> $GITHUB_STEP_SUMMARY
    exit 1
  fi
fi

# Check include_files logic
if [ -n "$TARGET_BRANCHES" ] && [ -z "$INCLUDE_FILES" ] && [ "$CHECK_ONLY" = "false" ]; then
  echo "❌ Error: include_files is required when target_branches is specified in sync mode."
  echo "## ❌ Workflow Error" >> $GITHUB_STEP_SUMMARY
  echo "" >> $GITHUB_STEP_SUMMARY
  echo "**Error:** include_files is required when target_branches is specified in sync mode." >> $GITHUB_STEP_SUMMARY
  echo "" >> $GITHUB_STEP_SUMMARY
  echo "**Solution:** Please either:" >> $GITHUB_STEP_SUMMARY
  echo "- Specify files to sync in include_files (e.g., 'actions,workflows/perform_tests.yml')" >> $GITHUB_STEP_SUMMARY
  echo "- Use 'ALL' in include_files to sync all .github files" >> $GITHUB_STEP_SUMMARY
  echo "- Use 'ALL' in target_branches to sync all branches" >> $GITHUB_STEP_SUMMARY
  echo "- Enable check_only mode to check differences without syncing" >> $GITHUB_STEP_SUMMARY
  exit 1
fi

# Convert comma-separated string to array
IFS=',' read -ra BRANCH_ARRAY <<< "$TARGET_BRANCHES"
IFS=',' read -ra EXCLUDE_ARRAY <<< "$EXCLUDE_BRANCHES"

# Create a filtered array excluding specified branches
FILTERED_BRANCHES=()
for branch in "${BRANCH_ARRAY[@]}"; do
  branch=$(echo "$branch" | xargs)  # Trim whitespace
  if [ -n "$branch" ]; then
    # Check if branch should be excluded
    EXCLUDED=false
    for exclude_branch in "${EXCLUDE_ARRAY[@]}"; do
      exclude_branch=$(echo "$exclude_branch" | xargs)  # Trim whitespace
      if [ "$branch" = "$exclude_branch" ]; then
        EXCLUDED=true
        break
      fi
    done
    
    if [ "$EXCLUDED" = false ]; then
      FILTERED_BRANCHES+=("$branch")
    else
      echo "🚫 Excluding branch: $branch"
    fi
  fi
done

echo "=========================================="
echo "Starting process for ${#FILTERED_BRANCHES[@]} branch(es)"
echo "Check only mode: $CHECK_ONLY"
echo "Excluded branches: $EXCLUDE_BRANCHES"
echo "=========================================="

for branch in "${FILTERED_BRANCHES[@]}"; do
  echo ""
  echo "=========================================="
  if [ "$CHECK_ONLY" = "true" ]; then
    echo "🔍 Checking branch: $branch"
  else
    echo "🔄 Processing branch: $branch"
  fi
  echo "=========================================="
  
  # Check if branch exists
  if git ls-remote --heads origin "$branch" | grep -q "$branch"; then
    echo "✅ Branch $branch exists"
    
    # Get the latest commit hash for main branch
    MAIN_COMMIT=$(git rev-parse origin/main)
    echo "📋 Main branch commit: ${MAIN_COMMIT:0:8}"
    
    # Get the latest commit hash for target branch
    TARGET_COMMIT=$(git rev-parse "origin/$branch")
    echo "📋 Target branch commit: ${TARGET_COMMIT:0:8}"
    
    # Check if .github folder exists in target branch
    if git ls-tree -r --name-only "origin/$branch" | grep -q "^\.github/"; then
      echo "📁 .github folder exists in $branch"
      
      # Get the latest modification time of .github files in main
      MAIN_GITHUB_TIME=$(git log --format="%ct" --max-count=1 -- .github/ | head -1)
      
      # Get the latest modification time of .github files in target branch
      TARGET_GITHUB_TIME=$(git log --format="%ct" --max-count=1 "origin/$branch" -- .github/ | head -1)
      
      # Convert timestamps to readable format
      MAIN_GITHUB_DATE=$(date -d "@$MAIN_GITHUB_TIME" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "Unknown")
      TARGET_GITHUB_DATE=$(date -d "@$TARGET_GITHUB_TIME" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "Unknown")
      
      echo "🕐 Main .github last modified: $MAIN_GITHUB_DATE (timestamp: $MAIN_GITHUB_TIME)"
      echo "🕐 Target .github last modified: $TARGET_GITHUB_DATE (timestamp: $TARGET_GITHUB_TIME)"
      
      # Check if we should sync or just show differences
      if [ "$CHECK_ONLY" = "true" ]; then
        echo "🔍 Check mode - analyzing differences for $branch..."
        
        # Get list of .github files in main (excluding sync-github-folder.yml)
        echo "📋 Analyzing .github files in main branch..."
        MAIN_GITHUB_FILES=$(git ls-tree -r --name-only origin/main | grep "^\.github/" | grep -v "sync-github-folder.yml" | sort)
        
        # Get list of .github files in target branch
        echo "📋 Analyzing .github files in $branch branch..."
        TARGET_GITHUB_FILES=$(git ls-tree -r --name-only "origin/$branch" | grep "^\.github/" | sort)
        
        # Find files that exist in main but not in target
        MISSING_FILES=$(comm -23 <(echo "$MAIN_GITHUB_FILES") <(echo "$TARGET_GITHUB_FILES") 2>/dev/null || echo "")
        
        # Find files that exist in target but not in main
        EXTRA_FILES=$(comm -13 <(echo "$MAIN_GITHUB_FILES") <(echo "$TARGET_GITHUB_FILES") 2>/dev/null || echo "")
        
        # Check for content differences in common files
        DIFFERENT_FILES=""
        COMMON_FILES=$(comm -12 <(echo "$MAIN_GITHUB_FILES") <(echo "$TARGET_GITHUB_FILES") 2>/dev/null || echo "")
        for file in $COMMON_FILES; do
          if [ -n "$file" ] && ! git diff --quiet "origin/main:$file" "origin/$branch:$file" 2>/dev/null; then
            DIFFERENT_FILES="$DIFFERENT_FILES $file"
          fi
        done
        
        # Report findings
        if [ -z "$MISSING_FILES" ] && [ -z "$EXTRA_FILES" ] && [ -z "$DIFFERENT_FILES" ]; then
          echo "✅ Branch $branch is up to date with main"
        else
          if [ -n "$MISSING_FILES" ]; then
            echo "📄 Files missing in $branch (would be added):"
            echo "$MISSING_FILES" | sed 's/^/   - /'
          fi
          
          if [ -n "$EXTRA_FILES" ]; then
            echo "📄 Files in $branch not in main (would be removed):"
            echo "$EXTRA_FILES" | sed 's/^/   - /'
          fi
          
          if [ -n "$DIFFERENT_FILES" ]; then
            echo "📄 Files with different content in $branch:"
            echo "$DIFFERENT_FILES" | sed 's/^/   - /'
          fi
        fi
        
      else
        # Normal sync mode
        if [ -z "$TARGET_GITHUB_TIME" ] || [ "$MAIN_GITHUB_TIME" -gt "$TARGET_GITHUB_TIME" ]; then
          echo "🔄 Syncing .github folder to $branch..."
          
          # Create a new branch from target branch
          echo "📝 Creating temporary branch sync-github-$branch"
          git checkout -b "sync-github-$branch" "origin/$branch"
          
          # Copy .github folder from main (excluding sync-github-folder.yml)
          echo "📋 Copying .github folder from main (excluding sync-github-folder.yml)"
          if [ -n "$INCLUDE_FILES" ]; then
            if [ "$INCLUDE_FILES" = "ALL" ]; then
              echo "📋 Copying all .github files (ALL mode)"
              git checkout origin/main -- .github/
            else
              echo "📋 Copying specific files: $INCLUDE_FILES"
              # Convert comma-separated string to array and copy each file/folder
              IFS=',' read -ra FILES_ARRAY <<< "$INCLUDE_FILES"
              for file_item in "${FILES_ARRAY[@]}"; do
                file_item=$(echo "$file_item" | xargs)  # Trim whitespace
                if [ -n "$file_item" ]; then
                  # Remove .github/ prefix if present to normalize the path
                  NORMALIZED_PATH=$(echo "$file_item" | sed 's|^\.github/||')
                  echo "📄 Copying: .github/$NORMALIZED_PATH"
                  git checkout origin/main -- ".github/$NORMALIZED_PATH"
                fi
              done
            fi
          else
            # Copy entire .github folder
            git checkout origin/main -- .github/
          fi
          
          # Remove sync-github-folder.yml if it exists in target branch
          if [ -f ".github/workflows/sync-github-folder.yml" ]; then
            echo "🗑️  Removing sync-github-folder.yml from target branch"
            git rm -f .github/workflows/sync-github-folder.yml
          fi
          
          # Remove workflow files that don't exist in main
          echo "🧹 Cleaning up workflow files not present in main..."
          for workflow_file in .github/workflows/*.yml .github/workflows/*.yaml; do
            if [ -f "$workflow_file" ]; then
              workflow_name=$(basename "$workflow_file")
              if ! git ls-tree -r --name-only origin/main | grep -q "^\.github/workflows/$workflow_name$"; then
                echo "🗑️  Removing workflow not in main: $workflow_name"
                git rm -f "$workflow_file"
              fi
            fi
          done
          
          # Check if there are any changes
          if git diff --staged --quiet; then
            echo "ℹ️  No changes to sync for $branch"
            git checkout main
            git branch -D "sync-github-$branch"
            echo "🧹 Cleaned up temporary branch"
          else
            # Show what files will be changed
            echo "📄 Files to be updated:"
            git diff --staged --name-only | sed 's/^/   - /'
            
            # Store files for summary
            UPDATED_FILES=$(git diff --staged --name-only)
            
            # Commit and push changes
            echo "💾 Committing changes..."
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git commit -m "ci: sync .github folder from main branch"
            
            # Push to target branch
            echo "🚀 Pushing changes to $branch..."
            git push origin "sync-github-$branch:$branch"
            
            # Cleanup
            git checkout main
            git branch -D "sync-github-$branch"
            
            echo "✅ Successfully synced .github folder to $branch"
            
            # Add to summary
            echo "---" >> $GITHUB_STEP_SUMMARY
            echo "#### $branch" >> $GITHUB_STEP_SUMMARY
            echo "**Files updated:** $(echo "$UPDATED_FILES" | wc -l 2>/dev/null || echo "0")" >> $GITHUB_STEP_SUMMARY
            echo "$UPDATED_FILES" | sed 's/^/- /' >> $GITHUB_STEP_SUMMARY
            echo "---" >> $GITHUB_STEP_SUMMARY
            echo "" >> $GITHUB_STEP_SUMMARY
          fi
        else
          echo "⏭️  Skipping $branch - target branch .github files are newer or same age"
          echo "   Main: $MAIN_GITHUB_DATE"
          echo "   Target: $TARGET_GITHUB_DATE"
        fi
      fi
    else
      echo "📁 .github folder doesn't exist in $branch"
      
      if [ "$CHECK_ONLY" = "true" ]; then
        echo "🔍 Check mode - .github folder doesn't exist in $branch"
        echo "📄 Files that would be added from main:"
        git ls-tree -r --name-only origin/main | grep "^\.github/" | grep -v "sync-github-folder.yml" | sed 's/^/   - /'
      else
        echo "📁 Creating .github folder in $branch..."
        
        # Create a new branch from target branch
        echo "📝 Creating temporary branch sync-github-$branch"
        git checkout -b "sync-github-$branch" "origin/$branch"
        
        # Copy .github folder from main (excluding sync-github-folder.yml)
        echo "📋 Copying .github folder from main (excluding sync-github-folder.yml)"
        if [ -n "$INCLUDE_FILES" ]; then
          if [ "$INCLUDE_FILES" = "ALL" ]; then
            echo "📋 Copying all .github files (ALL mode)"
            git checkout origin/main -- .github/
          else
            echo "📋 Copying specific files: $INCLUDE_FILES"
            # Convert comma-separated string to array and copy each file/folder
            IFS=',' read -ra FILES_ARRAY <<< "$INCLUDE_FILES"
            for file_item in "${FILES_ARRAY[@]}"; do
              file_item=$(echo "$file_item" | xargs)  # Trim whitespace
              if [ -n "$file_item" ]; then
                # Remove .github/ prefix if present to normalize the path
                NORMALIZED_PATH=$(echo "$file_item" | sed 's|^\.github/||')
                echo "📄 Copying: .github/$NORMALIZED_PATH"
                git checkout origin/main -- ".github/$NORMALIZED_PATH"
              fi
            done
          fi
        else
          # Copy entire .github folder
          git checkout origin/main -- .github/
        fi
        
        # Remove sync-github-folder.yml if it exists in target branch
        if [ -f ".github/workflows/sync-github-folder.yml" ]; then
          echo "🗑️  Removing sync-github-folder.yml from target branch"
          git rm -f .github/workflows/sync-github-folder.yml
        fi
        
        # Remove workflow files that don't exist in main
        echo "🧹 Cleaning up workflow files not present in main..."
        for workflow_file in .github/workflows/*.yml .github/workflows/*.yaml; do
          if [ -f "$workflow_file" ]; then
            workflow_name=$(basename "$workflow_file")
            if ! git ls-tree -r --name-only origin/main | grep -q "^\.github/workflows/$workflow_name$"; then
              echo "🗑️  Removing workflow not in main: $workflow_name"
              git rm -f "$workflow_file"
            fi
          fi
        done
        
        # Show what files will be added
        echo "📄 Files to be added:"
        git diff --staged --name-only | sed 's/^/   - /'
        
        # Store files for summary
        ADDED_FILES=$(git diff --staged --name-only)
        
        # Commit and push changes
        echo "💾 Committing changes..."
        git config user.name "github-actions[bot]"
        git config user.email "github-actions[bot]@users.noreply.github.com"
        git commit -m "ci: add .github folder from main branch"
        
        # Push to target branch
        echo "🚀 Pushing changes to $branch..."
        git push origin "sync-github-$branch:$branch"
        
        # Cleanup
        git checkout main
        git branch -D "sync-github-$branch"
        
        echo "✅ Successfully created .github folder in $branch"
        
        # Add to summary
        echo "---" >> $GITHUB_STEP_SUMMARY
        echo "#### $branch" >> $GITHUB_STEP_SUMMARY
        echo "**Files added:** $(echo "$ADDED_FILES" | wc -l 2>/dev/null || echo "0")" >> $GITHUB_STEP_SUMMARY
        echo "$ADDED_FILES" | sed 's/^/- /' >> $GITHUB_STEP_SUMMARY
        echo "---" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
      fi
    fi
  else
    echo "❌ Branch $branch does not exist, skipping..."
  fi
  
  echo "=========================================="
  if [ "$CHECK_ONLY" = "true" ]; then
    echo "Finished checking branch: $branch"
  else
    echo "Finished processing branch: $branch"
  fi
  echo "=========================================="
done

echo ""
echo "=========================================="
if [ "$CHECK_ONLY" = "true" ]; then
  echo "🎉 Check process completed!"
  
  # Create summary for check mode
  echo "## 📊 GitHub Folder Sync Check Summary" >> $GITHUB_STEP_SUMMARY
  echo "" >> $GITHUB_STEP_SUMMARY
  echo "**Mode:** Check Only (No changes made)" >> $GITHUB_STEP_SUMMARY
  echo "**Branches processed:** ${#FILTERED_BRANCHES[@]}" >> $GITHUB_STEP_SUMMARY
  if [ -n "$EXCLUDE_BRANCHES" ]; then
    echo "**Excluded branches:** $EXCLUDE_BRANCHES" >> $GITHUB_STEP_SUMMARY
  fi
  echo "" >> $GITHUB_STEP_SUMMARY
  
  # Initialize summary variables
  TOTAL_BRANCHES=${#FILTERED_BRANCHES[@]}
  UP_TO_DATE_BRANCHES=0
  BRANCHES_WITH_DIFFERENCES=0
  BRANCHES_WITHOUT_GITHUB=0
  
  # Process each branch for summary
  for branch in "${FILTERED_BRANCHES[@]}"; do
    if git ls-remote --heads origin "$branch" | grep -q "$branch"; then
      if git ls-tree -r --name-only "origin/$branch" | grep -q "^\.github/"; then
        # Get list of .github files in main (excluding sync-github-folder.yml)
        MAIN_GITHUB_FILES=$(git ls-tree -r --name-only origin/main | grep "^\.github/" | grep -v "sync-github-folder.yml" | sort)
        
        # Get list of .github files in target branch
        TARGET_GITHUB_FILES=$(git ls-tree -r --name-only "origin/$branch" | grep "^\.github/" | sort)
        
        # Find differences
        MISSING_FILES=$(comm -23 <(echo "$MAIN_GITHUB_FILES") <(echo "$TARGET_GITHUB_FILES") 2>/dev/null || echo "")
        EXTRA_FILES=$(comm -13 <(echo "$MAIN_GITHUB_FILES") <(echo "$TARGET_GITHUB_FILES") 2>/dev/null || echo "")
        
        # Check for content differences in common files
        DIFFERENT_FILES=""
        COMMON_FILES=$(comm -12 <(echo "$MAIN_GITHUB_FILES") <(echo "$TARGET_GITHUB_FILES") 2>/dev/null || echo "")
        
        for file in $COMMON_FILES; do
          if [ -n "$file" ] && ! git diff --quiet "origin/main:$file" "origin/$branch:$file" 2>/dev/null; then
            DIFFERENT_FILES="$DIFFERENT_FILES $file"
          fi
        done
        
        # Add to summary
        if [ -z "$MISSING_FILES" ] && [ -z "$EXTRA_FILES" ] && [ -z "$DIFFERENT_FILES" ]; then
          UP_TO_DATE_BRANCHES=$((UP_TO_DATE_BRANCHES + 1))
        else
          # Новое форматирование: блок ветки с разделителями
          echo "---" >> $GITHUB_STEP_SUMMARY
          echo "#### $branch" >> $GITHUB_STEP_SUMMARY
          
          if [ -n "$MISSING_FILES" ]; then
            MISSING_COUNT=$(echo "$MISSING_FILES" | wc -l 2>/dev/null || echo "0")
            echo "Missing files: $MISSING_COUNT" >> $GITHUB_STEP_SUMMARY
            echo "$MISSING_FILES" | sed 's/^/- /' >> $GITHUB_STEP_SUMMARY
            echo "" >> $GITHUB_STEP_SUMMARY
          fi
          
          if [ -n "$EXTRA_FILES" ]; then
            EXTRA_COUNT=$(echo "$EXTRA_FILES" | wc -l 2>/dev/null || echo "0")
            echo "Extra files: $EXTRA_COUNT" >> $GITHUB_STEP_SUMMARY
            echo "$EXTRA_FILES" | while read -r file; do
              if [ "$file" = ".github/workflows/sync-github-folder.yml" ]; then
                echo "- $file - should exist only in MAIN" >> $GITHUB_STEP_SUMMARY
              else
                echo "- $file" >> $GITHUB_STEP_SUMMARY
              fi
            done
            echo "" >> $GITHUB_STEP_SUMMARY
          fi
          
          if [ -n "$DIFFERENT_FILES" ]; then
            DIFFERENT_COUNT=$(echo "$DIFFERENT_FILES" | wc -w 2>/dev/null || echo "0")
            echo "Files with differences: $DIFFERENT_COUNT" >> $GITHUB_STEP_SUMMARY
            echo "$DIFFERENT_FILES" | tr ' ' '\n' | sed 's/^/- /' >> $GITHUB_STEP_SUMMARY
            echo "" >> $GITHUB_STEP_SUMMARY
          fi
          
          echo "---" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          BRANCHES_WITH_DIFFERENCES=$((BRANCHES_WITH_DIFFERENCES + 1))
        fi
      else
        # Форматирование для веток без .github
        echo "---" >> $GITHUB_STEP_SUMMARY
        echo "#### $branch" >> $GITHUB_STEP_SUMMARY
        echo "**No .github folder**" >> $GITHUB_STEP_SUMMARY
        echo "---" >> $GITHUB_STEP_SUMMARY
        echo "" >> $GITHUB_STEP_SUMMARY
        BRANCHES_WITHOUT_GITHUB=$((BRANCHES_WITHOUT_GITHUB + 1))
      fi
    fi
  done
  
  echo "" >> $GITHUB_STEP_SUMMARY
  echo "### 📈 Summary Statistics" >> $GITHUB_STEP_SUMMARY
  echo "- **Total branches:** $TOTAL_BRANCHES" >> $GITHUB_STEP_SUMMARY
  echo "- **Up to date:** $UP_TO_DATE_BRANCHES" >> $GITHUB_STEP_SUMMARY
  echo "- **With differences:** $BRANCHES_WITH_DIFFERENCES" >> $GITHUB_STEP_SUMMARY
  echo "- **Without .github folder:** $BRANCHES_WITHOUT_GITHUB" >> $GITHUB_STEP_SUMMARY
  echo "" >> $GITHUB_STEP_SUMMARY
  echo "### 📋 Branches with Differences" >> $GITHUB_STEP_SUMMARY
  echo "Only branches with differences are shown in the summary above."
  
else
  echo "🎉 Sync process completed!"
  
  # Create summary for sync mode
  echo "## 🔄 GitHub Folder Sync Summary" >> $GITHUB_STEP_SUMMARY
  echo "" >> $GITHUB_STEP_SUMMARY
  echo "**Mode:** Sync (Changes applied)" >> $GITHUB_STEP_SUMMARY
  echo "**Branches processed:** ${#FILTERED_BRANCHES[@]}" >> $GITHUB_STEP_SUMMARY
  if [ -n "$EXCLUDE_BRANCHES" ]; then
    echo "**Excluded branches:** $EXCLUDE_BRANCHES" >> $GITHUB_STEP_SUMMARY
  fi
  echo "" >> $GITHUB_STEP_SUMMARY
  echo "> Note: Detailed sync results are shown in the logs above." >> $GITHUB_STEP_SUMMARY
fi
echo "=========================================="
