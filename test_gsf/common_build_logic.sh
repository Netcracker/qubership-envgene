get_latest_version_dirname_in_path() {
  local latest_version_dir=$(ls -d *@* | sort -V | tail -n 1)
  echo $latest_version_dir
}

get_latest_package_version_path() {
  local project_path=$1

  latest_version_dir=$(get_latest_version_dirname_in_path)
  latest_version=$(echo $latest_version_dir | cut -d "@" -f2)

  echo "${project_path}/${latest_version_dir}/git-system-follower-package/scripts/${latest_version}"
}

get_latest_version_templates_path() {
  local project_path=$1 

  local latest_ver_path=$(get_latest_package_version_path $project_path)
  echo "${latest_ver_path}/templates"
}

download_docker_image() {
  local image="$1"
  local dest_dir="$2"

  docker pull "$image"

  local cid
  cid=$(docker create "$image")
  trap 'docker rm -f "$cid" >/dev/null 2>&1 || true' RETURN

  mkdir -p "$dest_dir"
  docker cp "$cid":/opt/github "$dest_dir"

  docker rm -f "$cid" >/dev/null
  trap - RETURN
}

prepare_templates_common() {
  local project_path=$1
  local has_onsite=$2

  local templates_path=$(get_latest_version_templates_path $project_path)
  echo "Preparing templates in $templates_path"

  if [ "${download_github_workflow}" == "true" ]; then
    local docker_image="artifactorycn.netcracker.com:17152/netcracker/qubership-instance-repo-pipeline:1.5.8"
    local github_dest="${templates_path}/default/{{cookiecutter.gsf_repository_name}}"

    download_docker_image "$docker_image" "$github_dest"

    cp -rf "${templates_path}/default/{{cookiecutter.gsf_repository_name}}/github/." "${templates_path}/default/{{cookiecutter.gsf_repository_name}}/.github"
    rm -rf "${templates_path}/default/{{cookiecutter.gsf_repository_name}}/github"

    workflow_file="${templates_path}/default/{{cookiecutter.gsf_repository_name}}/.github/workflows/pipeline.yml"
    append_file="${templates_path}/default/{{cookiecutter.gsf_repository_name}}/.github/to_merge_with_gh_workflow/cmdb.yml"

    { printf '\n\n'; cat "$append_file"; } >> "$workflow_file"

    cat "${templates_path}/default/{{cookiecutter.gsf_repository_name}}/.github/workflows/pipeline.yml"
  fi

  rm -rf "${templates_path}/offsite"
  cp -rf "${templates_path}/default" "${templates_path}/offsite"
  if [ "${ENVGENE_UPDATE_COOKIECUTTER_TEMPLATES}" == "true" ]; then
    sed -i 's/gsf_repository/project/g' "${templates_path}/offsite/cookiecutter.json"
    mv "${templates_path}/offsite/{{cookiecutter.gsf_repository_name}}"  "${templates_path}/offsite/{{cookiecutter.project_name}}"
  fi

  if [ "$has_onsite" != "true" ]; then
    return 0
  fi

  rm -rf "${templates_path}/onsite"
  cp -rf "${templates_path}/default" "${templates_path}/onsite"
  local start="include:"
  local end="    file: 'templates/api.yaml'"
  local replacement="  - local: envgene_module/api.yaml"
  local gitlab_ci_file="${templates_path}/onsite/{{cookiecutter.gsf_repository_name}}/.gitlab-ci.yml"
  sed -i "/$start/,/$end/{/$start/{p;};/$end/{p;d;};d;}" "$gitlab_ci_file" # remove all line after start(not included) to end(included)
  sed -i "/$start/ a $replacement" "$gitlab_ci_file"
  if [ "${ENVGENE_UPDATE_COOKIECUTTER_TEMPLATES}" == "true" ]; then
    sed -i 's/gsf_repository/project/g' "${templates_path}/onsite/cookiecutter.json"
    mv "${templates_path}/onsite/{{cookiecutter.gsf_repository_name}}"  "${templates_path}/onsite/{{cookiecutter.project_name}}"
  fi
}

build_docker_gear_for_gsf() {
  if [ "${ENVGENE_UPDATE_COOKIECUTTER_TEMPLATES}" == "true" ]; then
    echo "ENVGENE_UPDATE_COOKIECUTTER_TEMPLATES is set to 'true' skipping docker build and"
    echo "removing GSF specific parameter from templates cookiecutter.json files"
    return 0
  fi

  local project_path=$1
  local docker_tag=$2

  project_name=$(basename $project_path)
  latest_version_name=$(get_latest_version_dirname_in_path)

  package_path="${latest_version_name}/git-system-follower-package"

  echo "Starting docker build with $package_path"

  docker build -f "../Dockerfile" --build-arg PACKAGE_PATH="$package_path" -t $docker_tag .
  for id in $DOCKER_NAMES
  do
      docker tag $docker_tag $id
  done
}
