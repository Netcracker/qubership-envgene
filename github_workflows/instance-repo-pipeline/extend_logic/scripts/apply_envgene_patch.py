#!/usr/bin/env python3
import os
import re
import shutil
import sys
from pathlib import Path

try:
    from ruamel.yaml import YAML
except ImportError:
    print("Error: ruamel.yaml required. Add to Dockerfile: pip install ruamel.yaml", file=sys.stderr)
    sys.exit(1)


def resolve_version_tag():
    """Tag used as a subdirectory under --output-dir (matches pipeline image version)."""
    tag = (
        os.environ.get("DOCKER_IMAGE_TAG")
        or os.environ.get("INSTANCE_REPO_PIPELINE_IMAGE_TAG")
        or "latest"
    ).strip()
    return tag or "latest"


def sanitize_tag(tag: str) -> str:
    """Filesystem-safe directory name; rejects path separators."""
    tag = (tag or "").strip()
    if not tag:
        return "latest"
    if ".." in tag or "/" in tag or "\\" in tag:
        raise ValueError(
            f"Invalid DOCKER_IMAGE_TAG: {tag!r} (must not contain path separators)"
        )
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", tag)
    if not safe or not re.search(r"[0-9a-zA-Z]", safe):
        return "latest"
    return safe


# ========== MERGE ENV: add or replace variables in .env files ==========

def do_merge_env(target_file, content):
    """Add or replace KEY=value in .env file."""
    text = target_file.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    # Parse existing: key -> (line_index, full_line)
    existing = {}
    for i, line in enumerate(lines):
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            key = s.split("=", 1)[0].strip()
            if key:
                existing[key] = (i, line)

    to_add = {k: v for k, v in content.items() if k not in existing}
    to_update = {k: v for k, v in content.items() if k in existing}

    if not to_add and not to_update:
        return "skipped (no changes)"

    def format_env(key, val):
        val_str = str(val).strip('"\'')
        return f'{key}="{val_str}"' if " " in val_str or "\n" in val_str else f"{key}={val_str}"

    # Replace existing
    for key, value in to_update.items():
        idx, _ = existing[key]
        lines[idx] = format_env(key, value) + "\n"

    # Append new at end (no extra blank line)
    if to_add:
        new_lines = "".join(format_env(k, v) + "\n" for k, v in to_add.items())
        lines.append(new_lines)

    target_file.write_text("".join(lines), encoding="utf-8")

    parts = []
    if to_update:
        parts.append(f"updated {list(to_update.keys())}")
    if to_add:
        parts.append(f"inserted {list(to_add.keys())}")
    return "; ".join(parts)


# ========== MERGE YAML PATH: add keys to block at dotted path (no section needed) ==========

def _find_block_by_path(lines, path_str):
    """Find (line_index, content_indent) of block at path like jobs.process_environment_variables.outputs."""
    parts = path_str.split(".")
    search_start = 0
    block_line = None
    content_indent = 2
    prev_indent = -1

    for part in parts:
        found = None
        for i in range(search_start, len(lines)):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            line_indent = len(line) - len(line.lstrip())
            if ":" in stripped and not stripped.startswith("-"):
                key = stripped.split(":")[0].strip()
                if key == part and line_indent > prev_indent:
                    found = (i, line_indent)
                    search_start = i + 1
                    break
        if found is None:
            return None, 2
        block_line, prev_indent = found
        content_indent = prev_indent + 2

    return block_line, content_indent


