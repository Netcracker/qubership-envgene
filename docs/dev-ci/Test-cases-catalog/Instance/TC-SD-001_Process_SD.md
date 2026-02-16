# Test Case ID: EnvGene_SD_TC_01_Process_SD

**Description**

This test case verifies that when `SD_DATA` contains a single Solution Descriptor (SD) object in JSON-in-string format.

**Preconditions**

- The Instance Repository exists and is accessible

**Steps**

1. Configure the command `envgene-build-instance` with the following parameters:

   - `params.envgene_environment_id`: `<cluster-name>/<env-name>`
   - `params.trigger_type`: `CREATE_PIPELINE`
   - `params.sd_source_type`: `json`
   - `params.sd_data`: *(see payload in **Input Data** below)*

2. Run the command `envgene-build-instance`.

**Expected Results**

- The pipeline completes with status **SUCCESS**

**Input Data**

Use the following payload value for `params.sd_data`:

```json
"{\"version\":2.1,\"type\":\"solutionDeploy\",\"deployMode\":\"composite\",\"applications\":[{\"version\":\"MONITORING:0.64.1\",\"deployPostfix\":\"platform-monitoring\"},{\"version\":\"postgres:1.32.6\",\"deployPostfix\":\"postgresql\"}]}"