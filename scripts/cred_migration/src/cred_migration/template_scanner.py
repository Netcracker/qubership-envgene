"""Template-repo cred discovery: scan consumer templates, infer cred types from usage.

Used by plan_cmd template branch when the Credential Template file
(`external-credentials.yml.j2`) does not yet exist for a solution.
"""

import re
from pathlib import Path

import yaml

# Value macro (all three prefixes) — group 1 = cred_id, group 2 = field.
_VALUE_MACRO_RE = re.compile(
    r"""\$\{\s*(?:envgen\.|cmdb\.)?creds\.get\s*\(\s*['"](?P<cred_id>[\w.-]+)['"]\s*\)\s*\.\s*(?P<field>\w+)\s*\}"""
)

# Hash-style macro key: value is the cred-id, fields implicit (username+password).
_HASH_MACRO_RE = re.compile(
    r"""['"]?\s*#creds(?:cl|ns)?\{[^}]*\}\s*['"]?\s*:\s*['"]?(?P<cred_id>[\w.-]+)['"]?"""
)

# Built-in cred field: `credentialsId: <cred-id>` (also defaultCredentialsId, tokenSecret,
# credential, credentials).
_BUILTIN_FIELD_RE = re.compile(
    r"""(?:credentialsId|defaultCredentialsId|tokenSecret|credential|credentials)\s*:\s*['"]?(?P<cred_id>[\w.-]+)['"]?"""
)

_BUILTIN_MARKER = "__builtin__"

# Consumer template file patterns per solution. Recursive globs cover both flat and nested
# Namespaces/ layouts, plus plain .yml/.yaml files.
_SOLUTION_CONSUMER_PATTERNS = (
    "*.yml.j2", "**/*.yml.j2",
    "*.yml", "**/*.yml",
    "*.yaml", "**/*.yaml",
)

# ParameterSet file patterns under templates/parameters/. Shared across solutions.
_PARAMETERS_PATTERNS = (
    "**/*.yml.j2", "**/*.yml", "**/*.yaml",
)

# Exclude Credential Template itself from consumer scan (it lists creds, doesn't reference them).
_CRED_TEMPLATE_NAME = "external-credentials.yml.j2"


def collect_cred_usages_from_text(text):
    """Extract cred usages from raw template text.

    Returns {cred_id: set(field_or_marker)} where field is `username`/`password`/`secret` (from
    value macros) or `__builtin__` (from Built-in cred field ref). Hash-macros contribute both
    `username` and `password`.
    """
    usages = {}
    for m in _VALUE_MACRO_RE.finditer(text):
        cred_id = m.group("cred_id")
        field = m.group("field")
        usages.setdefault(cred_id, set()).add(field)
    for m in _HASH_MACRO_RE.finditer(text):
        cred_id = m.group("cred_id")
        usages.setdefault(cred_id, set()).update({"username", "password"})
    for m in _BUILTIN_FIELD_RE.finditer(text):
        cred_id = m.group("cred_id")
        # Skip if this cred-id already has field usages (Built-in adds no new info).
        if cred_id not in usages:
            usages[cred_id] = set()
        usages[cred_id].add(_BUILTIN_MARKER)
    return usages


def infer_cred_type_from_usages(fields):
    """Infer cred type from the collected usage fields.

    - Any of {username, password} → usernamePassword (multi-field).
    - Otherwise (secret and/or __builtin__) → secret (single-value).
    """
    if fields & {"username", "password"}:
        return "usernamePassword"
    return "secret"


def list_env_template_solutions(repo_root):
    """Return sorted list of solution dirs under templates/env_templates/."""
    base = Path(repo_root) / "templates" / "env_templates"
    if not base.exists():
        return []
    return sorted(p for p in base.iterdir() if p.is_dir())


def scan_solution_consumer_creds(solution_dir):
    """Scan all consumer templates in a solution dir; return {cred_id: inferred_type}."""
    solution_dir = Path(solution_dir)
    combined = {}
    seen_files = set()
    for pattern in _SOLUTION_CONSUMER_PATTERNS:
        for f in solution_dir.glob(pattern):
            if f in seen_files or f.name == _CRED_TEMPLATE_NAME:
                continue
            seen_files.add(f)
            text = f.read_text(encoding="utf-8", errors="ignore")
            for cred_id, fields in collect_cred_usages_from_text(text).items():
                combined.setdefault(cred_id, set()).update(fields)
    return {cred_id: infer_cred_type_from_usages(fields) for cred_id, fields in combined.items()}


def scan_parameters_creds(repo_root):
    """Scan `templates/parameters/**/*` for cred usages; return {cred_id: inferred_type}.

    Superset - returns every cred-id referenced anywhere in ParameterSets. Callers should
    prefer `scan_descriptor_creds` for per-descriptor precision.
    """
    base = Path(repo_root) / "templates" / "parameters"
    if not base.exists():
        return {}
    combined = {}
    seen_files = set()
    for pattern in _PARAMETERS_PATTERNS:
        for f in base.glob(pattern):
            if f in seen_files:
                continue
            seen_files.add(f)
            text = f.read_text(encoding="utf-8", errors="ignore")
            for cred_id, fields in collect_cred_usages_from_text(text).items():
                combined.setdefault(cred_id, set()).update(fields)
    return {cred_id: infer_cred_type_from_usages(fields) for cred_id, fields in combined.items()}


