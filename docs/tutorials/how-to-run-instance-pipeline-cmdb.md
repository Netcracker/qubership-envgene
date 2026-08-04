# Tutorial: Run the Instance Pipeline (CMDB Workflow)

- [Tutorial: Run the Instance Pipeline (CMDB Workflow)](#tutorial-run-the-instance-pipeline-cmdb-workflow)
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

- Execute the Instance pipeline using the CMDB workflow
- Select the required pipeline parameters
- Understand which pipeline jobs are executed
- Verify that the environment was successfully generated
- Locate generated artifacts

# Prerequisites

Before starting, ensure that:

- An Instance Repository already exists.
- A Template Repository is available.
- The required Environment Template has already been promoted.
- A valid Application Definition exists in CMDB.
- Required CI/CD variables are configured.
- You have permission to run pipelines.

# When to Use This Workflow

Use this workflow when your environment lifecycle is integrated with CMDB and you want EnvGene to synchronize the generated environment with CMDB as part of the pipeline.

# Scenario

Assume you want to generate an environment named:

```
prod-cluster/prod-01
```

using the latest promoted Environment Template and import the generated data into CMDB.

# Step 1: Prepare the Environment

Verify that:

- the required Environment Template exists
- the required Solution Descriptor is available (if applicable)
- CMDB contains the Application Definition

# Step 2: Launch the Instance Pipeline

Open the Instance repository.

Navigate to:

```
CI/CD → Pipelines → Run pipeline
```

Select the target branch and start a new pipeline.

# Step 3: Configure Pipeline Parameters

Typical parameters include:

```text
ENV_NAMES=prod-cluster/prod-01
ENV_BUILD=true
GENERATE_EFFECTIVE_SET=true
CMDB_IMPORT=true
```

Additional parameters depend on your deployment scenario.

For the complete parameter reference, see:

- Instance Pipeline Parameters
- EnvGene Repository Variables

# Step 4: Understand the Pipeline Execution

Depending on the selected parameters, the pipeline creates a sequence of jobs.

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
        ↓
cmdb_import
```

For a complete description of every job, see **EnvGene Pipelines**.

# Step 5: Verify the Results

After the pipeline completes, verify:

- Environment Instance files were updated.
- Effective Set was generated (if enabled).
- Changes were committed back to the repository.
- CMDB import completed successfully.
- Pipeline finished without errors.

# Related Documentation

- EnvGene Pipelines
- Instance Pipeline Parameters
- How to Generate an Effective Set
- Calculator CLI