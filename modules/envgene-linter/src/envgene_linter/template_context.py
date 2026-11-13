"""Bounded, read-only template source evidence for PLACE-12 recommendations."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .model import Category, Scope
from .parsing import ParseFailure, parse_json, parse_yaml
from .security_values import literal_name
from .yaml_values import equal
from .yamlio import LoadedYaml

_DESCRIPTOR_EXTENSIONS = (".yml.j2", ".yaml.j2", ".yml", ".yaml")
_PARAMETER_SUFFIXES = (".json", ".yml", ".yaml", ".j2")
_FIELDS = {
    Category.DEPLOY: ("deployParameterSets", "deployParameters", "deploy"),
    Category.E2E: ("e2eParameterSets", "e2eParameters", "pipeline"),
    Category.TECHNICAL: (
        "technicalConfigurationParameterSets",
        "technicalConfigurationParameters",
        "runtime",
    ),
}


def _stem(path: Path) -> str:
    return next(
        (
            path.name[: -len(ext)]
            for ext in _DESCRIPTOR_EXTENSIONS
            if path.name.endswith(ext)
        ),
        path.stem,
    )


def _tagged(value: Any) -> bool:
    return getattr(getattr(value, "tag", None), "value", None) is not None


@dataclass
class _Source:
    path: Path
    loaded: LoadedYaml | None = None
    partial: bool = False
    problem: str | None = None


def _static_membership(source: _Source, entry: dict, category: Category) -> bool:
    if source.partial or source.loaded is None:
        return False
    override = entry.get("template_override", {})
    if not isinstance(override, dict) or _tagged(override):
        return False
    field = _FIELDS[category][0]
    for references in (source.loaded.doc.get(field, []), override.get(field, [])):
        if not isinstance(references, list) or _tagged(references):
            return False
        if any(
            not literal_name(ref) or _tagged(ref) or "{#" in ref for ref in references
        ):
            return False
    return True


def _entry_position(descriptor: _Source, path: tuple) -> tuple[int, int] | None:
    return descriptor.loaded.exact_position(path)


@dataclass
class TemplateProposal:
    descriptor: str | None = None
    stem: str | None = None
    attachment: dict | None = None
    definitions: tuple[str, ...] = ()
    reason: str | None = None
    entry_path: tuple[str | int, ...] = ()
    entry_position: tuple[int, int] | None = None
    reference_present: bool = False


@dataclass
class ExistingParameterSet:
    reference: str
    path: Path
    loaded: LoadedYaml | None = None
    attachment: TemplateProposal | None = None
    reason: str | None = None


def common_stem(scope: Scope) -> str:
    parts = [
        scope.target,
        *([scope.application] if scope.application else []),
        "common",
        _FIELDS[scope.category][2],
    ]
    return "-".join(
        re.sub(r"[^a-z0-9]+", "-", part.lower()).strip("-") or "shared"
        for part in parts
    )[:120].rstrip("-")


class TemplateContext:
    def __init__(self, root: Path):
        root = Path(root).absolute()
        self._root = root
        self.directory = root if root.name == "templates" else root / "templates"
        self.problem = None
        if (
            root.is_symlink()
            or self.directory.is_symlink()
            or not self.directory.is_dir()
        ):
            self.problem = (
                "The supplied path has no readable, unlinked templates directory."
            )
        self._cache: dict[Path, _Source] = {}
        self._parameters: list[_Source] | None = None
        self._reserved: set[str] = set()
        self._relocations: set[str] = set()
        self._template_references: set[str] | None = None
        self._reference_scan_complete = True
        self._names: dict[tuple, str] = {}

    def _label(self, path: Path) -> str:
        return "templates/" + path.relative_to(self.directory).as_posix()

    def _read(self, path: Path) -> _Source:
        if self._root.is_symlink() or self.directory.is_symlink():
            return _Source(
                path,
                problem="The supplied template source is linked and cannot be inspected.",
            )
        if path in self._cache:
            return self._cache[path]
        source = _Source(path)
        self._cache[path] = source
        try:
            relative = path.relative_to(self.directory)
            if ".." in relative.parts or any(
                (self.directory / Path(*relative.parts[:n])).is_symlink()
                for n in range(1, len(relative.parts) + 1)
            ):
                raise ValueError("linked or external source")
            with path.open(encoding="utf-8") as stream:
                text = stream.read(2_000_001)
            if len(text) > 2_000_000:
                raise ValueError("source size limit")
            if path.suffix == ".json":
                parse_json(text)
            if "{%" in text:
                source.partial = True
                # Only content before control flow is unconditional source evidence.
                text = text[: text.rfind("\n", 0, text.index("{%")) + 1]
            doc = parse_yaml(text)
            if not isinstance(doc, dict) or _tagged(doc):
                raise ValueError("source is not an ordinary mapping")
            source.loaded = LoadedYaml(path, doc)
        except (OSError, UnicodeError, ParseFailure, ValueError):
            source.problem = f"Cannot inspect {self._label(path)} as static YAML."
        return source

    def _path(self, value: Any) -> Path | None:
        if not isinstance(value, str):
            return None
        relative = re.sub(r"^\{\{\s*templates_dir\s*\}\}/", "", value)
        if any(marker in relative for marker in ("{{", "{%", "{#", "${")):
            return None
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or not relative:
            return None
        return self.directory / path

    def _parameter_sources(self) -> list[_Source]:
        if self._parameters is not None:
            return self._parameters
        self._parameters = []
        directory = self.directory / "parameters"
        if directory.is_symlink():
            self.problem = "The local parameters directory is linked. Name uniqueness cannot be verified."
            return self._parameters
        if not directory.exists():
            return self._parameters

        def onerror(error):
            self.problem = "Cannot enumerate local ParameterSets. Name uniqueness cannot be verified."

        for parent, directories, files in os.walk(
            directory, followlinks=False, onerror=onerror
        ):
            if any((Path(parent) / name).is_symlink() for name in directories):
                self.problem = "Local ParameterSet directories contain links. Name uniqueness cannot be verified."
            directories[:] = sorted(
                name for name in directories if not (Path(parent) / name).is_symlink()
            )
            for name in sorted(files):
                path = Path(parent) / name
                if path.suffix not in _PARAMETER_SUFFIXES:
                    continue
                self._reserved.add(_stem(path).casefold())
                source = self._read(path)
                self._parameters.append(source)
        return self._parameters

    def _entry(self, name: str, scope: Scope):
        if not re.fullmatch(r"[\w-]+", name):
            return (
                None,
                None,
                "The template name cannot be resolved to a local descriptor filename.",
            )
        descriptor = next(
            (
                self.directory / "env_templates" / (name + ext)
                for ext in _DESCRIPTOR_EXTENSIONS
                if (self.directory / "env_templates" / (name + ext)).exists()
            ),
            None,
        )
        if descriptor is None:
            return (
                None,
                None,
                "The named template descriptor was not found in the local source.",
            )
        source = self._read(descriptor)
        if source.problem or source.partial:
            return (
                source,
                None,
                source.problem
                or "Descriptor membership depends on Jinja control flow.",
            )
        doc = source.loaded.doc
        if scope.target == "cloud":
            cloud = doc.get("cloud")
            entry = {"template_path": cloud} if isinstance(cloud, str) else cloud
            entries = [entry] if isinstance(entry, dict) else []
        else:
            entries = []
            namespaces = doc.get("namespaces", [])
            for entry in namespaces if isinstance(namespaces, list) else []:
                if not isinstance(entry, dict):
                    continue
                path = self._path(entry.get("template_path"))
                postfix = entry.get("deploy_postfix") or (
                    path.name.replace(".yml.j2", "").replace(".yaml.j2", "")
                    if path
                    else None
                )
                if postfix == scope.target:
                    entries.append(entry)
        if len(entries) != 1 or _tagged(entries[0]):
            return (
                source,
                None,
                "The association target has no unique static descriptor entry.",
            )
        return source, entries[0], None

    def _reserve(
        self,
        name: str,
        artifact: str,
        scope: Scope,
        identity: tuple,
        references: tuple[str, ...],
    ) -> str:
        key = (name, artifact, scope, identity)
        if key in self._names:
            return self._names[key]
        self._reserved.update(reference.casefold() for reference in references)
        base = common_stem(scope)
        stem, ordinal = base, 2
        while stem.casefold() in self._reserved:
            stem, ordinal = f"{base}-{ordinal}", ordinal + 1
        self._reserved.add(stem.casefold())
        self._names[key] = stem
        return stem

    def _definitions(
        self,
        descriptor: _Source,
        source: _Source,
        entry: dict,
        scope: Scope,
        entries: list,
        references: list,
    ) -> tuple[str, ...]:
        _, object_field, _ = _FIELDS[scope.category]
        found = []

        def inspect(candidate: _Source, container: tuple, note: str = ""):
            if candidate.loaded is None:
                return
            for path, expected in entries:
                node = candidate.loaded.doc
                try:
                    for part in (*container, *path):
                        if _tagged(node):
                            raise KeyError(part)
                        node = node[part]
                except (KeyError, IndexError, TypeError):
                    continue
                dynamic = _tagged(node) or (
                    isinstance(node, str)
                    and any(marker in node for marker in ("{{", "{%", "${"))
                )
                comparison = None if dynamic else equal(expected, node)
                status = (
                    "same value"
                    if comparison is True
                    else "different value"
                    if comparison is False
                    else "unresolved value"
                )
                line, column = candidate.loaded.position((*container, *path))
                found.append(
                    f"{'.'.join(path)}: {self._label(candidate.path)}:{line}:{column} ({status}{note})"
                )

        if scope.application is None:
            inspect(
                source, (object_field,), ", Jinja prefix only" if source.partial else ""
            )
            if scope.target == "cloud":
                inspect(descriptor, ("cloud", "template_override", object_field))
            else:
                for i, namespace in enumerate(
                    descriptor.loaded.doc.get("namespaces", [])
                ):
                    if namespace is entry:
                        inspect(
                            descriptor,
                            ("namespaces", i, "template_override", object_field),
                        )
        for reference in references:
            expression = re.escape(reference)
            dynamic = "{{" in reference
            if dynamic:
                expression = ".*".join(
                    re.escape(part) for part in re.split(r"\{\{.*?\}\}", reference)
                )
            matches = [
                candidate
                for candidate in self._parameter_sources()
                if re.fullmatch(expression, _stem(candidate.path))
            ]
            note = ", dynamic reference; selection unresolved" if dynamic else ""
            if len(matches) > 1 and not dynamic:
                note += ", ambiguous ParameterSet name"
            for candidate in matches:
                if candidate.loaded is None:
                    found.append(candidate.problem)
                    continue
                if scope.application is None:
                    inspect(candidate, ("parameters",), note)
                else:
                    applications = candidate.loaded.doc.get("applications", [])
                    for i, application in enumerate(
                        applications if isinstance(applications, list) else []
                    ):
                        if (
                            isinstance(application, dict)
                            and application.get("appName") == scope.application
                        ):
                            inspect(candidate, ("applications", i, "parameters"), note)
        return tuple(dict.fromkeys(found))

    def _known_template_references(self) -> set[str] | None:
        if self._template_references is not None:
            return self._template_references if self._reference_scan_complete else None
        references: set[str] = set()
        fields = {field[0] for field in _FIELDS.values()}

        def onerror(_error):
            self._reference_scan_complete = False

        for parent, directories, files in os.walk(
            self.directory / "env_templates", followlinks=False, onerror=onerror
        ):
            if any((Path(parent) / name).is_symlink() for name in directories):
                self._reference_scan_complete = False
            directories[:] = [
                name for name in directories if not (Path(parent) / name).is_symlink()
            ]
            for name in files:
                path = Path(parent) / name
                if path.suffix not in _PARAMETER_SUFFIXES:
                    continue
                if path.is_symlink():
                    self._reference_scan_complete = False
                    continue
                source = self._read(path)
                if source.partial or source.problem:
                    try:
                        with path.open(encoding="utf-8") as stream:
                            text = stream.read(2_000_001)
                        if len(text) > 2_000_000:
                            raise ValueError("source size limit")
                        references.update(re.findall(r"[\w.-]+", text))
                    except (OSError, UnicodeError, ValueError):
                        self._reference_scan_complete = False
                pending = [source.loaded.doc] if source.loaded is not None else []
                seen = set()
                while pending:
                    value = pending.pop()
                    if not isinstance(value, (dict, list)) or id(value) in seen:
                        continue
                    seen.add(id(value))
                    if isinstance(value, list):
                        pending.extend(value)
                        continue
                    for key, child in value.items():
                        if key in fields and isinstance(child, list):
                            references.update(
                                item for item in child if isinstance(item, str)
                            )
                        pending.append(child)
        self._template_references = references
        return references if self._reference_scan_complete else None

    def relocation_destination(
        self, name: str, scope: Scope, reference: str
    ) -> str | None:
        if (
            self.problem
            or not re.fullmatch(r"[\w-][\w.-]*", reference)
            or self._root.is_symlink()
            or self.directory.is_symlink()
        ):
            return None
        sources = self._parameter_sources()
        occupied = {_stem(source.path).casefold() for source in sources}
        proposed = {
            name.casefold() for name in self._names.values()
        } | self._relocations
        destination = self.directory / "parameters" / f"{reference}.yml"
        if (
            self.problem
            or reference.casefold() in occupied | proposed
            or destination.exists()
            or destination.is_symlink()
        ):
            return None
        _descriptor, entry, reason = self._entry(name, scope)
        if reason or "parent" in entry or "overrides-parent" in entry:
            return None
        path = self._path(entry.get("template_path"))
        if path is None or self._read(path).problem:
            return None
        if not _static_membership(self._read(path), entry, scope.category):
            return None
        template_references = self._known_template_references()
        if template_references is None or reference in template_references:
            return None
        self._reserved.add(reference.casefold())
        self._relocations.add(reference.casefold())
        return f"templates/parameters/{reference}.yml"

    def existing_paramset(
        self,
        name: str,
        scope: Scope,
        entries: list,
        references: tuple[str, ...],
    ) -> ExistingParameterSet | None:
        sources = self._parameter_sources()
        names = list(
            dict.fromkeys(
                [
                    *(references if len(references) == 1 else ()),
                    common_stem(scope),
                ]
            )
        )
        for reference in names:
            matches = [
                s for s in sources if _stem(s.path).casefold() == reference.casefold()
            ]
            if not matches:
                continue
            source = matches[0]
            target = ExistingParameterSet(reference, source.path, source.loaded)
            if self.problem or len(matches) != 1:
                target.reason = (
                    self.problem or "The existing ParameterSet name is ambiguous."
                )
            elif (
                source.problem
                or source.partial
                or source.path.suffix == ".j2"
                or _stem(source.path) != reference
            ):
                target.reason = (
                    source.problem
                    or "The existing ParameterSet is not a static, exact-name source."
                )
            elif source.loaded.doc.get("name") != reference:
                target.reason = (
                    "The existing ParameterSet filename and name do not agree."
                )
            else:
                target.attachment = self.propose(
                    name,
                    "",
                    scope,
                    entries,
                    reuse=reference,
                )
                target.reason = target.attachment.reason
            return target
        return None

    def propose(
        self,
        name: str,
        artifact: str,
        scope: Scope,
        entries: list,
        *,
        identity: tuple = (),
        source_references: tuple[str, ...] = (),
        reuse: str | None = None,
    ) -> TemplateProposal:
        if self.problem or self._root.is_symlink() or self.directory.is_symlink():
            return TemplateProposal(
                reason=self.problem or "The supplied template source is linked."
            )
        self._parameter_sources()
        if self.problem:
            return TemplateProposal(reason=self.problem)
        descriptor, entry, reason = self._entry(name, scope)
        label = self._label(descriptor.path) if descriptor else None
        if reason:
            return TemplateProposal(descriptor=label, reason=reason)
        entry_path = (
            ("cloud",)
            if scope.target == "cloud"
            else (
                "namespaces",
                next(
                    index
                    for index, candidate in enumerate(
                        descriptor.loaded.doc["namespaces"]
                    )
                    if candidate is entry
                ),
            )
        )
        entry_position = _entry_position(descriptor, entry_path)
        if entry_position is None:
            return TemplateProposal(
                descriptor=label,
                entry_path=entry_path,
                reason="The selected entry uses YAML anchors or inherited keys. Inspect their consumers before choosing an edit location.",
            )
        if (
            "parent" in entry
            or "overrides-parent" in entry
            or "template_path" not in entry
        ):
            return TemplateProposal(
                descriptor=label,
                reason="Inspect overrides-parent and the external parent before choosing an attachment.",
            )
        path = self._path(entry.get("template_path"))
        if path is None:
            return TemplateProposal(
                descriptor=label,
                reason="The selected template_path is dynamic or outside the local templates directory.",
            )
        source = self._read(path)
        if source.problem:
            return TemplateProposal(descriptor=label, reason=source.problem)
        binding, _, _ = _FIELDS[scope.category]
        override = entry.get("template_override", {})
        if not isinstance(override, dict) or _tagged(override):
            return TemplateProposal(
                descriptor=label,
                reason="The existing template_override is not a static mapping.",
            )
        base_refs = source.loaded.doc.get(binding, [])
        extra_refs = override.get(binding, [])
        if any(
            not isinstance(refs, list)
            or _tagged(refs)
            or any(not isinstance(ref, str) for ref in refs)
            for refs in (base_refs, extra_refs)
        ):
            return TemplateProposal(
                descriptor=label,
                reason=f"The existing {binding} references are not a static list.",
            )
        definitions = self._definitions(
            descriptor, source, entry, scope, entries, [*base_refs, *extra_refs]
        )
        if not _static_membership(source, entry, scope.category):
            return TemplateProposal(
                descriptor=label,
                definitions=definitions,
                entry_path=entry_path,
                entry_position=entry_position,
                reason="Template ParameterSet membership is conditional or dynamic.",
            )
        stem = reuse or self._reserve(
            name,
            artifact,
            scope,
            identity,
            (*source_references, *base_refs, *extra_refs),
        )
        fragment = {
            key: entry[key]
            for key in ("template_path", "deploy_postfix", "name")
            if key in entry
        }
        reference_present = stem in [*base_refs, *extra_refs]
        fragment["template_override"] = {
            binding: [*extra_refs] if reference_present else [*extra_refs, stem]
        }
        attachment = (
            {"cloud": fragment}
            if scope.target == "cloud"
            else {"namespaces": [fragment]}
        )
        return TemplateProposal(
            label,
            stem,
            attachment,
            definitions,
            entry_path=entry_path,
            entry_position=entry_position,
            reference_present=reference_present,
        )
