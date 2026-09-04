#!/usr/bin/env python3
import click

from qubership_pipelines_common_library.v1.utils.utils_cli import utils_cli

@click.group()
def cli():
    """"""

@cli.group()
def plan():
    """Deploy Plan modification commands"""

@plan.command("merge")
@utils_cli
def calculate_plan(**kwargs):
    from dpg.v1.plan import PlanDeploymentMerge
    command = PlanDeploymentMerge(**kwargs)
    command.run()

@plan.command("calculate")
@utils_cli
def calculate_plan(**kwargs):
    from dpg.v1.plan import PlanDeploymentCalculate
    command = PlanDeploymentCalculate(**kwargs)
    command.run()

@plan.command("map")
@utils_cli
def calculate_plan(**kwargs):
    from dpg.v1.plan import PlanDeploymentMapNamespaces
    command = PlanDeploymentMapNamespaces(**kwargs)
    command.run()

@plan.command("filter")
@utils_cli
def filter_plan(**kwargs):
    from dpg.v1.plan import PlanDeploymentFilter
    command = PlanDeploymentFilter(**kwargs)
    command.run()

if __name__ == "__main__":
    cli()
