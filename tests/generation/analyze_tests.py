import csv
import glob
import os
import re

csv_path = "temp_csv.md"

with open(csv_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# find the start of the csv data
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

# Find all implemented scenarios in feature files
feature_files = glob.glob('tests/features/**/*.feature', recursive=True)
implemented_scenarios = set()
for ff in feature_files:
    with open(ff, 'r', encoding='utf-8') as f:
        content = f.read()
        scenarios = re.findall(r'Scenario:\s*(.*)', content)
        for s in scenarios:
            implemented_scenarios.add(s.strip())

# Find all documented use cases
doc_files = glob.glob('docs/use-cases/**/*.md', recursive=True)
documented_usecases = set()
for df in doc_files:
    with open(df, 'r', encoding='utf-8') as f:
        content = f.read()
        # look for headings that might be use cases
        # like "### UC-SD-1: Single SD_VERSION with `replace` mode"
        # or just extract the UC-XXX-YY part
        ucs = re.findall(r'(UC-[A-Z0-9-]+)', content)
        for uc in ucs:
            documented_usecases.add(uc)
        
        tcs = re.findall(r'(TC-[A-Z0-9-]+-[0-9]+)', content)
        for tc in tcs:
            documented_usecases.add(tc)

print(f"Total spreadsheet tests: {len(spreadsheet_tests)}")
print(f"Total implemented scenarios: {len(implemented_scenarios)}")
print(f"Total documented UCs/TCs: {len(documented_usecases)}")

missing_impl = []
missing_doc = []

for t in spreadsheet_tests:
    name = t['Test Name']
    # Check implementation
    is_impl = False
    for impl in implemented_scenarios:
        if name in impl or name.split(':')[0] in impl:
            is_impl = True
            break
    
    if not is_impl:
        missing_impl.append(t)
    
    # Check documentation
    uc_match = re.search(r'(UC-[A-Z0-9-]+|TC-[A-Z0-9-]+-[0-9]+)', name)
    is_doc = False
    if uc_match:
        uc_code = uc_match.group(1)
        if uc_code in documented_usecases:
            is_doc = True
    
    if uc_match and not is_doc:
        missing_doc.append(t)

md_path = "analysis_results.md"
with open(md_path, 'w', encoding='utf-8') as f:
    f.write("# Analysis Results: Missing Implementations and Documentation\n\n")
    
    f.write("## Summary\n")
    f.write(f"- **Total spreadsheet tests:** {len(spreadsheet_tests)}\n")
    f.write(f"- **Total implemented scenarios:** {len(implemented_scenarios)}\n")
    f.write(f"- **Total documented UCs/TCs:** {len(documented_usecases)}\n")
    f.write(f"- **Missing Implementation:** {len(missing_impl)}\n")
    f.write(f"- **Missing Documentation:** {len(missing_doc)}\n\n")

    f.write("## Missing Implementations\n")
    f.write("| Feature | Sub-feature | Test Name |\n")
    f.write("|---------|-------------|-----------|\n")
    for t in missing_impl:
        f.write(f"| {t['Feature']} | {t['Sub-feature']} | {t['Test Name']} |\n")

    f.write("\n## Missing Documentation\n")
    f.write("| Feature | Sub-feature | Test Name |\n")
    f.write("|---------|-------------|-----------|\n")
    for t in missing_doc:
        f.write(f"| {t['Feature']} | {t['Sub-feature']} | {t['Test Name']} |\n")

