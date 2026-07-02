from pytest_bdd import scenarios
from tests.shared_steps.unified_pipeline_steps import *
from tests.shared_steps.topology_steps import *

scenarios('../features/cluster_endpoint_topology_context/cluster-endpoint-topology-context.feature')
