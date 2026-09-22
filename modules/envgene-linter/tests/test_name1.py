from envgene_linter.discovery import build_index
from envgene_linter.model import Action, IssueType, Severity
from envgene_linter.rules.name1 import check


def _name1(repo):
    return check(build_index(repo.root))


def test_three_kafka_keys_one_value(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset(
        "cluster-01",
        "env-01",
        "cloud-deploy",
        {
            "KAFKA_URL": "kafka.internal:9092",
            "BOOTSTRAP_SERVERS": "kafka.internal:9092",
            "STREAMING_BROKER_ADDRESS": "kafka.internal:9092",
        },
    )
    findings = _name1(repo)
    assert len(findings) == 1
    item = findings[0]
    assert item.rule == "NAME-1"
    assert item.severity is Severity.INFORMATION
    assert item.issue_type is IssueType.INFORMATION
    assert item.action is Action.REVIEW
    assert set(item.related) == {"BOOTSTRAP_SERVERS", "KAFKA_URL", "STREAMING_BROKER_ADDRESS"}
    assert len(item.locations) == 3
    assert item.message == (
        "Keys BOOTSTRAP_SERVERS, KAFKA_URL, STREAMING_BROKER_ADDRESS share the value "
        "'kafka.internal:9092'."
    )
    assert item.hint == (
        "Review whether they mean the same concept for the same consumer. "
        "Do not collapse them unless that is intended."
    )


def test_nested_map_is_a_distinct_key(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    path = (
        repo.root / "environments/cluster-01/env-01/Inventory/parameters/cloud-deploy.yml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "name: cloud-deploy\n"
        "parameters:\n"
        "  BOOTSTRAP_SERVERS: kafka.internal:9092\n"
        "  outer:\n"
        "    KAFKA_URL: kafka.internal:9092\n",
        encoding="utf-8",
    )
    findings = _name1(repo)
    assert len(findings) == 1
    assert set(findings[0].related) == {"BOOTSTRAP_SERVERS", "outer.KAFKA_URL"}


def test_same_key_in_two_files_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["a"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["b"]})
    repo.env_paramset("cluster-01", "env-01", "a", {"KAFKA_URL": "kafka.internal:9092"})
    repo.env_paramset("cluster-01", "env-02", "b", {"KAFKA_URL": "kafka.internal:9092"})
    assert _name1(repo) == []


def test_username_password_placeholder_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset(
        "cluster-01",
        "env-01",
        "cloud-deploy",
        {"POSTGRES_DBA_USER": "test-user", "POSTGRES_DBA_PASSWORD": "test-user"},
    )
    assert _name1(repo) == []


def test_empty_int_bool_are_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset(
        "cluster-01",
        "env-01",
        "cloud-deploy",
        {"A": "", "B": 1, "C": True, "D": 1},
    )
    assert _name1(repo) == []


def test_orphan_paramset_is_ignored(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["bound"]})
    repo.env_paramset("cluster-01", "env-01", "bound", {"KEEP": "ok"})
    repo.env_paramset(
        "cluster-01",
        "env-01",
        "orphan",
        {"KAFKA_URL": "kafka.internal:9092", "BOOTSTRAP_SERVERS": "kafka.internal:9092"},
    )
    assert _name1(repo) == []


def test_orphan_cannot_contaminate_selected_value_group(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["bound"]})
    repo.env_paramset("cluster-01", "env-01", "bound", {"KAFKA_URL": "same"})
    repo.env_paramset("cluster-01", "env-01", "orphan", {"BOOTSTRAP_SERVERS": "same"})
    assert _name1(repo) == []


def test_jinja_paramset_is_skipped(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    jinja = (
        repo.root
        / "environments/cluster-01/env-01/Inventory/parameters/cloud-deploy.yml.j2"
    )
    jinja.parent.mkdir(parents=True, exist_ok=True)
    jinja.write_text(
        "name: cloud-deploy\n"
        "parameters:\n"
        "  KAFKA_URL: kafka.internal:9092\n"
        "  BOOTSTRAP_SERVERS: kafka.internal:9092\n",
        encoding="utf-8",
    )
    assert _name1(repo) == []


def test_application_parameters_use_app_prefix(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    path = (
        repo.root / "environments/cluster-01/env-01/Inventory/parameters/cloud-deploy.yml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "name: cloud-deploy\n"
        "applications:\n"
        "  - appName: billing\n"
        "    parameters:\n"
        "      KAFKA_URL: kafka.internal:9092\n"
        "      BOOTSTRAP_SERVERS: kafka.internal:9092\n",
        encoding="utf-8",
    )
    findings = _name1(repo)
    assert len(findings) == 1
    assert set(findings[0].related) == {
        "billing.BOOTSTRAP_SERVERS",
        "billing.KAFKA_URL",
    }
