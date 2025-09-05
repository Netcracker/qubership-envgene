import re
from envgenehelper import logger

from scripts.build_env.jinja_filters import JINJA_FILTERS

general_warn_message = (
    "All Ansible built-in filters (ansible.builtin.*) in this template need to be removed/replaced. "
    "Using such filters is no longer allowed. Only standard/custom Jinja2 filters should be used. "
    f"List of Jinja2 custom filters: {list(JINJA_FILTERS.keys())}"
)

REPLACEMENTS = [
    # ansible.builtin.to_nice_yaml -> to_nice_yaml
    (
        re.compile(r"(\|\s*)ansible\.builtin\.to_nice_yaml(\s*(?:\([^)]*\))?)"),
        r"\1to_nice_yaml\2",
        "ansible.builtin.to_nice_yaml",
    ),
    # lookup('ansible.builtin.env', 'VAR') -> env_vars.VAR
    (
        re.compile(r"lookup\(\s*'ansible\.builtin\.env'\s*,\s*'([^']+)'\s*\)"),
        r"env_vars.\1",
        "ansible.builtin.env lookup",
    ),
]


def replace_ansible_stuff(template_str: str, template_path: str = "") -> str:
    result = template_str
    for pattern, replacement, name in REPLACEMENTS:
        for match in pattern.finditer(result):
            if template_path:
                logger.warning(
                    "Replaced %s in template '%s'. %s",
                    name,
                    template_path,
                    general_warn_message,
                )
            else:
                logger.warning(
                    "Replaced %s in snippet: %r. %s",
                    name,
                    match.string,
                    general_warn_message,
                )
        result = pattern.sub(replacement, result)

    return result
