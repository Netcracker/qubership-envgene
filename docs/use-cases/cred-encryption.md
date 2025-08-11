
# Credential Encryption Use Cases

- [Credential Encryption Use Cases](#credential-encryption-use-cases)
  - [Description](#description)
    - [UC-1. Enabling SOPS Encryption in Repository](#uc-1-enabling-sops-encryption-in-repository)
    - [UC-2. Adding a New Sensitive Parameter with SOPS in Shade Credential Mode](#uc-2-adding-a-new-sensitive-parameter-with-sops-in-shade-credential-mode)
    - [UC-3. Modifying the value of a sensitive parameter](#uc-3-modifying-the-value-of-a-sensitive-parameter)
    - [UC-4. Migrating from Fernet to SOPS](#uc-4-migrating-from-fernet-to-sops)

## Description

The use cases described below pertain to the [Credential Encryption](/docs/features/cred-encryption.md) functionality.

### UC-1. Enabling SOPS Encryption in Repository

**Description:** Describes enabling credential encryption using the SOPS backend in an EnvGene repository. Encryption should be enabled in sync with other systems integrated with EnvGene, such as consumers of the effective set.

**Prerequisites:**

- Local Local pre-commit is installed

**Process:**

1. The EnvGene Admin generates an age key pair
2. The EnvGene Admin provides the public key from the pair to the e2e Admin
3. The e2e Admin creates a combined public key by aggregating the public keys of all systems involved in managing sensitive parameters (i.e., systems that encrypt and decrypt)
4. The e2e Admin provides the combined public key (PUBLIC_AGE_KEYS) to the EnvGene Admin
5. The EnvGene Admin sets the repository variables:
   1. [PUBLIC_AGE_KEYS](/docs/instance-pipeline-parameters.md#public_age_keys)
   2. [ENVGENE_AGE_PRIVATE_KEY](/docs/instance-pipeline-parameters.md#envgene_age_private_key)
6. The EnvGene Admin enables [GitLab Server-side Git Hooks](/docs/features/cred-encryption.md#gitlab-server-side-git-hooks) for the repository
7. The Admin updates `config.yml`:

   ```yaml
   crypt: true
   crypt_backend: "SOPS"
   crypt_create_shades: true
   ```

8. The Admin runs the Local pre-commit manually to encrypt the repository
9. The Local pre-commit encrypts credentials in the repository, creating shade files
10. The Admin pushes the changes to the remote repository
11. The Server-side hook validates the changes
12. The Server-side hook accepts the commit

**Result**:

- All Credentials in the repo are encrypted

### UC-2. Adding a New Sensitive Parameter with SOPS in Shade Credential Mode

**Description:** Add a new sensitive parameter to a Credential file when SOPS with Shade mode is enabled.

**Prerequisites:**

- Encryption is enabled
- SOPS backend is configured
- Shade mode is enabled
- Local Local pre-commit is installed

**Process:**

1. Configurator adds a sensitive parameter using the cred macro in an Env Template
2. The Env Template is built and published as an artifact
3. Configurator runs EnvGene to generate an Env Instance using the artifact from step 2
4. EnvGene generates the Env Instance (including Credentials)
5. Configurator sets the value of the sensitive parameter in the Credential
6. Configurator commits the change locally
7. The Local Local pre-commit creates a Shade file for the Credential
8. The Local Local pre-commit encrypts Shade file
9. The Local Local pre-commit replaces the user-provided value in the main Credential file with `ValueIsSet`
10. Configurator pushes the changes to the remote repository
11. The Server-side hook validates the changes
12. The Server-side hook accepts the commit

**Result:**

- The new encrypted Credential is stored in the remote instance repository

### UC-3. Modifying the value of a sensitive parameter

**Description:** Change the value of a sensitive parameter in a Credential file when SOPS with Shade mode is enabled.

**Prerequisites:**

- Encryption is enabled
- SOPS backend is configured
- Shade mode is enabled
- Local Local pre-commit is installed

**Process:**

1. The Configurator sets a new value for the sensitive parameter in the Credential file (replacing `ValueIsSet`).
2. The Configurator commits the change locally.
3. The Local pre-commit updates the value in the corresponding Shade Credential file.
4. The Local pre-commit encrypts the updated Shade file.
5. The Local pre-commit replaces the value in the main Credential file with `ValueIsSet`.
6. The Admin pushes the changes to the remote repository.
7. The Server-side hook validates the changes.
8. The Server-side hook accepts the commit.

**Result:**

- The updated encrypted Credential is stored in the remote instance repository

---

### UC-4. Migrating from Fernet to SOPS

**Description:** Migration of all repository credentials from the Fernet encryption backend to the SOPS backend with Shade mode enabled.

**Prerequisites:**

- Fernet backend is configured
- All repository credentials are encrypted with Fernet
- Fernet key is set in repository variables
- Local Local pre-commit is installed

**Process:**

1. The admin removes the Fernet secret key from the repository variables
2. The admin adds the SOPS secret key to the repository variables
3. The admin runs a decryption script to decrypt all credentials in the repository
4. The admin updates the backend in `config.yml`:

   ```yaml
   crypt_backend: "SOPS"
   crypt_create_shades: true
   ```

5. The admin commits the changes locally
6. The Local pre-commit encrypts all credentials in the repository using SOPS, creating Shade files
7. The admin pushes the changes to the remote repository
8. The Server-side hook validates the changes
9. The Server-side hook accepts the commit

**Result:**

- All repository credentials are encrypted using the SOPS backend with Shade credential mode enabled
