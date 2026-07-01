import os
import glob
import re

logs_dir = r"tests/e2e-tests"
docs_dir = r"docs/use-cases"

# 1. Parse all UCs from documents
documented_ucs = {} # uc -> filename
for doc_file in glob.glob(f"{docs_dir}/**/*.md", recursive=True):
    if os.path.basename(doc_file).lower() == 'readme.md':
        continue
    with open(doc_file, 'r', encoding='utf-8') as f:
        content = f.read()
        ucs = re.findall(r'(UC-[A-Z0-9-]+)', content)
        for uc in set(ucs):
            if uc not in documented_ucs:
                documented_ucs[uc] = set()
            documented_ucs[uc].add(os.path.basename(doc_file))

# 2. Parse test execution from logs
test_results = {}
test_failures = {}

# Regex to match pytest test lines
# e.g.: tests/step_defs/test_envgene_null_value_validation.py::test_ucnvv3_all_values_resolved <- ../module/venv/lib/python3.12/site-packages/pytest_bdd/scenario.py FAILED
# e.g.: tests/step_defs/test_envgene_null_value_validation.py::test_ucnvv3_all_values_resolved PASSED
test_line_re = re.compile(r'::(test_[a-zA-Z0-9_]+)\s*(?:<-.*?)?\s+(PASSED|FAILED|SKIPPED|XFAIL|XPASS|ERROR)')
# Regex to match summary failures
# e.g.: FAILED tests/step_defs/test_envgene_null_value_validation.py::test_ucnvv3_all_values_resolved - AssertionError: ...
summary_fail_re = re.compile(r'(?:^[0-9T:.-]+Z\s+)?(FAILED|ERROR)\s+.*?::(test_[a-zA-Z0-9_]+)\s+-\s+(.*)')

for log_file in glob.glob(f"{logs_dir}/*.txt"):
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            
            # Match test execution
            if '::test_' in line:
                m = test_line_re.search(line)
                if m:
                    func_name = m.group(1)
                    status = m.group(2)
                    test_results[func_name] = status
            
            # Match failure reasons
            if line.startswith('FAILED ') or line.startswith('ERROR '):
                m = summary_fail_re.search(line)
                if m:
                    func_name = m.group(2)
                    reason = m.group(3)
                    test_failures[func_name] = reason

# 3. Map test functions to UCs
def normalize_uc(uc):
    return uc.upper().replace('-', '')

def normalize_func(func_name):
    # e.g. test_ucnvv3_all_values_resolved -> ucnvv3
    # e.g. test_uc_eig_nf_1_something -> uceignf1
    m = re.match(r'^test_([a-zA-Z0-9_]+)', func_name)
    if m:
        core = m.group(1)
        core = core.replace('_', '').upper()
        if core.startswith('UC'):
            return core
    return func_name.upper()

doc_ucs_normalized = {normalize_uc(uc): uc for uc in documented_ucs}
# some tests might not have 'UC' in name but are just test names

mapped_results = []
unmapped_results = []

for func_name, status in test_results.items():
    func_norm = normalize_func(func_name)
    # try to find a matching doc uc
    matched_uc = None
    # Sort by length descending to match more specific UCs first (e.g. UC-SD-1a before UC-SD-1)
    for norm_uc, orig_uc in sorted(doc_ucs_normalized.items(), key=lambda x: len(x[0]), reverse=True):
        pattern1 = r'^.*?' + re.escape(norm_uc) + r'(?!\d)'
        pattern2 = r'^.*?' + re.escape(norm_uc.replace('UC', '')) + r'(?!\d)'
        if re.search(pattern1, func_norm) or re.search(pattern2, func_norm):
            matched_uc = orig_uc
            break
            
    if matched_uc:
        mapped_results.append({
            'uc': matched_uc,
            'func_name': func_name,
            'status': status,
            'reason': test_failures.get(func_name, '')
        })
    else:
        unmapped_results.append({
            'func_name': func_name,
            'status': status,
            'reason': test_failures.get(func_name, '')
        })

# Create markdown report
md_path = "use_cases_report.md"
with open(md_path, 'w', encoding='utf-8') as f:
    f.write("# Use Cases Test Coverage Report\n\n")
    
    f.write("## Summary\n")
    f.write(f"- **Total Use Cases Documented:** {len(documented_ucs)}\n")
    
    mapped_uc_set = {t['uc'] for t in mapped_results}
    f.write(f"- **Total Tests Implemented:** {len(mapped_uc_set)}\n")
    
    coverage = (len(mapped_uc_set) / len(documented_ucs)) * 100 if documented_ucs else 0
    f.write(f"- **Overall Coverage:** {coverage:.1f}%\n\n")
    
    untested_ucs = sorted([uc for uc in documented_ucs if uc not in mapped_uc_set])
    
    f.write("## Missing Use Cases (Not Implemented)\n")
    if untested_ucs:
        for uc in untested_ucs:
            f.write(f"- {uc} (in {', '.join(documented_ucs[uc])})\n")
    else:
        f.write("*None!*\n")
    f.write("\n")
    
    # Group by document
    docs_to_ucs = {}
    for uc, docs in documented_ucs.items():
        for doc in docs:
            if doc not in docs_to_ucs:
                docs_to_ucs[doc] = []
            docs_to_ucs[doc].append(uc)
            
    for doc in sorted(docs_to_ucs.keys()):
        f.write(f"## Document: {doc}\n")
        for uc in sorted(docs_to_ucs[doc]):
            status_emoji = "⚠️ MISSING"
            for t in mapped_results:
                if t['uc'] == uc:
                    if t['status'] in ('PASSED', 'XPASS'):
                        status_emoji = "✅ PASSED"
                    elif t['status'] == 'XFAIL':
                        status_emoji = "⏭️ XFAIL (expected failure)"
                    elif t['status'] in ('FAILED', 'ERROR'):
                        status_emoji = f"❌ FAILED (`{t['func_name']}`)"
                    else:
                        status_emoji = f"⏸️ {t['status']}"
                    break
            f.write(f"- {uc}: {status_emoji}\n")
        f.write("\n")

print(f"Report successfully generated at {md_path}")
