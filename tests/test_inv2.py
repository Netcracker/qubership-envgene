import sys, json
from tests.framework.workspace import EnvGeneWorkspace
from pathlib import Path
import tempfile

d = tempfile.mkdtemp()
ws = EnvGeneWorkspace(Path(d))
ws.run_pipeline(extra_env={
    'ENV_INVENTORY_CONTENT': json.dumps({'envDefinition': {'action': 'create_or_replace', 'content': {'name': 'test'}}})
})
print(ws.stderr)
