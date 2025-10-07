import pytest
from filter_namespaces import filter_namespaces

@pytest.fixture
def sample_namespaces():
    return [ 'ns1','ns2','ns3']

@pytest.fixture
def sample_bgd():
    return {
        "peerNamespace": {"name": "ns1"},
        "originNamespace": {"name": "ns3"},
    }

def test_no_filter_returns_all(sample_namespaces, sample_bgd):
    result = filter_namespaces(sample_namespaces, "", sample_bgd)
    assert len(result) == 3
    assert {ns for ns in result} == {"ns1", "ns2", "ns3"}

def test_inclusion_filter_by_name(sample_namespaces, sample_bgd):
    result = filter_namespaces(sample_namespaces, "ns1,ns3", sample_bgd)
    assert len(result) == 2
    assert {ns for ns in result} == {"ns1", "ns3"}

def test_exclusion_filter_by_name(sample_namespaces, sample_bgd):
    result = filter_namespaces(sample_namespaces, "!ns2", sample_bgd)
    assert len(result) == 2
    assert {ns for ns in result} == {"ns1", "ns3"}

def test_inclusion_filter_with_alias(sample_namespaces, sample_bgd):
    result = filter_namespaces(sample_namespaces, "@peer,@origin", sample_bgd)
    assert len(result) == 2
    assert {ns for ns in result} == {"ns1", "ns3"}

def test_exclusion_filter_with_alias(sample_namespaces, sample_bgd):
    result = filter_namespaces(sample_namespaces, "!@alias1", sample_bgd)
    assert len(result) == 2
    assert {ns for ns in result} == {"ns2", "ns3"}

def test_invalid_alias_raises_error(sample_namespaces, sample_bgd):
    with pytest.raises(ValueError) as exc:
        filter_namespaces(sample_namespaces, "@unknown", sample_bgd)
    assert "Unknown alias" in str(exc.value)
