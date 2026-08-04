from unittest.mock import MagicMock, patch

import pytest

from cloud_passport.main import run_cloud_passport


@pytest.mark.unit
def test_run_cloud_passport_triggers_discovery_and_processes_files(monkeypatch, tmp_path):
    env_name = "cluster-1/env-1"
    monkeypatch.setenv("FULL_ENV_NAME", env_name)
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("CI_API_V4_URL", "https://gitlab.example.com/api/v4")

    config_dir = tmp_path / "configuration"
    config_dir.mkdir()
    (config_dir / "integration.yml").write_text(
        "cp_discovery:\n"
        "  gitlab:\n"
        "    project: org/discovery\n"
        "    branch: main\n"
        "    token: envgen.creds.get('discovery-cred').secret\n"
    )

    mock_client = MagicMock()
    mock_client.trigger_pipeline.return_value = {"id": 42, "status": "running"}
    mock_client.http.get_json.return_value = {"status": "success"}
    mock_client.get_pipeline_jobs.return_value = [
        {"name": "prepare", "id": 1},
        {"name": "get_cloud_passport", "id": 99},
    ]
    mock_client.get_project_variables.return_value = [{"key": "SECRET_KEY", "value": "discovery-secret"}]
    mock_client.api_url = "https://gitlab.example.com/api/v4"
    mock_client.headers = {"PRIVATE-TOKEN": "discovery-token"}

    with patch("cloud_passport.main.GitLabClient", return_value=mock_client), \
            patch("cloud_passport.main.fetch_cred_value", return_value="discovery-token"), \
            patch("cloud_passport.main.get_cred_config"), \
            patch("cloud_passport.main.unpack_archive"), \
            patch("cloud_passport.main.process_discovery_files") as mock_process, \
            patch("cloud_passport.main.time.sleep"):
        run_cloud_passport()

    mock_client.trigger_pipeline.assert_called_once_with(
        project_path="org/discovery",
        ref="main",
        variables={"ENV_NAME": env_name},
    )
    mock_client.download_job_artifacts.assert_called_once_with(
        "org/discovery",
        99,
        "/tmp/archive.zip",
    )
    mock_process.assert_called_once()
    assert mock_process.call_args[0][0] == env_name
