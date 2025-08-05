# Template Override Test Cases

- [Template Override Test Cases](#template-override-test-cases)
  - [TC-002-001: Template override on Cloud and Namespace level. Override includes paramsets with comments](#tc-002-001-template-override-on-cloud-and-namespace-level-override-includes-paramsets-with-comments)

This describes test cases for the [Template Override](/docs/features/template-override.md) feature

## TC-002-001: Template override on Cloud and Namespace level. Override includes paramsets with comments

**Status:** Active

**Test Data:**

- test_templates/env_templates/test-solution-structure-template.yaml
- test_templates/env_templates/test-solution-structure-template/cloud.yml.j2
- test_templates/env_templates/test-solution-structure-template/Namespaces/app-core.yml.j2
- test_templates/parameters/paramset-A.yaml
- test_templates/parameters/app/app-common.yml.j2
- test_environments/cluster01/env01/cloud.yml
- test_environments/cluster01/env01/Namespaces/app-core/namespace.yml
- test_environments/cluster01/env01/cloud.yml

**Pre-requisites:**

- `template_override` is used in Template Descriptor for override xParameterSets for Cloud and Namespace:

```yaml
...
cloud:
  template_path: <path-to-the-cloud-template-file>
  template_override:     
    deployParameterSets:
      - paramset-A
    e2eParameters:
      - paramset-A
    technicalConfigurationParameters:
      - paramset-A
namespaces:
  - template_path: <path-to-ns-template>
    template_override:
      deployParameterSets:
        - paramset-A
      e2eParameters:
        - paramset-A
      technicalConfigurationParameters:
        - paramset-A
...
```

- Cloud and Namespace templates have xParameterSets defined with comments:

```yaml
...
deployParameterSets:
  # comment line
  - paramset-B
e2eParameterSets:
  # comment line
  - paramset-B
technicalConfigurationParameterSets:
  # comment line
  - paramset-B
...
```

- Parameter sets `paramset-A`, `paramset-B` are created in the Template repository

**Steps:**

- `ENV_NAMES`: `<env-id>` # Single env-id
- `ENV_BUILDER`: `true`

**Expected Results:**

- Cloud and Namespace objects of the resulting Environment Instance contain:

```yaml
...
deployParameterSets: []
e2eParameterSets: []
technicalConfigurationParameterSets: []
...
```

- Cloud and Namespace objects of the resulting env instance don't contain `# comment line`
