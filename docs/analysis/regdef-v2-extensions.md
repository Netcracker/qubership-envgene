# RegDef v2 extensions

- [RegDef v2 extensions](#regdef-v2-extensions)
  - [Open questions](#open-questions)
  - [Limitations](#limitations)
  - [Extensions](#extensions)
    - [EXT1 — `scopes`](#ext1--scopes)
      - [Key: a subset of the r/w/d primitives](#key-a-subset-of-the-rwd-primitives)
    - [EXT2 — The `REGISTRY_CREDENTIALS` variable](#ext2--the-registry_credentials-variable)
    - [EXT3 — Extend `authConfig` to match what QCL already supports](#ext3--extend-authconfig-to-match-what-qcl-already-supports)
    - [EXT4 — Repositories by artifact type](#ext4--repositories-by-artifact-type)
    - [EXT5 — OCI helm in separate sections](#ext5--oci-helm-in-separate-sections)
    - [EXT6 — Repository: `url` + `repoName`](#ext6--repository-url--reponame)
  - [Model](#model)
  - [`authConfig` method catalog](#authconfig-method-catalog)
  - [Artifact sections](#artifact-sections)
  - [Examples](#examples)

## Open questions

1. Which set of repository roles (snapshot, staging, release, snapshotGroup, releaseGroup, ...) is needed?
   One unified set across all artifact types?
   Which roles are mandatory and which optional?
   Or use separate Registry Definitions?
   "Red zone" case
2. Should `helmLibConfig` and `helmAppConfig` be unified?
3. Should `mavenConfig` be split into two types — one for the DD, one for maven libraries?
4. Extend `provider` with `gitlab`
5. Make artifact type flexible:

    ```yaml
    <registry-name>:
      artifactType: enum [ maven, docker, helm_lib_http, helm_app_http, helm_lib_oci, helm_app_oci ]
      authConfig: string
      repositories: list
    ```

6. Rename `scopes` to `securityScopes`, `accessRoles` or something else
7. Extend artifact types with apm

## Limitations

1. `authConfig` binds at the artifact-section level, not per repository. All repositories in a section share one `authConfig`.
   No way to point `snapshot` and `release` within the same section at registries with different authentication.

## Extensions

### EXT1 — `scopes`

`scopes` maps an operation to a `credId` — the identity that performs it. It is required, except for `anonymous` (no credential, so `scopes`
is not needed).

Each key maps to a `credId` - a key into `REGISTRY_CREDENTIALS.data.<regName>` (EXT2).

#### Key: a subset of the r/w/d primitives

`r` = read, `w` = write/create, `d` = delete; combinations `r | w | d | rw | rd | wd | rwd`.

```yaml
scopes:
  r: reg-read          # pull only
  rw: reg-push         # read + write
  rwd: reg-admin       # read + write + delete
```

### EXT2 — The `REGISTRY_CREDENTIALS` variable

`credId` points to a payload in the consumer CI/CD variable `REGISTRY_CREDENTIALS`.

The variable is required whenever `scopes` is used: for every `authMethod` except `anonymous`.

The payload is a secret (user/password, keys, SA JSON, client secret), or a non-secret identifier (`roleArn` for assume_role, `serviceAccount`
for federation). `assume_role` with `awsSourceCredentialsId` adds a separate `credId` for the bootstrap secret.

`data` is namespaced by `regName`: `data.<regName>.<credId>`. Inside a payload, each field is either a literal or a vals reference.

```yaml
kind: RegistryCredentials
version: v1
data:
  <regName>:
    <credId>: <payload>
```

Payload shapes by authMethod:

```yaml
# nexus / artifactory × user_pass
nexus-read:
  username: string          # literal | ref+vault://…
  password: string          # literal | ref+vault://…

# gcp × service_account
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

# aws × assume_role
aws-role-read:
  roleArn: string           # non-secret identifier; literal (vals allowed but pointless)

# gcp × federation
gcp-fed-read:
  serviceAccount: string    # non-secret identifier; literal (vals allowed but pointless)

# anonymous: no credential
```

Two complete examples with every payload type: one all vals references, one all literal values.

```yaml
# REGISTRY_CREDENTIALS — all vals references
kind: RegistryCredentials
version: v1
data:
  my-registry:                # RegDef.name
    nexus-cred:               # user_pass
      username: ref+vault://secret/data/registry/nexus#username
      password: ref+vault://secret/data/registry/nexus#password
    aws-cred:                 # aws secret
      accessKeyId:     ref+vault://secret/data/registry/aws#accessKeyId
      secretAccessKey: ref+vault://secret/data/registry/aws#secretAccessKey
      sessionToken:    ref+vault://secret/data/registry/aws#sessionToken
    gcp-cred:                 # gcp service_account
      secret: ref+vault://secret/data/registry/gcp#json
    azure-cred:               # azure oauth2
      clientId:     ref+vault://secret/data/registry/azure#clientId
      clientSecret: ref+vault://secret/data/registry/azure#clientSecret
    aws-role-cred:            # aws assume_role (non-secret roleArn)
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
    nexus-cred:               # user_pass
      username: reader
      password: s3cr3t
    aws-cred:                 # aws secret
      accessKeyId:     AKIAIOSFODNN7EXAMPLE
      secretAccessKey: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
      sessionToken:    FwoGZXIvYXdzEBYaEXAMPLE
    gcp-cred:                 # gcp service_account
      secret: ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsIC4uLiB9Cg==
    azure-cred:               # azure oauth2
      clientId:     11111111-2222-3333-4444-555555555555
      clientSecret: aBcD3fG~hIjKlMnOpQrStUvWxYz0123456789
    aws-role-cred:            # aws assume_role (non-secret roleArn)
      roleArn: arn:aws:iam::123456789012:role/eg-reg-admin
    gcp-fed-cred:             # gcp federation (non-secret serviceAccount)
      serviceAccount: eg-reg@my-project.iam.gserviceaccount.com
```

### EXT3 — Extend `authConfig` to match what QCL already supports

- `awsService` (`codeartifact` | `ecr`): the AWS registry service, with different token flows (CodeArtifact for maven/npm; ECR for Docker and OCI artifacts, e.g. helm OCI).
- `azureService` (`acr` | `artifacts`): the Azure service (ACR for Docker and OCI artifacts; Azure Artifacts for packages).
- `gcpScopes`: optional OAuth scopes (QCL `with_service_account_key` / `with_oidc_creds`), default `cloud-platform`.
- `azureOauth2Params`: optional token-request params, grant and scope (QCL `with_oauth2_custom_data`).
- `awsSourceCredentialsId`: optional STS bootstrap key (AWS `source_profile`); empty = IRSA / workload identity.

### EXT4 — Repositories by artifact type

| type           | roles (repositories)                                    |
|----------------|---------------------------------------------------------|
| `maven`        | snapshot, staging, release, snapshotGroup, releaseGroup |
| `docker`       | snapshot, staging, release, group                       |
| `go`           | snapshot, release, proxy                                |
| `npm`          | snapshot, release                                       |
| `raw`          | snapshot, release, staging, proxy                       |
| `helmLib`      | staging, release                                        |
| `helmApp`      | staging, release, group, dev                            |
| `helmLibOci` ¹ | staging, release                                        |
| `helmAppOci` ¹ | staging, release, group, dev                            |

¹ roles mirror helmLib/helmApp.

### EXT5 — OCI helm in separate sections

OCI helm goes in separate sections, one per helm form: `helmLibOciConfig` + `helmAppOciConfig`. HTTP helm stays in `helmLibConfig` / `helmAppConfig`.

### EXT6 — Repository: `url` + `repoName`

- `url`: the full pull/push URL.
- `repoName`: the repository key, used by the control plane only. It is not part of pull or push, since `url` is self-sufficient.
  Set it explicitly, because you cannot derive it from a proxied or opaque `url` (for example, `url=cdn.company.com/charts` with repository key
  `helm-prod-virtual`).

Set `repoName` only on concrete repositories that use authentication. For `anonymous`, group, and proxy, leave it out.

An OCI Docker registry uses one of two notations:

- path, `host/repoName/image`:
  - `123456789.dkr.ecr.eu-west-1.amazonaws.com/docker-releases/myapp:1.0` (ECR)
  - `europe-docker.pkg.dev/my-project/docker-releases/myapp:1.0` (GCP-AR)
  - `artifactory.company.com/docker-releases/myapp:1.0` (Artifactory repo-path)
- authority, port or subdomain, `host:port/image` or `repoName.host/image`:
  - `artifactory.company.com:18082/myapp:1.0` (port; Nexus/Artifactory)
  - `docker-releases.artifactory.company.com/myapp:1.0` (subdomain; Artifactory)

In both, `url` is the full pull base, and `repoName` stays separate (control plane).

`authConfig.baseUrl` is the registry server's control-plane (REST) URL. It is not a pull base: pull uses the per-repo `url`, and you never
append the repository to `baseUrl`. It applies to artifactory and nexus only. `anonymous` does not need it, because the control plane requires
authentication.

```yaml
<type>Config:
  authConfig: <name>
  repositories:
    <repo>:
      url: https://nexus.company.internal/repository/maven-releases
      repoName: maven-releases
```

## Model

```yaml
# Mandatory
# Object kind
kind: RegistryDefinition
# Mandatory
# Registry Definition object version
version: v2
# Mandatory
# Name of the registry — site unique
name: string
# Mandatory
# Named registry profiles. Referenced by artifact sections via `authConfig: <name>`.
authConfig:
  <auth-config-name>:
    # Mandatory
    # Registry provider
    provider: enum [ artifactory, nexus, gcp, aws, azure ]
    # Mandatory
    # Authentication method; valid values depend on `provider` (see table below)
    authMethod: enum [ anonymous, user_pass, secret, service_account, oauth2, federation, assume_role ]
    # Optional
    # Registry server root (control-plane/REST: AQL / promote / manage) — `provider: artifactory` | `nexus` with auth
    # (NOT `authMethod: anonymous`; cloud uses the provider endpoint fields below). NOT a pull base — pull uses per-repo `url`.
    baseUrl: string

    # --- Identity binding ---
    # scopes.<key> maps the operation to a credId. Mandatory for all `authMethod` except `authMethod: anonymous`.
    # Key = subset of primitives r/w/d (r=read, w=write/create, d=delete): r|w|d|rw|rd|wd|rwd.
    # Value = credId: a local key into `REGISTRY_CREDENTIALS.data.<this def's name>`.
    #   The payload under the credId follows authMethod: a secret (user_pass/secret/service_account/oauth2),
    #   or a non-secret identifier (roleArn/serviceAccount).
    scopes:
      <r|w|d|rw|rd|wd|rwd>: string     # credId

    # --- Provider-specific fields ---
    # Optional
    # AWS registry service (selects token flow)
    # Used with `provider: aws` only
    awsService: enum [ codeartifact, ecr ]
    # Optional
    # Used with `provider: aws` only
    awsRegion: string
    # Optional
    # Used with `provider: aws` only; required for CodeArtifact
    awsDomain: string
    # Optional
    # Session-name prefix for AssumeRole
    # Used with `provider: aws` AND `authMethod: assume_role` only
    awsRoleSessionPrefix: string
    # Optional
    # Bootstrap credential for STS (AWS source_profile); empty -> IRSA / workload identity
    # Used with `provider: aws` AND `authMethod: assume_role` only
    awsSourceCredentialsId: string
    # Optional
    # OIDC interaction
    # Used with `provider: gcp` AND `authMethod: federation` only
    gcpOIDC:
      # Mandatory
      # URL of external OIDC server
      URL: string
      # Optional
      # Custom parameters for the OIDC server
      customParams:
        - <key>: <value>
    # Optional
    # Used with `provider: gcp` AND `authMethod: federation` only
    gcpRegProject: string
    # Optional
    # Used with `provider: gcp` AND `authMethod: federation` only
    gcpRegPoolId: string
    # Optional
    # Used with `provider: gcp` AND `authMethod: federation` only
    gcpRegProviderId: string
    # Optional
    # OAuth scopes; default https://www.googleapis.com/auth/cloud-platform
    # Used with `provider: gcp` only
    gcpScopes:
      - string
    # Optional
    # Used with `provider: gcp` only
    gcpRegion: string
    # Optional
    # Azure registry service
    # Used with `provider: azure` only
    azureService: enum [ acr, artifacts ]
    # Optional
    # Used with `provider: azure` only
    azureTenantId: string
    # Optional
    # Used with `provider: azure` only; required for ACR
    azureACRName: string
    # Optional
    # Target resource for ACR
    # Used with `provider: azure` only
    azureACRResource: string
    # Optional
    # Token-request params (grant / scope)
    # Used with `provider: azure` AND `authMethod: oauth2` only
    azureOauth2Params:
      <key>: <value>

# Each artifact section is Optional, present only for types the app uses.
# `repositories` — map `role -> { url, repoName }`.
# Repository shape:
#   <repo>:
#     url: string        # full pull/push base (http URL | oci host/host:port/repo.host) — carries addressing style
#     repoName: string   # repo-key for control-plane only (AQL/promote/manage); NOT for pull/push; omit for anonymous and group/proxy

mavenConfig:
  authConfig: string
  repositories:
    snapshot: <repo>
    staging: <repo>
    release: <repo>
    snapshotGroup: <repo>     # read aggregate — url only
    releaseGroup: <repo>      # read aggregate — url only

dockerConfig:
  authConfig: string
  repositories:
    snapshot: <repo>
    staging: <repo>
    release: <repo>
    group: <repo>             # read aggregate — url only

helmLibConfig:
  authConfig: string
  repositories:
    staging: <repo>
    release: <repo>

helmAppConfig:
  authConfig: string
  repositories:
    staging: <repo>
    release: <repo>
    group: <repo>             # read aggregate — url only
    dev: <repo>

helmLibOciConfig:
  authConfig: string
  repositories:
    staging: <repo>
    release: <repo>

helmAppOciConfig:
  authConfig: string
  repositories:
    staging: <repo>
    release: <repo>
    group: <repo>             # read aggregate — url only
    dev: <repo>

goConfig:
  authConfig: string
  repositories:
    snapshot: <repo>
    release: <repo>
    proxy: <repo>             # read-through — url only

npmConfig:
  authConfig: string
  repositories:
    snapshot: <repo>
    release: <repo>

rawConfig:
  authConfig: string
  repositories:
    snapshot: <repo>
    release: <repo>
    staging: <repo>
    proxy: <repo>             # read-through — url only
```

**Valid `authMethod` values per `provider`:**

| Provider      | Valid `authMethod` values                    |
|---------------|----------------------------------------------|
| `artifactory` | `anonymous`, `user_pass`                     |
| `nexus`       | `anonymous`, `user_pass`                     |
| `gcp`         | `anonymous`, `service_account`, `federation` |
| `aws`         | `anonymous`, `secret`, `assume_role`         |
| `azure`       | `anonymous`, `oauth2`                        |

**Identity per `authMethod`**. The `scopes.<key>` value is a `credId`; the payload it points to in the variable depends on `authMethod`:

| `authMethod`      | `credId` payload (in `REGISTRY_CREDENTIALS.data`)        |
|-------------------|----------------------------------------------------------|
| `anonymous`       | —                                                        |
| `user_pass`       | `username` + `password`                                  |
| `secret`          | `accessKeyId` + `secretAccessKey` (+ `sessionToken`)     |
| `service_account` | `secret` (SA JSON)                                       |
| `oauth2`          | `clientId` + `clientSecret`                              |
| `federation`      | `serviceAccount` (non-secret)                            |
| `assume_role`     | `roleArn` (non-secret) ¹                                 |

¹ `assume_role` + `awsSourceCredentialsId`: the STS bootstrap secret is a separate `credId` (payload `accessKeyId` + `secretAccessKey`).

**`scopes` keys — subset of r/w/d primitives:**

| Key   | Rights                 |
|-------|------------------------|
| `r`   | read                   |
| `w`   | write / create         |
| `d`   | delete                 |
| `rw`  | read + write           |
| `rd`  | read + delete          |
| `wd`  | write + delete         |
| `rwd` | read + write + delete  |

Empty = no access. For `anonymous`, `scopes` is not needed (no credential).

## `authConfig` method catalog

All valid provider × authMethod pairs.

```yaml
authConfig:

  # anonymous — EnvGene ✅ + QCL —
  public:
    provider: nexus
    authMethod: anonymous

  # Artifactory × user_pass — EnvGene ✅ + QCL —
  artifactory-up:
    provider: artifactory
    authMethod: user_pass
    baseUrl: https://artifactory.company.com/artifactory
    scopes:
      r: artifactory-read
      rw: artifactory-publish
    # REGISTRY_CREDENTIALS.data.<regName>:
    #   artifactory-read:
    #     username: ref+vault://secret/data/registry/artifactory#read-user       # reader
    #     password: ref+vault://secret/data/registry/artifactory#read-pass       # s3cr3t-r34d
    #   artifactory-publish:
    #     username: ref+vault://secret/data/registry/artifactory#publish-user    # publisher
    #     password: ref+vault://secret/data/registry/artifactory#publish-pass    # s3cr3t-publ1sh

  # Nexus × user_pass — EnvGene ✅ + QCL —
  nexus-up:
    provider: nexus
    authMethod: user_pass
    baseUrl: https://nexus.company.internal
    scopes:
      r: nexus-read
      rw: nexus-publish
    # REGISTRY_CREDENTIALS.data.<regName>:
    #   nexus-read:
    #     username: ref+vault://secret/data/registry/nexus#read-user             # reader
    #     password: ref+vault://secret/data/registry/nexus#read-pass             # s3cr3t-r34d
    #   nexus-publish:
    #     username: ref+vault://secret/data/registry/nexus#publish-user          # publisher
    #     password: ref+vault://secret/data/registry/nexus#publish-pass          # s3cr3t-publ1sh

  # GCP × service_account — EnvGene ✅ + QCL ✅
  gcp-sa:
    provider: gcp
    authMethod: service_account
    gcpRegProject: my-project
    gcpRegion: europe-west1
    gcpScopes:                              # EXT3: optional, default https://www.googleapis.com/auth/cloud-platform
      - https://www.googleapis.com/auth/cloud-platform
    scopes:
      r: gcp-sa-read
      rw: gcp-sa-publish
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
    scopes:                                   # credId payload is a serviceAccount (non-secret; EXT2)
      r: gcp-fed-read
      rw: gcp-fed-publish
    # REGISTRY_CREDENTIALS.data.<regName>:
    #   gcp-fed-read:
    #     serviceAccount: eg-reg-read@my-project.iam.gserviceaccount.com      # literal (non-secret)
    #   gcp-fed-publish:
    #     serviceAccount: eg-reg-publish@my-project.iam.gserviceaccount.com

  # AWS × secret — EnvGene ✅ + QCL ✅
  aws-secret:
    provider: aws
    authMethod: secret
    awsService: codeartifact                # EXT3: codeartifact|ecr
    awsRegion: eu-west-1
    awsDomain: codeartifact.eu-west-1.amazonaws.com
    scopes:
      r: aws-key-read
      rw: aws-key-publish
    # REGISTRY_CREDENTIALS.data.<regName>:
    #   aws-key-read:
    #     accessKeyId: ref+vault://secret/data/registry/aws-read#accessKeyId            # AKIAIOSFODNN7EXAMPLE
    #     secretAccessKey: ref+vault://secret/data/registry/aws-read#secretAccessKey    # wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    #   aws-key-publish:
    #     accessKeyId: ref+vault://secret/data/registry/aws-publish#accessKeyId         # AKIAI44QH8DHBEXAMPLE
    #     secretAccessKey: ref+vault://secret/data/registry/aws-publish#secretAccessKey # je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY

  # AWS × assume_role — EnvGene ❌ + QCL ✅
  aws-assume:
    provider: aws
    authMethod: assume_role
    awsService: ecr                           # EXT3: codeartifact|ecr
    awsRegion: eu-west-1
    awsRoleSessionPrefix: eg
    awsSourceCredentialsId: aws-bootstrap     # EXT3: set -> bootstrap key (source_profile); empty -> IRSA
    scopes:                                   # credId payload is a roleArn (non-secret; EXT2)
      r: aws-role-read
      rw: aws-role-publish
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
    azureOauth2Params:                                  # EXT3: optional, token-request params grant/scope
      grant_type: client_credentials
      scope: https://myregistry.azurecr.io/.default
    scopes:
      r: azure-sp-read
      rw: azure-sp-publish
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
mavenConfig:                          # https
  authConfig: aws-secret
  repositories:
    snapshot:
      url: https://codeartifact.eu-west-1.amazonaws.com/maven/maven-snapshots
      repoName: maven-snapshots
    staging:
      url: https://codeartifact.eu-west-1.amazonaws.com/maven/maven-staging
      repoName: maven-staging
    release:
      url: https://codeartifact.eu-west-1.amazonaws.com/maven/maven-releases
      repoName: maven-releases
    snapshotGroup:
      url: https://codeartifact.eu-west-1.amazonaws.com/maven/maven-snapshot-group
    releaseGroup:
      url: https://codeartifact.eu-west-1.amazonaws.com/maven/maven-release-group

dockerConfig:                         # oci
  authConfig: artifactory-up
  repositories:
    snapshot:
      url: artifactory.company.com:18080
      repoName: docker-snapshots
    staging:
      url: artifactory.company.com:18081
      repoName: docker-staging
    release:
      url: artifactory.company.com:18082
      repoName: docker-releases
    group:
      url: artifactory.company.com:18083

helmLibConfig:                         # https
  authConfig: nexus-up
  repositories:
    staging:
      url: https://nexus.company.internal/repository/helm-staging
      repoName: helm-staging
    release:
      url: https://nexus.company.internal/repository/helm-releases
      repoName: helm-releases

helmAppConfig:                         # https
  authConfig: nexus-up
  repositories:
    staging:
      url: https://nexus.company.internal/repository/helm-staging
      repoName: helm-staging
    release:
      url: https://nexus.company.internal/repository/helm-releases
      repoName: helm-releases
    group:
      url: https://nexus.company.internal/repository/helm-group
    dev:
      url: https://nexus.company.internal/repository/helm-dev
      repoName: helm-dev

# EXT5: OCI helm in separate sections
helmLibOciConfig:                      # oci
  authConfig: artifactory-up
  repositories:
    staging:
      url: artifactory.company.com:18090
      repoName: helm-oci-staging
    release:
      url: artifactory.company.com:18091
      repoName: helm-oci-releases

# EXT5: OCI helm in separate sections
helmAppOciConfig:                      # oci
  authConfig: artifactory-up
  repositories:
    staging:
      url: artifactory.company.com:18092
      repoName: helm-app-oci-staging
    release:
      url: artifactory.company.com:18093
      repoName: helm-app-oci-releases
    group:
      url: artifactory.company.com:18094
    dev:
      url: artifactory.company.com:18095
      repoName: helm-app-oci-dev

goConfig:                           # https
  authConfig: nexus-up
  repositories:
    snapshot:
      url: https://nexus.company.internal/repository/go-snapshots
      repoName: go-snapshots
    release:
      url: https://nexus.company.internal/repository/go-releases
      repoName: go-releases
    proxy:
      url: https://goproxy.internal/go/

npmConfig:                          # https
  authConfig: nexus-up
  repositories:
    snapshot:
      url: https://nexus.company.internal/repository/npm-snapshots
      repoName: npm-snapshots
    release:
      url: https://nexus.company.internal/repository/npm-releases
      repoName: npm-releases

rawConfig:                          # https
  authConfig: nexus-up
  repositories:
    snapshot:
      url: https://nexus.company.internal/repository/raw-snapshots
      repoName: raw-snapshots
    release:
      url: https://nexus.company.internal/repository/raw-releases
      repoName: raw-releases
    staging:
      url: https://nexus.company.internal/repository/raw-staging
      repoName: raw-staging
    proxy:
      url: https://proxy.raw.local/raw
```

## Examples

Each example is a standalone RegDef file (its `REGISTRY_CREDENTIALS` variable is a trailing comment):

1. [Shared Platform Registry — artifactory + anonymous](regdef-v2-extensions/shared-platform-registry.yaml)
2. [Shared Platform Registry — artifactory + user_pass + Vault cred store](regdef-v2-extensions/shared-platform-registry-vault.yaml)
3. [Onsite — nexus + user_pass](regdef-v2-extensions/nexus-onsite.yaml)
4. [Onsite — gcp + nexus](regdef-v2-extensions/gcp-onsite.yaml)
5. [Onsite — aws ECR + CodeArtifact + secret](regdef-v2-extensions/aws-onsite.yaml)
