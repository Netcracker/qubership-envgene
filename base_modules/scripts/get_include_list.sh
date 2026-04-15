#!/bin/bash

CI_FILE="$1"

include_list=$(shyaml get-value include <"${CI_FILE}" 2>/dev/null || true)
if [[ "$include_list" != "" ]]; then
      include_list_length=$(($(shyaml get-value include <"${CI_FILE}" | shyaml get-length) - 1))
      for i in $(seq 0 $include_list_length); do
          include_project=$(shyaml get-value include."$i" <"${CI_FILE}" 2>/dev/null | shyaml get-value project 2>/dev/null || true)
          if [[ "$include_project" != "" ]]; then
              include_project_full_path=$(shyaml get-value include."$i" <"${CI_FILE}" | shyaml get-value project)
              include_project_branch=$(shyaml get-value include."$i" <"${CI_FILE}" | shyaml get-value ref)
              include_project_file=$(shyaml get-value include."$i" <"${CI_FILE}" | shyaml get-value file)

              include_project_group=${include_project_full_path%/*}
              include_project_repo=${include_project_full_path##*/}

              if [[ "$include_project_file" == *"api.yaml"* || "$include_project_file" == *"pipeline.yaml"* ]]; then
                  module_project_path_result=$(env | grep "${include_project_full_path}") || true
                  IFS='=' read -r -a module_project_path_array <<<"$module_project_path_result"
                  module_project_path=${module_project_path_array[0]}

                  module_project=${include_project_repo}
                  module_group=${include_project_group}
                  module_full_path=${include_project_full_path}
                  module_version=${include_project_branch}
                  module_name=${module_project_path//_project_path/}

                  # if <module_name>_project_path not specifed
                  : "${module_name:=$module_project}"

                  cat <<YAML
- name: ${module_name}
      project: ${module_project}
      group: ${module_group}
      full_path: ${module_full_path}
      version: ${module_version}
YAML
              else
                  echo "Included file is not a module or pipeline template ($include_project_file)" >/dev/stderr
              fi
          else
              unsupported_type=$(shyaml get-value include."$i" <"${CI_FILE}" 2>/dev/null || true)
              echo "Included file of unsupported type (${unsupported_type}). Only inlude:file is supported now" >/dev/stderr
          fi
      done
else
      echo "Nothing to include. Check that your ci file contains include section" >/dev/stderr
fi
