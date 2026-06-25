import re

path = 'tests/features/unified_pipeline_success/auto-environment-name.feature'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('"ENV_BUILDER" is set to "true"', '"ENV_BUILDER" is set to "false"')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
