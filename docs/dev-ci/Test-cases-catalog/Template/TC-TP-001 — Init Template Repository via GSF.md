# Test Case ID: EnvGene_Template_TC_01_Init_TemplateRepo_From_GSF

**Description**

This test case verifies that an empty GitLab repository can be successfully initialized as a valid EnvGene Template Repository using GSF.

**Preconditions**

- An empty template repository exists in GitLab
- The repository does not contain any EnvGene-related files.
- `git-clean-repository`  has been executed

**Steps**

1. Configure the pipeline with the following parameters:
   - `gitlab_project = <group>/<envgene-template-repo>`
   - `type = GITLAB_GSF`
   - `gitlab_branch = master`
   - `gsf_image_name = artifactory...`
   - `gsf_extra_params._is_init = "true"`

2. Run `gitlab-maintenance-pipeline` with:
   - `SD_VERSION = <sd-artifact>:<version>`

**Expected Results**

- The pipeline completes with status **SUCCESS**