def do_merge_yaml_path(target_file, content, path_str):
    """Merge content into YAML block at dotted path (e.g. jobs.process_environment_variables.outputs)."""
    lines = target_file.read_text(encoding="utf-8").splitlines(keepends=True)

    block_line, block_indent = _find_block_by_path(lines, path_str)
    if block_line is None:
        raise ValueError(f"Block '{path_str}' not found")

    block_key_indent = block_indent - 2
    existing = {}
    for i in range(block_line + 1, len(lines)):
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())
        if line.strip() and line_indent <= block_key_indent:
            break
        s = line.strip()
        if s and not s.startswith("#") and ":" in s and not s.startswith("-"):
            key = s.split(":")[0].strip()
            if key:
                existing[key] = (i, line)

    to_add = {k: v for k, v in content.items() if k not in existing}
    to_update = {k: v for k, v in content.items() if k in existing}

    if not to_add and not to_update:
        return "skipped (no changes)"

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096

    for key, value in to_update.items():
        idx, old_line = existing[key]
        indent = len(old_line) - len(old_line.lstrip())
        from io import StringIO
        buf = StringIO()
        yaml.dump({key: value}, buf)
        formatted = buf.getvalue().rstrip().split("\n")
        new_line = "".join(" " * indent + s + "\n" for s in formatted)
        lines[idx] = new_line

    if to_add:
        from io import StringIO
        buf = StringIO()
        yaml.dump(to_add, buf)
        text = buf.getvalue().rstrip()
        spaces = " " * block_indent
        indented = "\n".join(spaces + (s.lstrip() if s.startswith(" ") else s) for s in text.split("\n"))
        lines.insert(block_line + 1, indented + "\n")

    target_file.write_text("".join(lines), encoding="utf-8")

    parts = []
    if to_update:
        parts.append(f"updated {list(to_update.keys())}")
    if to_add:
        parts.append(f"inserted {list(to_add.keys())}")
    return "; ".join(parts)


# ========== MERGE: add or replace keys after comment #SECTION (YAML) ==========

def do_merge(target_file, content, section):
    lines = target_file.read_text(encoding="utf-8").splitlines(keepends=True)

    # Find the line with comment (e.g. #DOCKER_IMAGE_NAMES)
    section_line = None
    indent = 2
    for i, line in enumerate(lines):
        text = line.strip()
        if text.startswith("#") and section.upper() in text.upper():
            section_line = i
            indent = len(line) - len(line.lstrip())
            break

    if section_line is None:
        raise ValueError(f"Section #{section} not found")

    # Collect all existing keys in file: key -> (line_number, line)
    existing = {}
    for i, line in enumerate(lines):
        text = line.strip()
        if text and not text.startswith("#") and ":" in text and not text.startswith("-"):
            key = text.split(":")[0].strip()
            if key:
                existing[key] = (i, line)

    # Split: what to add, what to replace
    to_add = {k: v for k, v in content.items() if k not in existing}
    to_update = {k: v for k, v in content.items() if k in existing}

    if not to_add and not to_update:
        return "skipped (no changes)"

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096

    # Replace existing keys
    for key, value in to_update.items():
        idx, old_line = existing[key]
        spaces = " " * (len(old_line) - len(old_line.lstrip()))
        from io import StringIO
        buf = StringIO()
        yaml.dump({key: value}, buf)
        formatted = buf.getvalue().rstrip().split("\n")
        new_line = "".join(spaces + s + "\n" for s in formatted)
        lines[idx] = new_line

    # Insert new keys after section comment
    if to_add:
        from io import StringIO
        buf = StringIO()
        yaml.dump(to_add, buf)
        text = buf.getvalue().rstrip()
        spaces = " " * max(indent, 2)
        indented = "\n".join(spaces + (s.lstrip() if s.startswith(" ") else s) for s in text.split("\n"))
        lines.insert(section_line + 1, indented + "\n")

    target_file.write_text("".join(lines), encoding="utf-8")

    parts = []
    if to_update:
        parts.append(f"updated {list(to_update.keys())}")
    if to_add:
        parts.append(f"inserted {list(to_add.keys())}")
    return "; ".join(parts)


# ========== INSERT: insert block after/before ### SECTION ### or by step name ==========

def find_insert_position(lines, section, after=True):
    """Find position and indent of marker line.
    after=True: insert after ### SECTION - END ###
    after=False: insert before ### SECTION - START ###
    Returns (insert_pos, base_indent)."""
    marker = f"### {section} - {'END' if after else 'START'} ###"
    for i, line in enumerate(lines):
        if marker in line.strip():
            indent = len(line) - len(line.lstrip())
            # after: insert at i+1; before: insert at i
            pos = i + 1 if after else i
            return pos, indent
    return None, 0


