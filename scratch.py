import re
from pathlib import Path

feature_file = Path("tests/features/unified_pipeline_success/calculator-cli.feature")
content = feature_file.read_text(encoding='utf-8')
matches = re.findall(r'matches the reference "(.*)"', content)

for m in matches:
    print(f"Parsed string from feature file: {repr(m)}")
