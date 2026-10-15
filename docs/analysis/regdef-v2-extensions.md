# RegDef v2 extensions

- [RegDef v2 extensions](#regdef-v2-extensions)
  - [Open questions](#open-questions)
  - [Extensions](#extensions)
    - [EXT1 — `scopes`](#ext1--scopes)
      - [Key: a subset of the r/w/d primitives](#key-a-subset-of-the-rwd-primitives)
    - [EXT2 — The `REGISTRY_CREDENTIALS` variable](#ext2--the-registry_credentials-variable)
    - [EXT3 — Extend `authConfig` to match what QCL already supports](#ext3--extend-authconfig-to-match-what-qcl-already-supports)
    - [EXT4 — Repositories by artifact type](#ext4--repositories-by-artifact-type)
    - [EXT5 — OCI helm in separate sections](#ext5--oci-helm-in-separate-sections)
    - [EXT6 — Repository: `url` + `repoName`](#ext6--repository-url--reponame)
  - [Model](#model)
  - [authConfig method catalog](#authconfig-method-catalog)
  - [Artifact sections](#artifact-sections)
  - [Examples](#examples)
    - [1. Offsite — artifactory + anonymous (no scopes) + multi-repo (snapshot, staging, release)](#1-offsite--artifactory--anonymous-no-scopes--multi-repo-snapshot-staging-release)
    - [2. Offsite — artifactory + secret store + scopes + multi-repo](#2-offsite--artifactory--secret-store--scopes--multi-repo)
    - [3. Onsite — nexus + secret store + scopes `rw` + single-repo](#3-onsite--nexus--secret-store--scopes-rw--single-repo)
    - [4. Onsite — gcp + creds in CI/CD + scopes + single-repo](#4-onsite--gcp--creds-in-cicd--scopes--single-repo)
    - [5. Onsite — aws + creds in CI/CD + scopes + single-repo](#5-onsite--aws--creds-in-cicd--scopes--single-repo)

## Open questions

1. RegDef storage: per site (cn, mb, sit, uat, prod, …)?

## Extensions

### EXT1 — `scopes`

`scopes` picks the identity for an operation. It is required, except for `anonymous` (no credential, so `scopes` is not needed).

Each key holds an object with exactly one field. The processor dispatches on the field name:

- `credId`: a secret; a local key into `REGISTRY_CREDENTIALS.data.<regName>`.
- `roleArn`: an inline AWS role ARN (assume_role; not a secret, no var).
- `serviceAccount`: an inline GCP service-account email (federation; not a secret, no var).

#### Key: a subset of the r/w/d primitives

`r` = read, `w` = write/create, `d` = delete; combinations `r | w | d | rw | rd | wd | rwd`.

```yaml
scopes:
  r:
    credId: reg-read         # secret -> var (pull only)
  w:
    credId: reg-push         # secret -> var (push only)
  rwd:
    credId: reg-admin        # secret -> var (read + write + delete)
```

```yaml
scopes:                      # assume_role
  r:
    roleArn: arn:aws:iam::123456789012:role/eg-reg-read
  w:
    roleArn: arn:aws:iam::123456789012:role/eg-reg-publish
  rwd:
    roleArn: arn:aws:iam::123456789012:role/eg-reg-admin
```

```yaml
scopes:                      # federation
  r:
    serviceAccount: eg-reg-read@my-project.iam.gserviceaccount.com
  w:
    serviceAccount: eg-reg-publish@my-project.iam.gserviceaccount.com
  rwd:
    serviceAccount: eg-reg-admin@my-project.iam.gserviceaccount.com
```

### EXT2 — The `REGISTRY_CREDENTIALS` variable

`credId` points to a secret in the consumer CI/CD variable `REGISTRY_CREDENTIALS`.

The RegDef stores only `credId`, never a value and never a vals reference.

The variable is required only when a `credId` is used. Without a secret (federation, anonymous, assume_role on IRSA) there is no var;
assume_role with `awsSourceCredentialsId` needs a var to hold the bootstrap secret.

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

# assume_role (roleArn) / federation (serviceAccount): inline under scope, NOT in REGISTRY_CREDENTIALS
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
```

### EXT3 — Extend `authConfig` to match what QCL already supports

- `awsService` (`codeartifact` | `ecr`): the AWS registry service, with different token flows (CodeArtifact for maven, ECR for docker).
- `azureService` (`acr` | `artifacts`): the Azure service (ACR for docker, Azure Artifacts for packages).
- `gcpScopes`: optional OAuth scopes (QCL `with_service_account_key` / `with_oidc_creds`), default `cloud-platform`.
- `azureOauth2Params`: optional token-request params, grant and scope (QCL `with_oauth2_custom_data`).
- `awsSourceCredentialsId`: optional base key for the STS call (AWS `source_profile`; QCL requires it).

### EXT4 — Repositories by artifact type

| type         | roles (repositories)                                    |
|--------------|---------------------------------------------------------|
| maven        | snapshot, staging, release, snapshotGroup, releaseGroup |
| docker       | snapshot, staging, release, group                       |
| go           | snapshot, release, proxy                                |
| npm          | snapshot, release                                       |
| raw          | snapshot, release, staging, proxy                       |
| helm         | staging, release                                        |
| helmApp      | staging, release, group, dev                            |
| helmOci ¹    | staging, release                                        |
| helmAppOci ¹ | staging, release, group, dev                            |

¹ roles mirror helm/helmApp.

### EXT5 — OCI helm in separate sections

OCI helm goes in separate sections, one per helm form: `helmOciConfig` + `helmAppOciConfig`. HTTP helm stays in `helmConfig` / `helmAppConfig`.

### EXT6 — Repository: `url` + `repoName`

- `url`: the full pull/push URL.
- `repoName`: the repo key, used by the control plane only. It is not part of pull or push, since `url` is self-sufficient. Set it explicitly, because you cannot derive it from a proxied or opaque `url` (for example, `url=cdn.company.com/charts` with repo key `helm-prod-virtual`).

Set `repoName` only on concrete repos that use authentication. For `anonymous`, group, and proxy, leave it out.

An OCI docker registry uses one of two notations:

- path, `host/repoName/image`:
  - `123456789.dkr.ecr.eu-west-1.amazonaws.com/docker-releases/myapp:1.0` (ECR)
  - `europe-docker.pkg.dev/my-project/docker-releases/myapp:1.0` (GCP-AR)
  - `artifactory.company.com/docker-releases/myapp:1.0` (Artifactory repo-path)
- authority, port or subdomain, `host:port/image` or `repoName.host/image`:
  - `artifactory.company.com:18082/myapp:1.0` (port; Nexus/Artifactory)
  - `docker-releases.artifactory.company.com/myapp:1.0` (subdomain; Artifactory)

In both, `url` is the full pull base, and `repoName` stays separate (control plane).

`authConfig.baseUrl` is the registry server's control-plane (REST) URL. It is not a pull base: pull uses the per-repo `url`, and you never append the repo to `baseUrl`. It applies to artifactory and nexus only. `anonymous` does not need it, because the control plane requires authentication.

**Option A (chosen) — `repositories`:**

```yaml
<type>Config:
  authConfig: <name>
  repositories:
    <repo>:
      url: https://nexus.company.internal/repository/maven-releases
      repoName: maven-releases
```

**Option B (alternative) — flat `*Uri` + `*RepoName`:**

```yaml
<type>Config:
  authConfig: <name>
  <repo>Uri: https://nexus.company.internal/repository/maven-releases
  <repo>RepoName: maven-releases
```

## Model

```yaml
# Mandatory
# Registry Definition object version (unchanged; these are v2 extensions)
version: "2.0"
# Mandatory
# Name of the registry — MUST be unique (REGISTRY_CREDENTIALS.data is namespaced by it, see EXT2)
name: string
# Optional
# Named authentication profiles; referenced by artifact sections via `authConfig: <name>`
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
    # (NOT `authMethod: anonymous`; cloud uses the provider endpoint fields below). NOT a pull base — pull uses per-repo `url` (see EXT6).
    baseUrl: string

    # --- Identity binding (scopes; EXT1) ---
    # scopes.<key> selects the IDENTITY for the operation. Mandatory, EXCEPT `authMethod: anonymous`.
    # Key = subset of primitives r/w/d (r=read, w=write/create, d=delete): r|w|d|rw|rd|wd|rwd.
    # Value = object with EXACTLY ONE field (oneOf); the processor dispatches on the field name:
    #   credId         -> local key into `REGISTRY_CREDENTIALS.data.<this def's name>` (secret; namespaced by regName, see EXT2)
    #   roleArn        -> inline AWS role ARN (assume_role; non-secret; no var)
    #   serviceAccount -> inline GCP SA email (federation; non-secret; no var)
    scopes:
      <r|w|d|rw|rd|wd|rwd>:
        credId: string            # OR: roleArn: string | serviceAccount: string

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
# `repositories` — map `role -> { url, repoName }` (EXT6, Option A). Roles per type — EXT4.
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

helmConfig:
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

helmOciConfig:
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

**Identity per `authMethod`** (the `scopes.<key>` value; EXT1):

| `authMethod`      | `scopes.<key>` field | Where the value lives / payload                                  |
|-------------------|----------------------|------------------------------------------------------------------|
| `anonymous`       | — (no `scopes`)      | —                                                                |
| `user_pass`       | `credId`             | var `data`: `username` + `password`                              |
| `secret`          | `credId`             | var `data`: `accessKeyId` + `secretAccessKey` (+ `sessionToken`) |
| `service_account` | `credId`             | var `data`: `secret` (SA JSON)                                   |
| `oauth2`          | `credId`             | var `data`: `clientId` + `clientSecret`                          |
| `federation`      | `serviceAccount`     | inline (not a secret; no var)                                    |
| `assume_role`     | `roleArn`            | inline (not a secret; no var) ¹                                  |

¹ `assume_role` + `awsSourceCredentialsId`: the STS bootstrap secret is a separate `credId` → var; `roleArn` stays inline.

**`scopes` keys — subset of r/w/d primitives (EXT1):**

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

## authConfig method catalog

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
      r:
        credId: artifactory-read
      w:
        credId: artifactory-publish
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
      r:
        credId: nexus-read
      w:
        credId: nexus-publish
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
      r:
        credId: gcp-sa-read
      w:
        credId: gcp-sa-publish
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
    scopes:                                   # serviceAccount inline (not a secret -> no var)
      r:
        serviceAccount: eg-reg-read@my-project.iam.gserviceaccount.com
      w:
        serviceAccount: eg-reg-publish@my-project.iam.gserviceaccount.com

  # AWS × secret — EnvGene ✅ + QCL ✅
  aws-secret:
    provider: aws
    authMethod: secret
    awsService: codeartifact                # EXT3: codeartifact|ecr
    awsRegion: eu-west-1
    awsDomain: codeartifact.eu-west-1.amazonaws.com
    scopes:
      r:
        credId: aws-key-read
      w:
        credId: aws-key-publish
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
    scopes:                                   # roleArn inline (not a secret -> no var)
      r:
        roleArn: arn:aws:iam::123456789012:role/eg-reg-read
      w:
        roleArn: arn:aws:iam::123456789012:role/eg-reg-publish
    # REGISTRY_CREDENTIALS.data.<regName>:          # only when awsSourceCredentialsId is set
    #   aws-bootstrap:
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
      r:
        credId: azure-sp-read
      w:
        credId: azure-sp-publish
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
mavenConfig:                        # http
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
      url: https://codeartifact.eu-west-1.amazonaws.com/maven/maven-snapshot-group   # read aggregate
    releaseGroup:
      url: https://codeartifact.eu-west-1.amazonaws.com/maven/maven-release-group    # read aggregate

dockerConfig:                       # oci (Artifactory: port per docker repo, group is native)
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
      url: artifactory.company.com:18083                                             # read aggregate

helmConfig:                         # http
  authConfig: nexus-up
  repositories:
    staging:
      url: https://nexus.company.internal/repository/helm-staging
      repoName: helm-staging
    release:
      url: https://nexus.company.internal/repository/helm-releases
      repoName: helm-releases

helmAppConfig:                      # http
  authConfig: nexus-up
  repositories:
    staging:
      url: https://nexus.company.internal/repository/helm-staging
      repoName: helm-staging
    release:
      url: https://nexus.company.internal/repository/helm-releases
      repoName: helm-releases
    group:
      url: https://nexus.company.internal/repository/helm-group                    # read aggregate
    dev:
      url: https://nexus.company.internal/repository/helm-dev
      repoName: helm-dev

# EXT5: OCI helm in separate sections
helmOciConfig:                      # oci path-style (repo in the url path)
  authConfig: aws-assume
  repositories:
    staging:
      url: 123456789.dkr.ecr.eu-west-1.amazonaws.com/helm-staging
      repoName: helm-staging
    release:
      url: 123456789.dkr.ecr.eu-west-1.amazonaws.com/helm-releases
      repoName: helm-releases

# EXT5: OCI helm in separate sections
helmAppOciConfig:                   # oci path-style (ECR: no group — cloud has no virtual repos)
  authConfig: aws-assume
  repositories:
    staging:
      url: 123456789.dkr.ecr.eu-west-1.amazonaws.com/helm-staging
      repoName: helm-staging
    release:
      url: 123456789.dkr.ecr.eu-west-1.amazonaws.com/helm-releases
      repoName: helm-releases
    dev:
      url: 123456789.dkr.ecr.eu-west-1.amazonaws.com/helm-dev
      repoName: helm-dev

goConfig:                           # http
  authConfig: nexus-up
  repositories:
    snapshot:
      url: https://nexus.company.internal/repository/go-snapshots
      repoName: go-snapshots
    release:
      url: https://nexus.company.internal/repository/go-releases
      repoName: go-releases
    proxy:
      url: https://goproxy.internal/go/                                              # read-through

npmConfig:                          # http
  authConfig: nexus-up
  repositories:
    snapshot:
      url: https://nexus.company.internal/repository/npm-snapshots
      repoName: npm-snapshots
    release:
      url: https://nexus.company.internal/repository/npm-releases
      repoName: npm-releases

rawConfig:                          # http
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
      url: https://proxy.raw.local/raw                                               # read-through
```

## Examples

### 1. Offsite — artifactory + anonymous (no scopes) + multi-repo (snapshot, staging, release)

```yaml
name: reg-public
authConfig:
  anon:
    provider: artifactory
    authMethod: anonymous
mavenConfig:
  authConfig: anon
  repositories:
    snapshot:
      url: https://artifactory.offsite.example.com/nc.dmp.mvn.snapshots
    staging:
      url: https://artifactory.offsite.example.com/nc.dmp.mvn.staging
    release:
      url: https://artifactory.offsite.example.com/nc.dmp.mvn
dockerConfig:
  authConfig: anon
  repositories:
    snapshot:
      url: artifactory.offsite.example.com:17107
    staging:
      url: artifactory.offsite.example.com:17099
    release:
      url: artifactory.offsite.example.com:17097
helmAppConfig:
  authConfig: anon
  repositories:
    staging:
      url: https://artifactory.offsite.example.com/nc.helm.charts.staging
    release:
      url: https://artifactory.offsite.example.com/nc.helm.charts.release
```

Consumer CI/CD vars: none

### 2. Offsite — artifactory + secret store + scopes + multi-repo

```yaml
name: reg-offsite
authConfig:
  offsite-store:
    provider: artifactory
    authMethod: user_pass
    baseUrl: https://artifactory.offsite.example.com
    scopes:
      r:
        credId: offsite-read
      w:
        credId: offsite-publish
mavenConfig:
  authConfig: offsite-store
  repositories:
    snapshot:
      url: https://artifactory.offsite.example.com/nc.dmp.mvn.snapshots
      repoName: nc.dmp.mvn.snapshots
    staging:
      url: https://artifactory.offsite.example.com/nc.dmp.mvn.staging
      repoName: nc.dmp.mvn.staging
    release:
      url: https://artifactory.offsite.example.com/nc.dmp.mvn
      repoName: nc.dmp.mvn
dockerConfig:
  authConfig: offsite-store
  repositories:
    snapshot:
      url: artifactory.offsite.example.com:17107
      repoName: docker-snapshots
    release:
      url: artifactory.offsite.example.com:17097
      repoName: docker-releases
```

Consumer CI/CD vars: `REGISTRY_CREDENTIALS` (+ `VAULT_ADDR` + `VAULT_TOKEN` to resolve vals):

```yaml
kind: RegistryCredentials
version: v1
data:
  reg-offsite:                # = RegDef.name
    offsite-read:
      username: ref+vault://secret/data/offsite/artifactory#read-user
      password: ref+vault://secret/data/offsite/artifactory#read-pass
    offsite-publish:
      username: ref+vault://secret/data/offsite/artifactory#publish-user
      password: ref+vault://secret/data/offsite/artifactory#publish-pass
```

### 3. Onsite — nexus + secret store + scopes `rw` + single-repo

```yaml
name: reg-onsite
authConfig:
  onsite:
    provider: nexus
    authMethod: user_pass
    baseUrl: https://nexus.customer.internal
    scopes:
      rw:
        credId: onsite-rw
mavenConfig:
  authConfig: onsite
  repositories:
    release:
      url: https://nexus.customer.internal/repository/maven-releases
      repoName: maven-releases
dockerConfig:
  authConfig: onsite
  repositories:
    release:
      url: docker.customer.internal
      repoName: releases
helmAppConfig:
  authConfig: onsite
  repositories:
    release:
      url: https://nexus.customer.internal/repository/helm-releases
      repoName: helm-releases
```

Consumer CI/CD vars: `REGISTRY_CREDENTIALS` (+ `VAULT_ADDR` + `VAULT_TOKEN`):

```yaml
kind: RegistryCredentials
version: v1
data:
  reg-onsite:                 # = RegDef.name
    onsite-rw:
      username: ref+vault://secret/data/registry/onsite#username
      password: ref+vault://secret/data/registry/onsite#password
```

### 4. Onsite — gcp + creds in CI/CD + scopes + single-repo

```yaml
name: reg-gcp
authConfig:
  onsite-gcp:
    provider: gcp
    authMethod: service_account
    gcpRegProject: customer-proj
    gcpRegion: europe-west1
    scopes:
      r:
        credId: gcp-sa-read
      w:
        credId: gcp-sa-publish
mavenConfig:
  authConfig: onsite-gcp
  repositories:
    release:
      url: https://europe-west1-maven.pkg.dev/customer-proj/maven-release
      repoName: maven-release
dockerConfig:
  authConfig: onsite-gcp
  repositories:
    release:
      url: europe-west1-docker.pkg.dev/customer-proj/docker-release
      repoName: docker-release
```

Consumer CI/CD vars: `REGISTRY_CREDENTIALS`:

```yaml
kind: RegistryCredentials
version: v1
data:
  reg-gcp:                    # = RegDef.name
    gcp-sa-read:
      secret: "<SA-JSON read>"
    gcp-sa-publish:
      secret: "<SA-JSON publish>"
```

### 5. Onsite — aws + creds in CI/CD + scopes + single-repo

```yaml
name: reg-aws
authConfig:
  onsite-aws-ca:
    provider: aws
    authMethod: secret
    awsService: codeartifact
    awsRegion: eu-west-1
    awsDomain: 123456789.d.codeartifact.eu-west-1.amazonaws.com
    scopes:
      r:
        credId: aws-read
      w:
        credId: aws-publish
  onsite-aws-ecr:
    provider: aws
    authMethod: secret
    awsService: ecr
    awsRegion: eu-west-1
    scopes:
      r:
        credId: aws-read
      w:
        credId: aws-publish
mavenConfig:
  authConfig: onsite-aws-ca
  repositories:
    release:
      url: https://123456789.d.codeartifact.eu-west-1.amazonaws.com/maven/app-release
      repoName: app-release
dockerConfig:
  authConfig: onsite-aws-ecr
  repositories:
    release:
      url: 123456789.dkr.ecr.eu-west-1.amazonaws.com/app
      repoName: app
```

Consumer CI/CD vars: `REGISTRY_CREDENTIALS`:

```yaml
kind: RegistryCredentials
version: v1
data:
  reg-aws:                    # = RegDef.name
    aws-read:
      accessKeyId: AKIAIOSFODNN7EXAMPLE
      secretAccessKey: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
    aws-publish:
      accessKeyId: AKIAI44QH8DHBEXAMPLE
      secretAccessKey: je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY
```