def find_step_position(lines, step_name, after=True):
    """Find insert position by step name (e.g. 'Create env file for container').
    after=True: insert after the step ends; after=False: insert before the step starts.
    Step name matching is case-insensitive and supports partial match.
    Returns (insert_pos, base_indent) or (None, 0)."""
    step_indent = None
    step_start = None
    step_end = None
    step_name_lower = step_name.lower().strip()

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Match step: - name: "..." or - name: '...' or - name: ...
        m = re.match(r'^-\s*name\s*:\s*(?:"([^"]*)"|\'([^\']*)\'|(\S.*?))\s*$', stripped)
        if m:
            name = (m.group(1) or m.group(2) or m.group(3) or "").strip()
            if step_name_lower in name.lower() or name.lower() in step_name_lower:
                line_indent = len(line) - len(line.lstrip())
                step_start = i
                step_indent = line_indent
                # Step continues until next step (- name:) at same indent
                for j in range(i + 1, len(lines)):
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    if not next_stripped:
                        continue
                    next_indent = len(next_line) - len(next_line.lstrip())
                    # Next step: "- name:" at same indent level
                    if (next_indent <= step_indent and next_stripped.startswith("-") and
                            re.match(r'^-\s*name\s*:', next_stripped)):
                        step_end = j
                        break
                if step_end is None:
                    step_end = len(lines)
                break

    if step_start is None:
        return None, 0

    base_indent = step_indent if step_indent is not None else 6
    if after:
        return step_end, base_indent
    return step_start, base_indent


def fix_indent(text, spaces=4):
    lines = text.split("\n")
    min_indent = min((len(s) - len(s.lstrip()) for s in lines if s.strip()), default=0)
    result = []
    for s in lines:
        if s.strip():
            stripped = s[min_indent:] if min_indent else s
            result.append(" " * spaces + stripped)
        else:
            result.append("")
    return "\n".join(result)


def _make_insertion(content, base_indent, pos, total_lines):
    """Build insertion string with 2 empty lines before and after content."""
    content = fix_indent(content.rstrip(), spaces=max(base_indent, 4))
    return "\n\n" + content + "\n\n"


def do_insert(target_file, content, after_section=None, before_section=None,
              after_step=None, before_step=None, skip_if=None):
    """Insert content at position determined by section marker or step name.
    Exactly one of after_section, before_section, after_step, before_step must be set."""
    text = target_file.read_text(encoding="utf-8")
    if skip_if and skip_if in text:
        return "skipped (already present)"

    lines = text.splitlines(keepends=True)
    pos = None
    base_indent = 0

    if after_section:
        pos, base_indent = find_insert_position(lines, after_section, after=True)
        if pos is None:
            raise ValueError(f"Marker '### {after_section} - END ###' not found")
    elif before_section:
        pos, base_indent = find_insert_position(lines, before_section, after=False)
        if pos is None:
            raise ValueError(f"Marker '### {before_section} - START ###' not found")
    elif after_step:
        pos, base_indent = find_step_position(lines, after_step, after=True)
        if pos is None:
            raise ValueError(f"Step '{after_step}' not found")
    elif before_step:
        pos, base_indent = find_step_position(lines, before_step, after=False)
        if pos is None:
            raise ValueError(f"Step '{before_step}' not found")
    else:
        raise ValueError("One of after_section, before_section, after_step, before_step required")

    insertion = _make_insertion(content, base_indent, pos, len(lines))
    lines.insert(pos, insertion)
    target_file.write_text("".join(lines), encoding="utf-8")
    return "inserted"


# ========== MAIN LOGIC ==========

