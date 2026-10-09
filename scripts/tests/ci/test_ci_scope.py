import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[3] / ".github/scripts/ci_scope.py"


class CiScopeTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.directory = Path(self.temporary_directory.name)
        self.repository = self.directory / "repository"
        self.repository.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "CI Tests")
        self.git("config", "user.email", "ci-tests@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.base = self.commit({"docs/guide.md": "guide", "src/code.py": "pass"})

    def git(self, *arguments):
        return subprocess.check_output(
            ["git", *arguments], cwd=self.repository, stderr=subprocess.PIPE, text=True,
        ).strip()

    def commit(self, changes, message="fix: Update files"):
        for name, content in changes.items():
            path = self.repository / name
            if content is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
        self.git("add", "-A")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def scope(self, head, message="fix: Update files", base=None, event_name="push", inputs=None):
        base = self.base if base is None else base
        event = {
            "before": base, "after": head, "head_commit": {"message": message},
            "pull_request": {"base": {"sha": base}, "head": {"sha": head}, "title": "docs: PR title"},
            "inputs": inputs or {},
        }
        event_path = self.directory / "event.json"
        output_path = self.directory / "output"
        event_path.write_text(json.dumps(event))
        output_path.write_text("")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)], cwd=self.repository,
            env=os.environ | {
                "GITHUB_EVENT_NAME": event_name, "GITHUB_EVENT_PATH": str(event_path),
                "GITHUB_OUTPUT": str(output_path),
            }, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        outputs = dict(line.split("=", 1) for line in output_path.read_text().splitlines())
        for value in outputs.values():
            self.assertIn(value, ("true", "false"))
        return {name: value == "true" for name, value in outputs.items()}

    def test_docs_only_ignores_message(self):
        for message in ("feat: Update guide", "Docs: Update guide", "docs(scope): Update guide"):
            with self.subTest(message=message):
                head = self.commit({"docs/nested/a \t\n.md": message}, message)
                self.assertTrue(self.scope(head, message)["skip_tests_and_build"])

    def test_prefix_is_exact_and_independent_of_paths(self):
        for message, expected in (
            ("docs: Update code\n\nfix: Example", True), ("docs:Update code", True),
            ("docs(scope): Update code", False), ("Docs: Update code", False),
            ("DOCS: Update code", False), (" docs: Update code", False),
            ("fix: Update code\n\ndocs: Example", False),
        ):
            with self.subTest(message=message):
                head = self.commit({"src/code.py": message}, message)
                self.assertEqual(self.scope(head, message)["skip_tests_and_build"], expected)
                self.assertEqual(self.scope(head, message, event_name="pull_request")["skip_tests_and_build"], expected)

    def test_mixed_changes_run_tests(self):
        head = self.commit({"docs/guide.md": "updated", "src/code.py": "updated"})
        self.assertFalse(self.scope(head)["skip_tests_and_build"])

    def test_docs_must_be_at_root(self):
        for name in ("README.md", "src/docs/guide.md", "docs-other/guide.md"):
            with self.subTest(name=name):
                base = self.git("rev-parse", "HEAD")
                head = self.commit({name: "updated"})
                self.assertFalse(self.scope(head, base=base)["skip_tests_and_build"])

    def test_added_modified_and_deleted_docs(self):
        base = self.commit({"docs/remove.md": "old"})
        head = self.commit({"docs/new.md": "new", "docs/guide.md": "updated", "docs/remove.md": None})
        self.assertTrue(self.scope(head, base=base)["skip_tests_and_build"])

    def test_rename_within_docs(self):
        self.git("mv", "docs/guide.md", "docs/renamed.md")
        self.assertTrue(self.scope(self.commit({}))["skip_tests_and_build"])

    def test_rename_out_of_docs(self):
        self.git("mv", "docs/guide.md", "src/guide.md")
        self.assertFalse(self.scope(self.commit({}))["skip_tests_and_build"])

    def test_rename_into_docs(self):
        self.git("mv", "src/code.py", "docs/code.py")
        self.assertFalse(self.scope(self.commit({}))["skip_tests_and_build"])

    def test_push_checks_all_commits_and_only_head_message(self):
        self.commit({"src/code.py": "updated"}, "docs: Update code")
        head = self.commit({"docs/guide.md": "updated"})
        self.assertFalse(self.scope(head)["skip_tests_and_build"])

    def test_multiple_docs_commits(self):
        self.commit({"docs/guide.md": "updated"})
        head = self.commit({"docs/nested/guide.md": "new"})
        self.assertTrue(self.scope(head)["skip_tests_and_build"])

    def test_empty_or_unavailable_diff_needs_docs_prefix(self):
        for base in (self.base, "f" * 40, "0" * 40, ""):
            with self.subTest(base=base):
                self.assertFalse(self.scope(self.base, base=base)["skip_tests_and_build"])
                self.assertTrue(self.scope(self.base, "docs: Update guide", base=base)["skip_tests_and_build"])

    def test_deleted_code_runs_tests(self):
        self.assertFalse(self.scope(self.commit({"src/code.py": None}))["skip_tests_and_build"])

    def test_manual_runs_ignore_skip_rules(self):
        head = self.commit({"docs/guide.md": "updated"}, "docs: Update guide")
        self.assertFalse(self.scope(head, "docs: Update guide", event_name="workflow_dispatch")["skip_tests_and_build"])

    def test_pr_uses_head_message_not_checkout_message_or_title(self):
        head = self.commit({"src/code.py": "updated"})
        self.git("commit", "--allow-empty", "-qm", "docs: Merge PR")
        self.assertFalse(self.scope(head, event_name="pull_request")["skip_tests_and_build"])

    def test_unavailable_pr_message_runs_tests(self):
        self.assertFalse(self.scope("f" * 40, "docs: Unverified message", event_name="pull_request")["skip_tests_and_build"])

    def test_push_build_rules_preserve_contains_semantics(self):
        head = self.commit({"src/code.py": "updated"})
        for message, build in (
            ("feat: Add feature", True), ("fix: Correct code", True),
            ("chore: Update API\n\nBREAKING CHANGE: Remove method", True),
            ("FEAT: Add feature", True), ("chore: Document fix: example", True),
            ("chore: Update code", False), ("test: Add coverage", False),
            ("feat(scope): Add feature", False), ("feat!: Change API", False),
        ):
            with self.subTest(message=message):
                self.assertEqual(self.scope(head, message), {
                    "skip_tests_and_build": False, "run_tests": True,
                    "build_envgene": build, "build_gsf_instance": build,
                    "build_gsf_discovery": build,
                })

    def test_docs_skip_all_dev_tests_and_builds(self):
        docs_head = self.commit({"docs/guide.md": "updated"}, "feat: Update guide")
        code_head = self.commit({"src/code.py": "updated"}, "docs: Explain fix: example")
        for head, message in (
            (docs_head, "feat: Update guide"), (code_head, "docs: Explain fix: example"),
        ):
            with self.subTest(message=message):
                self.assertEqual(self.scope(head, message), {
                    "skip_tests_and_build": True, "run_tests": False,
                    "build_envgene": False, "build_gsf_instance": False,
                    "build_gsf_discovery": False,
                })

    def test_manual_build_flags_are_independent(self):
        head = self.commit({"docs/guide.md": "updated"}, "docs: Update guide")
        for tests_only, envgene, instance, discovery, expected in (
            ("false", "true", "true", "true", (True, True, True)),
            ("true", "true", "true", "true", (False, True, True)),
            ("false", "false", "true", "true", (False, True, True)),
            ("false", "true", "false", "false", (True, False, False)),
            ("false", "false", "true", "false", (False, True, False)),
            ("false", "false", "false", "true", (False, False, True)),
            ("true", "true", "false", "false", (False, False, False)),
            ("false", "false", "false", "false", (False, False, False)),
        ):
            with self.subTest(flags=(tests_only, envgene, instance, discovery)):
                outputs = self.scope(head, "docs: Update guide", event_name="workflow_dispatch", inputs={
                    "tests-only": tests_only, "build-envgene": envgene,
                    "build-gsf-instance": instance, "build-gsf-discovery": discovery,
                })
                self.assertEqual(outputs, {
                    "skip_tests_and_build": False, "run_tests": True,
                    "build_envgene": expected[0], "build_gsf_instance": expected[1],
                    "build_gsf_discovery": expected[2],
                })

    def test_only_last_push_message_selects_builds(self):
        self.commit({"src/code.py": "updated"}, "feat: Add feature")
        head = self.commit({"docs/guide.md": "updated"}, "chore: Update guide")
        self.assertEqual(self.scope(head, "chore: Update guide"), {
            "skip_tests_and_build": False, "run_tests": True,
            "build_envgene": False, "build_gsf_instance": False,
            "build_gsf_discovery": False,
        })

    def test_unavailable_diff_preserves_push_build_selection(self):
        self.assertEqual(self.scope(self.base, "fix: Correct code", base="f" * 40), {
            "skip_tests_and_build": False, "run_tests": True,
            "build_envgene": True, "build_gsf_instance": True,
            "build_gsf_discovery": True,
        })

    def test_pr_does_not_select_dev_docker_builds(self):
        head = self.commit({"src/code.py": "updated"})
        self.assertEqual(self.scope(head, event_name="pull_request"), {
            "skip_tests_and_build": False, "run_tests": True,
            "build_envgene": False, "build_gsf_instance": False,
            "build_gsf_discovery": False,
        })


if __name__ == "__main__":
    unittest.main()
