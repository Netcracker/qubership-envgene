import os
from pathlib import Path


class BaseTest:
    base_dir = Path(__file__).resolve().parents[3]
    test_data_dir = base_dir / "test_data"
    os.environ['CI_PROJECT_DIR'] = str(test_data_dir)
