from pathlib import Path

import envgenehelper.business_helper as business_helper

business_helper.get_schema_dir = lambda: Path(__file__).resolve().parents[2] / "schemas"
