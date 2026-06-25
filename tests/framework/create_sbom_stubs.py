import os
import re
from pathlib import Path

FEATURE_DIR = Path('/workspace/tests/features/sbom_storage_migration')
TEST_DATA_DIR = Path('/workspace/test_data')
GOLDEN_DIR = Path('/workspace/test_data/golden')

def process_features():
    if not FEATURE_DIR.exists(): return
    for feature_file in FEATURE_DIR.glob('*.feature'):
        with open(feature_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        scenarios = re.split(r'\n  Scenario: ', content)
        new_content = scenarios[0]
        
        for scenario in scenarios[1:]:
            lines = scenario.split('\n')
            title = lines[0].strip()
            
            match = re.search(r'([A-Z0-9\-\.]+):', title)
            if match:
                uc_code = match.group(1).lower().replace('-', '_').replace('.', '_')
                ref_name = match.group(1).lower().replace('.', '-')
            else:
                safe_title = re.sub(r'[^a-zA-Z0-9]', '_', title).lower()[:15]
                uc_code = f"sbom_{safe_title}"
                ref_name = f"sbom-{safe_title.replace('_', '-')}"
                
            base_name = f"{uc_code}_base"
            scenario_mod = scenario.replace('"e2e/base"', f'"{base_name}"')
            
            if 'Then the orchestrator completes successfully' in scenario_mod and 'matches the reference' not in scenario_mod:
                scenario_mod = scenario_mod.replace(
                    'Then the orchestrator completes successfully',
                    f'Then the orchestrator completes successfully\n    And the environment instance "test-cluster/test-env" matches the reference "{ref_name}"'
                )
                
            new_content += '\n  Scenario: ' + scenario_mod
            
            base_dir = TEST_DATA_DIR / base_name
            golden_dir = GOLDEN_DIR / ref_name
            
            base_dir.mkdir(parents=True, exist_ok=True)
            golden_dir.mkdir(parents=True, exist_ok=True)
            
            config_dir = base_dir / 'configuration'
            config_dir.mkdir(exist_ok=True)
            (config_dir / 'config.yml').write_text("crypt: false\nplacement_mode: root\n")
            
            env_dir = base_dir / 'environments' / 'test-cluster' / 'test-env' / 'Inventory'
            env_dir.mkdir(parents=True, exist_ok=True)
            (env_dir / 'env_definition.yml').write_text('inventory:\n  tenantName: "Tenant"\n  cloudName: "test-cluster"\nenvTemplate:\n  name: "simple"\n')
            
            golden_env_dir = golden_dir / 'Inventory'
            golden_env_dir.mkdir(parents=True, exist_ok=True)
            (golden_dir / 'Inventory' / 'env_definition.yml').write_text('inventory:\n  tenantName: "Tenant"\n  cloudName: "test-cluster"\nenvTemplate:\n  name: "simple"\n')

        with open(feature_file, 'w', encoding='utf-8') as f:
            f.write(new_content)

if __name__ == '__main__':
    process_features()
    print("Done generating stubs for sbom_storage_migration.")
