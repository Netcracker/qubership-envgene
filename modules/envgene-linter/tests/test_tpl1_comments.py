import pytest

from envgene_linter.model import Action
from test_tpl1 import findings, parameter, write
from test_tpl1_repository_scope import descriptor, tpl1


@pytest.mark.parametrize('source', [
    '# VALUE: "{{ current_env.name }}"\nparameters: {}\n',
    'parameters: {} # {% if enabled %}\n',
    'parameters: {}\n  # {{ current_env.name }}\n',
    '# {{ unclosed\nparameters: {} # }}\n',
    'parameters: {} # {# template comment #}\n',
    'VALUE: plain # "{{ current_env.name }}"\n',
    'VALUE: don\'t render # {{ current_env.name }}\n',
    'VALUE: a "quoted" word # {{ current_env.name }}\n',
    'VALUE: first line\n  " # {{ current_env.name }}"\n',
    r'VALUE: "escaped \\" # {{ current_env.name }}' + '\n',
])
def test_yaml_comments_do_not_produce_findings(repo, source):
    parameter(repo, source)
    assert findings(repo) == []


@pytest.mark.parametrize('source,position', [
    ('VALUE: "# {{ current_env.name }}"\n', (1, 11)),
    ("VALUE: '# {{ current_env.name }}'\n", (1, 11)),
    (r'VALUE: "escaped \" # {{ current_env.name }}"' + '\n', (1, 22)),
    ("VALUE: 'it''s # {{ current_env.name }}'\n", (1, 17)),
    ('VALUE: "first line\n# {{ current_env.name }}"\n', (2, 3)),
    ('VALUE: |\n  # {{ current_env.name }}\n', (2, 5)),
    ('VALUE: >-\n  # {{ current_env.name }}\n', (2, 5)),
    ('VALUE: |2 # {{ ignored }}\n  # {{ current_env.name }}\n', (2, 5)),
    ('items:\n  - VALUE: |2\n      # {{ current_env.name }}\n', (3, 9)),
    ('items:\n  - |2\n    # {{ current_env.name }}\n', (3, 7)),
    ('VALUE: |\n    first line\n  # {{ ignored }}\nOTHER: "{{ current_env.name }}"\n', (4, 9)),
    ('VALUE: >\n\n  # {{ current_env.name }}\n# {{ ignored }}\n', (3, 5)),
])
def test_hash_in_scalar_content_is_still_checked(repo, source, position):
    parameter(repo, source)
    assert [(item.line, item.column, item.action) for item in findings(repo)] == [(*position, Action.FIX)]


@pytest.mark.parametrize('source', [
    'VALUE: !!str "# {{ current_env.name }}"\n',
    'VALUE: &name "# {{ current_env.name }}"\n',
    'VALUE: !<tag:yaml.org,2002:str> "# {{ current_env.name }}"\n',
    '{"# key": "{{ current_env.name }}"}\n',
])
def test_scalar_properties_and_flow_quotes_keep_active_content(repo, source):
    parameter(repo, source)
    assert [item.action for item in findings(repo)] == [Action.FIX]


@pytest.mark.parametrize('source', [
    '"VALUE": |\n  # {{ current_env.name }}\n',
    "'VALUE': >-\n  # {{ current_env.name }}\n",
    '---\n  " # {{ current_env.name }}"\n',
    'VALUE: first line\n  "# {{ current_env.name }}"\n',
])
def test_quoted_keys_and_document_markers_preserve_scalar_content(repo, source):
    parameter(repo, source)
    assert [item.action for item in findings(repo)] == [Action.FIX]


@pytest.mark.parametrize('suffix,expected_count', [('', 1), ('{% if enabled %}\n', 2)])
@pytest.mark.parametrize('source', [
    '--- |\n  # {{ current_env.name }}\n',
    '--- "prefix # {{ current_env.name }}"\n',
    '? "prefix # {{ current_env.name }}"\n: value\n',
    '{? "prefix # {{ current_env.name }}": value}\n',
    '? |\n  # {{ current_env.name }}\n: value\n',
])
def test_explicit_yaml_nodes_keep_active_jinja(repo, source, suffix, expected_count):
    parameter(repo, source + suffix)
    assert [item.action for item in findings(repo)] == [Action.FIX] * expected_count


@pytest.mark.parametrize('suffix,expected', [
    ('', [(1, 15, Action.FIX)]),
    ('{% endif %}\n', [(1, 15, Action.FIX), (3, 1, Action.FIX)]),
])
def test_statement_in_plain_scalar_does_not_expose_continuation_comment(repo, suffix, expected):
    parameter(repo, 'VALUE: prefix {% if enabled %}\n  "hello # {{ current_env.name }}"\n' + suffix)
    assert [(item.line, item.column, item.action) for item in findings(repo)] == expected


@pytest.mark.parametrize('suffix,expected', [
    ('', []),
    ('{% if enabled %}\n', [(4, 1, Action.FIX)]),
])
def test_closing_delimiter_in_comment_cannot_complete_quoted_expression(repo, suffix, expected):
    parameter(repo, 'VALUE: "{{ incomplete"\n# }}\n# {{ current_env.name }}\n' + suffix)
    assert [(item.line, item.column, item.action) for item in findings(repo)] == expected


@pytest.mark.parametrize('source,position', [
    ('# {{ unclosed\nVALUE: "{{ current_env.name }}"\n', (2, 9)),
    ('# {% if ignored %}\nVALUE: "{{ current_env.name }}" # {{ ignored }}\n', (2, 9)),
    ('# "unclosed quote {{ ignored }}\nVALUE: "{{ current_env.name }}"\n', (2, 9)),
    ('# {{ ignored }}\nVALUE: {{ current_env.name }}\n', (2, 8)),
    ('# {{ ignored }}\n{% if enabled %}\nVALUE: [\n', (2, 1)),
    ('VALUE: "{{ current_env.name }}" # {{ ignored }}\n', (1, 9)),
])
def test_comments_do_not_hide_active_jinja_or_shift_positions(repo, source, position):
    parameter(repo, source)
    assert [(item.line, item.column, item.action) for item in findings(repo)] == [(*position, Action.FIX)]


@pytest.mark.parametrize('source,expected', [
    ('VALUE: plain\n    # first\n    # second\nN: "{{ current_env.name }}"\n',
     [(4, 5, Action.FIX)]),
    ('VALUE: plain\n  # first\n  # second\n"{{ current_env.key }}": plain\n',
     [(4, 2, Action.FIX)]),
    ('VALUE: plain # first\n\n  # second\nNEXT: "{{ current_env.name }}"\n',
     [(4, 8, Action.FIX)]),
    ('# {{ current_env.name }}', []),
])
def test_grouped_comments_never_mask_the_next_active_line(repo, source, expected):
    parameter(repo, source)
    assert [(item.line, item.column, item.action) for item in findings(repo)] == expected


def test_commented_descriptor_field_is_ignored(tmp_path):
    write(tmp_path / 'templates/env_templates/dev.yaml',
          descriptor('#envSpecificSchema: "{{ templates_dir }}/schema.yml"\n'))
    assert tpl1(tmp_path) == []


@pytest.mark.parametrize('placeholder', ['id', 'externalId'])
def test_application_placeholders_remain_review(repo, placeholder):
    parameter(repo, 'VALUE: "https://example.invalid/task/{{' + placeholder + '}}" # {{ current_env.name }}\n')
    assert [(item.line, item.column, item.action) for item in findings(repo)] == [(1, 38, Action.REVIEW)]
