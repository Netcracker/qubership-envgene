import os
from pathlib import Path
import yaml

TEST_DATA_DIR = Path("test_data/cucumber")

valid_template_artifact = {
    "registry": "artifactory",
    "templateRepository": "snapshotRepository",
    "artifact": {
        "group_id": "org.qubership.deploy.product",
        "artifact_id": "test-solution-structure",
        "version": "0.0.1"
    }
}

for i in [1, 2, 3, 5]:
    env_num = f"0{i}" if i != 5 else "04"
    env_dir = TEST_DATA_DIR / f"uc_aen_end_{i}_base" / "environments" / "cluster01" / f"env{env_num}" / "Inventory"
    env_file = env_dir / "env_definition.yml"
    
    if env_file.exists():
        with open(env_file, "r") as f:
            data = yaml.safe_load(f)
            
        if "envTemplate" in data:
            data["envTemplate"]["templateArtifact"] = valid_template_artifact
            
        with open(env_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        print(f"Fixed {env_file}")
