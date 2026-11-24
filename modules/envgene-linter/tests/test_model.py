from pathlib import Path

from envgene_linter.model import Finding, Location, Severity


def _finding(**overrides) -> Finding:
    data = dict(
        rule="PLACE-2",
        severity=Severity.WARNING,
        path=Path("a.yml"),
        line=4,
        column=3,
        key="K",
        scope="s",
        message="m",
        hint="h",
    )
    data.update(overrides)
    return Finding(**data)


def test_file_locations_falls_back_to_primary():
    finding = _finding()
    assert finding.locations == ()
    assert finding.file_locations() == (Location(Path("a.yml"), 4, 3),)


def test_file_locations_uses_explicit_tuple():
    extra = Location(Path("b.yml"), 8, 5)
    finding = _finding(locations=(extra,))
    assert finding.file_locations() == (extra,)
