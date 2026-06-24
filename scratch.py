import subprocess
import os
import sys

env = os.environ.copy()
env['PYTHONPATH'] = "f:/project/qubership-envgene;f:/project/qubership-envgene/python/envgene;f:/project/qubership-envgene/python/artifact-searcher;f:/project/qubership-envgene/python/integration;f:/project/qubership-envgene/python/jschon-sort;f:/project/qubership-envgene/scripts"

res = subprocess.run([sys.executable, "-m", "pytest", "scripts/tests/env-build/test_render_envs.py", "-v"], env=env, cwd="f:/project/qubership-envgene", capture_output=True, text=True)
print(res.stdout)
print(res.stderr)
