from envgene_linter.engine import run_check


def test_place1_not_ok(testdata):
    findings = [item for item in run_check(testdata / "place1" / "not-ok").findings if item.rule == "PLACE-1"]
    assert len(findings) == 1
    assert findings[0].key == "MONITORING_URL"


def test_place1_ok(testdata):
    findings = [item for item in run_check(testdata / "place1" / "ok").findings if item.rule == "PLACE-1"]
    assert findings == []


def test_place2_not_ok(testdata):
    findings = [item for item in run_check(testdata / "place2" / "not-ok").findings if item.rule == "PLACE-2"]
    assert len(findings) == 1
    assert findings[0].key == "LOG_LEVEL"


def test_place2_ok(testdata):
    findings = [item for item in run_check(testdata / "place2" / "ok").findings if item.rule == "PLACE-2"]
    assert findings == []


def test_place3_not_ok(testdata):
    findings = [item for item in run_check(testdata / "place3" / "not-ok").findings if item.rule == "PLACE-3"]
    assert findings == []


def test_place3_ok(testdata):
    findings = [item for item in run_check(testdata / "place3" / "ok").findings if item.rule == "PLACE-3"]
    assert findings == []


def test_place4_not_ok(testdata):
    findings = [item for item in run_check(testdata / "place3" / "not-ok").findings if item.rule == "PLACE-4"]
    assert len(findings) == 2
    assert {item.key for item in findings} == {"DBAAS_AGGREGATOR_ADDRESS"}


def test_place4_ok(testdata):
    findings = [item for item in run_check(testdata / "place4" / "ok").findings if item.rule == "PLACE-4"]
    assert findings == []


def test_place6_not_ok(testdata):
    findings = [item for item in run_check(testdata / "place6" / "not-ok").findings if item.rule == "PLACE-6"]
    assert len(findings) == 1
    assert findings[0].key == "bss"


def test_place6_ok(testdata):
    findings = [item for item in run_check(testdata / "place6" / "ok").findings if item.rule == "PLACE-6"]
    assert findings == []


def test_place7_not_ok(testdata):
    findings = [item for item in run_check(testdata / "place7" / "not-ok").findings if item.rule == "PLACE-7"]
    assert len(findings) == 1
    assert findings[0].key == "shared"


def test_place7_ok(testdata):
    findings = [item for item in run_check(testdata / "place7" / "ok").findings if item.rule == "PLACE-7"]
    assert findings == []


def test_place8_not_ok(testdata):
    findings = [f for f in run_check(testdata / "place8/not-ok").findings if f.rule == "PLACE-8"]
    assert {f.key for f in findings} == {"empty", "empty-profile", "empty-creds"}
    assert len(findings) == 3


def test_place8_ok(testdata):
    assert not [f for f in run_check(testdata / "place8/ok").findings if f.rule == "PLACE-8"]
