#!/bin/bash
set -e
job=$1
retries=0
exit_code=0

pattern="^[A-Z]+-[0-9]+$"

echo "CI_PROJECT_DIR=${CI_PROJECT_DIR}"
echo "CI_SERVER_HOST=${CI_SERVER_HOST}"
echo "CI_PROJECT_PATH=${CI_PROJECT_PATH}"
echo "CI_COMMIT_REF_NAME=${CI_COMMIT_REF_NAME}"
echo "GITLAB_USER_EMAIL=${GITLAB_USER_EMAIL}"
echo "GITLAB_USER_LOGIN=${GITLAB_USER_LOGIN}"
echo "GITLAB_TOKEN=${GITLAB_TOKEN}"
echo "ENV_NAME=${ENV_NAME}"
echo "CLUSTER_NAME=${CLUSTER_NAME}"
echo "ENVIRONMENT_NAME=${ENVIRONMENT_NAME}"
echo "DEPLOYMENT_TICKET_ID=${DEPLOYMENT_TICKET_ID}"
echo "COMMIT_ENV=${COMMIT_ENV}"
echo "COMMIT_MESSAGE=${COMMIT_MESSAGE}"

export ticket_id=${DEPLOYMENT_TICKET_ID}

# commit message
if [ -z "${COMMIT_MESSAGE}" ]; then 
    message="${ticket_id} [ci_skip] Update \"${CLUSTER_NAME}/${ENVIRONMENT_NAME}\" environment"
else 
    message="${ticket_id} ${COMMIT_MESSAGE}"
fi
echo "Commit message is: ${message}"

# copying environments folder to temp storage
echo "Moving env environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME} artifacts to temporary location"
mkdir -p /tmp/artifact_environments
mkdir -p /tmp/artifact_environments/${CLUSTER_NAME}

if [ "${COMMIT_ENV}" = "true" ]; then
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

if [ -e gitlab-ci/prefix_build ]; then
  echo "Copy gitlab-ci"
  mkdir -p /tmp/gitlab-ci
  cp -r gitlab-ci /tmp

  echo "Copy templates"
  mkdir -p /tmp/templates
  cp -r templates /tmp
fi


# remove all contents including hidden files, it will be given from git pull
echo "Clearing contents of repository"
rm -rf ".git"
rm -rf -- ..?* .[!.]* *
# creating empty git repo
echo "Initing new repository"
git init
git config --global --add safe.directory ${CI_PROJECT_DIR}
git config --global user.email ${GITLAB_USER_EMAIL}
git config --global user.name ${GITLAB_USER_LOGIN}
git config pull.rebase true
# pulling into empty git repo
git remote add origin "${CI_SERVER_PROTOCOL}://project_22172_bot:${GITLAB_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git"
echo "Pulling contents from GIT"
git pull origin ${CI_COMMIT_REF_NAME}
# moving back environments folder and committing
echo "Moving back /tmp/artifact_environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME}"

if [ "${COMMIT_ENV}" = "true" ]; then
  rm -rf environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME}
  cp -r /tmp/artifact_environments/${CLUSTER_NAME}/${ENVIRONMENT_NAME} environments/${CLUSTER_NAME}/
fi

if [ -e /tmp/artifact_environments/${CLUSTER_NAME}/cloud-passport ]; then
  rm -rf environments/${CLUSTER_NAME}/cloud-passport
  cp -r /tmp/artifact_environments/${CLUSTER_NAME}/cloud-passport environments/${CLUSTER_NAME}/
fi

if [ -e /tmp/configuration ]; then
  echo "Moving back config folder"
  cp -r /tmp/configuration .
fi

if [ -e /tmp/gitlab-ci ]; then
  rm -rf gitlab-ci
  echo "Moving back gitlab-ci folder"
  cp -r /tmp/gitlab-ci .

  rm -rf templates
  echo "Moving back templates folder"
  cp -r /tmp/templates .
  message="${ticket_id} [ci_build_parameters] Update gitlab-ci configurations"
fi

echo "Commiting changes"
git add ./*
diff_status=0
git diff --cached --exit-code || diff_status=$?
if [ $diff_status -ne 0 ]; then 
  echo "See diff above for changed files. Committing..."
  git commit -am "${message}"
  # pushing to repo
  git push origin HEAD:${CI_COMMIT_REF_NAME} || exit_code=$?
else
  echo "We have NOTHING to commit. Skipping..."
fi

# echo "exit CODE: ${exit_code}"
if [ "$exit_code" -ne 0 ]
then
    while [ "$exit_code" -ne 0 ] && [ "$retries" -ne 10 ]
    do
        echo "fail to push, retries: $retries"
        exit_code=0
        retries=$((retries+1))
        echo "Try to pull changes"
        git pull origin ${CI_COMMIT_REF_NAME}
        echo "Try to push, retries: $retries"
        git push origin HEAD:${CI_COMMIT_REF_NAME} || exit_code=$?
        sleep 5
    done
fi

exit $exit_code
