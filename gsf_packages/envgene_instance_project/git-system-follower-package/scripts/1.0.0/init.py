# Copyright 2024-2025 NetCracker Technology Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from git_system_follower.develop.api.types import Parameters
from git_system_follower.develop.api.templates import create_template


def main(parameters: Parameters):
    """Install envgene-instance-project package
    
    Creates GitLab CI/CD file structure for envgene instance project.
    Uses variables from cookiecutter.json or passed via --extra.
    """
    # Collect template variables from parameters
    template_variables = {}
    
    # Pass all variables from extras to template
    for name, extra in parameters.extras.items():
        template_variables[name] = extra.value
    
    # Create default template
    create_template(parameters, 'default', template_variables)

