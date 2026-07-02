import csv
import glob
import os
import re

csv_path = r"/workspace/temp_csv.md"

with open(csv_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = 0
for i, line in enumerate(lines):
    if line.startswith('Feature,Sub-feature,Test Name'):
        start_idx = i
        break

csv_lines = lines[start_idx:]
reader = csv.DictReader(csv_lines)

spreadsheet_tests = []
for row in reader:
    test_name = row.get('Test Name', '').strip()
    if test_name and test_name != 'Test Name':
        spreadsheet_tests.append({
            'Feature': row.get('Feature', '').strip(),
            'Sub-feature': row.get('Sub-feature', '').strip(),
            'Test Name': test_name,
            'UC status': row.get('UC status ', '').strip()
        })

# Find implemented
feature_files = glob.glob('/workspace/tests/features/**/*.feature', recursive=True)
implemented_scenarios = set()
for ff in feature_files:
    with open(ff, 'r', encoding='utf-8') as f:
        content = f.read()
        scenarios = re.findall(r'Scenario:\s*(.*)', content)
        for s in scenarios:
            implemented_scenarios.add(s.strip())

missing_impl = []
for t in spreadsheet_tests:
    name = t['Test Name']
    is_impl = False
    for impl in implemented_scenarios:
        if name in impl or name.split(':')[0] in impl:
            is_impl = True
            break
    if not is_impl:
        missing_impl.append(t)

# Group by Feature -> Sub-feature
grouped = {}
for t in missing_impl:
    feat = t['Feature']
    sub = t['Sub-feature']
    if not sub:
        sub = "general"
    
    if feat not in grouped:
        grouped[feat] = {}
    if sub not in grouped[feat]:
        grouped[feat][sub] = []
    grouped[feat][sub].append(t)

# Generate skeleton files
base_dir = "/workspace/tests/features/todo"
os.makedirs(base_dir, exist_ok=True)

import string

def clean_filename(name):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned = ''.join(c for c in name if c in valid_chars)
    return cleaned.replace(' ', '_').lower()

for feat, subs in grouped.items():
    feat_dir = os.path.join(base_dir, clean_filename(feat))
    os.makedirs(feat_dir, exist_ok=True)
    
    for sub, tests in subs.items():
        file_path = os.path.join(feat_dir, f"{clean_filename(sub)}.feature")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Feature: {feat} - {sub} (TODO)\n")
            f.write(f"  As a developer\n")
            f.write(f"  I want to have these scenarios implemented\n\n")
            
            for t in tests:
                f.write(f"  @todo\n")
                f.write(f"  Scenario: {t['Test Name']}\n")
                f.write(f"    Given pending implementation\n")
                f.write(f"    When pending implementation\n")
                f.write(f"    Then pending implementation\n\n")

print(f"Generated skeletons for {len(missing_impl)} tests in {base_dir}")
