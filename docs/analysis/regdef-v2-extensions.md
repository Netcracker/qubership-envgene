# RegDef v2 extensions

- [RegDef v2 extensions](#regdef-v2-extensions)
  - [Open questions](#open-questions)
  - [Limitations](#limitations)
  - [Extensions](#extensions)
    - [EXT1 — `accessRoles`](#ext1--accessroles)
      - [Roles](#roles)
    - [EXT2 — The `REGISTRY_CREDENTIALS` variable](#ext2--the-registry_credentials-variable)
    - [EXT3 — Extend `authConfig` to match what QCL already supports](#ext3--extend-authconfig-to-match-what-qcl-already-supports)
    - [EXT4 — Repositories by artifact type](#ext4--repositories-by-artifact-type)
    - [EXT5 — New artifact types](#ext5--new-artifact-types)
    - [EXT6 — Repository: `url` + `repoName`](#ext6--repository-url--reponame)
  - [Model](#model)
  - [`authConfig` method catalog](#authconfig-method-catalog)
  - [Artifact sections](#artifact-sections)
  - [Examples](#examples)

## Open questions

1. [Done] Which set of repository types (snapshot, staging, release, snapshotGroup, releaseGroup, ...) is needed?

    A: snapshot, release - mandatory, others are optional. extendable. See EXT4

2. Should `helmLibConfig` and `helmAppConfig` be unified?

3. [Done] Should `mavenConfig` be split into two types — one for the DD, one for maven libraries?

   A: Yes

   1. `mavenDD` - all cloud DD related files (.json, .zip, ...)
   2. `maven` - smart plug, sample repository, envgene template, ...

4. [Done] Extend `provider` with `gitlab`?

    A: Not now, may be later

5. [Done] Allow multiple registries for the same artifact type in one Reg Def?

    A: No — one registry per artifact type (no such cases).

6. [Done] Rename `scopes` to `securityScopes`, `accessRoles` or something else?

   A: Yes

   1. `scopes` -> `accessRoles`
   2. `r` -> `read`, `rw` -> `publish`, `rwd` -> `manage`

7. [Done] Extend artifact types with `apm`?

    A: No, use gsf gear (Docker)

8. [Done] "Red zone" case — how Reg Defs are scoped across sites

    A: A site is an environment that holds exactly one instance of each registry type (one `maven`, one `docker`, ...).
    Each site has its own separate set of Registry Definitions. Multiple registries of the same type are therefore
    modeled by separate Reg Def sets, not within a single Reg Def (see Q5).

9. [Done] How to bind consumer configuration to a repository

    ```yaml
    # Option 1 — per-repo boolean flags
    - type: snapshot
      buildTarget: true       # default false
      deliveryTarget: true    # default false

    # Option 2 — targets list
    - type: snapshot
      targets:
        - build
        - cleanup
        - delivery

    # Option 3 — per-operation consumerConfig block
    - type: snapshot
      consumerConfig:
        build:
          defaultTarget: true
        cleanup:
          key: value
        delivery:
          key: value
    
    # **chosen** Option 4 — no consumer specific config in Reg Def
    ```

10. [Done] Extend registry type with `ftp`, `s3`, `smb` for delivery cases?
    1. Opt1: extend Reg Def
    2. Opt2: store it in delivery tool/pipeline config **chosen**

11. [Done] Extend registry provider with GitLab container registry?

    A: Can be extended later

12. [Done] How to handle promote/delivery cases - move artifact from one registry to other one

    A: Source and destination (may be multiple) should be described in promote/delivery config

## Limitations

1. `authConfig` binds at the `registries` entry (artifact-type) level, not per repository. All repositories in an
   entry share one `authConfig`. No way to point `snapshot` and `release` within the same entry at registries with
   different authentication.
2. Proxy routing is not modeled. Whether traffic goes via a proxy or direct is consumer side configuration
   (`HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY`).

## Extensions

### EXT1 — `accessRoles`

`accessRoles` maps a role to a `credId` — the identity that performs that class of operations. It is required,
except for `anonymous` (no credential, so `accessRoles` is not needed).

Each role maps to a `credId` - a key into `REGISTRY_CREDENTIALS.data.<regName>` (EXT2).

#### Roles

Three fixed roles:

- `read` — pull / resolve.
- `publish` — read + write/create.
- `manage` — read + write + delete.

```yaml
accessRoles:
  read: reg-read          # pull only
  publish: reg-push       # read + write
  manage: reg-admin       # read + write + delete
```

### EXT2 — The `REGISTRY_CREDENTIALS` variable

`credId` points to a payload in the consumer CI/CD variable `REGISTRY_CREDENTIALS`.

The variable is required whenever `accessRoles` is used: for every `authMethod` except `anonymous`.

The payload is a secret (user/password, keys, SA JSON, client secret), or a non-secret identifier (`roleArn` for
assumeRole, `serviceAccount` for federation). `assumeRole` with `awsSourceCredentialsId` adds a separate `credId`
for the bootstrap secret.

`data` is namespaced by `regName`: `data.<regName>.<credId>`. Inside a payload, each field is either a literal or a
vals reference.

```yaml
kind: RegistryCredentials
version: v1
data:
  <regName>:
    <credId>: <payload>
```

Payload shapes by authMethod:

```yaml
# nexus / artifactory × userPass
nexus-read:
  username: string          # literal | ref+vault://…
  password: string          # literal | ref+vault://…

# gcp × serviceAccount
gcp-sa-read:
  secret: string            # literal (SA JSON base64) | ref+vault://…

# aws × secret
aws-key-read:
  accessKeyId: string       # literal | ref+vault://…
  secretAccessKey: string   # literal | ref+vault://…
  sessionToken: string      # literal | ref+vault://…

# azure × oauth2
azure-sp-read:
  clientId: string
  clientSecret: string

# aws × assumeRole
aws-role-read:
  roleArn: string           # non-secret identifier, literal (vals allowed but pointless)

# gcp × federation
gcp-fed-read:
  serviceAccount: string    # non-secret identifier, literal (vals allowed but pointless)

# anonymous: no credential
```

Two complete examples with every payload type: one all vals references, one all literal values.

```yaml
# REGISTRY_CREDENTIALS — all vals references
kind: RegistryCredentials
version: v1
data:
  my-registry:                # RegDef.name
    nexus-cred:               # userPass
      username: ref+vault://secret/data/registry/nexus#username
      password: ref+vault://secret/data/registry/nexus#password
    aws-cred:                 # aws secret
      accessKeyId:     ref+vault://secret/data/registry/aws#accessKeyId
      secretAccessKey: ref+vault://secret/data/registry/aws#secretAccessKey
      sessionToken:    ref+vault://secret/data/registry/aws#sessionToken
    gcp-cred:                 # gcp serviceAccount
      secret: ref+vault://secret/data/registry/gcp#json
    azure-cred:               # azure oauth2
      clientId:     ref+vault://secret/data/registry/azure#clientId
      clientSecret: ref+vault://secret/data/registry/azure#clientSecret
    aws-role-cred:            # aws assumeRole (non-secret roleArn)
      roleArn: ref+vault://secret/data/registry/aws#roleArn
    gcp-fed-cred:             # gcp federation (non-secret serviceAccount)
      serviceAccount: ref+vault://secret/data/registry/gcp#serviceAccount
```

```yaml
# REGISTRY_CREDENTIALS — all literal values
kind: RegistryCredentials
version: v1
data:
  my-registry:                # RegDef.name
    nexus-cred:               # userPass
      username: reader
      password: s3cr3t
    aws-cred:                 # aws secret
      accessKeyId:     AKIAIOSFODNN7EXAMPLE
      secretAccessKey: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
      sessionToken:    FwoGZXIvYXdzEBYaEXAMPLE
    gcp-cred:                 # gcp serviceAccount
      secret: ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsIC4uLiB9Cg==
    azure-cred:               # azure oauth2
      clientId:     11111111-2222-3333-4444-555555555555
      clientSecret: aBcD3fG~hIjKlMnOpQrStUvWxYz0123456789
    aws-role-cred:            # aws assumeRole (non-secret roleArn)
      roleArn: arn:aws:iam::123456789012:role/eg-reg-admin
    gcp-fed-cred:             # gcp federation (non-secret serviceAccount)
      serviceAccount: eg-reg@my-project.iam.gserviceaccount.com
```

### EXT3 — Extend `authConfig` to match what QCL already supports

- `awsService` (`codeArtifact` | `ecr`): the AWS registry service, with different token flows. CodeArtifact serves
  maven and npm. ECR serves Docker and OCI artifacts, for example helm OCI.
- `azureService` (`acr` | `artifacts`): the Azure service. ACR serves Docker and OCI artifacts. Azure Artifacts
  serves packages.
- `gcpScopes`: optional OAuth scopes (QCL `with_service_account_key` / `with_oidc_creds`), default `cloud-platform`.
- `azureOAuth2Params`: optional token-request params, grant and scope (QCL `with_oauth2_custom_data`).
- `awsSourceCredentialsId`: optional STS bootstrap key (AWS `source_profile`). Empty means IRSA or workload identity.

### EXT4 — Repositories by artifact type

snapshot, release - mandatory, others are optional. extendable.
Within a registry each repository type appears at most once — `type` is unique per entry.

| artifact type  | repository types                                        |
|----------------|---------------------------------------------------------|
| `maven`        | snapshot, staging, release, snapshotGroup, releaseGroup |
| `mavenDD`      | snapshot, staging, release, snapshotGroup, releaseGroup |
| `docker`       | snapshot, staging, release, group                       |
| `go`           | snapshot,          release, group, proxy                |
| `npm`          | snapshot,          release, group                       |
| `raw`          | snapshot, staging, release                              |
| `python`       | snapshot, staging, release                              |
| `helmLib`      | snapshot,          release                              |
| `helmApp`      | snapshot, staging, release, group                       |
| `helmLibOCI` ¹ | snapshot,          release                              |
| `helmAppOCI` ¹ | snapshot, staging, release, group                       |

¹ types mirror helmLib/helmApp.

### EXT5 — New artifact types

A new artifact type is added as another `registries` entry with its own `artifactType`, `authConfig`, and
`repositories`. The set of artifact types is not fixed — it is extendable. Examples:

- **OCI helm** — kept separate from classic (index-based) helm (`helmLib` / `helmApp`):

```yaml
registries:
  - artifactType: helmLibOCI
    authConfig: string
    repositories:
      - type: string
        url: string
        repoName: string
  - artifactType: helmAppOCI
    authConfig: string
    repositories:
      - type: string
        url: string
        repoName: string
```

- **python**:

```yaml
registries:
  - artifactType: python
    authConfig: string
    repositories:
      - type: string
        url: string
        repoName: string
```

### EXT6 — Repository: `url` + `repoName`

- `url`: the full pull/push URL.
- `repoName`: the repository key, used by the control plane only. It is not part of pull or push, since `url` is
  self-sufficient. Set it explicitly, because you cannot derive it from a proxied or opaque `url` (for example,
  `url=cdn.company.com/charts` with repository key `helm-prod-virtual`).

Set `repoName` only on concrete repositories that use authentication. For `anonymous`, group, and proxy, leave it out.

An OCI Docker registry uses one of two notations:

- path, `host/repoName/image`:
  - `123456789.dkr.ecr.eu-west-1.amazonaws.com/docker-releases/myapp:1.0` (ECR)
  - `europe-docker.pkg.dev/my-project/docker-releases/myapp:1.0` (GCP-AR)
  - `artifactory.company.com/docker-releases/myapp:1.0` (Artifactory repo-path)
- authority, port or subdomain, `host:port/image` or `repoName.host/image`:
  - `artifactory.company.com:18082/myapp:1.0` (port, Nexus/Artifactory)
  - `docker-releases.artifactory.company.com/myapp:1.0` (subdomain, Artifactory)

In both, `url` is the full pull base, and `repoName` stays separate (control plane).

`authConfig.baseUrl` is the registry server's control-plane (REST) URL. It is not a pull base: pull uses the
per-repo `url`, and you never append the repository to `baseUrl`. It applies to artifactory and nexus only.
`anonymous` does not need it, because the control plane requires authentication.

```yaml
registries:
  - artifactType: maven
    authConfig: <name>
    repositories:
      - type: release
        url: https://nexus.company.internal/repository/maven-releases
        repoName: maven-releases
```

## Model

```yaml
# Mandatory. Object kind.
kind: RegistryDefinition
# Mandatory. Registry Definition object version.
version: v2
# Mandatory. Registry name, unique per site.
name: string
# Mandatory. Named auth profiles, referenced by `registries` entries via `authConfig: <name>`.
authConfig:
  <auth-config-name>:
    # Mandatory. Registry provider.
    provider: enum [ artifactory, nexus, gcp, aws, azure ]
    # Mandatory. Authentication method. Valid values depend on `provider` (see table below).
    authMethod: enum [ anonymous, userPass, secret, serviceAccount, oauth2, federation, assumeRole ]
    # Optional. Control-plane (REST) URL, not a pull base. Pull uses the per-repo `url`.
    # `provider: artifactory` or `nexus`, non-anonymous authMethod only.
    baseUrl: string

    # Identity binding. `accessRoles` maps a role to a credId. Mandatory except for `authMethod: anonymous`.
    # Roles: `read` (pull), `publish` (read and write), `manage` (read, write, and delete).
    # Each value is a credId, a local key into `REGISTRY_CREDENTIALS.data.<name>`.
    accessRoles:
      <read|publish|manage>: string     # credId

    # --- Provider-specific fields ---
    # Optional. AWS registry service, selects the token flow. `provider: aws` only.
    awsService: enum [ codeArtifact, ecr ]
    # Optional. AWS region. `provider: aws` only.
    awsRegion: string
    # Optional. CodeArtifact domain. Required for `awsService: codeArtifact`.
    awsDomain: string
    # Optional. Session-name prefix for AssumeRole. `authMethod: assumeRole` only.
    awsRoleSessionPrefix: string
    # Optional. Bootstrap credential for STS (AWS `source_profile`). Empty means IRSA or workload identity.
    # `authMethod: assumeRole` only.
    awsSourceCredentialsId: string
    # Optional. OIDC interaction. `authMethod: federation` only.
    gcpOIDC:
      # Mandatory. External OIDC server URL.
      URL: string
      # Optional. Custom parameters for the OIDC server.
      customParams:
        - <key>: <value>
    # Optional. GCP project. `authMethod: federation` only.
    gcpRegProject: string
    # Optional. Workload identity pool ID. `authMethod: federation` only.
    gcpRegPoolId: string
    # Optional. Workload identity provider ID. `authMethod: federation` only.
    gcpRegProviderId: string
    # Optional. OAuth scopes. Default https://www.googleapis.com/auth/cloud-platform. `provider: gcp` only.
    gcpScopes:
      - string
    # Optional. GCP region. `provider: gcp` only.
    gcpRegion: string
    # Optional. Azure registry service. `provider: azure` only.
    azureService: enum [ acr, artifacts ]
    # Optional. Azure tenant ID. `provider: azure` only.
    azureTenantId: string
    # Optional. ACR registry name. Required for `azureService: acr`.
    azureACRName: string
    # Optional. Target resource for ACR. `provider: azure` only.
    azureACRResource: string
    # Optional. Token-request params (grant and scope). `authMethod: oauth2` only.
    azureOAuth2Params:
      <key>: <value>

# Mandatory.
# Per-artifact-type registry entries. Each binds one artifact type to its authConfig and repositories, one entry per type.
registries:
    # Mandatory. Artifact type this entry serves.
  - artifactType: enum [ maven, mavenDD, docker, helmLib, helmApp, helmLibOCI, helmAppOCI, go, npm, raw, python ]
    # Mandatory. Reference to an `authConfig` profile by name.
    authConfig: string
    # Mandatory. Repositories for this artifact type. At least snapshot and release.
    # One repository per type, `type` is unique within the entry.
    repositories:
      - type: string       # repository type. snapshot and release mandatory, others optional. Unique within the entry.
        url: string        # full pull/push base (http URL, or OCI host / host:port / repo.host). Carries addressing style.
        repoName: string   # control-plane only. Not for pull/push. Omit for anonymous, group, proxy.
```

**Valid `authMethod` values per `provider`:**

| Provider      | Valid `authMethod` values                   |
|---------------|---------------------------------------------|
| `artifactory` | `anonymous`, `userPass`                     |
| `nexus`       | `anonymous`, `userPass`                     |
| `gcp`         | `anonymous`, `serviceAccount`, `federation` |
| `aws`         | `anonymous`, `secret`, `assumeRole`         |
| `azure`       | `anonymous`, `oauth2`                       |

**Identity per `authMethod`**. The `accessRoles.<role>` value is a `credId`. The payload it points to in the
variable depends on `authMethod`:

| `authMethod`     | `credId` payload (in `REGISTRY_CREDENTIALS.data`)    |
|------------------|------------------------------------------------------|
| `anonymous`      | —                                                    |
| `userPass`       | `username` + `password`                              |
| `secret`         | `accessKeyId` + `secretAccessKey` (+ `sessionToken`) |
| `serviceAccount` | `secret` (SA JSON)                                   |
| `oauth2`         | `clientId` + `clientSecret`                          |
| `federation`     | `serviceAccount` (non-secret)                        |
| `assumeRole`     | `roleArn` (non-secret) ¹                             |

¹ `assumeRole` + `awsSourceCredentialsId`: the STS bootstrap secret is a separate `credId`
(payload `accessKeyId` + `secretAccessKey`).

**`accessRoles` — three fixed roles:**

| Role      | Rights                 |
|-----------|------------------------|
| `read`    | read (pull)            |
| `publish` | read + write / create  |
| `manage`  | read + write + delete  |

For `anonymous`, `accessRoles` is not needed.

## `authConfig` method catalog

All valid provider × authMethod pairs.

```yaml
authConfig:

  # anonymous — EnvGene ✅ + QCL —
  public:
    provider: nexus
    authMethod: anonymous

  # Artifactory × userPass — EnvGene ✅ + QCL —
  artifactory-up:
    provider: artifactory
    authMethod: userPass
    baseUrl: https://artifactory.company.com/artifactory
    accessRoles:
      read: artifactory-read
      publish: artifactory-publish
    # REGISTRY_CREDENTIALS.data.<regName>:
    #   artifactory-read:
    #     username: ref+vault://secret/data/registry/artifactory#read-user       # reader
    #     password: ref+vault://secret/data/registry/artifactory#read-pass       # s3cr3t-r34d
    #   artifactory-publish:
    #     username: ref+vault://secret/data/registry/artifactory#publish-user    # publisher
    #     password: ref+vault://secret/data/registry/artifactory#publish-pass    # s3cr3t-publ1sh

  # Nexus × userPass — EnvGene ✅ + QCL —
  nexus-up:
    provider: nexus
    authMethod: userPass
    baseUrl: https://nexus.company.internal
    accessRoles:
      read: nexus-read
      publish: nexus-publish
    # REGISTRY_CREDENTIALS.data.<regName>:
    #   nexus-read:
    #     username: ref+vault://secret/data/registry/nexus#read-user             # reader
    #     password: ref+vault://secret/data/registry/nexus#read-pass             # s3cr3t-r34d
    #   nexus-publish:
    #     username: ref+vault://secret/data/registry/nexus#publish-user          # publisher
    #     password: ref+vault://secret/data/registry/nexus#publish-pass          # s3cr3t-publ1sh

  # GCP × serviceAccount — EnvGene ✅ + QCL ✅
  gcp-sa:
    provider: gcp
    authMethod: serviceAccount
    gcpRegProject: my-project
    gcpRegion: europe-west1
    gcpScopes:                              # EXT3: optional, default https://www.googleapis.com/auth/cloud-platform
      - https://www.googleapis.com/auth/cloud-platform
    accessRoles:
      read: gcp-sa-read
      publish: gcp-sa-publish
    # REGISTRY_CREDENTIALS.data.<regName>:
    #   gcp-sa-read:
    #     secret: ref+vault://secret/data/registry/gcp-sa-read#json        # ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsIC4uLiB9Cg== (base64 SA-JSON)
    #   gcp-sa-publish:
    #     secret: ref+vault://secret/data/registry/gcp-sa-publish#json     # ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsIC4uLiB9Cg==

  # GCP × federation — EnvGene ❌ + QCL ✅
  gcp-fed:
    provider: gcp
    authMethod: federation
    gcpRegProject: my-project
    gcpRegPoolId: pool-1
    gcpRegProviderId: prov-1
    gcpRegion: europe-west1
    gcpScopes:                              # EXT3: optional, default https://www.googleapis.com/auth/cloud-platform
      - https://www.googleapis.com/auth/cloud-platform
    gcpOIDC:
      URL: https://sts.googleapis.com/v1/token
      customParams:
        - audience: "//iam.googleapis.com/projects/123456789/locations/global/workloadIdentityPools/pool-1/providers/prov-1"
        - subjectTokenType: "urn:ietf:params:oauth:token-type:jwt"
        - tokenFormatType: "urn:ietf:params:oauth:token-type:access_token"
        - scope: "https://www.googleapis.com/auth/cloud-platform"
    accessRoles:                                   # credId payload is a serviceAccount (non-secret, EXT2)
      read: gcp-fed-read
      publish: gcp-fed-publish
    # REGISTRY_CREDENTIALS.data.<regName>:
    #   gcp-fed-read:
    #     serviceAccount: eg-reg-read@my-project.iam.gserviceaccount.com      # literal (non-secret)
    #   gcp-fed-publish:
    #     serviceAccount: eg-reg-publish@my-project.iam.gserviceaccount.com

  # AWS × secret — EnvGene ✅ + QCL ✅
  aws-secret:
    provider: aws
    authMethod: secret
    awsService: codeArtifact                # EXT3: codeArtifact|ecr
    awsRegion: eu-west-1
    awsDomain: codeartifact.eu-west-1.amazonaws.com
    accessRoles:
      read: aws-key-read
      publish: aws-key-publish
    # REGISTRY_CREDENTIALS.data.<regName>:
    #   aws-key-read:
    #     accessKeyId: ref+vault://secret/data/registry/aws-read#accessKeyId            # AKIAIOSFODNN7EXAMPLE
    #     secretAccessKey: ref+vault://secret/data/registry/aws-read#secretAccessKey    # wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    #   aws-key-publish:
    #     accessKeyId: ref+vault://secret/data/registry/aws-publish#accessKeyId         # AKIAI44QH8DHBEXAMPLE
    #     secretAccessKey: ref+vault://secret/data/registry/aws-publish#secretAccessKey # je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY

  # AWS × assumeRole — EnvGene ❌ + QCL ✅
  aws-assume:
    provider: aws
    authMethod: assumeRole
    awsService: ecr                           # EXT3: codeArtifact|ecr
    awsRegion: eu-west-1
    awsRoleSessionPrefix: eg
    awsSourceCredentialsId: aws-bootstrap     # EXT3: set means a bootstrap key (source_profile), empty means IRSA
    accessRoles:                                   # credId payload is a roleArn (non-secret, EXT2)
      read: aws-role-read
      publish: aws-role-publish
    # REGISTRY_CREDENTIALS.data.<regName>:
    #   aws-role-read:
    #     roleArn: arn:aws:iam::123456789012:role/eg-reg-read          # literal (non-secret)
    #   aws-role-publish:
    #     roleArn: arn:aws:iam::123456789012:role/eg-reg-publish
    #   aws-bootstrap:                                                 # only when awsSourceCredentialsId is set
    #     accessKeyId: ref+vault://secret/data/registry/aws-bootstrap#accessKeyId           # AKIAIOSFODNN7EXAMPLE
    #     secretAccessKey: ref+vault://secret/data/registry/aws-bootstrap#secretAccessKey   # wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

  # Azure × oauth2 — EnvGene ❌ + QCL ✅
  acr:
    provider: azure
    authMethod: oauth2
    azureService: acr                                   # EXT3: acr|artifacts
    azureTenantId: <tenant>
    azureACRName: myregistry
    azureACRResource: https://myregistry.azurecr.io
    azureOAuth2Params:                                  # EXT3: optional, token-request params grant/scope
      grant_type: client_credentials
      scope: https://myregistry.azurecr.io/.default
    accessRoles:
      read: azure-sp-read
      publish: azure-sp-publish
    # REGISTRY_CREDENTIALS.data.<regName>:
    #   azure-sp-read:
    #     clientId: ref+vault://secret/data/registry/azure-sp-read#clientId            # 11111111-2222-3333-4444-555555555555
    #     clientSecret: ref+vault://secret/data/registry/azure-sp-read#clientSecret    # aBcD3fG~hIjKlMnOpQrStUvWxYz0123456789
    #   azure-sp-publish:
    #     clientId: ref+vault://secret/data/registry/azure-sp-publish#clientId         # 66666666-7777-8888-9999-000000000000
    #     clientSecret: ref+vault://secret/data/registry/azure-sp-publish#clientSecret # zYxW9vU~tSrQpOnMlKjIhGfEdCbA9876543210
```

## Artifact sections

```yaml
registries:
  - artifactType: maven                 # https
    authConfig: aws-secret
    repositories:
      - type: snapshot
        url: https://codeartifact.eu-west-1.amazonaws.com/maven/maven-snapshots
        repoName: maven-snapshots
      - type: staging
        url: https://codeartifact.eu-west-1.amazonaws.com/maven/maven-staging
        repoName: maven-staging
      - type: release
        url: https://codeartifact.eu-west-1.amazonaws.com/maven/maven-releases
        repoName: maven-releases
      - type: snapshotGroup
        url: https://codeartifact.eu-west-1.amazonaws.com/maven/maven-snapshot-group
      - type: releaseGroup
        url: https://codeartifact.eu-west-1.amazonaws.com/maven/maven-release-group

  - artifactType: docker                # oci
    authConfig: artifactory-up
    repositories:
      - type: snapshot
        url: artifactory.company.com:18080
        repoName: docker-snapshots
      - type: staging
        url: artifactory.company.com:18081
        repoName: docker-staging
      - type: release
        url: artifactory.company.com:18082
        repoName: docker-releases
      - type: group
        url: artifactory.company.com:18083

  - artifactType: helmLib               # https
    authConfig: nexus-up
    repositories:
      - type: staging
        url: https://nexus.company.internal/repository/helm-staging
        repoName: helm-staging
      - type: release
        url: https://nexus.company.internal/repository/helm-releases
        repoName: helm-releases

  - artifactType: helmApp               # https
    authConfig: nexus-up
    repositories:
      - type: staging
        url: https://nexus.company.internal/repository/helm-staging
        repoName: helm-staging
      - type: release
        url: https://nexus.company.internal/repository/helm-releases
        repoName: helm-releases
      - type: group
        url: https://nexus.company.internal/repository/helm-group
      - type: dev
        url: https://nexus.company.internal/repository/helm-dev
        repoName: helm-dev

  # EXT5: OCI helm as separate artifact types
  - artifactType: helmLibOCI            # oci
    authConfig: artifactory-up
    repositories:
      - type: staging
        url: artifactory.company.com:18090
        repoName: helm-oci-staging
      - type: release
        url: artifactory.company.com:18091
        repoName: helm-oci-releases

  - artifactType: helmAppOCI            # oci
    authConfig: artifactory-up
    repositories:
      - type: staging
        url: artifactory.company.com:18092
        repoName: helm-app-oci-staging
      - type: release
        url: artifactory.company.com:18093
        repoName: helm-app-oci-releases
      - type: group
        url: artifactory.company.com:18094
      - type: dev
        url: artifactory.company.com:18095
        repoName: helm-app-oci-dev

  - artifactType: go                    # https
    authConfig: nexus-up
    repositories:
      - type: snapshot
        url: https://nexus.company.internal/repository/go-snapshots
        repoName: go-snapshots
      - type: release
        url: https://nexus.company.internal/repository/go-releases
        repoName: go-releases
      - type: proxy
        url: https://goproxy.internal/go/

  - artifactType: npm                   # https
    authConfig: nexus-up
    repositories:
      - type: snapshot
        url: https://nexus.company.internal/repository/npm-snapshots
        repoName: npm-snapshots
      - type: release
        url: https://nexus.company.internal/repository/npm-releases
        repoName: npm-releases

  - artifactType: raw                   # https
    authConfig: nexus-up
    repositories:
      - type: snapshot
        url: https://nexus.company.internal/repository/raw-snapshots
        repoName: raw-snapshots
      - type: release
        url: https://nexus.company.internal/repository/raw-releases
        repoName: raw-releases
      - type: staging
        url: https://nexus.company.internal/repository/raw-staging
        repoName: raw-staging
      - type: proxy
        url: https://proxy.raw.local/raw
```

## Examples

Each example is a standalone RegDef file (its `REGISTRY_CREDENTIALS` variable is a trailing comment):

1. [Shared Platform Registry — artifactory + anonymous](regdef-v2-extensions/shared-platform-registry.yaml)
2. [Shared Platform Registry — artifactory + userPass + Vault cred store](regdef-v2-extensions/shared-platform-registry-vault.yaml)
3. [Onsite — nexus + userPass](regdef-v2-extensions/nexus-onsite.yaml)
4. [Onsite — gcp + nexus](regdef-v2-extensions/gcp-onsite.yaml)
5. [Onsite — aws ECR + CodeArtifact + secret](regdef-v2-extensions/aws-onsite.yaml)
