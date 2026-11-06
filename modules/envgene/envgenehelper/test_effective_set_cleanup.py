from pathlib import Path

import pytest

from envgenehelper.effective_set_cleanup import clean_namespaces


@pytest.mark.unit
def test_cleanup_rejects_invalid_namespace_mapping(tmp_path: Path) -> None:
    effective_set = tmp_path / "effective-set"
    deployment = effective_set / "deployment"
    deployment.mkdir(parents=True)
    (deployment / "mapping.yaml").write_text("env-core: /deployment/..\n")
    preserved = effective_set / "preserved.yaml"
    preserved.write_text("keep: value\n")

    with pytest.raises(ValueError, match="env-core"):
        clean_namespaces(effective_set, "env-core")

    assert preserved.read_text() == "keep: value\n"
