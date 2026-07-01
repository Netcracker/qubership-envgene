from pytest_bdd import scenarios
from tests.shared_steps.git_hook_steps import *
from tests.shared_steps.common_steps import *

scenarios('../features/git_hooks/credential-encryption-pre-hook.feature')
