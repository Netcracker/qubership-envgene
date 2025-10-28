import re
from envgenehelper import logger

from scripts.build_env.jinja.jinja import JINJA_FILTERS

general_warn_message = (
    "All Ansible built-in filters (ansible.builtin.*) in this template need to be removed/replaced. "
    "Using such filters is no longer allowed. Only standard/custom Jinja2 filters should be used. "
    f"List of Jinja2 custom filters: {list(JINJA_FILTERS.keys())}"
)

incorrect_template_warn_message = (
    "Invalid template: Template was automatically fixed."
)

leading_underscore_warn_message = (
    "Template contained variables with leading underscores (_var). "
    "Underscore prefix was automatically removed. "
    "Leading underscores don't make sense in python-based templates, unlike ansible before"
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
    (
        re.compile(r"\|\s*default\((['\"])(.+?)\1\s*\)"),
        r"| default(\1\2\1, true)",
        "jinja2 default without true",
        incorrect_template_warn_message
    ),
    # {{ _var }} -> {{ var }}
    (
        re.compile(r"(?<=\b)_([a-zA-Z_][a-zA-Z0-9_]*)"),
        r"\1",
        "Jinja variable with leading underscore",
        leading_underscore_warn_message,
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
                    "Replaced %s in template '%s'. %s",
                    name,
                    template_path,
                    message,
                )
            else:
                logger.warning(
                    "Replaced %s in template: %r. %s",
                    name,
                    match.string,
                    message,
                )
            logger.info(
                "Pattern: %s | Match: %r -> Replacement: %r",
                name,
                match.group(0),
                pattern.sub(replacement, match.group(0)),
            )
        template_str = pattern.sub(replacement, template_str)

    return template_str
