from envgenehelper import logger
import json
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # Adding optional argument
    parser.add_argument("-a_arg", "--artifact_dest", help = "")
    parser.add_argument("-b_arg", "--build_env_path", help = "")
    parser.add_argument("-c_arg", "--envgen_debug", help = "")
    parser.add_argument("-d_arg", "--env_name", help = "")
    parser.add_argument("-e_arg", "--base_dir", help = "")
    parser.add_argument("-f_arg", "--env_template_vers", help = "")
    parser.add_argument("-g_arg", "--envs_directory_path", help = "")
    parser.add_argument("-h_arg", "--registry_config_path", help = "")
    parser.add_argument("-i_arg", "--cred_config_path", help = "")

    # Read arguments from command line
    args = parser.parse_args()

    g_artifact_dest = args.artifact_dest
    g_build_env_path = args.build_env_path
    g_envgen_debug = args.envgen_debug
    g_env_name = args.env_name
    g_base_dir = args.base_dir
    g_env_template_vers = args.env_template_vers
    g_envs_directory_path = args.envs_directory_path
    g_registry_config_path = args.registry_config_path
    g_cred_config_path = args.cred_config_path

    env_build_params = {
      "ARTIFACT_DEST": g_artifact_dest,
      "BUILD_ENV_PATH": g_build_env_path,
      "ENVGEN_DEBUG": g_envgen_debug,
      "ENV_NAME": g_env_name,
      "BASE_DIR": g_base_dir,
      "ENV_TEMPLATE_VERSION": g_env_template_vers,
      "ENVS_DIRECTORY_PATH": g_envs_directory_path,
      "CRED_CONFIG_PATH": g_cred_config_path,
      "REGISTRY_CONFIG_PATH": g_registry_config_path
    }

    logger.info(f'env_build_vars={json.dumps(env_build_params, ensure_ascii=False, indent=2)}')
