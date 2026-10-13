"""Tests for the deploy-plan filter feature, including negation (!) support."""

import pytest

from dpg.v1.cmd.cmd import Filter, _parse_filter, _matches_filter, DeploymentPlanGeneratorCommand
from dpg.v1.internal.deployment_plan.models import DeployPlan, DeployPlanEntity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_entity(
    name: str,
    version: str = "1.0",
    namespace: str = "ns",
    wave: int = 0,
    deploy_postfix: str = "",
) -> DeployPlanEntity:
    return DeployPlanEntity(
        version=f"{name}:{version}",
        namespace=namespace,
        wave=wave,
        deployPostfix=deploy_postfix,
    )


def make_plan(*entities: DeployPlanEntity) -> DeployPlan:
    return DeployPlan(entities=list(entities))


# ---------------------------------------------------------------------------
# _parse_filter
# ---------------------------------------------------------------------------

class TestParseFilter:
    def test_none_returns_empty_filter(self):
        f = _parse_filter(None)
        assert f.is_empty()

    def test_empty_string_returns_empty_filter(self):
        f = _parse_filter("")
        assert f.is_empty()

    def test_plain_tokens_go_to_include(self):
        f = _parse_filter("core,ns")
        assert f.include == {"core", "ns"}
        assert f.exclude == set()

    def test_negated_tokens_go_to_exclude(self):
        f = _parse_filter("!core,!ns")
        assert f.include == set()
        assert f.exclude == {"core", "ns"}

    def test_mixed_include_and_exclude(self):
        f = _parse_filter("core,!other")
        assert f.include == {"core"}
        assert f.exclude == {"other"}

    def test_various_separators(self):
        f = _parse_filter("core;ns !other")
        assert "core" in f.include
        assert "ns" in f.include
        assert "other" in f.exclude

    def test_newline_separator(self):
        f = _parse_filter("core\nns")
        assert f.include == {"core", "ns"}


# ---------------------------------------------------------------------------
# _matches_filter
# ---------------------------------------------------------------------------

class TestMatchesFilter:
    def test_empty_filter_accepts_everything(self):
        assert _matches_filter("anything", Filter()) is True

    def test_include_only_accepts_matching_value(self):
        f = Filter(include={"core", "ns"})
        assert _matches_filter("core", f) is True
        assert _matches_filter("other", f) is False

    def test_exclude_only_rejects_matching_value(self):
        f = Filter(exclude={"core"})
        assert _matches_filter("core", f) is False
        assert _matches_filter("ns", f) is True

    def test_include_and_exclude_value_in_include_not_in_exclude(self):
        f = Filter(include={"core", "ns"}, exclude={"other"})
        assert _matches_filter("core", f) is True

    def test_include_and_exclude_value_in_both_is_rejected(self):
        # exclude wins when a value somehow appears in both sets
        f = Filter(include={"core"}, exclude={"core"})
        assert _matches_filter("core", f) is False

    def test_include_and_exclude_value_in_neither_is_rejected(self):
        f = Filter(include={"core"}, exclude={"other"})
        assert _matches_filter("unknown", f) is False


# ---------------------------------------------------------------------------
# DeploymentPlanGeneratorCommand.filter — end-to-end
# ---------------------------------------------------------------------------

class TestFilterCommand:
    def _plan(self):
        return make_plan(
            make_entity("App-A", namespace="ns-1", wave=0, deploy_postfix="core"),
            make_entity("App-B", namespace="ns-2", wave=1, deploy_postfix="ns"),
            make_entity("App-C", namespace="ns-1", wave=2, deploy_postfix="core"),
        )

    def test_no_filters_returns_all(self, tmp_path):
        result = DeploymentPlanGeneratorCommand.filter(
            self._plan(), output_file=tmp_path / "out.yaml"
        )
        assert len(result.entities) == 3

    def test_include_by_postfix(self, tmp_path):
        result = DeploymentPlanGeneratorCommand.filter(
            self._plan(), deploy_postfix_filter="core", output_file=tmp_path / "out.yaml"
        )
        assert all(e.deploy_postfix == "core" for e in result.entities)
        assert len(result.entities) == 2

    def test_exclude_by_postfix(self, tmp_path):
        result = DeploymentPlanGeneratorCommand.filter(
            self._plan(), deploy_postfix_filter="!core", output_file=tmp_path / "out.yaml"
        )
        assert all(e.deploy_postfix != "core" for e in result.entities)
        assert len(result.entities) == 1

    def test_include_by_component_name(self, tmp_path):
        result = DeploymentPlanGeneratorCommand.filter(
            self._plan(), component_names_filter="App-A", output_file=tmp_path / "out.yaml"
        )
        assert len(result.entities) == 1
        assert result.entities[0].version.startswith("App-A")

    def test_exclude_by_component_name(self, tmp_path):
        result = DeploymentPlanGeneratorCommand.filter(
            self._plan(), component_names_filter="!App-A,!App-B", output_file=tmp_path / "out.yaml"
        )
        assert len(result.entities) == 1
        assert result.entities[0].version.startswith("App-C")

    def test_include_by_namespace(self, tmp_path):
        result = DeploymentPlanGeneratorCommand.filter(
            self._plan(), namespace_filter="ns-1", output_file=tmp_path / "out.yaml"
        )
        assert len(result.entities) == 2
        assert all(e.namespace == "ns-1" for e in result.entities)

    def test_exclude_by_namespace(self, tmp_path):
        result = DeploymentPlanGeneratorCommand.filter(
            self._plan(), namespace_filter="!ns-1", output_file=tmp_path / "out.yaml"
        )
        assert len(result.entities) == 1
        assert result.entities[0].namespace == "ns-2"

    def test_include_by_wave(self, tmp_path):
        result = DeploymentPlanGeneratorCommand.filter(
            self._plan(), wave_filter="0,1", output_file=tmp_path / "out.yaml"
        )
        assert len(result.entities) == 2
        assert all(e.wave in (0, 1) for e in result.entities)

    def test_exclude_by_wave(self, tmp_path):
        result = DeploymentPlanGeneratorCommand.filter(
            self._plan(), wave_filter="!2", output_file=tmp_path / "out.yaml"
        )
        assert len(result.entities) == 2
        assert all(e.wave != 2 for e in result.entities)

    def test_mixed_include_and_exclude_on_same_dimension(self, tmp_path):
        # keep only "core" postfix, but also exclude App-C
        result = DeploymentPlanGeneratorCommand.filter(
            self._plan(),
            deploy_postfix_filter="core",
            component_names_filter="!App-C",
            output_file=tmp_path / "out.yaml",
        )
        assert len(result.entities) == 1
        assert result.entities[0].version.startswith("App-A")
