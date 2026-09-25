from pathlib import Path

from envgene_linter.model import Finding, Location, Severity
from envgene_linter.report import render


def test_render_no_findings():
    assert render([]) == (
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
        "INT-4\nNo findings\n\n"
        "NAME-1\nNo findings\n\n"
        "NAME-2\nNo findings\n\nNAME-3\nNo findings\n\nNAME-4\nNo findings\n\nNAME-8\nNo findings\n"
    )


def test_render_one_finding():
    finding = Finding(
        rule="PLACE-1",
        severity=Severity.WARNING,
        path=Path("environments/c/e/Inventory/parameters/p.yml"),
        line=4,
        key="K",
        scope="c cloud/deploy",
        message="problem text",
        hint="move it",
    )
    assert render([finding]) == (
        "PLACE-1\n"
        "environments/c/e/Inventory/parameters/p.yml:4:1\n"
        "warning\n"
        "problem text\n"
        "move it\n"
        "\n"
        "PLACE-2\n"
        "No findings\n"
        "\n"
        "PLACE-3\n"
        "No findings\n"
        "\n"
        "PLACE-4\n"
        "No findings\n"
        "\n"
        "PLACE-6\n"
        "No findings\n"
        "\n"
        "PLACE-7\n"
        "No findings\n"
        "\n"
        "PLACE-8\n"
        "No findings\n"
        "\n"
        "PLACE-9\n"
        "No findings\n"
        "\n"
        "PLACE-10\n"
        "No findings\n"
        "\n"
        "SEC-1\n"
        "No findings\n"
        "\n"
        "SEC-3\n"
        "No findings\n"
        "\n"
        "SEC-4\n"
        "No findings\n"
        "\n"
        "SEC-5\n"
        "No findings\n"
        "\n"
        "INT-2\nNo findings\n\n"
        "INT-3\nNo findings\n\n"
        "INT-4\nNo findings\n\n"
        "NAME-1\n"
        "No findings\n"
        "\n"
        "NAME-2\n"
        "No findings\n"
        "\n"
        "NAME-3\n"
        "No findings\n"
        "\n"
        "NAME-4\n"
        "No findings\n\n"
        "NAME-8\nNo findings\n"
    )


def test_render_place2_after_place1():
    a = Finding(
        rule="PLACE-1",
        severity=Severity.WARNING,
        path=Path("a.yml"),
        line=1,
        key="A",
        scope="s",
        message="ma",
        hint="ha",
    )
    b = Finding(
        rule="PLACE-2",
        severity=Severity.WARNING,
        path=Path("b.yml"),
        line=2,
        key="B",
        scope="s",
        message="mb",
        hint="hb",
    )
    assert render([a, b]) == (
        "PLACE-1\na.yml:1:1\nwarning\nma\nha\n\nPLACE-2\nb.yml:2:1\nwarning\nmb\nhb\n"
        "\nPLACE-3\nNo findings\n\nPLACE-4\nNo findings\n\nPLACE-6\nNo findings\n\n"
        "PLACE-7\nNo findings\n\nPLACE-8\nNo findings\n\nPLACE-9\nNo findings\n\n"
        "PLACE-10\nNo findings\n\n"
        "SEC-1\nNo findings\n\n"
        "SEC-3\nNo findings\n\n"
        "SEC-4\nNo findings\n\n"
        "SEC-5\nNo findings\n\n"
        "INT-2\nNo findings\n\n"
        "INT-3\nNo findings\n\n"
        "INT-4\nNo findings\n\n"
        "NAME-1\nNo findings\n\nNAME-2\nNo findings\n\n"
        "NAME-3\nNo findings\n\nNAME-4\nNo findings\n\nNAME-8\nNo findings\n"
    )


