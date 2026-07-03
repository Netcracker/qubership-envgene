from pathlib import Path

import envgenehelper.business_helper as business_helper


def _test_get_schema_dir(level=3):
    return Path(business_helper.__file__).resolve().parents[level] / "schemas"


business_helper.get_schema_dir = _test_get_schema_dir
