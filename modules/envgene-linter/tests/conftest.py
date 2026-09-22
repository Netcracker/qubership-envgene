from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest


@pytest.fixture
def testdata() -> Path:
    return Path(__file__).resolve().parent.parent / "testdata"


@dataclass
class RepoBuilder:
    root: Path
    _written: dict[tuple[str, str], None] = field(default_factory=dict)

    def env(
        self,
        cluster: str,
        name: str,
        deploy: dict[str, list[str]] | None = None,
        e2e: dict[str, list[str]] | None = None,
        technical: dict[str, list[str]] | None = None,
        cloud_passport: str | None = None,
        artifact: str | None = None,
    ) -> RepoBuilder:
        inventory = self.root / "environments" / cluster / name / "Inventory"
        inventory.mkdir(parents=True, exist_ok=True)
        lines = ["inventory:", f"  environmentName: {name}"]
        if cloud_passport:
            lines.append(f"  cloudPassport: {cloud_passport}")
        lines.extend(["envTemplate:", "  name: composite"])
        if artifact is not None:
            lines.append(f"  artifact: {artifact}")
        for field_name, bindings in (
            ("envSpecificParamsets", deploy),
            ("envSpecificE2EParamsets", e2e),
            ("envSpecificTechnicalParamsets", technical),
        ):
            if not bindings:
                continue
            lines.append(f"  {field_name}:")
            for target, names in bindings.items():
                lines.append(f"    {target}:")
                lines.extend(f"      - {item}" for item in names)
        (inventory / "env_definition.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self

    def _paramset(self, directory: Path, name: str, params: dict | None) -> RepoBuilder:
        directory.mkdir(parents=True, exist_ok=True)
        body = ["name: " + name, "parameters:"]
        for key, value in (params or {}).items():
            rendered = value if isinstance(value, str) else repr(value)
            if isinstance(value, str):
                rendered = value
            body.append(f"  {key}: {rendered}")
        (directory / f"{name}.yml").write_text("\n".join(body) + "\n", encoding="utf-8")
        return self

    def site_paramset(self, name: str, params: dict | None = None) -> RepoBuilder:
        return self._paramset(self.root / "environments" / "parameters", name, params)

    def cluster_paramset(self, cluster: str, name: str, params: dict | None = None) -> RepoBuilder:
        return self._paramset(self.root / "environments" / cluster / "parameters", name, params)

    def env_paramset(self, cluster: str, env: str, name: str, params: dict | None = None) -> RepoBuilder:
        return self._paramset(
            self.root / "environments" / cluster / env / "Inventory" / "parameters", name, params
        )

    def passport(
        self,
        name: str,
        sections: dict | None = None,
        *,
        cluster: str | None = None,
        env: str | None = None,
        folder: str = "cloud-passport",
    ) -> RepoBuilder:
        if cluster and env:
            directory = self.root / "environments" / cluster / env / "Inventory" / folder
        elif cluster:
            directory = self.root / "environments" / cluster / folder
        else:
            directory = self.root / "environments" / folder
        directory.mkdir(parents=True, exist_ok=True)
        lines = ["version: 1.5"]
        for section, values in (sections or {}).items():
            lines.append(f"{section}:")
            for key, value in values.items():
                rendered = value if isinstance(value, str) else repr(value)
                lines.append(f"  {key}: {rendered}")
        (directory / f"{name}.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return self


@pytest.fixture
def repo(tmp_path: Path) -> RepoBuilder:
    return RepoBuilder(tmp_path)