# ---- Descriptor-based scanning (per-descriptor precise cred discovery) ----

# Fields in a consumer template that name ParameterSets to follow. Excludes
# technicalConfigurationParameterSets per Assumption 5.
_TRACKED_PARAMSET_FIELDS = ("deployParameterSets", "e2eParameterSets")


def list_descriptors(repo_root):
    """Return sorted list of Template Descriptor file paths under templates/env_templates/."""
    base = Path(repo_root) / "templates" / "env_templates"
    if not base.exists():
        return []
    return sorted(
        p for p in base.iterdir()
        if p.is_file() and p.suffix in (".yaml", ".yml")
    )


def _strip_templates_dir(path_str, repo_root):
    """Resolve a Jinja `{{ templates_dir }}/...` path to an absolute repo path."""
    stripped = path_str.replace("{{ templates_dir }}", "templates").replace(
        "{{templates_dir}}", "templates"
    ).lstrip("/")
    return Path(repo_root) / stripped


def parse_descriptor(descriptor_path, repo_root):
    """Return list of absolute template file paths this descriptor references.

    Extracts `tenant`, `cloud`, `composite_structure` scalars, and `namespaces[].template_path`.
    Descriptor-level `parametersets` field is not processed (per design decision).
    """
    text = Path(descriptor_path).read_text(encoding="utf-8")
    doc = yaml.safe_load(text) or {}
    refs = []
    for field in ("tenant", "cloud", "composite_structure"):
        value = doc.get(field)
        if isinstance(value, str):
            refs.append(_strip_templates_dir(value, repo_root))
    for ns in doc.get("namespaces") or []:
        tp = ns.get("template_path") if isinstance(ns, dict) else None
        if isinstance(tp, str):
            refs.append(_strip_templates_dir(tp, repo_root))
    return refs


def build_paramset_index(repo_root):
    """Scan `templates/parameters/**/*.{yml,yaml,yml.j2}` and index files by inner `name:` field."""
    base = Path(repo_root) / "templates" / "parameters"
    if not base.exists():
        return {}
    index = {}
    seen_files = set()
    for pattern in _PARAMETERS_PATTERNS:
        for f in base.glob(pattern):
            if f in seen_files:
                continue
            seen_files.add(f)
            try:
                doc = yaml.safe_load(f.read_text(encoding="utf-8", errors="ignore"))
            except yaml.YAMLError:
                continue
            if isinstance(doc, dict) and isinstance(doc.get("name"), str):
                index[doc["name"]] = f
    return index


def _collect_paramset_names_from_template(text):
    """Parse a template text and extract paramset names from tracked fields.

    Uses lightweight regex - avoids full YAML parse when the file may be Jinja-templated.
    """
    names = set()
    for field in _TRACKED_PARAMSET_FIELDS:
        # Match `deployParameterSets: [...]` inline or block-list form.
        for m in re.finditer(
            rf"^{field}\s*:\s*(?:\[([^\]]*)\]|\n((?:\s*-\s*['\"]?[^\n]+['\"]?\n)+))",
            text, re.MULTILINE,
        ):
            body = m.group(1) or m.group(2) or ""
            for item in re.finditer(r"['\"]([\w.-]+)['\"]", body):
                names.add(item.group(1))
            # Also match unquoted list items in block form.
            for item in re.finditer(r"-\s*([\w.-]+)\s*$", body, re.MULTILINE):
                names.add(item.group(1))
    return names


def scan_descriptor_creds(descriptor_path, repo_root):
    """Return {cred_id: inferred_type} for creds reachable from this descriptor.

    Walks: descriptor → referenced templates → cred macros + tracked ParameterSet refs →
    resolved ParameterSet files → cred macros. Excludes `technicalConfigurationParameterSets`
    per Assumption 5.
    """
    repo_root = Path(repo_root)
    paramset_index = build_paramset_index(repo_root)

    combined = {}  # {cred_id: set of fields}
    seen_files = set()
    referenced_paramset_names = set()

    template_refs = parse_descriptor(descriptor_path, repo_root)
    for tpl in template_refs:
        if not tpl.exists() or tpl in seen_files:
            continue
        seen_files.add(tpl)
        text = tpl.read_text(encoding="utf-8", errors="ignore")
        for cred_id, fields in collect_cred_usages_from_text(text).items():
            combined.setdefault(cred_id, set()).update(fields)
        referenced_paramset_names.update(_collect_paramset_names_from_template(text))

    for name in referenced_paramset_names:
        paramset_file = paramset_index.get(name)
        if paramset_file is None or paramset_file in seen_files:
            continue
        seen_files.add(paramset_file)
        text = paramset_file.read_text(encoding="utf-8", errors="ignore")
        for cred_id, fields in collect_cred_usages_from_text(text).items():
            combined.setdefault(cred_id, set()).update(fields)

    return {cred_id: infer_cred_type_from_usages(fields) for cred_id, fields in combined.items()}
