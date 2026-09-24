import pytest

from click.testing import CliRunner

from envgene_linter.cli import main
from envgene_linter.html_report import REPORT_FILENAME


def test_check_reports_place1(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"MONITORING_URL": "https://m.example.com"})
    repo.env_paramset("cluster-01", "env-02", "env-params", {"MONITORING_URL": "https://m.example.com"})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    assert result.output.startswith("PLACE-1\n")
    assert "warning" in result.output
    assert "MONITORING_URL" in result.output


def test_check_no_findings(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    assert result.output.startswith(
        "PLACE-1\nNo findings\n\nPLACE-2\nNo findings\n\n"
        "PLACE-3\nNo findings\n\nPLACE-4\nNo findings\n\nPLACE-6\nNo findings\n\n"
        "PLACE-7\nNo findings\n\nPLACE-8\nNo findings\n\nPLACE-9\nNo findings\n\n"
        "PLACE-10\nNo findings\n\n"
        "SEC-1\nNo findings\n\n"
        "SEC-3\nNo findings\n\n"
        "SEC-4\nNo findings\n\n"
        "SEC-5\nNo findings\n\n"
        "INT-2\nNo findings\n\n"
        "INT-3\nNo findings\n\n"
        "NAME-1\nNo findings\n\n"
        "NAME-2\nNo findings\n\nNAME-3\n"
    )
    assert result.output.index("NAME-3") < result.output.index("NAME-4")
    name3 = result.output[result.output.index("NAME-3") : result.output.index("NAME-4")]
    assert "No findings" not in name3
    assert "information" in name3
    assert "env_definition" in name3
    assert "File 'env_definition' is not kebab-case." in name3
    name4 = result.output[result.output.index("NAME-4") :]
    assert "No findings" not in name4
    assert "information" in name4
    assert "env-params" in name4
    assert "ParameterSet 'env-params' must end with -deploy" in name4


def test_check_reports_name4_after_name3(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["bss"]})
    repo.env_paramset("cluster-01", "env-01", "bss", {"LOG_LEVEL": "info"})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    assert result.output.index("NAME-3") < result.output.index("NAME-4")
    name4 = result.output[result.output.index("NAME-4") :]
    assert "information" in name4
    assert "bss" in name4


def test_html_name4_section(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["bss"]})
    repo.env_paramset("cluster-01", "env-01", "bss", {"LOG_LEVEL": "info"})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    body = (repo.root / REPORT_FILENAME).read_text(encoding="utf-8")
    assert "NAME-4: Bound ParameterSet stem is &lt;subject&gt;-&lt;category&gt;" in body
    assert "Information" in body
    assert "Review" in body
    assert "chip-information" in body
    assert "chip-review" in body


def test_check_reports_place2_after_place1(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared", "env-params"]})
    repo.cluster_paramset("cluster-01", "shared", {"LOG_LEVEL": "info"})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"LOG_LEVEL": "info"})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    assert result.output.index("PLACE-1") < result.output.index("PLACE-2")
    assert "LOG_LEVEL" in result.output[result.output.index("PLACE-2") :]


