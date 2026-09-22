import pytest

from envgene_linter.security_values import classify, parse_reference, valid_external

TOKEN = 'ENC[AES256_GCM,data:YWJj,iv:YWJj,tag:YWJj,type:str]'
META = {'sops': {'mac': TOKEN, 'age': [{'recipient': 'age1synthetic', 'enc': 'synthetic-envelope'}], 'version': '3.8.1'}}


@pytest.mark.parametrize('value,state', [
    ('synthetic-secret', 'literal'), (True, 'literal'), (123, 'literal'),
    ('', 'empty'), (None, 'empty'),
    ('${UNVERIFIED_VARIABLE}', 'unknown'), ('{{ secret }}', 'unknown'),
    ('prefix ${creds.get("id").password}', 'unknown'),
    ('[encrypted:AES256_Fernet]synthetic', 'unsupported'),
    ('ENC[garbage]', 'unknown'), (TOKEN, 'unknown'),
])
def test_scalar_states(value, state):
    assert classify(value, {}) == state


def test_sops_is_value_specific_and_requires_metadata():
    assert classify(TOKEN, META) == 'protected'
    assert classify('plaintext', META) == 'literal'
    assert classify('prefix ' + TOKEN, META) == 'unknown'
    for meta in ({}, {'sops': {}}, {'sops': {'mac': TOKEN}}, {'sops': {'mac': 'bad', 'age': [{}]}}):
        assert classify(TOKEN, meta) == 'unknown'


@pytest.mark.parametrize('value,expected', [
    ('${creds.get("id").password}', ('id', 'password', 'local')),
    ("envgen.creds.get('id').secret", ('id', 'secret', 'system')),
    ("${ creds . get ( 'id' ) . username }", ('id', 'username', 'local')),
    ('${creds.get("id")}', None),
    ({'$type': 'credRef', 'credId': 'id', 'property': 'password'}, ('id', 'password', 'external')),
    ({'$type': 'credRef', 'credId': 'id'}, ('id', None, 'external')),
    ('${creds.get("id").secret}suffix', None),
    ('${creds.get("${DYNAMIC}").secret}', None),
    ({'$type': 'credRef', 'credId': '${DYNAMIC}'}, None),
    ({'$type': 'credRef', 'credId': 'id', 'property': 7}, None),
])
def test_only_complete_literal_references(value, expected):
    assert parse_reference(value) == expected


def test_external_requires_reference_shape_without_local_data():
    assert valid_external({'type': 'external', 'secretStore': 'store'})
    assert valid_external({'type': 'external', 'secretStore': 'store', 'properties': [{'name': 'password'}]})
    assert valid_external({'type': 'external'})
    assert not valid_external({'type': 'external', 'secretStore': 'store', 'data': {'password': 'visible'}})
    assert not valid_external({'type': 'external', 'secretStore': 'store', 'properties': [42]})


@pytest.mark.parametrize('entry', [
    {'type': 'external', 'password': 'visible'},
    {'type': 'external', 'create': 'not-bool'},
    {'type': 'external', 'properties': [{'name': 'custom'}]},
    {'type': 'external', 'properties': [{'name': 'password', 'value': 'visible'}]},
])
def test_unknown_external_shapes_are_not_assumed_safe(entry):
    entry["secretStore"] = "store"
    assert not valid_external(entry)


def test_external_reference_cannot_hide_inline_fields():
    assert parse_reference({'$type': 'credRef', 'credId': 'id', 'password': 'visible'}) is None
    assert parse_reference({'$type': 'credRef', 'credId': 'id', 'property': 'custom'}) is None


@pytest.mark.parametrize('updates', [
    {'version': ''}, {'version': '   '}, {'age': [{'enc': 'envelope'}]},
    {'age': [{'recipient': '', 'enc': 'envelope'}]},
])
def test_sops_requires_recipient_identity_and_nonblank_version(updates):
    meta = {**META['sops'], **updates}
    assert classify(TOKEN, {'sops': meta}) == 'unknown'


@pytest.mark.parametrize('value', ['${creds.get("id").token}', "envgen.creds.get('id')", "envgen.creds.get('id').token"])
def test_unsupported_local_forms_remain_unknown(value):
    assert parse_reference(value) is None
    assert classify(value, {}) == 'unknown'


def test_plain_dollar_characters_are_literal():
    assert classify('pa$$word', {}) == 'literal'
    assert classify('$UNVERIFIED', {}) == 'unknown'


def test_explicit_null_external_property_is_unknown():
    assert parse_reference({'$type': 'credRef', 'credId': 'id', 'property': None}) is None
