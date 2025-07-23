# EnvGene Pipelines

This document describes the CI/CD pipelines and jobs in these pipelines used in EnvGene. For each pipeline, the set and sequence of jobs is described. For each job, the conditions under which the job is executed and the Docker image used to run the job are specified.

Jobs are executed sequentially in the **listed order**. Depending on the condition, a job may or may not be executed. If any job in the sequence fails, the subsequent jobs in the flow are not executed.

The conditions for job execution, the sequence, and the Docker images are the same for both GitLab and GitHub CI/CD platforms.

> [!NOTE]
> This is the sequence of the core EnvGene. EnvGene is extensible: in extensions, the sequence may be changed and new jobs may be added.

## Instance pipeline

The main pipeline of the EnvGene Instance repository, in which the main functions of EnvGene are performed, such as Environment Instance generation, Effective Set generation, and others.

This pipeline is triggered manually by the user via the GitLab/GitHub UI or by an external system via the GitLab/GitHub API.

If multiple [`ENV_NAMES`](/docs/instance-pipeline-parameters.md#env_names) are specified:

- For each cluster from `ENV_NAMES`, parallel and independent Cloud Passport discovery flows are started, consisting of (`trigger_passport_job`, `get_passport_job`, `process_decryption_mode_job`).
- For each Environment from `ENV_NAMES`, parallel flows of the remaining jobs are started.

### [Instance pipeline] Job sequence

1. **trigger_passport**:
   - **Condition**: Runs if [`GET_PASSPORT: true`](/docs/instance-pipeline-parameters.md#get_passport) AND only one job per cluster
   - **Docker image**: None. The Discovery repository is triggered from the pipeline

2. **get_passport**:
   - **Condition**: Runs if [`GET_PASSPORT: true`](/docs/instance-pipeline-parameters.md#get_passport) AND only one job per cluster
   - **Docker image**: [`qubership-envgene`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-envgene)

3. **process_decryption_mode**:
   - **Condition**: Runs if [`GET_PASSPORT: true`](/docs/instance-pipeline-parameters.md#get_passport) AND [`IS_OFFSITE: true`](/docs/instance-pipeline-parameters.md#is_offsite) AND only one job per cluster
   - **Docker image**: [`qubership-envgene`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-envgene)

4. **env_inventory_generation**:
   - **Condition**: Runs if [`IS_TEMPLATE_TEST: false`](/docs/instance-pipeline-parameters.md#env_template_test) AND ([`ENV_SPECIFIC_PARAMETERS`](/docs/instance-pipeline-parameters.md#env_specific_params) OR [`ENV_TEMPLATE_NAME`](/docs/instance-pipeline-parameters.md#env_template_name))
   - **Docker image**: [`qubership-envgene`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-envgene)

5. **credential_rotation**:
   - **Condition**: Runs if [`CRED_ROTATION_PAYLOAD`](/docs/instance-pipeline-parameters.md#cred_rotation_payload) is provided
   - **Docker image**: [`qubership-envgene`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-envgene)

6. **env_build**:
   - **Condition**: Runs if [`ENV_BUILD: true`](/docs/instance-pipeline-parameters.md#env_builder).
   - **Docker image**: [`qubership-envgene`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-envgene)

7. **generate_effective_set**:
   - **Condition**: Runs if [`GENERATE_EFFECTIVE_SET: true`](/docs/instance-pipeline-parameters.md#generate_effective_set) OR [`SD_VERSION`](/docs/instance-pipeline-parameters.md#sd_version) OR [`SD_DATA`](/docs/instance-pipeline-parameters.md#sd_data)
   - **Docker image**: [`qubership-effective-set-generator`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-effective-set-generator)

8. **git_commit**:
   - **Condition**: Runs if there are jobs requiring changes to the repository AND [`IS_TEMPLATE_TEST: false`](/docs/instance-pipeline-parameters.md#env_template_test)
   - **Docker image**: [`qubership-envgene`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-envgene)