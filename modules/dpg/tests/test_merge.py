"""Tests for the deploy-plan merge feature.

Covers:
  - DeployPlanEntity.__eq__ / _id (identity key used during merge)
  - DeploymentPlanCalculator.merge (core merge logic)
  - DeploymentPlanGeneratorCommand.merge (facade: file I/O + multi-plan chaining)

Known bugs exposed by the test suite (tests are written for the *correct* behaviour
so they will FAIL against the current implementation):
  - models.py L29: `id += "/" + self.generation_id` — generation_id is a UUID object,
    concatenation with str raises TypeError; should be `str(self.generation_id)`.
  - deployment_plan.py L34: `dest.entities[index].wave` uses the source-side index to
    index into dest, which is wrong when entities appear in a different order in dest;
    should use `candidate_entity.wave` instead.
"""

import uuid
import pytest
import yaml

from dpg.v1.internal.deployment_plan.models import DeployPlan, DeployPlanEntity, GenerationType
from dpg.v1.internal.deployment_plan.deployment_plan import DeploymentPlanCalculator
from dpg.v1.cmd.cmd import DeploymentPlanGeneratorCommand


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_entity(
    name: str,
    version: str = "1.0",
    namespace: str = "ns",
    wave: int = 0,
    generation_type: GenerationType = GenerationType.UNIQ_FOR_APP,
    generation_id: str = "",
) -> DeployPlanEntity:
    return DeployPlanEntity(
        version=f"{name}:{version}",
        namespace=namespace,
        wave=wave,
        generationType=generation_type,
        generationId=generation_id,
    )


def make_plan(*entities: DeployPlanEntity) -> DeployPlan:
    return DeployPlan(entities=list(entities))


# ---------------------------------------------------------------------------
# DeployPlanEntity equality / identity
# ---------------------------------------------------------------------------

class TestDeployPlanEntityEquality:
    def test_same_app_same_namespace_are_equal(self):
        a = make_entity("App", namespace="ns-1", wave=0)
        b = make_entity("App", namespace="ns-1", wave=5)
        assert a == b

    def test_different_namespace_are_not_equal(self):
        a = make_entity("App", namespace="ns-1")
        b = make_entity("App", namespace="ns-2")
        assert a != b

    def test_different_app_name_are_not_equal(self):
        a = make_entity("App-A", namespace="ns")
        b = make_entity("App-B", namespace="ns")
        assert a != b

    def test_uniq_for_version_same_version_are_equal(self):
        a = make_entity("App", version="2.0", namespace="ns", generation_type=GenerationType.UNIQ_FOR_VERSION)
        b = make_entity("App", version="2.0", namespace="ns", generation_type=GenerationType.UNIQ_FOR_VERSION)
        assert a == b

    def test_uniq_for_version_different_version_are_not_equal(self):
        a = make_entity("App", version="1.0", namespace="ns", generation_type=GenerationType.UNIQ_FOR_VERSION)
        b = make_entity("App", version="2.0", namespace="ns", generation_type=GenerationType.UNIQ_FOR_VERSION)
        assert a != b

    def test_uniq_for_run_same_generation_id_are_equal(self):
        gid = str(uuid.uuid4())
        a = make_entity("App", namespace="ns", generation_type=GenerationType.UNIQ_FOR_RUN, generation_id=gid)
        b = make_entity("App", namespace="ns", generation_type=GenerationType.UNIQ_FOR_RUN, generation_id=gid)
        assert a == b

    def test_uniq_for_run_different_generation_id_are_not_equal(self):
        a = make_entity("App", namespace="ns", generation_type=GenerationType.UNIQ_FOR_RUN, generation_id=str(uuid.uuid4()))
        b = make_entity("App", namespace="ns", generation_type=GenerationType.UNIQ_FOR_RUN, generation_id=str(uuid.uuid4()))
        assert a != b


# ---------------------------------------------------------------------------
# DeploymentPlanCalculator.merge
# ---------------------------------------------------------------------------

