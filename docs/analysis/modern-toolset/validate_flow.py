#!/usr/bin/env python3
"""Consistency validator for flow.md (modern-toolset flow).

Structure: `## Flow` -> `### N. job` -> `#### N.M. step` -> numbered `Functions:`.
The `## Artifacts` table references producers/consumers as `job.step` numbers (e.g. 2.7, 3.1).

Checks:
- Artifacts table parses; every producer/consumer is a real step id or a known word.
- Every artifact has at least one producer and one consumer (or a terminal word).
- Name-match (soft): the referenced step's text mentions the artifact name.
"""
import re
import sys
from pathlib import Path

DOC = Path(__file__).with_name("flow.md")
WORDS = {"external", "committed", "many", "tbd"}
STEP_RE = re.compile(r"^####\s+(\d+\.\d+)\.\s+step\s+`([^`]+)`")


def parse_table(text):
    lines = text.splitlines()
    hdr = next(i for i, l in enumerate(lines) if l.startswith("| Artifact"))
    rows = []
    for l in lines[hdr + 2:]:
        if not l.startswith("|"):
            break
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if len(c) == 4:
            rows.append(c)
    return rows


def parse_steps(text):
    """Return {step_id: (name, block_text)} for the `## Flow` section."""
    scope = text.split("## Flow", 1)
    scope = scope[1] if len(scope) == 2 else text
    lines = scope.splitlines()
    heads = [(i, m.group(1), m.group(2)) for i, l in enumerate(lines)
             for m in [STEP_RE.match(l)] if m]
    steps = {}
    for idx, (i, sid, name) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        steps[sid] = (name, "\n".join(lines[i:end]))
    return steps


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def split_refs(cell):
    nums, words, bad = [], [], []
    for t in [x.strip() for x in cell.split(",") if x.strip()]:
        if re.fullmatch(r"\d+\.\d+", t):
            nums.append(t)
        elif t.lower() in WORDS:
            words.append(t)
        else:
            bad.append(t)
    return nums, words, bad


def main():
    text = DOC.read_text()
    rows = parse_table(text)
    steps = parse_steps(text)
    valid = set(steps)
    problems, misses = [], []

    print(f"steps found ({len(valid)}): {', '.join(sorted(valid, key=lambda s: [int(x) for x in s.split('.')]))}\n")
    print(f"{'artifact':28} {'producers':22} {'consumers':28} notes")
    print("-" * 100)
    seen = set()
    for name, path, prod, cons in rows:
        pn, pw, pb = split_refs(prod)
        cn, cw, cb = split_refs(cons)
        notes = []
        if name in seen:
            notes.append("DUP-NAME")
        seen.add(name)
        for t in pb + cb:
            notes.append(f"bad-ref:{t}")
        for t in pn + cn:
            if t not in valid:
                notes.append(f"no-step:{t}")
        if not pn and not pw and path.upper() != "TBD":
            notes.append("no-producer")
        if not cn and not cw:
            notes.append("no-consumer")
        print(f"{name:28} {prod:22} {cons:28} {'; '.join(notes)}")
        problems.extend(f"{name}: {n}" for n in notes)
        # soft name-match against referenced step blocks
        key = norm(name)
        if key and path.upper() != "TBD":
            for role, ids in (("prod", pn), ("cons", cn)):
                for t in ids:
                    blk = steps.get(t, ("", ""))[1]
                    if blk and key not in norm(blk):
                        misses.append(f"{name}: {role} {t} ({steps[t][0]}) does not mention it")

    print("\n=== PROBLEMS ===")
    for p in problems:
        print(" -", p)
    print("\n=== NAME-MATCH MISSES (soft) ===")
    for m in misses:
        print(" -", m)
    print(f"\n{len(problems)} structural + {len(misses)} name-match")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
