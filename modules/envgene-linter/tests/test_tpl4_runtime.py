import pytest

from envgene_linter.engine import run_check
from envgene_linter.model import Action


def findings(tmp_path, source, relative='templates/cloud.yml.j2'):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding='utf-8')
    return [item for item in run_check(tmp_path).findings if item.rule == 'TPL-4']


@pytest.mark.parametrize('source', [
    "{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') | default('') }}",
    "{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') | d('') }}",
    "{{ lookup( 'ansible.builtin.env' , 'PRIVATE_KEY' ) | default('') | upper }}",
    "{% if lookup('ansible.builtin.env', 'PRIVATE_KEY') is defined %}"
    "{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') }}{% endif %}",
    "{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') "
    "if lookup('ansible.builtin.env', 'PRIVATE_KEY') is defined else '' }}",
])
@pytest.mark.parametrize('relative', ['templates/cloud.yml.j2', 'templates/cloud.yaml.j2'])
def test_main_template_recognizes_protected_supported_environment_lookup(tmp_path, source, relative):
    assert findings(tmp_path, source, relative) == []


@pytest.mark.parametrize('source', [
    "{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') }}",
    "{{ lookup ('ansible.builtin.env', 'PRIVATE_KEY') | default('') }}",
    '{{ lookup("ansible.builtin.env", "PRIVATE_KEY") | default("") }}',
    "{{ lookup('ansible.builtin.env', 'PRIVATE_KEY', errors='ignore') | default('') }}",
    "{{ lookup('ansible.builtin.env', name='PRIVATE_KEY') | default('') }}",
    "{{ lookup('ansible.builtin.env', KEY) | default('') }}",
    "{{ lookup(*ARGS) | default('') }}",
    "{{ lookup(**KWARGS) | default('') }}",
    "{{ other('ansible.builtin.env', 'PRIVATE_KEY') | default('') }}",
    "{{ helper.lookup('ansible.builtin.env', 'PRIVATE_KEY') | default('') }}",
    "{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') | upper | default('') }}",
    "{{ (lookup('ansible.builtin.env', 'PRIVATE_KEY') + 1) | default('') }}",
    "{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') | default(FALLBACK) }}",
    "{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') | default('') }} {{ other() | default('') }}",
])
def test_unprotected_or_unsupported_calls_remain_review_candidates(tmp_path, source):
    result = findings(tmp_path, source)
    assert [(item.line, item.action) for item in result] == [(1, Action.REVIEW)]
    assert 'PRIVATE_KEY' not in repr(result)
    assert 'FALLBACK' not in repr(result)


@pytest.mark.parametrize('relative', ['templates/parameters.j2', 'templates/parameters/example.j2'])
def test_bare_jinja_template_does_not_assume_main_generator_lookup_rewrite(tmp_path, relative):
    result = findings(tmp_path, "{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') | default('') }}", relative)
    assert [item.line for item in result] == [1]


def test_descriptor_scalar_does_not_assume_main_generator_lookup_rewrite(tmp_path):
    source = ('tenant: tenant.yml.j2\n'
              'cloud: "{{ lookup(\'ansible.builtin.env\', \'PRIVATE_KEY\') | default(\'\') }}"\n'
              'namespaces: []\n')
    result = findings(tmp_path, source, 'templates/env_templates/example.yaml')
    assert [item.line for item in result] == [2]


def test_multiline_lookup_preserves_original_lines_and_document_prefix(tmp_path):
    source = ("---\n{{ lookup(\n 'ansible.builtin.env',\n 'PRIVATE_KEY'\n) | default('') }}\n"
              "{{ UNKNOWN }}\n{{ lookup(\n 'ansible.builtin.env',\n 'OTHER_KEY'\n) }}\n")
    result = findings(tmp_path, source)
    assert [item.line for item in result] == [6, 7]
    assert 'PRIVATE_KEY' not in repr(result)
    assert 'OTHER_KEY' not in repr(result)
    assert 'UNKNOWN' not in repr(result)