class TestDeploymentPlanCalculatorMerge:
    def test_new_entity_from_dest_is_appended(self):
        source = make_plan(make_entity("App-A", namespace="ns"))
        dest = make_plan(make_entity("App-B", namespace="ns"))

        result = DeploymentPlanCalculator.merge(source, dest)

        versions = [e.version for e in result.entities]
        assert "App-A:1.0" in versions
        assert "App-B:1.0" in versions

    def test_existing_entity_keeps_max_wave_when_dest_is_higher(self):
        source = make_plan(make_entity("App", namespace="ns", wave=1))
        dest = make_plan(make_entity("App", namespace="ns", wave=5))

        result = DeploymentPlanCalculator.merge(source, dest)

        assert len(result.entities) == 1
        assert result.entities[0].wave == 5

    def test_existing_entity_keeps_max_wave_when_source_is_higher(self):
        source = make_plan(make_entity("App", namespace="ns", wave=7))
        dest = make_plan(make_entity("App", namespace="ns", wave=2))

        result = DeploymentPlanCalculator.merge(source, dest)

        assert len(result.entities) == 1
        assert result.entities[0].wave == 7

    def test_existing_entity_same_wave_unchanged(self):
        source = make_plan(make_entity("App", namespace="ns", wave=3))
        dest = make_plan(make_entity("App", namespace="ns", wave=3))

        result = DeploymentPlanCalculator.merge(source, dest)

        assert result.entities[0].wave == 3

    def test_source_is_not_mutated(self):
        source = make_plan(make_entity("App", namespace="ns", wave=1))
        dest = make_plan(make_entity("App", namespace="ns", wave=9))

        DeploymentPlanCalculator.merge(source, dest)

        assert source.entities[0].wave == 1

    def test_mixed_new_and_existing_entities(self):
        """App-A exists in both (dest wave higher); App-B only in source; App-C only in dest."""
        source = make_plan(
            make_entity("App-A", namespace="ns", wave=0),
            make_entity("App-B", namespace="ns", wave=2),
        )
        dest = make_plan(
            make_entity("App-A", namespace="ns", wave=4),
            make_entity("App-C", namespace="ns", wave=1),
        )

        result = DeploymentPlanCalculator.merge(source, dest)

        by_name = {e.version.split(":")[0]: e for e in result.entities}
        assert set(by_name.keys()) == {"App-A", "App-B", "App-C"}
        assert by_name["App-A"].wave == 4
        assert by_name["App-B"].wave == 2
        assert by_name["App-C"].wave == 1

    def test_empty_source_dest_entities_all_appended(self):
        source = make_plan()
        dest = make_plan(
            make_entity("App-X", namespace="ns", wave=0),
            make_entity("App-Y", namespace="ns", wave=1),
        )

        result = DeploymentPlanCalculator.merge(source, dest)

        assert len(result.entities) == 2

    def test_empty_dest_result_equals_source(self):
        source = make_plan(make_entity("App", namespace="ns", wave=0))
        dest = make_plan()

        result = DeploymentPlanCalculator.merge(source, dest)

        assert len(result.entities) == 1
        assert result.entities[0].wave == 0

    def test_max_wave_correct_when_entities_in_different_order_in_dest(self):
        """Regression: dest.entities[index] uses the source index, which is wrong
        when dest has entities in a different order. The max wave must use
        candidate_entity.wave, not dest.entities[index].wave."""
        # source: [App-B(wave=1), App-A(wave=0)]  — B at index 0, A at index 1
        # dest:   [App-A(wave=5), App-B(wave=0)]  — A at index 0, B at index 1
        source = DeployPlan(entities=[
            make_entity("App-B", namespace="ns", wave=1),
            make_entity("App-A", namespace="ns", wave=0),
        ])
        dest = DeployPlan(entities=[
            make_entity("App-A", namespace="ns", wave=5),
            make_entity("App-B", namespace="ns", wave=0),
        ])

        result = DeploymentPlanCalculator.merge(source, dest)

        by_name = {e.version.split(":")[0]: e for e in result.entities}
        assert by_name["App-A"].wave == 5   # must pick dest wave=5, not dest[1].wave=0
        assert by_name["App-B"].wave == 1   # max(1, 0) = 1


