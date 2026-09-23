import pytest

from envgene_linter.discovery import build_index
from envgene_linter.model import Action, IssueType, Severity
from envgene_linter.rules.name3 import check

_HINT = (
    "Review whether this name can be kebab-case. "
    "Do not rename it if generation or other logic still depends on the current spelling."
)


def _name3(repo):
    return check(build_index(repo.root))


def test_cluster_not_kebab(repo):
    repo.env("Cluster_01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("Cluster_01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    findings = [item for item in _name3(repo) if item.key == "Cluster_01"]
    assert len(findings) == 1
    item = findings[0]
    assert item.rule == "NAME-3"
    assert item.severity is Severity.INFORMATION
    assert item.issue_type is IssueType.INFORMATION
    assert item.action is Action.REVIEW
    assert item.message == "Cluster directory 'Cluster_01' is not kebab-case."
    assert item.hint == _HINT
    assert item.scope == "Cluster directory"


def test_kebab_cluster_and_env_dirs_are_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    kinds = {item.scope for item in _name3(repo)}
    assert "Cluster directory" not in kinds
    assert "Environment directory" not in kinds


def test_env_not_kebab(repo):
    repo.env("cluster-01", "Env_01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "Env_01", "cloud-deploy", {"LOG_LEVEL": "info"})
    findings = [item for item in _name3(repo) if item.key == "Env_01"]
    assert len(findings) == 1
    assert findings[0].message == "Environment directory 'Env_01' is not kebab-case."


def test_namespace_not_kebab(repo):
    repo.env("cluster-01", "env-01", deploy={"Foo": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = repo.root / "environments/cluster-01/env-01/Namespaces/Foo"
    path.mkdir(parents=True)
    findings = [item for item in _name3(repo) if item.key == "Foo"]
    assert len(findings) == 1
    assert findings[0].message == "Namespace 'Foo' is not kebab-case."


def test_paramset_stem_not_kebab(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["Cloud_Deploy"]})
    repo.env_paramset("cluster-01", "env-01", "Cloud_Deploy", {"LOG_LEVEL": "info"})
    findings = [item for item in _name3(repo) if item.key == "Cloud_Deploy"]
    assert len(findings) == 1
    assert findings[0].message == "File 'Cloud_Deploy' is not kebab-case."
    assert findings[0].scope == "File"


def test_env_definition_is_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    findings = [item for item in _name3(repo) if item.key == "env_definition"]
    assert len(findings) == 1
    assert findings[0].scope == "File"
    assert findings[0].severity is Severity.INFORMATION
    assert findings[0].action is Action.REVIEW
    assert findings[0].message == "File 'env_definition' is not kebab-case."


def test_yaml_outside_index_is_ignored_when_unused(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = (
        repo.root
        / "environments/cluster-01/env-01/Inventory/credentials/Foo.yml"
    )
    path.parent.mkdir(parents=True)
    path.write_text("user: x\n", encoding="utf-8")
    findings = [item for item in _name3(repo) if item.key == "Foo"]
    assert findings == []


def test_hidden_yaml_is_ignored_when_unused(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = repo.root / "environments/cluster-01/.Secret.yml"
    path.write_text("k: v\n", encoding="utf-8")
    findings = [item for item in _name3(repo) if item.key == ".Secret"]
    assert findings == []


def test_hidden_cluster_directory_is_ignored_when_unused(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    (repo.root / "environments" / ".scratch").mkdir(parents=True)
    findings = [item for item in _name3(repo) if item.key == ".scratch"]
    assert findings == []


def test_inventory_dir_is_not_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    (repo.root / "environments" / "Inventory").mkdir()
    findings = [
        item
        for item in _name3(repo)
        if item.key == "Inventory" and item.scope == "Cluster directory"
    ]
    assert findings == []


def test_namespaces_dir_is_not_reported_as_cluster(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    (repo.root / "environments" / "Namespaces").mkdir()
    findings = [
        item
        for item in _name3(repo)
        if item.key == "Namespaces" and item.scope == "Cluster directory"
    ]
    assert findings == []


def test_inventory_yaml_file_is_ignored_when_unused(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    path = repo.root / "environments" / "cluster-01" / "Inventory.yml"
    path.write_text("inventory: {}\n", encoding="utf-8")
    findings = [item for item in _name3(repo) if item.key == "Inventory"]
    assert findings == []


def test_markdown_under_environments_is_not_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = repo.root / "environments/cluster-01/README.md"
    path.write_text("# hi\n", encoding="utf-8")
    assert all(item.key not in {"README", "README.md"} for item in _name3(repo))


def test_appdefs_at_repo_root_is_not_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = repo.root / "appdefs" / "Cloud_App.yml"
    path.parent.mkdir(parents=True)
    path.write_text("name: Cloud_App\n", encoding="utf-8")
    assert all(item.key != "Cloud_App" for item in _name3(repo))


def test_kebab_file_stem_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    assert all(item.key != "cloud-deploy" for item in _name3(repo))


def test_yaml_under_environments_git_is_not_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = repo.root / "environments" / ".git" / "Bad_Name.yml"
    path.parent.mkdir(parents=True)
    path.write_text("k: v\n", encoding="utf-8")
    assert all(item.key != "Bad_Name" for item in _name3(repo))


def test_git_yaml_file_is_ignored_when_unused(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = repo.root / "environments" / ".git.yml"
    path.write_text("k: v\n", encoding="utf-8")
    findings = [item for item in _name3(repo) if item.key == ".git"]
    assert findings == []


def test_git_cluster_directory_is_not_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    git_cluster = repo.root / "environments" / ".git"
    git_cluster.mkdir(parents=True, exist_ok=True)
    (git_cluster / "Env_Bad" / "Inventory").mkdir(parents=True)
    (git_cluster / "Env_Bad" / "Inventory" / "env_definition.yml").write_text(
        "inventory:\n  environmentName: Env_Bad\nenvTemplate:\n  name: composite\n",
        encoding="utf-8",
    )
    findings = [
        item for item in _name3(repo) if item.key in {".git", "Env_Bad"}
    ]
    assert findings == []


def test_unused_namespace_and_dangling_binding_are_ignored(repo):
    repo.env("c", "e", deploy={"Unused_Ns": ["missing"]})
    path = repo.root / "environments/c/e/Namespaces/Unused_Ns"
    path.mkdir(parents=True)
    assert all(item.key != "Unused_Ns" for item in _name3(repo))


def test_unbound_alias_and_shadowed_parameter_set_are_ignored(repo):
    repo.env("c", "e", deploy={"cloud": ["Bad_Name", "good-deploy"]})
    repo.site_paramset("Bad_Name")
    repo.cluster_paramset("c", "Bad_Name")
    repo.env_paramset("c", "e", "good-deploy")
    directory = repo.root / "environments/c/e/Inventory/parameters"
    (directory / "AAA_Unused.yml").symlink_to(directory / "good-deploy.yml")
    findings = _name3(repo)
    assert [item.path for item in findings if item.key == "Bad_Name"] == [
        repo.root / "environments/c/parameters/Bad_Name.yml"
    ]
    assert all(item.key != "AAA_Unused" for item in findings)


def test_selected_and_fixed_credentials_are_checked_by_direct_and_engine(repo):
    from envgene_linter.engine import run_check

    repo.env("c", "e")
    inventory = repo.root / "environments/c/e/Inventory"
    definition = inventory / "env_definition.yml"
    with definition.open("a") as stream:
        stream.write("  sharedMasterCredentialFiles: [Used_Creds]\n")
    directory = inventory / "credentials"
    directory.mkdir()
    for name in ("Used_Creds", "Unused_Creds", "inventory_generation_creds"):
        (directory / f"{name}.yml").write_text("{}\n")
    direct = _name3(repo)
    engine = [item for item in run_check(repo.root).findings if item.rule == "NAME-3"]
    assert direct == engine
    assert {item.key for item in direct} == {
        "env_definition", "Used_Creds", "inventory_generation_creds"
    }


def test_namespace_with_resolved_profile_is_checked(repo):
    repo.env("c", "e")
    inventory = repo.root / "environments/c/e/Inventory"
    with (inventory / "env_definition.yml").open("a") as stream:
        stream.write("  envSpecificResourceProfiles: {Used_Ns: profile}\n")
    profiles = inventory / "resource_profiles"
    profiles.mkdir()
    (profiles / "profile.yml").write_text("{}\n")
    (repo.root / "environments/c/e/Namespaces/Used_Ns").mkdir(parents=True)
    assert [item.key for item in _name3(repo) if item.scope == "Namespace"] == ["Used_Ns"]


def test_namespace_target_must_be_exact_child_name(repo):
    repo.env("c", "e", deploy={"good/": ["p"], "..": ["p"], ".": ["p"]})
    repo.env_paramset("c", "e", "p")
    (repo.root / "environments/c/e/Namespaces/good").mkdir(parents=True)
    assert [item for item in _name3(repo) if item.scope == "Namespace"] == []


pytestmark = pytest.mark.usefixtures("all_rules_enabled")
