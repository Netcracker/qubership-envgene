# Tutorial: Run the Instance Pipeline (Non-CMDB Workflow)

- [Tutorial: Run the Instance Pipeline (Non-CMDB Workflow)](#tutorial-run-the-instance-pipeline-non-cmdb-workflow)
- [What You Will Learn](#what-you-will-learn)
- [Prerequisites](#prerequisites)
- [When to Use This Workflow](#when-to-use-this-workflow)
- [Scenario](#scenario)
- [Step 1: Prepare the Environment](#step-1-prepare-the-environment)
- [Step 2: Launch the Instance Pipeline](#step-2-launch-the-instance-pipeline)
- [Step 3: Configure Pipeline Parameters](#step-3-configure-pipeline-parameters)
- [Step 4: Understand the Pipeline Execution](#step-4-understand-the-pipeline-execution)
- [Step 5: Verify the Results](#step-5-verify-the-results)
- [Related Documentation](#related-documentation)

# What You Will Learn

By the end of this tutorial you will know how to:

- Execute the Instance pipeline without CMDB integration
- Configure the required pipeline parameters
- Understand which pipeline jobs are executed
- Generate an Environment Instance and Effective Set
- Verify the generated repository content

# Prerequisites

Before starting, ensure that:

- An Instance Repository already exists.
- A Template Repository is available.
- The required Environment Template has already been promoted.
- Required CI/CD variables are configured.
- You have permission to run pipelines.

> **Note**
>
> This workflow does not require CMDB import.

# When to Use This Workflow

Use this workflow when you want EnvGene to generate or update an Environment Instance without synchronizing the results to CMDB.

Typical use cases include:

- Development environments
- Local validation
- Template testing
- Effective Set generation
- CI validation

# Scenario

Generate an environment named:

```
dev-cluster/dev-01
```

without importing data into CMDB.

# Step 1: Prepare the Environment

Verify that:

- the Environment Template is available
- required repository content exists
- Solution Descriptor is available (if required)

# Step 2: Launch the Instance Pipeline

Open the Instance repository.

Navigate to:

```
CI/CD → Pipelines → Run pipeline
```

Select the desired branch and start a new pipeline.

# Step 3: Configure Pipeline Parameters

Example:

```text
ENV_NAMES=dev-cluster/dev-01
ENV_BUILD=true
GENERATE_EFFECTIVE_SET=true
CMDB_IMPORT=false
```

Depending on the scenario, additional parameters may be required.

See **Instance Pipeline Parameters** for the complete parameter reference.

# Step 4: Understand the Pipeline Execution

Typical execution flow:

```
env_inventory_generation
        ↓
app_reg_def_process
        ↓
process_sd
        ↓
env_build
        ↓
generate_effective_set
        ↓
git_commit
```

Unlike the CMDB workflow, the **cmdb_import** job is skipped.

For detailed descriptions of every pipeline job, see **EnvGene Pipelines**.

# Step 5: Verify the Results

After the pipeline completes, verify:

- Environment Instance was generated.
- Effective Set was generated (if enabled).
- Repository changes were committed.
- No CMDB import job was executed.
- Pipeline completed successfully.

# Related Documentation

- EnvGene Pipelines
- Instance Pipeline Parameters
- How to Generate an Effective Set
- Calculator CLI