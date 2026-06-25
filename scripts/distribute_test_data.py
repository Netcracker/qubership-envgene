import os
import re
import shutil
from pathlib import Path
import yaml

FEATURES_DIR = Path("tests/features/unified_pipeline_success")
UNIFIED_BASE_DIR = Path("test_data/cucumber/unified_base")
CUCUMBER_DIR = Path("test_data/cucumber")
TEST_DATA_DIR = Path("test_data")

MAPPED_OLD_FOLDERS = {
    "uc_aen_end_1": "aen_end_1_base",
    "uc_aen_end_2": "aen_end_2_base",
    "uc_aen_end_3": "aen_end_3_base",
    "uc_aen_end_5": "aen_end_5_base",
    "uc_ard_tr_1": "ard_base",
    "uc_ard_tr_2": "ard_tr_2_base",
    "uc_ad_sd_7": "ad_sd_7_base",
    "uc_eig_es_3": "uc_eig_es_3_base",
    "uc_cust_e2e_1": "cust_e2e_1_base",
}

def create_config_if_missing(config_dir):
    config_file = config_dir / "config.yml"
    if not config_file.exists():
        os.makedirs(config_dir, exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("placement_mode: root\ncrypt: false\n")

def process_features():
    for feature_file in FEATURES_DIR.glob("*.feature"):
        with open(feature_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        current_scenario_id = None
        new_lines = []
        for i, line in enumerate(lines):
            scenario_match = re.search(r"Scenario:\s*(UC-[a-zA-Z0-9\-]+):", line)
            if scenario_match:
                current_scenario_id = scenario_match.group(1).lower().replace("-", "_")
            
            given_match = re.search(r'Given the workspace is initialized with test data from "(.*?)"', line)
            if given_match and current_scenario_id:
                old_path = given_match.group(1)
                new_data_path = f"cucumber/{current_scenario_id}_base"
                line = line.replace(old_path, new_data_path)
            
            env_match = re.search(r'And the pipeline parameter "ENV_NAMES" is set to "(.*?)"', line)
            if env_match and current_scenario_id:
                env_names = env_match.group(1)
                scenario_base_dir = CUCUMBER_DIR / f"{current_scenario_id}_base"
                
                dev_folder_name = MAPPED_OLD_FOLDERS.get(current_scenario_id)
                dev_folder = TEST_DATA_DIR / dev_folder_name if dev_folder_name else None
                
                if dev_folder and dev_folder.exists() and not scenario_base_dir.exists():
                    shutil.copytree(dev_folder, scenario_base_dir)
                else:
                    os.makedirs(scenario_base_dir, exist_ok=True)
                    
                    if not (scenario_base_dir / "mapping.json").exists() and (UNIFIED_BASE_DIR / "mapping.json").exists():
                        shutil.copy2(UNIFIED_BASE_DIR / "mapping.json", scenario_base_dir / "mapping.json")
                    
                    for env_name in env_names.split(","):
                        env_name = env_name.strip()
                        if not env_name: continue
                        
                        dst_env_dir = scenario_base_dir / "environments" / env_name
                        if dst_env_dir.exists():
                            continue
                            
                        # First try: e2e/{scenario_id} e.g. e2e/uc-bg-2
                        dashed_scenario_id = current_scenario_id.replace("_", "-")
                        src_env_specific = TEST_DATA_DIR / "e2e" / dashed_scenario_id / "environments" / env_name
                        
                        src_env_base = TEST_DATA_DIR / "e2e/base/environments" / env_name
                        fallback = TEST_DATA_DIR / "test_environments" / env_name
                        unified_fallback = UNIFIED_BASE_DIR / "environments" / env_name
                        
                        if src_env_specific.exists():
                            os.makedirs(dst_env_dir.parent, exist_ok=True)
                            shutil.copytree(src_env_specific, dst_env_dir)
                        elif src_env_base.exists():
                            os.makedirs(dst_env_dir.parent, exist_ok=True)
                            shutil.copytree(src_env_base, dst_env_dir)
                        elif fallback.exists():
                            os.makedirs(dst_env_dir.parent, exist_ok=True)
                            shutil.copytree(fallback, dst_env_dir)
                        elif unified_fallback.exists():
                            os.makedirs(dst_env_dir.parent, exist_ok=True)
                            shutil.copytree(unified_fallback, dst_env_dir)
                
                # ALWAYS ensure configuration directory is copied from test_data/configuration if it is missing or incomplete
                conf_dir = scenario_base_dir / "configuration"
                if not conf_dir.exists():
                    os.makedirs(conf_dir, exist_ok=True)
                
                # Copy missing files from test_data/configuration
                global_conf_dir = TEST_DATA_DIR / "configuration"
                if global_conf_dir.exists():
                    for item in os.listdir(global_conf_dir):
                        src_item = global_conf_dir / item
                        dst_item = conf_dir / item
                        if not dst_item.exists():
                            if src_item.is_dir():
                                shutil.copytree(src_item, dst_item)
                            else:
                                shutil.copy2(src_item, dst_item)
                
                create_config_if_missing(conf_dir)
                
            new_lines.append(line)
            
        with open(feature_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

if __name__ == "__main__":
    process_features()
    print("Test data distribution completed.")
