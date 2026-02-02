#!/bin/bash
set -e
job=$1
retries=0
exit_code=0

pattern="^[A-Z]+-[0-9]+$"

if [ -n "${GITHUB_ACTIONS}" ]; then
      # Logic for GitHub
      PLATFORM="github"
      SERVER_PROTOCOL="https"
      SERVER_HOST="github.com"
      PROJECT_PATH="${GITHUB_REPOSITORY}"
      REF_NAME="${GITHUB_REF_NAME}"
      USER_EMAIL="${GITHUB_USER_EMAIL}"
      USER_NAME="${GITHUB_USER_NAME}"
      TOKEN="${GITHUB_TOKEN}"
elif [ -n "${GITLAB_CI}" ]; then
      # Logic for GitLab
      PLATFORM="gitlab"
      SERVER_PROTOCOL="${CI_SERVER_PROTOCOL}"
      SERVER_HOST="${CI_SERVER_HOST}"
      PROJECT_PATH="${CI_PROJECT_PATH}"
      REF_NAME="${CI_COMMIT_REF_NAME}"
      USER_EMAIL="${GITLAB_USER_EMAIL}"
      USER_NAME="${GITLAB_USER_LOGIN}"
      TOKEN="${GITLAB_TOKEN}"
fi


echo "Platform: ${PLATFORM}"
echo "Server Protocol: ${SERVER_PROTOCOL}"
echo "Server Host: ${SERVER_HOST}"
echo "Project Path: ${PROJECT_PATH}"
echo "Branch/Ref Name: ${REF_NAME}"
echo "User Email: ${USER_EMAIL}"
echo "User Name: ${USER_NAME}"

if [ -z "${TOKEN}" ]; then
      echo "No auth token was found. Please check!"
      exit 1
fi

echo "ENV_NAME=${ENV_NAME}"
echo "CLUSTER_NAME=${CLUSTER_NAME}"
echo "ENVIRONMENT_NAME=${ENVIRONMENT_NAME}"
echo "DEPLOYMENT_TICKET_ID=${DEPLOYMENT_TICKET_ID}"
echo "COMMIT_ENV=${COMMIT_ENV}"
echo "COMMIT_MESSAGE=${COMMIT_MESSAGE}"
echo "DEPLOYMENT_SESSION_ID=${DEPLOY_SESSION_ID}"

export ticket_id=${DEPLOYMENT_TICKET_ID}

# commit message
if [ -z "${COMMIT_MESSAGE}" ]; then
      message="${ticket_id} [ci_skip] Update \"${CLUSTER_NAME}/${ENVIRONMENT_NAME}\" environment"
else
      message="${ticket_id} ${COMMIT_MESSAGE}"
fi
echo "Commit message: ${message}"



# copying environments folder to temp storage

echo "Moving env environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME} artifacts to temporary location"
mkdir -p /tmp/artifact_environments/${CLUSTER_NAME}

if [ "${COMMIT_ENV}" = "true" ] && [ -d "environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME}" ]; then
    cp -r environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME} /tmp/artifact_environments/${CLUSTER_NAME}/
fi

if [ -e environments/${CLUSTER_NAME}/cloud-passport ]; then
    cp -r environments/${CLUSTER_NAME}/cloud-passport /tmp/artifact_environments/${CLUSTER_NAME}/
fi

if [ -e configuration ]; then
    echo "Copy config folder"
    mkdir -p /tmp/configuration
    cp -r configuration /tmp
fi

if [ -e sboms ]; then
    echo "Copy sboms folder"
    mkdir -p /tmp/sboms
    cp -r sboms /tmp
fi

if [ -e gitlab-ci/prefix_build ]; then
    echo "Copy gitlab-ci"
    mkdir -p /tmp/gitlab-ci
    cp -r gitlab-ci /tmp

    echo "Copy templates"
    mkdir -p /tmp/templates
    cp -r templates /tmp
fi

echo "Saving cluster and site shared folders"
mkdir -p /tmp/artifact_shared

