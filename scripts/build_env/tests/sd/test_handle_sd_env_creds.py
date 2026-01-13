import asyncio
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from ruamel.yaml import YAML

os.environ['ENVIRONMENT_NAME'] = "temporary"
os.environ['CLUSTER_NAME'] = "temporary"
os.environ['CI_PROJECT_DIR'] = "temporary"

from handle_sd import download_sd_by_appver
from envgenehelper.env_helper import Environment

yaml = YAML()


class TestDownloadSdWithEnvCreds:
    """Test that download_sd_by_appver uses get_cred_config correctly"""

    @patch('handle_sd.get_cred_config')
    @patch('handle_sd.artifact.check_artifact_async')
    @patch('handle_sd.get_appdef_for_app')
    def test_download_sd_uses_get_cred_config(self, mock_get_appdef, mock_check_artifact, mock_get_creds):
        """Test that download_sd_by_appver uses existing get_cred_config utility"""
        mock_get_creds.return_value = {
            'aws-creds': {'type': 'usernamePassword', 'data': {'username': 'key', 'password': 'secret'}}
        }
        mock_app_def = MagicMock()
        mock_get_appdef.return_value = mock_app_def
        
        def capture_run(coro):
            return ("http://sd-url", ("repo", "/tmp/sd.json"))
        
        with patch('handle_sd.asyncio.run', side_effect=capture_run):
            with patch('handle_sd.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = '{"applications": []}'
                
                try:
                    env = Environment("/test/path", "test-cluster", "test-env")
                    download_sd_by_appver("test-app", "1.0.0", MagicMock(), env)
                except:
                    pass
        
        assert mock_get_creds.called