def test_check_reports_name1_after_place3(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset(
        "cluster-01",
        "env-01",
        "cloud-deploy",
        {"KAFKA_URL": "kafka.internal:9092", "BOOTSTRAP_SERVERS": "kafka.internal:9092"},
    )
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    assert result.output.index("PLACE-3") < result.output.index("PLACE-4") < result.output.index("PLACE-6") < result.output.index("PLACE-7") < result.output.index("PLACE-8") < result.output.index("PLACE-9") < result.output.index("NAME-1")
    name1 = result.output[result.output.index("NAME-1") :]
    assert "information" in name1
    assert "KAFKA_URL" in name1
    assert "BOOTSTRAP_SERVERS" in name1


def test_check_reports_name2_after_name1(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    path = (
        repo.root / "environments/cluster-01/env-01/Inventory/parameters/cloud-deploy.yml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "name: deploy-params\nparameters:\n  LOG_LEVEL: info\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    assert result.output.index("NAME-1") < result.output.index("NAME-2")
    name2 = result.output[result.output.index("NAME-2") :]
    assert "warning" in name2
    assert "cloud-deploy" in name2
    assert "deploy-params" in name2


def test_check_reports_name3_after_name2(repo):
    repo.env("Cluster_01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("Cluster_01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    assert result.output.index("NAME-2") < result.output.index("NAME-3")
    name3 = result.output[result.output.index("NAME-3") :]
    assert "information" in name3
    assert "Cluster_01" in name3


def test_html_name3_section(repo):
    repo.env("Cluster_01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("Cluster_01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    body = (repo.root / REPORT_FILENAME).read_text(encoding="utf-8")
    assert "NAME-3: Filenames, directories, and namespaces use kebab-case" in body
    assert "Information" in body
    assert "Review" in body
    assert "chip-information" in body
    assert "chip-review" in body


def test_html_name2_section(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    path = (
        repo.root / "environments/cluster-01/env-01/Inventory/parameters/cloud-deploy.yml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "name: deploy-params\nparameters:\n  LOG_LEVEL: info\n",
        encoding="utf-8",
    )
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    body = (repo.root / REPORT_FILENAME).read_text(encoding="utf-8")
    assert "NAME-2: Filename stem must equal the name field" in body
    assert "Warning" in body
    assert "Fix" in body
    assert "chip-warning" in body
    assert "chip-fix" in body


def test_html_name1_section(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset(
        "cluster-01",
        "env-01",
        "cloud-deploy",
        {"KAFKA_URL": "kafka.internal:9092", "BOOTSTRAP_SERVERS": "kafka.internal:9092"},
    )
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    body = (repo.root / REPORT_FILENAME).read_text(encoding="utf-8")
    assert "NAME-1: Different keys may name the same concept" in body
    assert "Information" in body
    assert "Review" in body
    assert "chip-information" in body
    assert "chip-review" in body


def test_check_reports_place3_after_place2(repo):
    repo.env(
        "cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]}, cloud_passport="passport"
    )
    repo.passport("passport", {"cloud": {"CLOUD_API_HOST": "api.example"}}, cluster=None)
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"TENANT": "acme"})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    assert result.output.index("PLACE-1") < result.output.index("PLACE-2") < result.output.index("PLACE-3")
    place3 = result.output[result.output.index("PLACE-3") : result.output.index("PLACE-4")]
    assert "Passport passport is not at the cluster layer." in place3
    assert "warning" in place3


def test_check_reports_place4_after_place3(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset(
        "cluster-01",
        "env-01",
        "cloud-deploy",
        {"CLOUD_API_HOST": "api.example"},
    )
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    assert result.output.index("PLACE-3") < result.output.index("PLACE-4") < result.output.index("PLACE-6") < result.output.index("PLACE-7") < result.output.index("PLACE-8") < result.output.index("PLACE-9") < result.output.index("NAME-1")
    place4 = result.output[result.output.index("PLACE-4") : result.output.index("PLACE-6")]
    assert "warning" in place4
    assert "CLOUD_API_HOST" in place4
    assert "Cloud Passport contract key" in place4


def test_html_place4_section(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset(
        "cluster-01",
        "env-01",
        "cloud-deploy",
        {"CLOUD_API_HOST": "api.example"},
    )
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    body = (repo.root / REPORT_FILENAME).read_text(encoding="utf-8")
    assert "PLACE-4: Cloud Passport keys do not belong in ParameterSets" in body
    assert "Warning" in body
    assert "Fix" in body
    assert "chip-warning" in body
    assert "chip-fix" in body


def test_check_reports_place6_after_place4(repo):
    repo.env("cluster-01", "env-01", e2e={"bss": ["env-1-pipeline"]})
    repo.env_paramset("cluster-01", "env-01", "env-1-pipeline", {"E2E": 1})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    assert result.output.index("PLACE-4") < result.output.index("PLACE-6") < result.output.index("PLACE-7") < result.output.index("PLACE-8") < result.output.index("PLACE-9") < result.output.index("NAME-1")
    place6 = result.output[result.output.index("PLACE-6") : result.output.index("PLACE-7")]
    assert "warning" in place6
    assert "bss" in place6
    assert "not the Cloud" in place6


def test_html_place6_section(repo):
    repo.env("cluster-01", "env-01", e2e={"bss": ["env-1-pipeline"]})
    repo.env_paramset("cluster-01", "env-01", "env-1-pipeline", {"E2E": 1})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    body = (repo.root / REPORT_FILENAME).read_text(encoding="utf-8")
    assert "PLACE-6: Pipeline ParameterSets bind to the Cloud" in body
    assert "Warning" in body
    assert "Fix" in body
    assert "chip-warning" in body
    assert "chip-fix" in body


def test_check_and_html_report_place7_before_name1_without_hiding_name4(repo):
    repo.env(
        "cluster-01",
        "env-01",
        deploy={"cloud": ["shared"]},
        technical={"bss": ["shared"]},
    )
    repo.env_paramset("cluster-01", "env-01", "shared", {"LOG_LEVEL": "info"})

    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])

    assert result.exit_code == 0
    assert result.output.index("PLACE-6") < result.output.index("PLACE-7") < result.output.index("PLACE-8") < result.output.index("PLACE-9") < result.output.index("NAME-1")
    place7 = result.output[result.output.index("PLACE-7") : result.output.index("PLACE-8")]
    assert "warning" in place7
    assert "ParameterSet 'shared' is bound to multiple categories: deploy, technical." in place7
    assert place7.count("env_definition.yml:") == 2
    assert "ParameterSet 'shared' must end with -deploy/technical" in result.output

    body = (repo.root / REPORT_FILENAME).read_text(encoding="utf-8")
    assert "PLACE-7: One category per ParameterSet" in body
    assert "Warning" in body
    assert "Fix" in body
    assert "chip-warning" in body
    assert "chip-fix" in body
    place7_html = body[
        body.index("PLACE-7: One category per ParameterSet") : body.index(
            "</details>", body.index("PLACE-7: One category per ParameterSet")
        )
    ]
    assert place7_html.count("env_definition.yml:") == 2
    assert "NAME-4: Bound ParameterSet stem is &lt;subject&gt;-&lt;category&gt;" in body


def test_place8_console_and_html_are_informational_and_exit_zero(repo):
    repo.env("c", "e")
    definition = repo.root / "environments/c/e/Inventory/env_definition.yml"
    with definition.open("a", encoding="utf-8") as stream:
        stream.write("  sharedMasterCredentialFiles: [empty]\n")
    path = repo.root / "environments/credentials/empty.yml"
    path.parent.mkdir(parents=True)
    path.write_text("{}\n", encoding="utf-8")

    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])

    assert result.exit_code == 0
    block = result.output[result.output.index("PLACE-8") : result.output.index("PLACE-9")]
    assert "information" in block
    assert "Credentials file 'empty.yml' is empty but is referenced or used by the generator." in block
    body = (repo.root / REPORT_FILENAME).read_text(encoding="utf-8")
    assert "PLACE-8: Referenced or used entities are empty" in body
    assert "chip-information" in body
    assert "chip-review" in body


def test_place9_console_and_html_are_warning_fix_and_exit_zero(repo):
    repo.env("c", "one", cloud_passport="one")
    repo.env("c", "two", cloud_passport="two")
    repo.passport("one", cluster="c")
    repo.passport("two", cluster="c")

    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])

    assert result.exit_code == 0
    block = result.output[result.output.index("PLACE-9") : result.output.index("NAME-1")]
    assert "warning" in block
    assert "default" in block
    assert result.output.index("PLACE-8") < result.output.index("PLACE-9") < result.output.index("NAME-1")
    body = (repo.root / REPORT_FILENAME).read_text(encoding="utf-8")
    assert "PLACE-9: One Cloud Passport per cluster" in body
    assert "chip-warning" in body
    assert "chip-fix" in body


def test_missing_environments_exits_2(tmp_path):
    result = CliRunner().invoke(main, ["check", str(tmp_path)])
    assert result.exit_code == 2
    assert "environments" in result.output


def test_console_flag_adds_findings_and_keeps_html(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    runner = CliRunner(mix_stderr=False)
    plain = runner.invoke(main, ["check", str(repo.root)])
    html = runner.invoke(main, ["check", str(repo.root), "--console"])
    assert html.exit_code == 0
    assert plain.exit_code == 0
    assert plain.stdout == ""
    assert html.stdout.startswith("PLACE-1\n")
    path = repo.root / REPORT_FILENAME
    assert path.is_file()
    body = path.read_text(encoding="utf-8")
    assert "NAME-3: Filenames, directories, and namespaces use kebab-case" in body
    assert "NAME-4: Bound ParameterSet stem is &lt;subject&gt;-&lt;category&gt;" in body
    assert "env_definition" in body
    assert "env-params" in body
    assert f"Report saved to: {path.resolve()}" in html.stderr
    assert f"Report saved to: {path.resolve()}" in plain.stderr
    assert "envgene-linter-report.html" in (repo.root / ".gitignore").read_text(encoding="utf-8")


def test_default_html_writes_findings_with_file_heading(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"MONITORING_URL": "https://m.example.com"})
    repo.env_paramset("cluster-01", "env-02", "env-params", {"MONITORING_URL": "https://m.example.com"})
    result = CliRunner().invoke(main, ["check", str(repo.root)])
    assert result.exit_code == 0
    body = (repo.root / REPORT_FILENAME).read_text(encoding="utf-8")
    assert "PLACE-1" in body
    assert "FILE" in body
    assert "environments/cluster-01/env-01/Inventory/parameters/env-params.yml" in body
    assert "environments/cluster-01/env-02/Inventory/parameters/env-params.yml" in body
    assert "MONITORING_URL" in body


@pytest.mark.parametrize("args", [[], ["."], ["--console"]])
def test_check_uses_current_directory(repo, monkeypatch, args):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    monkeypatch.chdir(repo.root)
    result = CliRunner(mix_stderr=False).invoke(main, ["check", *args])
    assert result.exit_code == 0, result.output
    assert (repo.root / REPORT_FILENAME).is_file()
    assert REPORT_FILENAME in (repo.root / ".gitignore").read_text(encoding="utf-8")
    assert f"Report saved to: {repo.root / REPORT_FILENAME}" in result.stderr
    if "--console" in args:
        assert result.stdout.startswith("PLACE-1\n")
    else:
        assert result.stdout == ""


def test_default_html_overwrites_existing_report(repo):
    repo.env("c", "e")
    path = repo.root / REPORT_FILENAME
    path.write_text("old report", encoding="utf-8")
    result = CliRunner().invoke(main, ["check", str(repo.root)])
    assert result.exit_code == 0
    assert "old report" not in path.read_text(encoding="utf-8")
    assert "NAME-3" in path.read_text(encoding="utf-8")


def test_check_relative_path_writes_to_target(repo, monkeypatch):
    repo.env("c", "e")
    monkeypatch.chdir(repo.root.parent)
    result = CliRunner(mix_stderr=False).invoke(main, ["check", repo.root.name])
    assert result.exit_code == 0
    assert (repo.root / REPORT_FILENAME).is_file()
    assert f"Report saved to: {repo.root / REPORT_FILENAME}" in result.stderr


def test_check_current_directory_without_environments_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(main, ["check"])
    assert result.exit_code == 2
    assert "not an instance repository: no environments/ directory" in result.output
    assert not (tmp_path / REPORT_FILENAME).exists()


def test_default_output_keeps_parsing_diagnostics(repo):
    repo.env("c", "e")
    (repo.root / "environments/c/e/Inventory/env_definition.yml").write_text(
        "inventory: [\n", encoding="utf-8"
    )
    result = CliRunner(mix_stderr=False).invoke(main, ["check", str(repo.root)])
    assert result.exit_code == 0
    assert result.stdout == ""
    assert "env_definition.yml" in result.stderr
    assert "Report saved to:" in result.stderr


def test_removed_html_flag_is_rejected(repo):
    repo.env("c", "e")
    result = CliRunner().invoke(main, ["check", str(repo.root), "--html"])
    assert result.exit_code == 2
    assert "No such option: --html" in result.output
    assert not (repo.root / REPORT_FILENAME).exists()


def test_html_keeps_existing_gitignore_lines(repo):
    gitignore = repo.root / ".gitignore"
    gitignore.write_text("*.pyc\n", encoding="utf-8")
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    text = gitignore.read_text(encoding="utf-8")
    assert text.startswith("*.pyc\n")
    assert "envgene-linter-report.html" in text


def test_html_non_utf8_gitignore_keeps_exit_0(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    (repo.root / ".gitignore").write_bytes(b"\xff\xfe*.pyc\n")
    result = CliRunner(mix_stderr=False).invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    assert (repo.root / REPORT_FILENAME).is_file()
    assert "Report saved to:" in result.stderr
    combined = f"{result.stdout}{result.stderr}{result.output}"
    assert "Traceback" not in combined
    assert "UnicodeDecodeError" not in combined


def test_html_gitignore_failure_warns_and_keeps_exit_0(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    (repo.root / ".gitignore").mkdir()
    result = CliRunner(mix_stderr=False).invoke(main, ["check", str(repo.root), "--console"])
    assert result.exit_code == 0
    assert (repo.root / REPORT_FILENAME).is_file()
    assert "cannot update .gitignore" in result.stderr
    assert "Report saved to:" in result.stderr


@pytest.mark.parametrize("args", [[], ["--console"]])
def test_html_write_failure_exits_2(repo, args):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    blocker = repo.root / REPORT_FILENAME
    blocker.mkdir()
    result = CliRunner(mix_stderr=False).invoke(main, ["check", str(repo.root), *args])
    assert result.exit_code == 2
    if args:
        assert result.stdout.startswith("PLACE-1\n")
    else:
        assert result.stdout == ""
    assert "cannot write HTML report" in result.stderr
    assert "Report saved to:" not in result.stderr


def test_sec5_reviews_generated_plaintext_without_disclosing_it(repo):
    repo.env('c', 'e')
    path = repo.root / 'environments/c/e/Credentials/credentials.yml'
    path.parent.mkdir(parents=True)
    path.write_text('private-identifier:\n  type: secret\n  data:\n    secret: synthetic-private-secret\n')
    result = CliRunner().invoke(main, ['check', str(repo.root), '--console'])
    assert result.exit_code == 0
    assert 'SEC-5\nNo findings' not in result.output
    assert 'literal value without recognized protection' in result.output
    html = (repo.root / REPORT_FILENAME).read_text()
    assert 'SEC-5: Review protection of connected secrets' in html
    for output in (result.output, html):
        assert 'private-identifier' not in output
        assert 'synthetic-private-secret' not in output


pytestmark = pytest.mark.usefixtures("all_rules_enabled")