# ---------------------------------------------------------------------------
# DeploymentPlanGeneratorCommand.merge  (file I/O layer)
# ---------------------------------------------------------------------------

class TestDeploymentPlanGeneratorCommandMerge:
    def test_empty_list_returns_none(self):
        result = DeploymentPlanGeneratorCommand.merge([])
        assert result is None

    def test_single_plan_returns_that_plan(self, tmp_path):
        plan = make_plan(make_entity("App", namespace="ns", wave=2))
        out = tmp_path / "out.yaml"

        result = DeploymentPlanGeneratorCommand.merge([plan], output_file=out)

        assert result is not None
        assert len(result.entities) == 1
        assert result.entities[0].wave == 2

    def test_two_plans_written_to_output_file(self, tmp_path):
        plan_a = make_plan(make_entity("App-A", namespace="ns", wave=0))
        plan_b = make_plan(make_entity("App-B", namespace="ns", wave=1))
        out = tmp_path / "deploy-plan.yaml"

        DeploymentPlanGeneratorCommand.merge([plan_a, plan_b], output_file=out)

        assert out.exists()
        data = yaml.safe_load(out.read_text())
        versions = [e["version"] for e in data]
        assert "App-A:1.0" in versions
        assert "App-B:1.0" in versions

    def test_two_plans_overlapping_takes_max_wave(self, tmp_path):
        plan_a = make_plan(make_entity("App", namespace="ns", wave=0))
        plan_b = make_plan(make_entity("App", namespace="ns", wave=3))
        out = tmp_path / "deploy-plan.yaml"

        result = DeploymentPlanGeneratorCommand.merge([plan_a, plan_b], output_file=out)

        assert result.entities[0].wave == 3

    def test_three_plans_merged_in_order(self, tmp_path):
        """Chaining: merge(plan1, plan2) then merge(result, plan3)."""
        plan_a = make_plan(make_entity("App-A", namespace="ns", wave=0))
        plan_b = make_plan(make_entity("App-B", namespace="ns", wave=1))
        plan_c = make_plan(
            make_entity("App-A", namespace="ns", wave=5),
            make_entity("App-C", namespace="ns", wave=2),
        )
        out = tmp_path / "deploy-plan.yaml"

        result = DeploymentPlanGeneratorCommand.merge([plan_a, plan_b, plan_c], output_file=out)

        by_name = {e.version.split(":")[0]: e for e in result.entities}
        assert set(by_name.keys()) == {"App-A", "App-B", "App-C"}
        assert by_name["App-A"].wave == 5

    def test_merge_from_yaml_files(self, tmp_path):
        file_a = tmp_path / "plan-a.yaml"
        file_b = tmp_path / "plan-b.yaml"
        out = tmp_path / "merged.yaml"

        file_a.write_text(yaml.dump([
            {"version": "App-A:1.0", "namespace": "ns", "wave": 0,
             "deployPostfix": "", "generationType": "UniqForApp", "generationId": ""},
        ]))
        file_b.write_text(yaml.dump([
            {"version": "App-A:1.0", "namespace": "ns", "wave": 2,
             "deployPostfix": "", "generationType": "UniqForApp", "generationId": ""},
            {"version": "App-B:1.0", "namespace": "ns", "wave": 0,
             "deployPostfix": "", "generationType": "UniqForApp", "generationId": ""},
        ]))

        result = DeploymentPlanGeneratorCommand.merge(
            [str(file_a), str(file_b)], output_file=out
        )

        by_name = {e.version.split(":")[0]: e for e in result.entities}
        assert by_name["App-A"].wave == 2
        assert "App-B" in by_name
