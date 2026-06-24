import sys, json
from tests.framework.workspace import EnvGeneWorkspace
from pathlib import Path
import tempfile

d = tempfile.mkdtemp()
ws = EnvGeneWorkspace(Path(d))
content = {
    'envDefinition': {
        'action': 'create_or_replace',
        'content': {
            'name': 'test',
            'inventory': {},
            'envTemplate': {}
        }
    }
}
ws.run_pipeline(extra_env={
    'ENV_INVENTORY_CONTENT': json.dumps(content)
})
print(ws.stderr)
