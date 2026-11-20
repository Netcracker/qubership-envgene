import os
from unittest.mock import MagicMock

import pytest

import envgene_shared.crypto.sops_handler as sops_handler
from envgene_shared.crypto.sops_handler import DCL2ARGO_AGE_PUBLIC_KEY_PARAM, \
    merge_pipeline_age_key_into_public_keys

PUBLIC_AGE_KEYS_ID = "PUBLIC_AGE_KEYS"
AGE_KEY = "age1newkeyfrompipelinecontext0000000000000000000000000000000000000"
EXISTING_KEY = "age1existingkey00000000000000000000000000000000000000000000"


@pytest.fixture(autouse=True)
def _restore_sops_global():
    original = sops_handler.PUBLIC_AGE_KEYS
    yield
    sops_handler.PUBLIC_AGE_KEYS = original


def write_pipeline_params(es_dir, params: dict):
    (es_dir / "pipeline").mkdir(parents=True, exist_ok=True)
    content = "\n".join(f"{key}: {value}" for key, value in params.items())
    (es_dir / "pipeline" / "parameters.yaml").write_text(content)


class TestMergePipelineAgeKey:
    @pytest.mark.unit
    def test_skips_when_crypt_disabled(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sops_handler, "get_crypt", lambda: False)
        es_dir = tmp_path / "effective-set"
        write_pipeline_params(es_dir, {DCL2ARGO_AGE_PUBLIC_KEY_PARAM: AGE_KEY, "DCL_GIT_BRANCH": "master"})
        monkeypatch.setenv(PUBLIC_AGE_KEYS_ID, EXISTING_KEY)

        merge_pipeline_age_key_into_public_keys(es_dir)

        assert os.environ[PUBLIC_AGE_KEYS_ID] == EXISTING_KEY

    @pytest.mark.unit
    def test_warns_when_pipeline_context_missing(self, tmp_path, monkeypatch):
        logger = MagicMock()
        monkeypatch.setattr(sops_handler, "logger", logger)
        es_dir = tmp_path / "effective-set"
        es_dir.mkdir()
        monkeypatch.setenv(PUBLIC_AGE_KEYS_ID, EXISTING_KEY)

        merge_pipeline_age_key_into_public_keys(es_dir)

        logger.warning.assert_called_once()
        assert os.environ[PUBLIC_AGE_KEYS_ID] == EXISTING_KEY

    @pytest.mark.unit
    def test_warns_when_key_missing_from_pipeline_context(self, tmp_path, monkeypatch):
        logger = MagicMock()
        monkeypatch.setattr(sops_handler, "logger", logger)
        es_dir = tmp_path / "effective-set"
        write_pipeline_params(es_dir, {"DCL_GIT_BRANCH": "master"})
        monkeypatch.setenv(PUBLIC_AGE_KEYS_ID, EXISTING_KEY)

        merge_pipeline_age_key_into_public_keys(es_dir)

        logger.warning.assert_called_once()
        assert os.environ[PUBLIC_AGE_KEYS_ID] == EXISTING_KEY

    @pytest.mark.unit
    def test_appends_key_to_existing_public_age_keys(self, tmp_path, monkeypatch):
        es_dir = tmp_path / "effective-set"
        write_pipeline_params(es_dir, {DCL2ARGO_AGE_PUBLIC_KEY_PARAM: AGE_KEY})
        monkeypatch.setenv(PUBLIC_AGE_KEYS_ID, EXISTING_KEY)

        merge_pipeline_age_key_into_public_keys(es_dir)

        assert os.environ[PUBLIC_AGE_KEYS_ID] == f"{EXISTING_KEY},{AGE_KEY}"
        assert sops_handler.PUBLIC_AGE_KEYS == f"{EXISTING_KEY},{AGE_KEY}"

    @pytest.mark.unit
    def test_raises_when_public_age_keys_missing(self, tmp_path, monkeypatch):
        es_dir = tmp_path / "effective-set"
        write_pipeline_params(es_dir, {DCL2ARGO_AGE_PUBLIC_KEY_PARAM: AGE_KEY})
        monkeypatch.delenv(PUBLIC_AGE_KEYS_ID, raising=False)

        with pytest.raises(ValueError):
            merge_pipeline_age_key_into_public_keys(es_dir)

    @pytest.mark.unit
    def test_no_duplicate_when_key_already_present(self, tmp_path, monkeypatch):
        es_dir = tmp_path / "effective-set"
        write_pipeline_params(es_dir, {DCL2ARGO_AGE_PUBLIC_KEY_PARAM: AGE_KEY})
        monkeypatch.setenv(PUBLIC_AGE_KEYS_ID, f"{EXISTING_KEY},{AGE_KEY}")

        merge_pipeline_age_key_into_public_keys(es_dir)

        assert os.environ[PUBLIC_AGE_KEYS_ID] == f"{EXISTING_KEY},{AGE_KEY}"
        assert sops_handler.PUBLIC_AGE_KEYS == f"{EXISTING_KEY},{AGE_KEY}"

    @pytest.mark.unit
    def test_keeps_order_and_trims_whitespace(self, tmp_path, monkeypatch):
        es_dir = tmp_path / "effective-set"
        write_pipeline_params(es_dir, {DCL2ARGO_AGE_PUBLIC_KEY_PARAM: f" {AGE_KEY} "})
        monkeypatch.setenv(PUBLIC_AGE_KEYS_ID, f" {EXISTING_KEY}, ")

        merge_pipeline_age_key_into_public_keys(es_dir)

        assert os.environ[PUBLIC_AGE_KEYS_ID] == f"{EXISTING_KEY},{AGE_KEY}"
        assert sops_handler.PUBLIC_AGE_KEYS == f"{EXISTING_KEY},{AGE_KEY}"


class TestGenerateEffectiveSetStep:
    @pytest.mark.unit
    @pytest.mark.parametrize("gitlab_deploy", [True, False])
    def test_merges_pipeline_age_key_after_effective_set(self, tmp_path, monkeypatch, gitlab_deploy):
        from pipeline import orchestrator
        calls = []
        for name in ("validate_creds", "validate_parameters", "apply_no_sd_mode", "sboms_retention_policy",
                     "generate_sboms"):
            monkeypatch.setattr(orchestrator, name, lambda *a, **k: None)
        monkeypatch.setattr(orchestrator, "run_gitlab_deploy_effective_set", lambda ctx: calls.append("gitlab"))
        monkeypatch.setattr(orchestrator, "run_legacy_sd_effective_set", lambda ctx: calls.append("legacy"))
        monkeypatch.setattr(orchestrator, "get_current_env_dir_from_env_vars", lambda: tmp_path)
        monkeypatch.setattr(orchestrator, "merge_pipeline_age_key_into_public_keys",
                            lambda es_dir: calls.append(es_dir))

        class Ctx:
            def is_gitlab_deploy(self):
                return gitlab_deploy

        orchestrator.GenerateEffectiveSetStep().execute(Ctx())

        assert calls == ["gitlab" if gitlab_deploy else "legacy", tmp_path / "effective-set"]
