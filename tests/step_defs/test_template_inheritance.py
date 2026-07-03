import os
from pytest_bdd import scenarios, given, when, then
from tests.framework.workspace import EnvGeneWorkspace
import pytest

scenarios('../features/template_inheritance/template-inheritance.feature')

@given('a child Template Repository is configured with parent-templates')
def child_template_configured(workspace: EnvGeneWorkspace):
    pass

@given('a child Template Repository references multiple parent templates')
def child_template_multiple_parents(workspace: EnvGeneWorkspace):
    pass

@given('the child Template Descriptor specifies composite_structure explicitly')
def child_template_composite_structure(workspace: EnvGeneWorkspace):
    pass

@given('a child Template Descriptor defines cloud.parent and overrides-parent section')
def child_template_cloud_overrides(workspace: EnvGeneWorkspace):
    pass

@given('a child Template Descriptor defines a namespace with parent and overrides-parent section')
def child_template_namespace_overrides(workspace: EnvGeneWorkspace):
    pass

@when('the template build pipeline is executed')
def execute_template_build_pipeline(workspace: EnvGeneWorkspace):
    pytest.xfail("Template build pipeline is external and not testable in this repo")

@then('the child template artifact inherits components from the basic-cloud parent')
def verify_pt1(workspace: EnvGeneWorkspace):
    pass

@then('the tenant and namespaces are composed from referenced parent templates')
def verify_pt2_tenant(workspace: EnvGeneWorkspace):
    pass

@then('cloud and composite_structure are taken from child repository sources')
def verify_pt2_cloud(workspace: EnvGeneWorkspace):
    pass

@then('the built artifact contains the explicit child composite_structure reference')
def verify_cs1(workspace: EnvGeneWorkspace):
    pass

@then('the child Cloud template is inherited from parent and updated by overrides-parent')
def verify_ov1(workspace: EnvGeneWorkspace):
    pass

@then('the child Namespace template is inherited from parent and updated by overrides-parent')
def verify_ov2(workspace: EnvGeneWorkspace):
    pass

