set -e

if [[ $env_name == *"/"* ]]; then
  arr=(${env_name//// })
  cloud_name=${arr[0]}
  env=${arr[-1]}
  env_kubeconfig=${CI_PROJECT_DIR}/environments/${cloud_name}/${env}/kubeconfig
  cloud_kubeconfig=${CI_PROJECT_DIR}/environments/${cloud_name}/kubeconfig
  template_path=${CI_PROJECT_DIR}/environments/${cloud_name}/${env}/cloud_template
  template_env_path=${CI_PROJECT_DIR}/environments/${cloud_name}/${env}/template_${env}
else
  env=${env_name}
  env_kubeconfig=${CI_PROJECT_DIR}/environments/${env}/kubeconfig
  template_path=${CI_PROJECT_DIR}/environments/${env}/cloud_template
  template_env_path=${CI_PROJECT_DIR}/environments/${env}/template_${env}
  ls ${CI_PROJECT_DIR}/environments/${env}
fi

if [[ -s "${template_env_path}.yaml" ]]; then
  echo "Found template for ${env}.yaml"
elif [[ -s "${template_env_path}.yml" ]]; then
  echo "Found template for ${env}.yml"
  mv ${template_env_path}.yml ${template_env_path}.yaml
elif [[ -s "${template_path}.yml" ]]; then
  echo "Found template for ${env}"
  mv ${template_path}.yml ${template_env_path}.yaml
elif [[ -s "${template_path}.yaml" ]]; then
  echo "Found template for ${env}"
  mv ${template_path}.yaml ${template_env_path}.yaml
else
  echo "template for ${env} not found in any of the paths: ${template_path}, ${template_env_path}"
  exit 1
fi

echo "Run 'cloud_passport_cli'"
if [[ -s "${env_kubeconfig}" ]]; then
  echo "Found kubeconfig ${env_kubeconfig}"
  cloud_passport_cli create \
    --config "${env_kubeconfig}" \
    --source-template "${CI_PROJECT_DIR}/${discovery_source_template}" \
    --dst-dir "${CI_PROJECT_DIR}/${discovery_dst_dir}" \
    --instance "${env}" \
    --secret-key "${SECRET_KEY}"

elif [[ -s "${cloud_kubeconfig}" ]]; then
  echo "Found kubeconfig ${cloud_kubeconfig}"
  cloud_passport_cli create \
    --config "${cloud_kubeconfig}" \
    --source-template "${CI_PROJECT_DIR}/${discovery_source_template}" \
    --dst-dir "${CI_PROJECT_DIR}/${discovery_dst_dir}" \
    --instance "${env}" \
    --secret-key "${SECRET_KEY}"
else

### Discovery host
  if [[ ! -z "${!k8s_host_name}" ]]; then
    echo "Found k8s_host_name $k8s_host_name"
    echo "${!k8s_host_name}"
    export k8s_host=${!k8s_host_name}
  elif [[ ! -z "$K8S_HOST" ]]; then
    echo "Not found K8S_HOST specified either via k8s_host_name variable, K8S_HOST will be used"
    echo "$K8S_HOST"
    export k8s_host=$K8S_HOST
  else
    echo "K8S_HOST not found"
    exit 1
  fi
  export discovery_host=$k8s_host

  ### k8s token
  if [[ ! -z "${!k8s_token_name}" ]]; then
    echo "Found k8s_token $k8s_token_name"
    export k8s_token=${!k8s_token_name}
  elif [[ ! -z "$K8S_TOKEN" ]]; then
    echo "Not found K8S_TOKEN specified either via k8s_token_name variable, K8S_TOKEN will be used"
    export k8s_token=${K8S_TOKEN}
  else
    echo "K8S_TOKEN not found"
    exit 1
  fi
  export discovery_api_token=$k8s_token

  ### discovery secret key
  if [[ ! -z "${!secret_key_name}" ]]; then
    echo "Found secret_key $secret_key_name"
    export secret_key=${!secret_key_name}
  elif [[ ! -z "$SECRET_KEY" ]]; then
    echo "Not found SECRET_KEY specified either via secret_key_name variable, SECRET_KEY will be used"
    export secret_key=${SECRET_KEY}
  else
    echo "SECRET_KEY not found"
    exit 1
  fi
  export discovery_secret_key=$secret_key

  echo "discovery_host: ${discovery_host}"
  echo "discovery_token_prefix: ${discovery_token_prefix}"
  echo "discovery_source_template: ${discovery_source_template}"
  echo "discovery_dst_dir: ${discovery_dst_dir}"
  echo "discovery_instance: ${discovery_instance}"

  echo "kube config (${file_path}) not found or file is empty. Trying to use environment vars for connection to k8s"
  cloud_passport_cli create \
    --api-token  "${discovery_api_token}" \
    --token-prefix "${discovery_token_prefix}" \
    --host "${discovery_host}" \
    --verify-ssl "${discovery_verify_ssl}" \
    --source-template "${CI_PROJECT_DIR}/${discovery_source_template}" \
    --dst-dir "${CI_PROJECT_DIR}/${discovery_dst_dir}" \
    --instance "${discovery_instance}" \
    --secret-key "${discovery_secret_key}"
fi
