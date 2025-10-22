# Project Repository

- [Project Repository](#project-repository)
  - [Repository Structure](#repository-structure)
    - [`parameters.yaml`](#parametersyaml)
    - [`credentials.yaml`](#credentialsyaml)

## Repository Structure

```text
└── projects
    └── <project-name>
        ├── parameters.yaml
        └── credentials.yaml
```

### `parameters.yaml`

```yaml
# Mandatory
# Name of the project
# Must be the same as parent folder name
name: string
# Mandatory
# Project repositories
repositories:
  <repository-name>:
    type: enum[ envgeneInstance, envgeneTemplate, envgeneDiscovery ]
    url: string
    # Pointer to Credential in credentials.yaml
    token: credential
    branches: list of strings
# Optional
envgeneTemplates:
  # Mandatory
  # The key is EnvGene environment template artifact name (application from the application:version notation)
  # The value is a list of template names inside the artifact
  <artifact-template-name>: list of strings
# Optional
# Extends the list of possible values for the `role` attribute of the Environment in this project
environmentRoleExtensions: list of strings
# Optional
# Extends the list of possible values for the `status` attribute of the Environment in this project
environmentStatusExtensions: list of strings
```

### `credentials.yaml`

Contains [Credential](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#credential) objects

```yaml
<credential-usernamePassword>:
  type: usernamePassword
  data:
    username: string
    password: string
<credential-secret>:
  type: secret
  data:
    secret: string
```

Example:

```yaml
name: ACME
repositories:
  instance:
    type: envgeneInstance
    url: https://git.acme.com/instance
    token: instance-cred
    branches:
      - master
  template:
    type: envgeneTemplate
    url: https://git.acme.com/template
    token: template-cred
    branches:
      - r25.3
      - r25.4
envgeneTemplates:
  envgene-acme:
    - main
    - dt
    - dm
environmentRoleExtensions:
  - SIT
  - UAT
environmentStatusExtensions:
  - MIGRATING
```

```yaml
instance-cred:
  type: secret
  data:
    secret: "MGE3MjYwNTQtZGE4My00MTlkLWIzN2MtZjU5YTg3NDA2Yzk0MzlmZmViZGUtYWY4_PF84_ba"
template-cred:
  type: secret
  data:
    secret: "MGE3MjYwNTQtZGE4My00MTlkLWIzN2MtZjU5YTg3NDA2Yzk0MzlmZmViZGUtYWY4_PF84_bb"
```
