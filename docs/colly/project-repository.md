# Project Repository

- [Project Repository](#project-repository)
  - [Repository Structure](#repository-structure)
    - [`parameters.yaml`](#parametersyaml)
    - [`credentials.yaml`](#credentialsyaml)
  - [To discuss](#to-discuss)

## Repository Structure

```text
└── projects
    ├── <customer-name>
    |   └── <project-name>
    |       ├── parameters.yaml
    |       └── credentials.yaml
    └── <other-project-name>
        ├── parameters.yaml
        └── credentials.yaml
```

The `<customer-name>` folder is optional.

Colly does not use `<customer-name>` or `<project-name>` from the folder names; instead, it reads `customerName` and `projectName` from inside the `parameters.yaml` file. For Colly, the projects are just a flat list. Folders are used only for better structure and readability for people.

Only two levels of folders are allowed (max depth: 2).

Any folder (within this folder depth limit) that contains a `parameters.yaml` file is considered a project folder.

### `parameters.yaml`

```yaml
# Mandatory
# Name of the customer
customerName: string
# Mandatory
# Name of the project
projectName: string
# To discuss. for different phases, there are different template versions from different branches
projectPhase: <???>
repositories:
  - # Mandatory
    # In MS1 only envgeneInstance is supported
    type: enum[ envgeneInstance, envgeneTemplate, envgeneDiscovery ]
    # Mandatory
    url: string
    # Pointer to Credential in credentials.yaml
    # In MS1, Colly will get access to the repository using a technical user, parameters for the user will be passed as a deployment parameter
    token: creds.get('<credential-id>').secret
    # Optional
    # If not set, the "default" branch is used (as in GitLab/GitHub)
    branches: list of strings # To discuss. Do we need mapping by phase? For discovery, to get template names from different branches
# Optional
# This is for MS1, we will do discovery later somehow
# Needs further thought because the same <artifact-template-name> can contain different templates in different versions
envgeneTemplates:
  # Mandatory
  # The key is EnvGene environment template artifact name (application from the application:version notation)
  # The value is a list of template names inside the artifact
  <artifact-template-name>: list of strings
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
customerName: ACME
projectName: ACME-bss
repositories:
  - type: envgeneInstance
    url: https://git.acme.com/instance
    token: instance-cred
  - type: envgeneTemplate
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

## To discuss

- [ ] Should the Project repository be used as the Maintenance inventory?

- [+] Use case for Colly using its own project repository:
  1. Read all projects and extract the URL, token, and branches from the `envgeneInstance` repositories in order to display the environments from these projects.
