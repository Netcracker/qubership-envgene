from pathlib import Path

from envgene_linter.discovery import build_index
from envgene_linter.effective import ALL_LAYERS, compute
from envgene_linter.model import Category, Scope
from envgene_linter.yamlio import load

GOLDEN = Path(__file__).resolve().parent.parent / "testdata" / "golden"


def test_effective_set_matches_vendored_leaves():
    index = build_index(GOLDEN / "instance")
    full = compute(index, index.environments[0], ALL_LAYERS)
    scope = Scope("cloud", Category.DEPLOY)
    expected = load(GOLDEN / "expected-leaves.yml").doc
    got = {
        leaf.key: (leaf.value, leaf.provenance.layer.value)
        for leaf in full.scopes[scope].values()
    }
    assert {item["key"]: (item["value"], item["layer"]) for item in expected} == got
    assert "KEEP_SITE" not in got
