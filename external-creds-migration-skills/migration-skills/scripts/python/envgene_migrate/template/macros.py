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
            if (
                isinstance(v, dict)
                and str(v.get("$type") or "") == "credRef"
            ):
                cid = v.get("credId")
                if isinstance(cid, str) and cid:
                    prop = v.get("property")
                    field = (
                        prop if prop in ("username", "password") else "secret"
                    )
                    _note_inferred(inferred, cid, field)
                continue
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


def collect_cred_refs_runtime_only(
    node: Any, *, assume_runtime: bool = False
) -> dict[str, str]:
    """Cred-ids under technicalConfigurationParameters only.

    When ``assume_runtime`` is True, treat ``node`` as already inside a runtime
    context (e.g. a technicalConfigurationParameterSets-bound paramset body)
    and walk it without requiring the wrapper key.
    """
    inferred: dict[str, str] = {}
    if assume_runtime:
        _walk_cred_refs(
            node,
            inferred,
            skip_runtime_subtrees=False,
            in_runtime=True,
        )
        return inferred

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
    node: Any,
    *,
    file_path: str,
    source: str = "technicalConfigurationParameters",
    assume_runtime: bool = False,
) -> list[dict[str, Any]]:
    """List credential macros under runtime blocks with operator guidance."""
    hits: list[dict[str, Any]] = []
    creds = collect_cred_refs_runtime_only(node, assume_runtime=assume_runtime)
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


def strip_runtime_macros_tree(
    node: Any,
    *,
    file_path: str,
    key_path: str = "",
    in_runtime: bool = False,
) -> tuple[Any, int]:
    """Remove credential macros/refs inside runtime context. Returns (node, count).

    When ``in_runtime`` is False, only descend into ``technicalConfigurationParameters``
    blocks (and recurse elsewhere without deleting). When True, drop hash-key macros,
    full-value macros, credRef maps, and Built-in cred-id fields; composite values raise.
    Does not convert anything to credRef.
    """
    count = 0
    if isinstance(node, dict):
        new_dict: dict[Any, Any] = {}
        for k, v in node.items():
            k_str = str(k) if k is not None else ""
            child_path = f"{key_path}.{k_str}" if key_path else k_str

            if k_str == RUNTIME_ROOT_KEY:
                stripped, c = strip_runtime_macros_tree(
                    v,
                    file_path=file_path,
                    key_path=child_path,
                    in_runtime=True,
                )
                count += c
                new_dict[k] = stripped
                continue

            if not in_runtime:
                stripped, c = strip_runtime_macros_tree(
                    v,
                    file_path=file_path,
                    key_path=child_path,
                    in_runtime=False,
                )
                count += c
                new_dict[k] = stripped
                continue

            hm = parse_hash_key(k_str) if isinstance(k, str) else None
            if hm:
                count += 1
                continue
            if isinstance(k, str) and k in BUILTIN_CRED_FIELDS and isinstance(v, str):
                count += 1
                continue
            if isinstance(v, dict) and str(v.get("$type") or "") == "credRef":
                count += 1
                continue
            if isinstance(v, str):
                if is_composite_macro_value(v):
                    raise CompositeMacroError(file_path, child_path, v)
                if parse_value_macro(v):
                    count += 1
                    continue
                new_dict[k] = v
                continue

            stripped, c = strip_runtime_macros_tree(
                v,
                file_path=file_path,
                key_path=child_path,
                in_runtime=True,
            )
            count += c
            new_dict[k] = stripped
        return new_dict, count

    if isinstance(node, list):
        out: list[Any] = []
        for i, item in enumerate(node):
            stripped, c = strip_runtime_macros_tree(
                item,
                file_path=file_path,
                key_path=f"{key_path}[{i}]",
                in_runtime=in_runtime,
            )
            count += c
            out.append(stripped)
        return out, count

    return node, count


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


def _split_line_newline(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    if line.endswith("\r"):
        return line[:-1], "\r"
    return line, ""


def surgical_strip_runtime_text(
    text: str,
    *,
    file_path: str,
    mode: str = "wrapper",
) -> tuple[str, int]:
    """Delete credential macro lines in-place. Does not re-dump the file.

    mode:
      - wrapper — only under ``technicalConfigurationParameters``
      - paramset — only under ``parameters`` / ``params`` (technical-bound paramsets)
    """
    if mode not in ("wrapper", "paramset"):
        raise ValueError(f"unknown surgical strip mode: {mode!r}")

    lines = text.splitlines(keepends=True)
    out: list[str] = []
    count = 0
    strip_stack: list[int] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        body, nl = _split_line_newline(line)
        indent = _line_indent(body)
        key = _yaml_key(body)

        while strip_stack and indent <= strip_stack[-1]:
            strip_stack.pop()

        if mode == "wrapper" and key == RUNTIME_ROOT_KEY:
            strip_stack.append(indent)
            out.append(line)
            i += 1
            continue

        if mode == "paramset" and key in ("parameters", "params"):
            strip_stack.append(indent)
            out.append(line)
            i += 1
            continue

        strip_on = bool(strip_stack) and indent > strip_stack[-1]
        if not strip_on:
            out.append(line)
            i += 1
            continue

        hm_line = _LINE_HASH_KEY_RE.match(body)
        vm_line = _LINE_VALUE_MACRO_RE.match(body)
        if hm_line or vm_line:
            count += 1
            i += 1
            continue

        if key is not None and ":" in body:
            val = body.split(":", 1)[1].strip().strip("'\"")
            if val and is_composite_macro_value(val):
                raise CompositeMacroError(file_path, key, val)
            if key in BUILTIN_CRED_FIELDS and val and not val.startswith(("{", "[", "|", ">")):
                count += 1
                i += 1
                continue

        # Multiline credRef map: key: \\n  $type: credRef ...
        if key is not None and body.rstrip().endswith(":"):
            j = i + 1
            while j < len(lines):
                nb, _ = _split_line_newline(lines[j])
                if not nb.strip() or nb.lstrip().startswith("#"):
                    j += 1
                    continue
                break
            else:
                out.append(line)
                i += 1
                continue
            nb, _ = _split_line_newline(lines[j])
            nindent = _line_indent(nb)
            nstripped = nb.lstrip(" ")
            if nindent > indent and nstripped.startswith("$type:") and "credRef" in nstripped:
                count += 1
                i += 1
                while i < len(lines):
                    cb, _ = _split_line_newline(lines[i])
                    if not cb.strip():
                        i += 1
                        continue
                    if _line_indent(cb) > indent:
                        i += 1
                        continue
                    break
                continue

        out.append(line)
        i += 1

    return "".join(out), count


def surgical_strip_runtime_file(
    path: "Path",
    *,
    mode: str = "wrapper",
    dry_run: bool = False,
) -> int:
    """Read path, surgically strip runtime macros, write only if count > 0."""
    from pathlib import Path as PathCls

    p = PathCls(path)
    text = p.read_text(encoding="utf-8")
    new_text, count = surgical_strip_runtime_text(
        text, file_path=str(p), mode=mode
    )
    if count and not dry_run:
        p.write_text(new_text, encoding="utf-8", newline="")
    return count