def test_render_place3_after_place2():
    finding = Finding(
        rule="PLACE-3",
        severity=Severity.WARNING,
        path=Path("c.yml"),
        line=3,
        key="C",
        scope="s",
        message="mc",
        hint="hc",
    )
    output = render([finding])
    assert output.index("PLACE-1") < output.index("PLACE-2") < output.index("PLACE-3")
    assert output == (
        "PLACE-1\nNo findings\n\nPLACE-2\nNo findings\n\n"
        "PLACE-3\nc.yml:3:1\nwarning\nmc\nhc\n\n"
        "PLACE-4\nNo findings\n\n"
        "PLACE-6\nNo findings\n\n"
        "PLACE-7\nNo findings\n\n"
        "PLACE-8\nNo findings\n\n"
        "PLACE-9\nNo findings\n\n"
        "PLACE-10\nNo findings\n\n"
        "SEC-1\nNo findings\n\n"
        "SEC-3\nNo findings\n\n"
        "SEC-4\nNo findings\n\n"
        "SEC-5\nNo findings\n\n"
        "INT-2\nNo findings\n\n"
        "INT-3\nNo findings\n\n"
        "INT-4\nNo findings\n\n"
        "NAME-1\nNo findings\n\nNAME-2\nNo findings\n\nNAME-3\nNo findings\n\nNAME-4\nNo findings\n\nNAME-8\nNo findings\n"
    )


def test_render_place4_after_place3():
    finding = Finding(
        rule="PLACE-4",
        severity=Severity.WARNING,
        path=Path("d.yml"),
        line=4,
        key="D",
        scope="s",
        message="md",
        hint="hd",
    )
    output = render([finding])
    assert (
        output.index("PLACE-1")
        < output.index("PLACE-2")
        < output.index("PLACE-3")
        < output.index("PLACE-4")
        < output.index("PLACE-6")
        < output.index("PLACE-7")
        < output.index("NAME-1")
    )
    assert output == (
        "PLACE-1\nNo findings\n\nPLACE-2\nNo findings\n\n"
        "PLACE-3\nNo findings\n\n"
        "PLACE-4\nd.yml:4:1\nwarning\nmd\nhd\n\n"
        "PLACE-6\nNo findings\n\n"
        "PLACE-7\nNo findings\n\n"
        "PLACE-8\nNo findings\n\n"
        "PLACE-9\nNo findings\n\n"
        "PLACE-10\nNo findings\n\n"
        "SEC-1\nNo findings\n\n"
        "SEC-3\nNo findings\n\n"
        "SEC-4\nNo findings\n\n"
        "SEC-5\nNo findings\n\n"
        "INT-2\nNo findings\n\n"
        "INT-3\nNo findings\n\n"
        "INT-4\nNo findings\n\n"
        "NAME-1\nNo findings\n\nNAME-2\nNo findings\n\nNAME-3\nNo findings\n\nNAME-4\nNo findings\n\nNAME-8\nNo findings\n"
    )


def test_render_place6_after_place4():
    finding = Finding(
        rule="PLACE-6",
        severity=Severity.WARNING,
        path=Path("e.yml"),
        line=5,
        key="bss",
        scope="s",
        message="me",
        hint="he",
    )
    output = render([finding])
    assert (
        output.index("PLACE-4")
        < output.index("PLACE-6")
        < output.index("PLACE-7")
        < output.index("NAME-1")
    )
    assert output == (
        "PLACE-1\nNo findings\n\nPLACE-2\nNo findings\n\n"
        "PLACE-3\nNo findings\n\nPLACE-4\nNo findings\n\n"
        "PLACE-6\ne.yml:5:1\nwarning\nme\nhe\n\n"
        "PLACE-7\nNo findings\n\n"
        "PLACE-8\nNo findings\n\n"
        "PLACE-9\nNo findings\n\n"
        "PLACE-10\nNo findings\n\n"
        "SEC-1\nNo findings\n\n"
        "SEC-3\nNo findings\n\n"
        "SEC-4\nNo findings\n\n"
        "SEC-5\nNo findings\n\n"
        "INT-2\nNo findings\n\n"
        "INT-3\nNo findings\n\n"
        "INT-4\nNo findings\n\n"
        "NAME-1\nNo findings\n\nNAME-2\nNo findings\n\nNAME-3\nNo findings\n\nNAME-4\nNo findings\n\nNAME-8\nNo findings\n"
    )