def apply_patch(patch_path, base_dir):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096

    with open(patch_path, encoding="utf-8") as f:
        operations = yaml.load(f)

    if operations is None:
        operations = []
    elif not isinstance(operations, list):
        operations = [operations]

    if not operations:
        return []

    def resolve_target(target_file_str):
        """Resolve target file path. If base_dir is output dir, map .github/ -> output_dir/."""
        if target_file_str.startswith(".github/") and base_dir != Path("."):
            return base_dir / target_file_str[len(".github/"):]
        return base_dir / target_file_str

    # Default target from first operation (for operations without own target_file)
    default_target = None
    for op in operations:
        if op.get("target_file"):
            default_target = resolve_target(op["target_file"])
            break

    if not default_target:
        raise ValueError("target_file required in patch (e.g. .github/workflows/Envgene.yml)")

    result = []

    for i, op in enumerate(operations):
        action = op.get("action")
        path_str = op.get("path") or op.get("target_file", "file")
        # Each operation can have its own target_file
        target_file = (
            resolve_target(op["target_file"]) if op.get("target_file") else default_target
        )

        if not target_file.is_file():
            raise FileNotFoundError(f"File not found: {target_file}")

        if not action:
            print(f"  [Skip] Operation {i+1}: missing action", file=sys.stderr)
            continue

        if action == "merge":
            section = op.get("section")
            content = op.get("content") or {}
            if not isinstance(content, dict):
                print(f"  [Skip] Operation {i+1}: content must be dict", file=sys.stderr)
                continue
            # .env files: merge without section (KEY=value format)
            if not section and str(target_file).endswith(".env"):
                msg = do_merge_env(target_file, content)
                result.append(f"merge env {path_str} ({msg})")
            elif section:
                msg = do_merge(target_file, content, section)
                result.append(f"merge {path_str} ({msg})")
            elif path_str and path_str != "file":
                # YAML merge by path (e.g. jobs.process_environment_variables.outputs)
                msg = do_merge_yaml_path(target_file, content, path_str)
                result.append(f"merge {path_str} ({msg})")
            else:
                print(f"  [Skip] Operation {i+1}: merge requires section, path, or .env target", file=sys.stderr)

        elif action == "insert":
            after_section = op.get("after_section")
            before_section = op.get("before_section")
            after_step = op.get("after_step")
            before_step = op.get("before_step")
            content = op.get("content")
            skip_if = op.get("skip_if_present")

            anchor_count = sum(1 for x in (after_section, before_section, after_step, before_step) if x)
            if anchor_count != 1:
                print(
                    f"  [Skip] Operation {i+1}: insert requires exactly one of "
                    "after_section, before_section, after_step, before_step",
                    file=sys.stderr
                )
                continue
            if content is None:
                print(f"  [Skip] Operation {i+1}: insert requires content", file=sys.stderr)
                continue
            if isinstance(content, dict):
                from io import StringIO
                buf = StringIO()
                yaml.dump(content, buf)
                content = buf.getvalue()

            msg = do_insert(
                target_file, content,
                after_section=after_section, before_section=before_section,
                after_step=after_step, before_step=before_step, skip_if=skip_if
            )
            anchor = after_section or before_section or after_step or before_step
            if after_section:
                anchor_type = "after_section"
            elif before_section:
                anchor_type = "before_section"
            elif after_step:
                anchor_type = "after_step"
            else:
                anchor_type = "before_step"
            result.append(f"insert {anchor_type} '{anchor}' ({msg})")

        else:
            print(f"  [Skip] Operation {i+1}: unknown action '{action}'", file=sys.stderr)

    return result


def init_output_dir(output_root, source_dir):
    """Remove output_root and .github, then copy source_dir into output_root."""
    output_path = Path(output_root)
    source_path = Path(source_dir)
    if not source_path.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_path}")
    for path in (output_path, Path(".github")):
        if path.exists():
            shutil.rmtree(path)
    shutil.copytree(source_path, output_path)
    print(f"Initialized {output_root} from {source_dir}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Apply YAML patch to Envgene.yml")
    parser.add_argument(
        "--output-dir",
        default="extended_github_instance_pipeline",
        help="Parent directory for artifacts. Snapshot is written under "
        "<output-dir>/<tag>/ where tag is from DOCKER_IMAGE_TAG or "
        "INSTANCE_REPO_PIPELINE_IMAGE_TAG (default: latest). "
        "Default parent: extended_github_instance_pipeline.",
    )
    parser.add_argument(
        "--init-from",
        default="/opt/github",
        help="Before applying patches, remove <output-dir>/<tag>/ and .github, copy this "
        "source into the versioned output directory. Default: /opt/github. Use --no-init to skip.",
    )
    parser.add_argument(
        "--no-init",
        action="store_true",
        help="Skip init step (do not rm/cp). Use when output-dir already exists.",
    )
    parser.add_argument(
        "patch",
        nargs="*",
        help="Patch file(s) (e.g. components/component-a.yaml components/variables.yaml). "
        "If omitted, only the base workflow is copied (no patches).",
    )
    args = parser.parse_args()

    version_tag = sanitize_tag(resolve_version_tag())
    base = Path(args.output_dir) / version_tag
    all_results = []

    try:
        if not args.patch:
            if not args.no_init:
                init_output_dir(base, args.init_from)
            print(
                f"Initialized {base} (no component patches to apply).",
                flush=True,
            )
            return

        if not args.no_init:
            init_output_dir(base, args.init_from)

        for patch_path in args.patch:
            patch_path = Path(patch_path)
            if not patch_path.is_file():
                raise FileNotFoundError(f"File not found: {patch_path}")
            all_results.extend(apply_patch(patch_path, base))
        if all_results:
            print("Applied:")
            for r in all_results:
                print(f"  - {r}")
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
