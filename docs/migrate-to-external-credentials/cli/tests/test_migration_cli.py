"""Tests for migration-cli collect and fill."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from migration_cli.collect import CollectCredentialValues
from migration_cli.errors import MatchError, MigrationCliError
from migration_cli.fill import FillExternalCredentialContext, FillRepositoryContexts

FIXTURES = Path(__file__).parent / "fixtures"
REPO = FIXTURES / "repo"
CONTEXT_ENV_A = (
    REPO
    / "environments"
    / "cluster"
    / "env-a"
    / "effective-set"
    / "external-credential"
    / "external-credentials.yaml"
)


def test_collect_tiered_structure_without_duplication(tmp_path: Path) -> None:
    out = tmp_path / "values.yaml"
    CollectCredentialValues(instance_root=REPO, out=out).run()

    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    cluster = data["clusters"]["cluster"]
    assert cluster["cloud"]["credentials"]["ID_CLOUD_ONLY"]["username"] == "cloud-user"
    assert cluster["shared"]["credentials"]["ID_SHARED_ONLY"]["secret"] == "shared-secret"
    assert cluster["environments"]["env-a"]["credentials"]["app-client-creds"]["username"] == "user-a"
    assert cluster["environments"]["env-b"]["credentials"]["app-client-creds"]["username"] == "user-b"
    assert "ID_SHARED_ONLY" not in cluster["environments"]["env-a"]["credentials"]
    assert "ID_CLOUD_ONLY" not in cluster["environments"]["env-a"]["credentials"]
    assert "environments" not in data


def test_fill_jenkins_export_matches_by_env(tmp_path: Path) -> None:
    out = tmp_path / "filled.yaml"
    FillExternalCredentialContext(
        context=CONTEXT_ENV_A,
        values=FIXTURES / "jenkins-export.yml",
        values_format="jenkins_export",
        out=out,
        tenant="demo",
        cloud="cloud",
    ).run()

    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    creds = data["credentials"]
    assert creds["app-client-creds"]["strategy"] == "create_if_absent"
    assert creds["app-client-creds"]["data"]["username"] == "jenkins-user"
    assert creds["app-client-creds"]["data"]["password"] == "jenkins-pass"
    assert creds["token2"]["data"]["value"] == "jenkins-secret"
    assert "generated-cred" not in creds


def test_fill_jenkins_export_falls_back_to_cluster(tmp_path: Path) -> None:
    context_path = (
        tmp_path
        / "environments"
        / "cluster"
        / "env-a"
        / "effective-set"
        / "external-credential"
        / "external-credentials.yaml"
    )
    context_path.parent.mkdir(parents=True)
    context_path.write_text(
        "credentials:\n"
        "  ID_CLUSTER_ONLY:\n"
        "    vals: ref+vault://x\n"
        "    strategy: fail_if_absent\n",
        encoding="utf-8",
    )
    out = tmp_path / "filled.yaml"
    FillExternalCredentialContext(
        context=context_path,
        values=FIXTURES / "jenkins-export.yml",
        values_format="jenkins_export",
        out=out,
        tenant="demo",
        cloud="cloud",
    ).run()

    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["credentials"]["ID_CLUSTER_ONLY"]["data"]["username"] == "cluster-user"
    assert data["credentials"]["ID_CLUSTER_ONLY"]["data"]["password"] == "cluster-pass"


def test_fill_jenkins_lists_tried_ids_on_miss(tmp_path: Path) -> None:
    export = tmp_path / "empty-export.yml"
    export.write_text("unrelated-id:\n  type: secret\n  secret: x\n", encoding="utf-8")
    with pytest.raises(MatchError) as exc_info:
        FillExternalCredentialContext(
            context=CONTEXT_ENV_A,
            values=export,
            values_format="jenkins_export",
            out=tmp_path / "filled.yaml",
            tenant="demo",
            cloud="cloud",
        ).run()
    message = str(exc_info.value)
    assert "demo-cloud-env-a-app-client-creds" in message
    assert "demo-cloud-cluster-app-client-creds" in message


def test_fill_instance_scoped_env_then_shared_then_cloud(tmp_path: Path) -> None:
    values_out = tmp_path / "values.yaml"
    CollectCredentialValues(instance_root=REPO, out=values_out).run()

    context = tmp_path / "external-credentials.yaml"
    context.write_text(
        "credentials:\n"
        "  app-client-creds:\n"
        "    vals: ref+vault://x\n"
        "    strategy: fail_if_absent\n"
        "  ID_SHARED_ONLY:\n"
        "    vals: ref+vault://x\n"
        "    strategy: fail_if_absent\n"
        "  ID_CLOUD_ONLY:\n"
        "    vals: ref+vault://x\n"
        "    strategy: fail_if_absent\n"
        "  token2:\n"
        "    vals: ref+vault://x\n"
        "    strategy: fail_if_absent\n"
        "  generated-cred:\n"
        "    vals: ref+vault://x\n"
        "    strategy: create_if_absent\n"
        "    data:\n"
        "      username: _generateValue\n",
        encoding="utf-8",
    )
    context_path = (
        tmp_path
        / "environments"
        / "cluster"
        / "env-a"
        / "effective-set"
        / "external-credential"
        / "external-credentials.yaml"
    )
    context_path.parent.mkdir(parents=True)
    context_path.write_text(context.read_text(encoding="utf-8"), encoding="utf-8")

    filled = tmp_path / "filled.yaml"
    FillExternalCredentialContext(
        context=context_path,
        values=values_out,
        values_format="instance_scoped",
        out=filled,
    ).run()

    data = yaml.safe_load(filled.read_text(encoding="utf-8"))
    creds = data["credentials"]
    assert creds["app-client-creds"]["data"]["username"] == "user-a"
    assert creds["token2"]["data"]["value"] == "secret-a"
    assert creds["ID_SHARED_ONLY"]["data"]["value"] == "shared-secret"
    assert creds["ID_CLOUD_ONLY"]["data"]["username"] == "cloud-user"
    assert "generated-cred" not in creds


def test_collect_fails_on_fernet_without_secret_key(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    env_def = repo / "environments" / "c1" / "e1" / "Inventory" / "env_definition.yml"
    creds = repo / "environments" / "c1" / "e1" / "Inventory" / "credentials" / "creds.yml"
    env_def.parent.mkdir(parents=True)
    creds.parent.mkdir(parents=True)
    env_def.write_text("---\n", encoding="utf-8")
    creds.write_text(
        "credentials:\n"
        "  enc:\n"
        "    type: secret\n"
        "    secret: '[encrypted:AES256_Fernet]dummy'\n",
        encoding="utf-8",
    )
    with pytest.raises(MigrationCliError) as exc_info:
        CollectCredentialValues(instance_root=repo, out=tmp_path / "values.yaml").run()
    assert "SECRET_KEY" in str(exc_info.value)


def test_fill_instance_scoped_cross_cluster_shared(tmp_path: Path) -> None:
    values = tmp_path / "values.yaml"
    values.write_text(
        "clusters:\n"
        "  acme-cluster-c:\n"
        "    shared:\n"
        "      credentials:\n"
        "        shared-client-secret:\n"
        "          type: usernamePassword\n"
        "          username: shared-user\n"
        "          password: shared-pass\n",
        encoding="utf-8",
    )
    context_path = (
        tmp_path
        / "environments"
        / "acme-cluster"
        / "env-b"
        / "effective-set"
        / "external-credential"
        / "external-credentials.yaml"
    )
    context_path.parent.mkdir(parents=True)
    context_path.write_text(
        "credentials:\n"
        "  shared-client-secret:\n"
        "    vals: acme-cluster--shared-credentials--shared-client-secret\n"
        "    strategy: fail_if_absent\n",
        encoding="utf-8",
    )
    out = tmp_path / "filled.yaml"
    FillExternalCredentialContext(
        context=context_path,
        values=values,
        values_format="instance_scoped",
        out=out,
    ).run()
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["credentials"]["shared-client-secret"]["data"]["username"] == "shared-user"


def test_fill_jenkins_suffix_fallback(tmp_path: Path) -> None:
    export = tmp_path / "jenkins-export.yml"
    export.write_text(
        "DEMO-CLOUD-saas-app-01-shared-client-secret:\n"
        "  type: usernamePassword\n"
        "  username: jenkins-user\n"
        "  password: jenkins-pass\n",
        encoding="utf-8",
    )
    context_path = (
        tmp_path
        / "environments"
        / "acme-cluster"
        / "env-b"
        / "effective-set"
        / "external-credential"
        / "external-credentials.yaml"
    )
    context_path.parent.mkdir(parents=True)
    context_path.write_text(
        "credentials:\n"
        "  shared-client-secret:\n"
        "    vals: acme-cluster--shared-credentials--shared-client-secret\n"
        "    strategy: fail_if_absent\n",
        encoding="utf-8",
    )
    out = tmp_path / "filled.yaml"
    FillExternalCredentialContext(
        context=context_path,
        values=export,
        values_format="jenkins_export",
        out=out,
        tenant="DEMO",
        cloud="CLOUD",
    ).run()
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["credentials"]["shared-client-secret"]["data"]["username"] == "jenkins-user"


def test_fill_repo_nested_instance_scoped(tmp_path: Path) -> None:
    values_out = tmp_path / "values.yaml"
    CollectCredentialValues(instance_root=REPO, out=values_out).run()

    out = tmp_path / "filled-all.yaml"
    FillRepositoryContexts(
        repo_root=REPO,
        values=values_out,
        values_format="instance_scoped",
        out=out,
    ).run()

    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    cred = data["credentials"]["cluster/env-a/app-client-creds"]
    assert cred["data"]["username"] == "user-a"
    assert data["credentials"]["cluster/env-a/token2"]["data"]["value"] == "secret-a"
    assert not any(k.startswith("cluster/env-b/") for k in data["credentials"])


def test_fill_repo_shared_cloud_passport_per_env(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    values = tmp_path / "values.yaml"
    values.write_text(
        "clusters:\n"
        "  acme-cluster:\n"
        "    cloud:\n"
        "      credentials:\n"
        "        cloud-deploy-sa-token:\n"
        "          type: secret\n"
        "          secret: token-379\n",
        encoding="utf-8",
    )

    for env_name, vals_suffix in (("env-b", "env-b"), ("env-c", "env-c")):
        context_path = (
            repo
            / "environments"
            / "acme-cluster"
            / env_name
            / "effective-set"
            / "external-credential"
            / "external-credentials.yaml"
        )
        context_path.parent.mkdir(parents=True)
        context_path.write_text(
            "credentials:\n"
            "  cloud-deploy-sa-token:\n"
            f"    vals: ref+gcpsecrets://project/acme-cluster--cloud-deploy-sa-token-{vals_suffix}\n"
            "    strategy: fail_if_absent\n",
            encoding="utf-8",
        )

    out = tmp_path / "filled-all.yaml"
    FillRepositoryContexts(
        repo_root=repo,
        values=values,
        values_format="instance_scoped",
        out=out,
    ).run()

    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    cred_a = data["credentials"]["acme-cluster/env-b/cloud-deploy-sa-token"]
    cred_b = data["credentials"]["acme-cluster/env-c/cloud-deploy-sa-token"]
    assert cred_a["data"]["value"] == "token-379"
    assert cred_b["data"]["value"] == "token-379"
    assert cred_a["vals"] != cred_b["vals"]
    assert "credId" not in cred_a
    assert "cluster" not in cred_a


def test_fill_repo_jenkins_values_dir(tmp_path: Path) -> None:
    exports = tmp_path / "exports"
    exports.mkdir()
    (exports / "demo.yml").write_text(
        "DEMO-CLOUD-saas-app-01-shared-client-secret:\n"
        "  type: usernamePassword\n"
        "  username: from-dir\n"
        "  password: pass\n",
        encoding="utf-8",
    )
    context_path = (
        tmp_path
        / "repo"
        / "environments"
        / "acme-cluster"
        / "env-b"
        / "effective-set"
        / "external-credential"
        / "external-credentials.yaml"
    )
    context_path.parent.mkdir(parents=True)
    context_path.write_text(
        "credentials:\n"
        "  shared-client-secret:\n"
        "    vals: acme-cluster--shared-credentials--shared-client-secret\n"
        "    strategy: fail_if_absent\n",
        encoding="utf-8",
    )
    out = tmp_path / "filled-all.yaml"
    FillRepositoryContexts(
        repo_root=tmp_path / "repo",
        values_dir=exports,
        values_format="jenkins_export",
        out=out,
    ).run()
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    cred = data["credentials"]["acme-cluster/env-b/shared-client-secret"]
    assert cred["data"]["username"] == "from-dir"


def test_fill_repo_partial_writes_matched_and_report(tmp_path: Path) -> None:
    exports = tmp_path / "exports"
    exports.mkdir()
    (exports / "shared.yml").write_text(
        "DEMO-CLOUD-acme-cluster-storage:\n"
        "  type: usernamePassword\n"
        "  username: store-user\n"
        "  password: store-pass\n",
        encoding="utf-8",
    )
    context_path = (
        tmp_path
        / "repo"
        / "environments"
        / "acme-cluster"
        / "env-a"
        / "effective-set"
        / "external-credential"
        / "external-credentials.yaml"
    )
    context_path.parent.mkdir(parents=True)
    context_path.write_text(
        "credentials:\n"
        "  storage:\n"
        "    vals: ref+gcp://x/storage\n"
        "    strategy: fail_if_absent\n"
        "  id_zookeeper_zooKeeper_client:\n"
        "    vals: ref+gcp://x/zk\n"
        "    strategy: fail_if_absent\n",
        encoding="utf-8",
    )
    out = tmp_path / "filled.yaml"
    report = tmp_path / "unmatched.yaml"
    with pytest.raises(MigrationCliError, match="Partial fill"):
        FillRepositoryContexts(
            repo_root=tmp_path / "repo",
            values_dir=exports,
            values_format="jenkins_export",
            out=out,
            tenant="DEMO",
            cloud="CLOUD",
            partial=True,
            report=report,
        ).run()

    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert "acme-cluster/env-a/storage" in data["credentials"]
    assert data["credentials"]["acme-cluster/env-a/storage"]["data"]["username"] == "store-user"
    assert "acme-cluster/env-a/id_zookeeper_zooKeeper_client" not in data["credentials"]

    report_doc = yaml.safe_load(report.read_text(encoding="utf-8"))
    assert report_doc["summary"]["matched"] == 1
    assert report_doc["summary"]["unmatched"] == 1
    assert report_doc["unmatched"][0]["credId"] == "id_zookeeper_zooKeeper_client"
