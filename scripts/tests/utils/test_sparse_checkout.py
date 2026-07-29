from unittest.mock import patch

import pytest

from utils.sparse_checkout import main


class TestSparseCheckout:
    @pytest.mark.unit
    def test_single_env_checks_out_full_paths(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        captured: dict = {}

        class FakeRepo:
            def configure(self) -> None:
                pass

            def sparse_checkout(self, paths: list[str], *, fetch: bool = True) -> None:
                captured["paths"] = paths
                captured["fetch"] = fetch

        with patch("utils.sparse_checkout.GitRepoManager", return_value=FakeRepo()), \
                patch(
                    "utils.sparse_checkout.get_sparse_checkout_paths",
                    return_value=["appdefs/", "environments/cluster-01/env-01"],
                ) as get_paths:
            main()

        get_paths.assert_called_once_with("cluster-01/env-01")
        assert captured["paths"] == ["appdefs/", "environments/cluster-01/env-01"]
        assert captured["fetch"] is True

    @pytest.mark.unit
    def test_multi_env_checks_out_empty_paths(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")
        captured: dict = {}

        class FakeRepo:
            def configure(self) -> None:
                pass

            def sparse_checkout(self, paths: list[str], *, fetch: bool = True) -> None:
                captured["paths"] = paths

        with patch("utils.sparse_checkout.GitRepoManager", return_value=FakeRepo()), \
                patch("utils.sparse_checkout.get_sparse_checkout_paths") as get_paths:
            main()

        get_paths.assert_not_called()
        assert captured["paths"] == []