def test_lookup_rewrite_respects_raw_blocks_comments_and_string_literals(tmp_path):
    source = ("{# lookup('ansible.builtin.env', 'PRIVATE_KEY') #}\n"
              "{% raw %}{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') }}{% endraw %}\n"
              '{{ "lookup(\'ansible.builtin.env\', \'PRIVATE_KEY\')" }}\n'
              "{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') | default('') }}\n"
              '{{ OTHER }}\n')
    assert [item.line for item in findings(tmp_path, source)] == [5]


def test_lookup_rewrite_preserves_explicit_environment_rebinding(tmp_path):
    source = ("{% if lookup('ansible.builtin.env', 'PRIVATE_KEY') is defined %}\n"
              '{% set env_vars = {} %}\n'
              "{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') }}\n{% endif %}")
    assert [item.line for item in findings(tmp_path, source)] == [3]


def test_lookup_analysis_never_renders_template(tmp_path):
    source = "{{ 1 / 0 }}{{ lookup('ansible.builtin.env', 'PRIVATE_KEY') | default('') }}"
    assert findings(tmp_path, source) == []


def descriptor(source):
    return 'tenant: tenant.yml.j2\ncloud: |\n  ' + source.replace('\n', '\n  ') + '\nnamespaces: []\n'


@pytest.mark.parametrize('reference', [
    'templates_dir',
    'current_env.name',
    'current_env.environmentName',
    'current_env.cloud',
    'current_env.cloudNameWithCluster',
    'current_env.description',
    'current_env.owners',
    'current_env.env_template',
    'current_env.envSpecificParamsets',
    'current_env.additionalTemplateVariables',
    'current_env.cluster',
    'current_env.cluster.cloud_api_protocol',
    'current_env.cluster.cloud_api_url',
    'current_env.cluster.cloud_api_port',
    'current_env.cluster.cloud_public_url',
    'current_env.cloud_passport',
    'current_env.solution_structure',
])
def test_descriptor_can_use_guaranteed_context_fields_without_presence_guards(tmp_path, reference):
    source = descriptor('{{ ' + reference + ' }}')
    assert findings(tmp_path, source, 'templates/env_templates/example.yaml') == []


@pytest.mark.parametrize('reference', [
    'current_env.tenant',
    'current_env.deployer',
    'current_env.additionalTemplateVariables.mode',
    'current_env.envSpecificParamsets.deploy',
    'current_env.cloud_passport.name',
    'current_env.solution_structure.application',
    'current_env.cluster.custom',
])
def test_descriptor_optional_fields_and_dictionary_children_remain_review_candidates(tmp_path, reference):
    source = descriptor('{{ ' + reference + ' }}')
    result = findings(tmp_path, source, 'templates/env_templates/example.yaml')
    assert [item.line for item in result] == [2]


@pytest.mark.parametrize('relative', ['templates/cloud.yml.j2', 'templates/cloud.yaml.j2',
                                     'templates/parameters/example.j2'])
def test_context_guarantees_are_not_expanded_for_arbitrary_full_templates(tmp_path, relative):
    result = findings(tmp_path, '{{ current_env.cloud }}\n{{ current_env.cluster.cloud_api_url }}', relative)
    assert [item.line for item in result] == [1, 2]


@pytest.mark.parametrize('source', [
    '{% set current_env = {} %}\n{{ current_env.cloud }}',
    '{% if true %}{% set current_env = {} %}{% endif %}\n{{ current_env.cluster.cloud_api_url }}',
    '{% macro helper(current_env) %}{{ current_env.cloud }}{% endmacro %}',
    '{% with current_env = {} %}{{ current_env.cloud }}{% endwith %}',
])
def test_descriptor_context_rebinding_invalidates_guaranteed_fields(tmp_path, source):
    result = findings(tmp_path, descriptor(source), 'templates/env_templates/example.yaml')
    assert [item.line for item in result] == [2]
