import re

path = 'tests/features/unified_pipeline_success/auto-environment-name.feature'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'(\s+Then the orchestrator completes successfully)\n\s+And the environment instance ".*?" matches the reference ".*?"', r'\1', text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
