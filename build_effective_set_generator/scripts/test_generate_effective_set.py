import filecmp
import pytest
from main import generate_effective_set_for_env
from envgenehelper import *

test_data = [
      ("etbss-ocp-mdc-09", "cse-toolset", "")
    , ("etbss-sb-ocp-01", "pl01", "")
    , ("etbss-sb-ocp-01", "platform-with-overrides", "")
    , ("cloud-with-passport-override", "cse-toolset", "")
]

g_inventory_dir = getAbsPath("../../test_data/test_environments")
g_source_dir = getAbsPath("../../test_data/test_effective_set")
g_test_dir = getAbsPath("../../tmp/test_effective_set")
delete_dir(g_test_dir)

@pytest.fixture(autouse=True)
def change_test_dir(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname+"/../..")

def fill_creds(env_dir): 
    cred_file_name = f"{env_dir}/Credentials/credentials.yml"
    if check_file_exists(cred_file_name):
      logger.info(f'File with creds exists: {cred_file_name}. Filling cred values.')
      contents = openFileAsString(cred_file_name)
      writeToFile(cred_file_name, contents.replace(" null ", " test_cred_val "))

@pytest.mark.parametrize("cluster_name, env_name, sd_version", test_data)
def test_render_envs(cluster_name, env_name, sd_version):
    copy_path(g_inventory_dir, g_test_dir)
    source_dir = f"{g_source_dir}/{cluster_name}/{env_name}"
    generated_dir = f"{g_test_dir}/{cluster_name}/{env_name}"
    fill_creds(generated_dir)
    generate_effective_set_for_env(cluster_name, env_name, g_test_dir)
    files_to_compare = get_all_files_in_dir(source_dir, source_dir+"/")
    logger.info(dump_as_yaml_format(files_to_compare))
    match, mismatch, errors = filecmp.cmpfiles(source_dir , generated_dir, files_to_compare, shallow=False)
    logger.info(f"Match: {dump_as_yaml_format(match)}")
    if len(mismatch) > 0:
        logger.error(f"Mismatch: {dump_as_yaml_format(mismatch)}")
    else:
        logger.info(f"Mismatch: {dump_as_yaml_format(mismatch)}")
    if len(errors) > 0:
        logger.fatal(f"Errors: {dump_as_yaml_format(errors)}")
    else:
        logger.info(f"Errors: {dump_as_yaml_format(errors)}")
    assert len(mismatch) == 0, f"Files from source and rendering result mismatch: {dump_as_yaml_format(mismatch)}"
    assert len(errors) == 0, f"Error during comparing source and rendering result: {dump_as_yaml_format(errors)}"