"""Macro recognition and credRef rewrite (apply-time)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Full-value macros only (anchored). Composite → fail at apply.
# Supports ${creds.get(...).field}, ${envgen.creds.get(...).field}, and bare
# envgen.creds.get(...).field (system integration.yml style).
_CREDS_GET_INNER = (
    # Quote forms: 'id', "id", or YAML ''id'' inside an outer single-quoted value.
    r"""(?:envgen\.|cmdb\.)?creds\.get\(\s*(?:''|['\"])([\w.-]+)(?:''|['\"])\s*\)"""
    r"""\.(username|password|secret)"""
)
VALUE_MACRO_RE = re.compile(
    rf"""^\s*(?:\$\{{\s*{_CREDS_GET_INNER}\s*\}}|{_CREDS_GET_INNER})\s*$""",
    re.IGNORECASE,
)

HASH_KEY_RE = re.compile(
    r"""^#creds(?:cl|ns)?\{\s*([\w.-]+)\s*,\s*(username|password|secret)\s*\}\s*$""",
    re.IGNORECASE,
)

# Loose detect for "macro embedded in larger string"
ANY_VALUE_MACRO_RE = re.compile(
    rf"""(?:\$\{{\s*{_CREDS_GET_INNER}\s*\}}|{_CREDS_GET_INNER})""",
    re.IGNORECASE,
)

# Surgical line rewrite: "key: <macro>" → key + credRef block (preserves rest of file).
_LINE_VALUE_MACRO_RE = re.compile(
    rf"""^(\s*)([^:#\n]+?):\s*"""
    rf"""(?P<q>['\"]?)(?:\$\{{\s*{_CREDS_GET_INNER}\s*\}}|{_CREDS_GET_INNER})(?P=q)"""
    rf"""\s*(#.*)?$""",
    re.IGNORECASE,
)
_LINE_HASH_KEY_RE = re.compile(
    r"""^(\s*)(#creds(?:cl|ns)?\{\s*([\w.-]+)\s*,\s*(username|password|secret)\s*\})\s*:\s*(.*)$""",
    re.IGNORECASE,
)
_SHARED_MASTER_EXT_RE = re.compile(
    r"""^(\s*-\s*)(['\"]?)([^'\"\n]+?)\.(ya?ml)(\2)(\s*(?:#.*)?)?$""",
    re.IGNORECASE,
)


REWRITE_ROOT_KEYS = frozenset(
    {"deployParameters", "e2eParameters", "parameters"}
)
RUNTIME_ROOT_KEY = "technicalConfigurationParameters"

RUNTIME_MACRO_ACTION = (
    "Remove this macro/reference from technicalConfigurationParameters before "
    "migration completes — after external-creds cutover the pipeline fails when "
    "runtime context still references credentials (credRef is not supported there)."
)

BUILTIN_CRED_FIELDS = frozenset(
    {
        "credentialsId",
        "defaultCredentialsId",
        "tokenSecret",
        "credential",
    }
)


@dataclass(frozen=True)
class MacroMatch:
    cred_id: str
    field: str  # username | password | secret
    form: str  # value | hash


def _groups_cred_field(m: re.Match[str]) -> tuple[str, str] | None:
    """Return (cred_id, field) from a match with duplicated capture groups."""
    g = m.groups()
    for i in range(0, len(g) - 1):
        a, b = g[i], g[i + 1]
        if not isinstance(a, str) or not isinstance(b, str):
            continue
        if b.lower() not in ("username", "password", "secret"):
            continue
        if a.lower() in ("username", "password", "secret"):
            continue
        if re.fullmatch(r"[\w.-]+", a):
            return a, b.lower()
    return None


def parse_value_macro(value: str) -> MacroMatch | None:
    if not isinstance(value, str):
        return None
    m = VALUE_MACRO_RE.match(value)
    if not m:
        return None
    pair = _groups_cred_field(m)
    if not pair:
        return None
    return MacroMatch(cred_id=pair[0], field=pair[1], form="value")


def parse_hash_key(key: str) -> MacroMatch | None:
    if not isinstance(key, str):
        return None
    m = HASH_KEY_RE.match(key.strip())
    if not m:
        return None
    return MacroMatch(cred_id=m.group(1), field=m.group(2).lower(), form="hash")


def is_composite_macro_value(value: str) -> bool:
    if not isinstance(value, str):
        return False
    if VALUE_MACRO_RE.match(value):
        return False
    return bool(ANY_VALUE_MACRO_RE.search(value))


def _note_inferred(
    inferred: dict[str, str], cid: str, field: str | None
) -> None:
    if field in ("username", "password"):
        inferred[cid] = "usernamePassword"
    elif field == "secret":
        inferred.setdefault(cid, "secret")
    else:
        inferred.setdefault(cid, "secret")


def _walk_cred_refs(
    node: Any,
    inferred: dict[str, str],
    *,
    skip_runtime_subtrees: bool,
    in_runtime: bool,
) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            k_str = str(k) if k is not None else ""
            next_runtime = in_runtime
            if k_str == RUNTIME_ROOT_KEY:
                if skip_runtime_subtrees:
                    continue
                next_runtime = True
            hm = parse_hash_key(k_str) if isinstance(k, str) else None
            if hm:
                _note_inferred(inferred, hm.cred_id, hm.field)
            if isinstance(k, str) and k in BUILTIN_CRED_FIELDS and isinstance(v, str):
                _note_inferred(inferred, v, "secret")
            if isinstance(v, str):
                vm = parse_value_macro(v)
                if vm:
                    _note_inferred(inferred, vm.cred_id, vm.field)
                else:
                    for m in ANY_VALUE_MACRO_RE.finditer(v):
                        pair = _groups_cred_field(m)
                        if pair:
                            _note_inferred(inferred, pair[0], pair[1])
            else:
                _walk_cred_refs(
                    v,
                    inferred,
                    skip_runtime_subtrees=skip_runtime_subtrees,
                    in_runtime=next_runtime,
                )
    elif isinstance(node, list):
        for item in node:
            _walk_cred_refs(
                item,
                inferred,
                skip_runtime_subtrees=skip_runtime_subtrees,
                in_runtime=in_runtime,
            )


def collect_cred_refs_excluding_runtime(node: Any) -> dict[str, str]:
    """Cred-ids for CT / deploy migration — skips technicalConfigurationParameters."""
    inferred: dict[str, str] = {}
    _walk_cred_refs(node, inferred, skip_runtime_subtrees=True, in_runtime=False)
    return inferred


def collect_cred_refs_runtime_only(node: Any) -> dict[str, str]:
    """Cred-ids under technicalConfigurationParameters only."""
    inferred: dict[str, str] = {}

    def walk_runtime(n: Any) -> None:
        if isinstance(n, dict):
            for k, v in n.items():
                if str(k) == RUNTIME_ROOT_KEY:
                    _walk_cred_refs(
                        v,
                        inferred,
                        skip_runtime_subtrees=False,
                        in_runtime=True,
                    )
                else:
                    walk_runtime(v)
        elif isinstance(n, list):
            for item in n:
                walk_runtime(item)

    walk_runtime(node)
    return inferred


def collect_runtime_macro_hits(
    node: Any, *, file_path: str, source: str = "technicalConfigurationParameters"
) -> list[dict[str, Any]]:
    """List credential macros under runtime blocks with operator guidance."""
    hits: list[dict[str, Any]] = []
    creds = collect_cred_refs_runtime_only(node)
    for cred_id in sorted(creds):
        hits.append(
            {
                "file": file_path,
                "credId": cred_id,
                "source": source,
                "action": RUNTIME_MACRO_ACTION,
            }
        )
    return hits


def extract_cred_ids_from_mapping(node: Any, found: set[str] | None = None) -> set[str]:
    """Collect cred-ids from macros and Built-in fields (for unbound ParameterSet detection)."""
    if found is None:
        found = set()
    if isinstance(node, dict):
        for k, v in node.items():
            hm = parse_hash_key(str(k)) if isinstance(k, str) else None
            if hm:
                found.add(hm.cred_id)
            if isinstance(k, str) and k in BUILTIN_CRED_FIELDS and isinstance(v, str):
                found.add(v)
            if isinstance(k, str) and k == "credId" and isinstance(v, str):
                found.add(v)
            if isinstance(v, str):
                vm = parse_value_macro(v)
                if vm:
                    found.add(vm.cred_id)
                else:
                    for m in ANY_VALUE_MACRO_RE.finditer(v):
                        pair = _groups_cred_field(m)
                        if pair:
                            found.add(pair[0])
            else:
                extract_cred_ids_from_mapping(v, found)
    elif isinstance(node, list):
        for item in node:
            extract_cred_ids_from_mapping(item, found)
    return found


class CompositeMacroError(Exception):
    def __init__(self, path: str, key_path: str, value: str):
        self.path = path
        self.key_path = key_path
        super().__init__(
            f"composite macro not rewriteable: file={path} key={key_path} value={value!r}"
        )


def _cred_ref_yaml_lines(indent: str, key: str, match: MacroMatch) -> list[str]:
    child = indent + "  "
    lines = [
        f"{indent}{key}:",
        f"{child}$type: credRef",
        f"{child}credId: {match.cred_id}",
    ]
    if match.field in ("username", "password"):
        lines.append(f"{child}property: {match.field}")
    return lines


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _yaml_key(line: str) -> str | None:
    stripped = line.lstrip(" ")
    if not stripped or stripped.startswith("#") or stripped.startswith("-"):
        return None
    if ":" not in stripped:
        return None
    return stripped.split(":", 1)[0].strip()


def surgical_rewrite_consumer_text(
    text: str,
    *,
    file_path: str,
    mode: str = "restricted",
) -> tuple[str, int]:
    """Replace credential macros in-place in YAML text. Does not re-dump the file.

    mode:
      - restricted — only under deployParameters / e2eParameters / parameters
        (and applications[].parameters via nested ``parameters:`` keys);
        never inside technicalConfigurationParameters.
      - unrestricted — any key except inside technicalConfigurationParameters
        (cloud-passport main, configuration/integration.yml, etc.).
    """
    if mode not in ("restricted", "unrestricted"):
        raise ValueError(f"unknown surgical mode: {mode!r}")

    lines = text.splitlines(keepends=True)
    out: list[str] = []
    count = 0
    # Stack of indent levels where rewrite is active (restricted mode).
    rewrite_stack: list[int] = []
    # When set, skip children with greater indent (runtime block).
    skip_deeper_than: int | None = None

    for line in lines:
        # Preserve exact newline
        nl = ""
        body = line
        if line.endswith("\r\n"):
            nl = "\r\n"
            body = line[:-2]
        elif line.endswith("\n"):
            nl = "\n"
            body = line[:-1]
        elif line.endswith("\r"):
            nl = "\r"
            body = line[:-1]

        indent = _line_indent(body)
        key = _yaml_key(body)

        if skip_deeper_than is not None:
            if indent > skip_deeper_than:
                out.append(line)
                continue
            skip_deeper_than = None

        if key == RUNTIME_ROOT_KEY:
            skip_deeper_than = indent
            out.append(line)
            continue

        # Maintain restricted rewrite regions
        while rewrite_stack and indent <= rewrite_stack[-1]:
            rewrite_stack.pop()

        if key in REWRITE_ROOT_KEYS:
            rewrite_stack.append(indent)

        rewrite_on = mode == "unrestricted" or bool(rewrite_stack)
        if not rewrite_on:
            out.append(line)
            continue

        # Composite: macro embedded in a larger non-full-value string on this line
        hm_line = _LINE_HASH_KEY_RE.match(body)
        vm_line = _LINE_VALUE_MACRO_RE.match(body)
        if not hm_line and not vm_line:
            # Detect composite on "key: value" lines only
            if key is not None and ":" in body:
                val = body.split(":", 1)[1].strip().strip("'\"")
                if val and is_composite_macro_value(val):
                    raise CompositeMacroError(file_path, key, val)
            out.append(line)
            continue

        if hm_line:
            ind, _raw_key, cid, field, _rest = (
                hm_line.group(1),
                hm_line.group(2),
                hm_line.group(3),
                hm_line.group(4).lower(),
                hm_line.group(5),
            )
            match = MacroMatch(cred_id=cid, field=field, form="hash")
            new_key = cid if field == "secret" else field
            block = _cred_ref_yaml_lines(ind, new_key, match)
            out.append("\n".join(block) + nl)
            count += 1
            continue

        assert vm_line is not None
        ind = vm_line.group(1)
        k = vm_line.group(2)
        pair = _groups_cred_field(vm_line)
        if not pair:
            out.append(line)
            continue
        match = MacroMatch(cred_id=pair[0], field=pair[1], form="value")
        block = _cred_ref_yaml_lines(ind, k, match)
        out.append("\n".join(block) + nl)
        count += 1

    return "".join(out), count


def surgical_rewrite_consumer_file(
    path: "Path",
    *,
    mode: str = "restricted",
) -> int:
    """Read path, surgically rewrite macros, write only if count > 0. Returns count."""
    from pathlib import Path as PathCls

    p = PathCls(path)
    text = p.read_text(encoding="utf-8")
    new_text, count = surgical_rewrite_consumer_text(
        text, file_path=str(p), mode=mode
    )
    if count:
        p.write_text(new_text, encoding="utf-8", newline="")
    return count


def strip_shared_master_extensions_in_env_definitions(repo_root: "Path") -> int:
    """Strip .yml/.yaml from sharedMasterCredentialFiles list entries. Returns edit count."""
    from pathlib import Path as PathCls

    root = PathCls(repo_root)
    paths = sorted(
        set(
            list(root.glob("environments/*/Inventory/env_definition.yml"))
            + list(root.glob("environments/*/*/Inventory/env_definition.yml"))
            + list(root.glob("environments/*/Inventory/env_definition.yaml"))
            + list(root.glob("environments/*/*/Inventory/env_definition.yaml"))
        )
    )
    total = 0
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        out: list[str] = []
        sm_indent: int | None = None
        file_count = 0
        for line in lines:
            if line.endswith("\r\n"):
                nl, body = "\r\n", line[:-2]
            elif line.endswith("\n"):
                nl, body = "\n", line[:-1]
            elif line.endswith("\r"):
                nl, body = "\r", line[:-1]
            else:
                nl, body = "", line
            indent = _line_indent(body)
            key = _yaml_key(body)
            if sm_indent is not None:
                if indent > sm_indent or (
                    indent == sm_indent and body.lstrip(" ").startswith("-")
                ):
                    m_sm = _SHARED_MASTER_EXT_RE.match(body)
                    if m_sm:
                        body = (
                            f"{m_sm.group(1)}{m_sm.group(2)}{m_sm.group(3)}"
                            f"{m_sm.group(2)}{m_sm.group(6) or ''}"
                        )
                        file_count += 1
                    out.append(body + nl)
                    continue
                sm_indent = None
            if key == "sharedMasterCredentialFiles":
                sm_indent = indent
            out.append(body + nl)
        if file_count:
            path.write_text("".join(out), encoding="utf-8", newline="")
            total += file_count
    return total


def _env_definition_paths_for_deployer_rel(
    repo_root: "Path", rel: str
) -> list["Path"]:
    """Map a to_delete deployer cred path to env_definition.yml(.yaml) targets."""
    from pathlib import Path as PathCls

    parts = PathCls(rel.replace("\\", "/")).parts
    if len(parts) < 3 or parts[0] != "environments":
        return []
    cluster = parts[1]
    root = PathCls(repo_root)
    cluster_dir = root / "environments" / cluster
    out: list[PathCls] = []
    if len(parts) >= 3 and parts[2] == "app-deployer":
        # Cluster-level app-deployer → all envs under that cluster
        for inv in sorted(cluster_dir.glob("*/Inventory")):
            for name in ("env_definition.yml", "env_definition.yaml"):
                p = inv / name
                if p.is_file():
                    out.append(p)
        return out
    if len(parts) >= 4 and parts[3] == "app-deployer":
        env = parts[2]
        inv = cluster_dir / env / "Inventory"
        for name in ("env_definition.yml", "env_definition.yaml"):
            p = inv / name
            if p.is_file():
                out.append(p)
    return out


def strip_inventory_deployer_text(text: str) -> tuple[str, int]:
    """Remove ``inventory.deployer`` scalar lines. Returns (new_text, removals)."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    inv_indent: int | None = None
    removed = 0
    for line in lines:
        if line.endswith("\r\n"):
            nl, body = "\r\n", line[:-2]
        elif line.endswith("\n"):
            nl, body = "\n", line[:-1]
        elif line.endswith("\r"):
            nl, body = "\r", line[:-1]
        else:
            nl, body = "", line
        indent = _line_indent(body)
        key = _yaml_key(body)
        if inv_indent is not None:
            if indent <= inv_indent and not body.lstrip(" ").startswith("-"):
                inv_indent = None
            elif indent > inv_indent and key == "deployer":
                removed += 1
                continue
        if key == "inventory":
            inv_indent = indent
        out.append(body + nl)
    return "".join(out), removed


def strip_inventory_deployer_in_env_definitions(
    repo_root: "Path", deployer_credential_rels: list[str]
) -> int:
    """Drop ``inventory.deployer`` where deployer creds are deleted. Returns edit count."""
    from pathlib import Path as PathCls

    targets: set[PathCls] = set()
    for rel in deployer_credential_rels:
        for p in _env_definition_paths_for_deployer_rel(repo_root, rel):
            targets.add(p)
    total = 0
    for path in sorted(targets):
        text = path.read_text(encoding="utf-8")
        new_text, n = strip_inventory_deployer_text(text)
        if n:
            path.write_text(new_text, encoding="utf-8", newline="")
            total += n
    return total
