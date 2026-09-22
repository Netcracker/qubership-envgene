from pathlib import Path

from envgene_linter.html_report import REPORT_FILENAME, ensure_report_ignored, render_html, report_path
from envgene_linter.model import Action, Finding, IssueType, Location, Severity


def _finding(**overrides) -> Finding:
    data = dict(
        rule="PLACE-2",
        severity=Severity.WARNING,
        path=Path("environments/c/e/Inventory/parameters/p.yml"),
        line=4,
        column=3,
        key="K",
        scope="s",
        message="problem text",
        hint="fix it",
    )
    data.update(overrides)
    return Finding(**data)


def test_report_path_is_visible_file_in_repo_root(tmp_path):
    assert report_path(tmp_path) == tmp_path / "envgene-linter-report.html"
    assert REPORT_FILENAME == "envgene-linter-report.html"


def test_two_place1_findings_one_rule_heading():
    a = _finding(rule="PLACE-1", path=Path("environments/a.yml"), message="ma", hint="ha")
    b = _finding(rule="PLACE-1", path=Path("environments/b.yml"), line=8, column=5, message="mb", hint="hb")
    body = render_html([a, b], Path("/repo"))
    assert body.count("<details") == 1
    assert "<details open" not in body
    assert '<details class="rule-section">' in body
    assert "open=" not in body
    assert "<summary" in body
    assert "PLACE-1: Same value belongs on a higher layer" in body
    assert "PLACE-2" not in body
    assert body.count('class="finding"') == 2
    assert "FILE" in body and "ISSUE" in body
    assert "TYPE" in body and "ACTION" in body and "FIX SUGGESTION" in body
    assert "environments/a.yml:4:3" in body
    assert "environments/b.yml:8:5" in body
    assert 'class="rule-section"' in body


def test_file_lists_all_locations():
    finding = _finding(
        rule="PLACE-1",
        path=Path("environments/a.yml"),
        locations=(
            Location(Path("environments/a.yml"), 4, 3),
            Location(Path("environments/b.yml"), 8, 5),
        ),
    )
    body = render_html([finding], Path("/repo"))
    assert "environments/a.yml:4:3" in body
    assert "environments/b.yml:8:5" in body


def test_rule_order_place1_then_place3():
    a = _finding(rule="PLACE-3", path=Path("environments/z.yml"))
    b = _finding(rule="PLACE-1", path=Path("environments/a.yml"))
    body = render_html([a, b], Path("/repo"))
    assert body.index("PLACE-1") < body.index("PLACE-3")
    assert "PLACE-2" not in body


def test_unknown_rule_has_heading_without_catalog_blurb():
    body = render_html([_finding(rule="OTHER")], Path("/repo"))
    assert "<summary" in body
    assert "OTHER" in body
    assert "OTHER:" not in body
    assert "Same value belongs on a higher layer" not in body


def test_zero_findings_says_no_findings():
    body = render_html([], Path("/repo"))
    assert "No findings" in body
    assert "<details" not in body
    assert "<h2" not in body


def test_angle_brackets_are_escaped():
    body = render_html([_finding(message="x < y & z")], Path("/repo"))
    assert "x &lt; y &amp; z" in body
    assert "x < y" not in body


def test_no_script_tags():
    body = render_html([_finding()], Path("/repo"))
    assert "<script" not in body
    assert "Do not commit this file" not in body
    assert "Envgene Linter Report" in body
    assert "chip-warning" in body
    assert "chip-fix" in body


def test_unknown_type_uses_gray_chip():
    body = render_html(
        [_finding(issue_type=IssueType.INFORMATION, action=Action.REVIEW)],
        Path("/repo"),
    )
    assert "Information" in body
    assert "Review" in body
    assert "chip-information" in body
    assert "chip-review" in body


def test_place8_uses_catalog_heading_and_information_review_chips():
    body = render_html(
        [
            _finding(
                rule="PLACE-8",
                severity=Severity.INFORMATION,
                issue_type=IssueType.INFORMATION,
                action=Action.REVIEW,
            )
        ],
        Path("/repo"),
    )
    assert "PLACE-8: Referenced or used entities are empty" in body
    assert "chip-information" in body
    assert "chip-review" in body


def test_place9_uses_catalog_heading_and_warning_fix_chips():
    body = render_html([_finding(rule="PLACE-9")], Path("/repo"))
    assert "PLACE-9: One Cloud Passport per cluster" in body
    assert "chip-warning" in body
    assert "chip-fix" in body


def test_ensure_report_ignored_creates_gitignore(tmp_path):
    ensure_report_ignored(tmp_path)
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == "envgene-linter-report.html\n"


def test_ensure_report_ignored_appends(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n", encoding="utf-8")
    ensure_report_ignored(tmp_path)
    assert gitignore.read_text(encoding="utf-8") == "*.pyc\nenvgene-linter-report.html\n"


def test_ensure_report_ignored_skips_when_present(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("/envgene-linter-report.html\n", encoding="utf-8")
    before = gitignore.read_bytes()
    ensure_report_ignored(tmp_path)
    assert gitignore.read_bytes() == before
