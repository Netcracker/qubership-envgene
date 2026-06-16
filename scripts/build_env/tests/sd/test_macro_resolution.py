import os

from scripts.build_env.tests.base_test import BaseTest

os.environ.setdefault("ENVIRONMENT_NAME", "env-01")
os.environ.setdefault("CLUSTER_NAME", "cluster-01")

from render_config_env import Context, render_obj_by_context


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ctx(**kwargs) -> Context:
    return Context(**kwargs)


def _render(template: dict, **ctx_vars) -> dict:
    return render_obj_by_context(template, _ctx(**ctx_vars))


# ---------------------------------------------------------------------------
# UC-CC-MR-1: Simple type resolution
# ---------------------------------------------------------------------------

class TestMacroSimpleTypeResolution(BaseTest):
    """
    UC-CC-MR-1 — macro references resolve context values into the template.

    Type note: render_obj_by_context works by converting the template dict to a YAML
    string (which quotes string values), substituting via Jinja2, then parsing back.
    Because template values like "{{ server_port }}" are YAML-quoted strings, the
    substituted result is also a YAML-quoted string — int/bool context values become
    their string representations ("8080", "True", "False").
    """

    def test_boolean_false_context_value_becomes_string(self):
        # UC-CC-MR-1: bool False → "False" (string). Not covered by the four-types test below.
        result = _render({"debug": "{{ debug_flag }}"}, debug_flag=False)
        assert result["debug"] == "False"
        assert isinstance(result["debug"], str)

    def test_all_four_types_resolved_in_one_template(self):
        # UC-CC-MR-1 full scenario — all parameter kinds together.
        # int/bool context vars become strings; string context vars stay strings.
        result = _render(
            {
                "api_port": "{{ server_port }}",
                "service_version": "{{ app_version }}",
                "use_ssl": "{{ ssl_enabled }}",
                "log_level": "{{ debug_mode }}",
            },
            server_port=8080,
            app_version="3.0",
            ssl_enabled=True,
            debug_mode="true",
        )
        assert result["api_port"] == "8080"
        assert result["service_version"] == "3.0"
        assert result["use_ssl"] == "True"
        assert result["log_level"] == "true"

    def test_integer_zero_becomes_string_zero(self):
        # Edge: integer 0 must not collapse to None/empty — must render as "0".
        result = _render({"timeout": "{{ zero_val }}"}, zero_val=0)
        assert result["timeout"] == "0"
        assert isinstance(result["timeout"], str)

    # ------------------------------------------------------------------
    # Negative
    # ------------------------------------------------------------------

    def test_missing_reference_renders_as_empty(self):
        # ChainableUndefined: undefined variable must not raise — renders to empty/None.
        result = _render({"key": "{{ nonexistent_var }}"})
        assert result.get("key") in (None, "", "None")

    def test_partial_string_with_defined_macro_substitutes_only_macro(self):
        # Macro embedded in a larger string — surrounding text must be preserved.
        result = _render({"url": "https://{{ host }}/api"}, host="example.com")
        assert result["url"] == "https://example.com/api"

    def test_partial_string_with_missing_macro_preserves_surrounding_text(self):
        # Undefined macro renders to empty string; the rest of the string stays intact.
        result = _render({"url": "prefix-{{ missing }}-suffix"})
        assert "prefix" in str(result.get("url", ""))
        assert "suffix" in str(result.get("url", ""))


# ---------------------------------------------------------------------------
# UC-CC-MR-2: Complex structure resolution
# ---------------------------------------------------------------------------

class TestMacroComplexStructureResolution(BaseTest):
    """
    UC-CC-MR-2 — macro substitution in nested dict templates with string context values.

    Limitation: passing dict or list objects as context variables does not work because
    Python's str() representation of dicts/lists is not valid YAML.  All context
    variables substituted via "{{ var }}" must be scalar (string, int, bool) values.
    """

    def test_nested_dict_template_all_leaf_macros_resolved(self):
        # UC-CC-MR-2: template IS a nested dict; all leaf values are macro references.
        # Each leaf gets substituted individually and the nested structure is preserved.
        result = _render(
            {
                "connection": {
                    "host": "{{ db_host }}",
                    "port": "{{ db_port }}",
                    "ssl": "{{ db_ssl }}",
                }
            },
            db_host="db.example.com",
            db_port="5432",
            db_ssl="true",
        )
        assert result["connection"]["host"] == "db.example.com"
        assert result["connection"]["port"] == "5432"
        assert result["connection"]["ssl"] == "true"

    def test_deeply_nested_dict_all_levels_preserved(self):
        # Three levels of nesting — macro substitution works at any depth.
        result = _render(
            {"a": {"b": {"c": "{{ leaf_val }}"}}},
            leaf_val="42",
        )
        assert result["a"]["b"]["c"] == "42"

    def test_list_in_template_with_macro_elements_resolved(self):
        # List template with macro elements — each item is substituted.
        result = _render(
            {"servers": ["{{ host1 }}", "{{ host2 }}"]},
            host1="host1.example.com",
            host2="host2.example.com",
        )
        assert isinstance(result["servers"], list)
        assert result["servers"][0] == "host1.example.com"
        assert result["servers"][1] == "host2.example.com"

    def test_multiline_string_in_template_value_collapses_to_single_line(self):
        # UC-CC-MR-2: when a multiline string is injected via {{ var }}, YAML single-quote
        # scalar normalization collapses internal newlines to spaces — multiline is NOT preserved.
        yaml_template = "line1\nline2\nline3\n"
        result = _render({"rendered_template": "{{ yaml_template }}"}, yaml_template=yaml_template)
        rendered = result["rendered_template"]
        # Newlines are not preserved through YAML single-quote normalization.
        assert "\n" not in rendered
        # All text tokens are still present.
        assert "line1" in rendered
        assert "line2" in rendered
        assert "line3" in rendered

    def test_string_concatenation_with_two_macros(self):
        # {{ host }}:{{ port }} — both macros substituted; result is a single string value.
        result = _render({"address": "{{ host }}:{{ port }}"}, host="db.example.com", port=5432)
        assert result["address"] == "db.example.com:5432"

    # ------------------------------------------------------------------
    # Negative
    # ------------------------------------------------------------------

    def test_missing_complex_reference_does_not_raise(self):
        # ChainableUndefined: missing variable in a template with a nested structure
        # must not raise and leaves other resolved keys intact.
        result = _render(
            {"cfg": "{{ missing_config }}", "host": "{{ db_host }}"},
            db_host="db.example.com",
        )
        assert result.get("cfg") in (None, "", "None", {})
        assert result["host"] == "db.example.com"


# ---------------------------------------------------------------------------
# Backward compatibility — ansible-style syntax rewriting
# ---------------------------------------------------------------------------

class TestMacroBackwardCompatibility(BaseTest):
    """Backward compat: replace_ansible_stuff rewrites deprecated patterns before rendering."""

    def test_underscore_variable_replaced_with_plain(self):
        # {{ _tenant }} → {{ tenant }} via replace_ansible_stuff.
        # Without the rewrite, _tenant would be undefined and render to empty string.
        result = _render({"label": "{{ _tenant }}"}, tenant="acme-corp")
        assert result["label"] == "acme-corp"

    def test_ansible_to_nice_yaml_filter_replaced_without_error(self):
        # ansible.builtin.to_nice_yaml → to_nice_yaml.
        # Must not raise TemplateError after replacement.
        result = render_obj_by_context(
            {"output": "{{ data | ansible.builtin.to_nice_yaml }}"},
            _ctx(data={"key": "value"}),
        )
        assert "key" in str(result.get("output", ""))
