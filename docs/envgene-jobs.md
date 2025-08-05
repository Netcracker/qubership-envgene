# EnvGene Jobs

This document describes the CI/CD jobs used in EnvGene. For each job, you will find:

- The conditions under which the job is executed
- The Docker image used to run the job

Jobs are executed sequentially in the order listed below. Depending on the Condition, a job may or may not be executed. If any job in the sequence fails, the subsequent jobs in the flow are not executed.

The criteria for job execution, the sequence, and the Docker images are the same for both GitLab and GitHub CI/CD platforms.

This is the sequence of core EnvGene. EnvGene is extensible: in extensions, the sequence may be changed and new jobs may be added.

If multiple `ENV_NAMES` are specified:

- For each cluster from `ENV_NAMES`, parallel and independent Cloud Passport discovery flows are started, consisting of (`trigger_passport_job`, `get_passport_job`, `process_decryption_mode_job`).
- For each Environment from `ENV_NAMES`, parallel flows of the remaining jobs are started.

## Job sequence

1. **trigger_passport_job**:
   - **Condition**: Runs if [`GET_PASSPORT: true`](/docs/instance-pipeline-parameters.md#get_passport) AND only one job per cluster
   - **Docker image**: None. The Discovery repository is triggered from the pipeline

2. **get_passport_job**:
   - **Condition**: Runs if [`GET_PASSPORT: true`](/docs/instance-pipeline-parameters.md#get_passport) AND only one job per cluster
   - **Docker image**: [`qubership-envgene`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-envgene)

3. **process_decryption_mode_job**:
   - **Condition**: Runs if [`GET_PASSPORT: true`](/docs/instance-pipeline-parameters.md#get_passport) AND [`IS_OFFSITE: true`](/docs/instance-pipeline-parameters.md#is_offsite) AND only one job per cluster
   - **Docker image**: [`qubership-envgene`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-envgene)

4. **env_inventory_generation_job**:
   - **Condition**: Runs if [`ENV_INVENTORY_INIT: true`](/docs/instance-pipeline-parameters.md#env_inventory_init) AND [`IS_TEMPLATE_TEST: false`](/docs/instance-pipeline-parameters.md#env_template_test)
   - **Docker image**: [`qubership-envgene`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-envgene)

5. **credential_rotation**:
   - **Condition**: Runs if [`CRED_ROTATION_PAYLOAD`](/docs/instance-pipeline-parameters.md#cred_rotation_payload) is provided
   - **Docker image**: [`qubership-envgene`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-envgene)

6. **env_build_job**:
   - **Condition**: Runs if [`ENV_BUILD: true`](/docs/instance-pipeline-parameters.md#env_builder).
   - **Docker image**: [`qubership-envgene`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-envgene)

7. **generate_effective_set_job**:
   - **Condition**: Runs if [`GENERATE_EFFECTIVE_SET: true`](/docs/instance-pipeline-parameters.md#generate_effective_set).
   - **Docker image**: [`qubership-effective-set-generator`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-effective-set-generator)

8. **git_commit_job**:
   - **Condition**: Runs if there are jobs requiring a commit AND [`IS_TEMPLATE_TEST: false`](/docs/instance-pipeline-parameters.md#env_template_test)
   - **Docker image**: [`qubership-envgene`](https://github.com/Netcracker/qubership-envgene/pkgs/container/qubership-envgene)
