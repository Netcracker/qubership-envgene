import os
import re
import shutil
from pathlib import Path

FEATURES_DIR = Path("tests/features/unified_pipeline_success")
CUCUMBER_DIR = Path("test_data/cucumber")
TEST_DATA_DIR = Path("test_data")

def clean_cucumber_dir():
    if CUCUMBER_DIR.exists():
        for item in os.listdir(CUCUMBER_DIR):
            if item != "unified_base":
                path = CUCUMBER_DIR / item
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    os.remove(path)

def process_features():
    clean_cucumber_dir()
    os.makedirs(CUCUMBER_DIR, exist_ok=True)
    
    for feature_file in FEATURES_DIR.glob("*.feature"):
        with open(feature_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        new_lines = []
        current_scenario_id = None
        
        for line in lines:
            scenario_match = re.search(r"Scenario:\s*(UC-[a-zA-Z0-9\-]+):", line)
            if scenario_match:
                current_scenario_id = scenario_match.group(1).lower().replace("-", "_")
                
            init_match = re.search(r'(.*Given the workspace is initialized with test data from ")([^"]+)(".*)', line)
            if init_match and current_scenario_id:
                prefix = init_match.group(1)
                original_path = init_match.group(2)
                suffix = init_match.group(3)
                
                # Copy data from original_path to cucumber/uc_{id}_base
                scenario_base_dir = CUCUMBER_DIR / f"{current_scenario_id}_base"
                src_dir = TEST_DATA_DIR / original_path
                
                if src_dir.exists():
                    # Check if it has an environments/ folder or is just a flat directory
                    # We usually copy the entire directory
                    if not scenario_base_dir.exists():
                        shutil.copytree(src_dir, scenario_base_dir)
                        
                    # Copy configuration if missing
                    conf_dir = scenario_base_dir / "configuration"
                    os.makedirs(conf_dir, exist_ok=True)
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
                else:
                    print(f"WARNING: Source dir {src_dir} does not exist for {current_scenario_id}")
                
                # Rewrite line
                line = f'{prefix}cucumber/{current_scenario_id}_base{suffix}\n'
                
            new_lines.append(line)
            
        with open(feature_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
if __name__ == "__main__":
    process_features()
    print("Test data distribution completed.")
