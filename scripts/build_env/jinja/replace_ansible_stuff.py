import re
from envgenehelper import logger
from jinja.jinja import JINJA_FILTERS

general_warn_message = (
    "All Ansible built-in filters (ansible.builtin.*) in this template need to be removed/replaced. "
    "Using such filters is no longer allowed. Only standard/custom Jinja2 filters should be used. "
    f"List of Jinja2 custom filters: {list(JINJA_FILTERS.keys())}"
)

incorrect_template_warn_message = (
    "Invalid template: Template was automatically fixed."
)

underscore_var_warn_message = (
    "Local variables with leading underscores (like {{ _tenant }}) are no longer supported. "
    "Use the main variable name instead (e.g. {{ tenant }})."
)

REPLACEMENTS = [
    # ansible.builtin.to_nice_yaml -> to_nice_yaml
    (
        re.compile(r"(\|\s*)ansible\.builtin\.to_nice_yaml(\s*(?:\([^)]*\))?)"),
        r"\1to_nice_yaml\2",
        "ansible.builtin.to_nice_yaml",
        general_warn_message
    ),
    # lookup('ansible.builtin.env', 'VAR') -> env_vars.VAR
    (
        re.compile(r"lookup\(\s*'ansible\.builtin\.env'\s*,\s*'([^']+)'\s*\)"),
        r"env_vars.\1",
        "ansible.builtin.env lookup",
        general_warn_message
    ),
    # | default('x') -> | default('x', true)
    (
        re.compile(r"\|\s*default\((['\"])(.+?)\1\s*\)"),
        r"| default(\1\2\1, true)",
        "jinja2 default without true",
        incorrect_template_warn_message
    ),
    # {{ _tenant }} -> {{ tenant }}
    (
        re.compile(r"{{\s*_(\w+)\s*}}"),
        r"{{ \1 }}",
        "jinja2 underscore variable",
        underscore_var_warn_message
    ),
]


def replace_ansible_stuff(template_str: str, template_path: str = "") -> str:
    template_str = template_str.lstrip()
    if template_str.startswith('---'):
        template_str = template_str.split('\n', 1)[1]

    for pattern, replacement, name, message in REPLACEMENTS:
        for match in pattern.finditer(template_str):
            if template_path:
                logger.warning(
                    "[JINJA] Replaced %s in template '%s'. %s",
                    name,
                    template_path,
                    message,
                )
            else:
                logger.warning(
                    "[JINJA] Replaced %s in template: %r. %s",
                    name,
                    match.string,
                    message,
                )
            logger.warning(
                "[JINJA] Pattern: %s | Match: %r -> Replacement: %r",
                name,
                match.group(0),
                pattern.sub(replacement, match.group(0)),
            )
        template_str = pattern.sub(replacement, template_str)

    return template_str


def escaping_quotation(yaml_text: str) -> str:
    def replace_line(line: str) -> str:
        if ':' not in line:
            return line

        key, value = line.split(':', 1)
        val = value.strip()

        if val.startswith('"${') and val.endswith('}"'):
            inner = val[1:-1]
            if '\\"' in inner:
                return line

            escaped_inner = inner.replace('"', '\\"')
            return f'{key}: "{escaped_inner}"'

        return line

    lines = yaml_text.splitlines()
    fixed_lines = [replace_line(line) for line in lines]
    return "\n".join(fixed_lines)