def test_render_place7_after_place6():
    finding = Finding(
        rule="PLACE-7",
        severity=Severity.WARNING,
        path=Path("env_definition.yml"),
        line=6,
        column=9,
        key="shared",
        scope="c/e",
        message="conflict",
        hint="split it",
        locations=(
            Location(Path("env_definition.yml"), 6, 9),
            Location(Path("env_definition.yml"), 9, 9),
        ),
    )
    output = render([finding])
    assert output.index("PLACE-6") < output.index("PLACE-7") < output.index("NAME-1")
    assert (
        "PLACE-7\nenv_definition.yml:6:9\nenv_definition.yml:9:9\n"
        "warning\nconflict\nsplit it\n"
    ) in output


def test_render_two_findings_one_header():
    a = Finding(
        rule="PLACE-1",
        severity=Severity.WARNING,
        path=Path("a.yml"),
        line=1,
        key="A",
        scope="s",
        message="ma",
        hint="ha",
    )
    b = Finding(
        rule="PLACE-1",
        severity=Severity.WARNING,
        path=Path("b.yml"),
        line=2,
        key="B",
        scope="s",
        message="mb",
        hint="hb",
    )
    assert render([a, b]) == (
        "PLACE-1\n"
        "a.yml:1:1\n"
        "warning\n"
        "ma\n"
        "ha\n"
        "\n"
        "b.yml:2:1\n"
        "warning\n"
        "mb\n"
        "hb\n"
        "\n"
        "PLACE-2\n"
        "No findings\n"
        "\n"
        "PLACE-3\n"
        "No findings\n"
        "\n"
        "PLACE-4\n"
        "No findings\n"
        "\n"
        "PLACE-6\n"
        "No findings\n"
        "\n"
        "PLACE-7\n"
        "No findings\n"
        "\n"
        "PLACE-8\n"
        "No findings\n"
        "\n"
        "PLACE-9\n"
        "No findings\n"
        "\n"
        "PLACE-10\n"
        "No findings\n"
        "\n"
        "SEC-1\n"
        "No findings\n"
        "\n"
        "SEC-3\n"
        "No findings\n"
        "\n"
        "SEC-4\n"
        "No findings\n"
        "\n"
        "SEC-5\n"
        "No findings\n"
        "\n"
        "INT-2\nNo findings\n\n"
        "INT-3\nNo findings\n\n"
        "INT-4\nNo findings\n\n"
        "NAME-1\n"
        "No findings\n"
        "\n"
        "NAME-2\n"
        "No findings\n"
        "\n"
        "NAME-3\n"
        "No findings\n"
        "\n"
        "NAME-4\n"
        "No findings\n\n"
        "NAME-8\nNo findings\n"
    )


def test_render_lists_all_locations():
    finding = Finding(
        rule="PLACE-1",
        severity=Severity.WARNING,
        path=Path("a.yml"),
        line=1,
        column=2,
        key="K",
        scope="s",
        message="ma",
        hint="ha",
        locations=(
            Location(Path("a.yml"), 1, 2),
            Location(Path("b.yml"), 8, 5),
        ),
    )
    output = render([finding])
    assert "a.yml:1:2\nb.yml:8:5\nwarning\nma\nha\n" in output


def test_render_place9_after_place8_and_before_place10():
    finding = Finding(
        rule="PLACE-9",
        severity=Severity.WARNING,
        path=Path("passport.yml"),
        line=1,
        key="default",
        scope="c",
        message="multiple passports",
        hint="keep one",
    )
    output = render([finding])
    assert (
        output.index("PLACE-8")
        < output.index("PLACE-9")
        < output.index("PLACE-10")
        < output.index("NAME-1")
    )
