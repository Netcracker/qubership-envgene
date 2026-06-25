import re

file_path = r"tests\features\unified_pipeline_success\credential-rotation.feature"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace namespace in ALL escaped JSON strings
content = content.replace(r'\"namespace\": \"test-cluster/test-env\"', r'\"namespace\": \"test-env-namespace\"')

# For all scenarios where CRED_ROTATION_FORCE is false, change `Then the orchestrator completes successfully` to `fails`
def replace_completes_to_fails(match):
    scenario_block = match.group(0)
    if 'set to "false"' in scenario_block or 'CRED_ROTATION_FORCE' not in scenario_block:
        return scenario_block.replace('completes successfully', 'fails')
    return scenario_block

content = re.sub(r'Scenario:.*?(?=Scenario:|$)', replace_completes_to_fails, content, flags=re.DOTALL)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