if [ -d environments/${CLUSTER_NAME} ]; then
    for dir in parameters credentials resource_profiles shared_template_variables; do
        SRC="environments/${CLUSTER_NAME}/$dir"
        if [ -d "$SRC" ]; then
            echo "Saving $SRC"
            mkdir -p "/tmp/artifact_shared/environments/${CLUSTER_NAME}"
            cp -r "$SRC" "/tmp/artifact_shared/environments/${CLUSTER_NAME}/"
        fi
    done
fi

if [ -d environments ]; then
    for dir in parameters credentials resource_profiles shared_template_variables; do
        SRC="environments/$dir"
        if [ -d "$SRC" ]; then
            echo "Saving $SRC"
            mkdir -p "/tmp/artifact_shared/environments"
            cp -r "$SRC" "/tmp/artifact_shared/environments/"
        fi
    done
fi

#Copying cred files modified as part of cred rotation job.
CREDS_FILE="environments/credfilestoupdate.yml"
if [ -f "$CREDS_FILE" ]; then
  echo "Processing $CREDS_FILE for copying filtered creds..."

  mkdir -p /tmp/updated_creds

  while IFS= read -r file_path; do
    echo "Credential update for $file_path"
    [[ -z "$file_path" || "$file_path" == \#* ]] && continue

    if echo "$file_path" | grep -q "${CLUSTER_NAME}/${ENVIRONMENT_NAME}/"; then
      continue
    fi

    if [ -f "$file_path" ]; then
      echo "Copying $file_path to /tmp/updated_creds/"
      target_path="/tmp/updated_creds/$file_path"
      mkdir -p "$(dirname "$target_path")"
      cp "$file_path" "$target_path"
    else
      echo "Warning: Source file does not exist: $file_path"
    fi
  done < "$CREDS_FILE"
fi

# remove all contents including hidden files, it will be given from git pull
echo "Clearing contents of repository"
rm -rf ".git"
rm -rf -- ..?* .[!.]* *


# creating empty git repo
echo "Initing new repository"
git init
git config --global --add safe.directory "$(pwd)"
git config --global user.email "${USER_EMAIL}"
git config --global user.name "${USER_NAME}"
git config pull.rebase true

# pulling into empty git repo

if [ -n "${GITHUB_ACTIONS}" ]; then
      REMOTE_URL="${SERVER_PROTOCOL}://${TOKEN}@${SERVER_HOST}/${PROJECT_PATH}.git"
elif [ -n "${GITLAB_CI}" ]; then
      REMOTE_URL="${SERVER_PROTOCOL}://project_22172_bot:${TOKEN}@${SERVER_HOST}/${PROJECT_PATH}.git"
fi

echo "Adding remote: ${REMOTE_URL}"
git remote add origin "${REMOTE_URL}"


echo "Pulling contents from GIT (branch: ${REF_NAME})"
git pull origin "${REF_NAME}"

# moving back environments folder and committing

echo "Restoring cluster and site shared folders"

for dir in parameters credentials resource_profiles shared_template_variables; do
    if [ -d /tmp/artifact_shared/environments/$dir ]; then
        rm -rf environments/$dir
        mkdir -p environments/$dir
        cp -r /tmp/artifact_shared/environments/$dir/. environments/$dir/
    fi
done

for dir in parameters credentials resource_profiles shared_template_variables; do
    if [ -d /tmp/artifact_shared/environments/${CLUSTER_NAME}/$dir ]; then
        rm -rf environments/${CLUSTER_NAME}/$dir
        mkdir -p environments/${CLUSTER_NAME}/$dir
        cp -r /tmp/artifact_shared/environments/${CLUSTER_NAME}/$dir/. environments/${CLUSTER_NAME}/$dir/
    fi
done


echo "Restoring environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME}"

if [ "${COMMIT_ENV}" = "true" ] && [ -d "/tmp/artifact_environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME}" ]; then
    rm -rf "environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME}"
    mkdir -p "environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME}"
    cp -r /tmp/artifact_environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME}/. "environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME}/"
fi

if [ -e /tmp/artifact_environments/${CLUSTER_NAME}/cloud-passport ]; then
    rm -rf environments/${CLUSTER_NAME}/cloud-passport
    mkdir -p environments/${CLUSTER_NAME}/cloud-passport
    cp -r /tmp/artifact_environments/${CLUSTER_NAME}/cloud-passport/. "environments/${CLUSTER_NAME}/cloud-passport/"
fi

if [ -e /tmp/configuration ]; then
    echo "Restoring config folder"
    cp -r /tmp/configuration .
fi

if [ -e /tmp/sboms ]; then
  echo "Restoring config folder"
  cp -r /tmp/sboms .
fi

if [ -e /tmp/gitlab-ci ]; then
    rm -rf gitlab-ci
    echo "Restoring gitlab-ci folder"
    cp -r /tmp/gitlab-ci .

    rm -rf templates
    echo "Restoring templates folder"
    cp -r /tmp/templates .
    message="${ticket_id} [ci_build_parameters] Update gitlab-ci configurations"
fi

if [ -n "${DEPLOY_SESSION_ID}" ]; then
    echo "Deployment session id is ${DEPLOY_SESSION_ID}"
    message="${message}"$'\n\n'"DEPLOYMENT-SESSION-ID: ${DEPLOY_SESSION_ID}"
    echo "Appended commit message with session id"
fi

if [ -d /tmp/updated_creds ]; then
    find /tmp/updated_creds -type f | while read tmp_file; do
      rel_path="${tmp_file#/tmp/updated_creds/}"  # Remove the /tmp path prefix
      if [ -f "$rel_path" ]; then
        echo "Copying file from $tmp_file to $rel_path"
        cp "$tmp_file" "$rel_path"
      else
        echo "Skipping: $rel_path does not exist in repo after pull"
      fi
    done
fi

echo "Checking changes..."
git add ./*
diff_status=0

git diff --cached --name-only
git diff --cached --quiet || diff_status=$?

if [ $diff_status -ne 0 ]; then
    echo "Changes detected. Committing..."
    git commit -am "${message}"

    echo "Pushing to origin HEAD:${REF_NAME}"
    echo "Current commit: $(git rev-parse HEAD)"
    echo "Remote commit: $(git rev-parse origin/${REF_NAME} 2>/dev/null || echo 'unknown')"

    # Temporarily disable exit on error for git push (we want to handle it ourselves)
    set +e
    git push origin HEAD:"${REF_NAME}"
    exit_code=$?
    set -e
else
    echo "No changes to commit. Skipping..."
fi

# Retry logic with exponential backoff and proper exit code handling
if [ "$exit_code" -ne 0 ]; then
      echo "⚠ Initial push failed with exit code: $exit_code"

      # Disable exit on error for retry loop (we want to handle errors ourselves)
      set +e

      while [ "$retries" -lt 10 ]; do
          retries=$((retries+1))

          # Exponential backoff with randomization to reduce collision probability
          # Formula: base_delay * retry_count + random(0-10)
          sleep_time=$((5 * retries + RANDOM % 10))
          echo "⚠ Push failed, retry attempt: $retries of 10"
          echo "Waiting ${sleep_time} seconds before retry..."
          sleep $sleep_time

          echo "Pulling latest changes from origin/${REF_NAME}..."
          git pull origin "${REF_NAME}"
          pull_exit_code=$?

          if [ "$pull_exit_code" -ne 0 ]; then
              echo "⚠ Pull failed with exit code: $pull_exit_code, continuing to next retry..."
              continue
          fi

          echo "Successfully pulled changes. Remote is now at: $(git rev-parse origin/${REF_NAME})"
          echo "Local HEAD is at: $(git rev-parse HEAD)"

          echo "Attempting push (retry $retries)..."
          git push origin HEAD:"${REF_NAME}"
          exit_code=$?

          if [ "$exit_code" -eq 0 ]; then
              echo "✅ Push succeeded on retry attempt $retries"
              break
          else
              echo "⚠ Push attempt $retries failed with exit code: $exit_code"
          fi
      done

      # Re-enable exit on error
      set -e

      if [ "$exit_code" -ne 0 ]; then
          echo "❌ Failed to push after $retries retry attempts"
          echo "Final exit code: $exit_code"
      fi
fi

exit $exit_code
