# `cert_apply`

- [`cert_apply`](#cert_apply)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Repository inputs](#repository-inputs)
  - [Processing flow](#processing-flow)
  - [Certificate validation and installation](#certificate-validation-and-installation)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Related documentation](#related-documentation)

## Description

The `cert_apply` logic adds CA certificates from a CI/CD variable and from two repository directories to the trust
store of the job. When the variable is unset and neither directory contains an entry, the logic adds
the default certificate built into the EnvGene image. For the concept, see
[System certificate configuration](/docs/features/system-certificate.md).

- **Runs when**: Once at the start of the `env-prepare` job, before the job's own work. No parameter skips the logic.

## Input parameters

| Parameter                                                                                  | Source                     | Required | Default | Values / format                                 | Effect                                                                       |
| ------------------------------------------------------------------------------------------ | -------------------------- | -------- | ------- | ----------------------------------------------- | ---------------------------------------------------------------------------- |
| [`SSL_CERTIFICATES_BUNDLE`](/docs/envgene-repository-variables.md#ssl_certificates_bundle) | CI/CD variable             | No       | None    | base64-encoded PEM, one certificate or a bundle | The logic installs the bundle. The default certificate is then not installed |
| `CI_SERVER_TLS_CA_FILE`                                                                    | GitLab predefined variable | No       | None    | Path to a PEM file, or PEM text                 | Git in the job trusts the GitLab server. The job trust store does not change |

## Repository inputs

| File                                             | Object               | What the logic uses                                       |
| ------------------------------------------------ | -------------------- | --------------------------------------------------------- |
| `ca_bundle/`                                     | CA certificate files | Every file directly in the directory, with any extension  |
| `configuration/certs/`                           | CA certificate files | Every file directly in the directory, with any extension  |
| Default certificate built into the EnvGene image | CA certificate file  | Only when no other source is found. Absent in some images |

## Processing flow

1. **Check job environment.**

   1. When the CI system does not provide the repository root directory, the logic fails. Otherwise the logic
      continues.

2. **Trust the GitLab server in Git.**

   1. When `CI_SERVER_TLS_CA_FILE` is set, the logic configures Git in the job to trust the certificate it holds. The
      variable can hold a file path or, in GitLab versions earlier than 16.6, PEM text. Otherwise the logic skips this
      block.

   This block does not change the trust store of the job and does not count as a certificate source in block 6.

3. **Install the bundle from `SSL_CERTIFICATES_BUNDLE`**

   1. When `SSL_CERTIFICATES_BUNDLE` is empty, the logic skips this block.

   2. When `SSL_CERTIFICATES_BUNDLE` contains text `BEGIN CERTIFICATE`, the logic fails, because the value is raw PEM
      instead of base64.

   3. The logic decodes `SSL_CERTIFICATES_BUNDLE` from base64.

   4. The logic validates and installs the decoded bundle as described in
      [Certificate validation and installation](#certificate-validation-and-installation).

   5. The logic sets the **source found** flag. The flag records that at least one certificate source was used in
      blocks 3 to 5.

4. **Install certificates from `ca_bundle/`**

   1. When directory `ca_bundle/` contains at least one entry, the logic sets the **source found** flag. An entry is a
      file or a subdirectory. An empty directory does not set the flag, and the logic skips this block.

   2. For each file directly in `ca_bundle/`, the logic validates and installs the file as described in
      [Certificate validation and installation](#certificate-validation-and-installation). Subdirectories are not
      read.

5. **Install certificates from `configuration/certs/`**

   1. When directory `configuration/certs/` contains at least one entry, the logic sets the **source found** flag. An
      entry is a file or a subdirectory. An empty directory does not set the flag, and the logic skips this block.

   2. For each file directly in `configuration/certs/`, the logic validates and installs the file as described in
      [Certificate validation and installation](#certificate-validation-and-installation). Subdirectories are not
      read.

6. **Fall back to the default certificate.**

   1. When the **source found** flag is set, the logic skips this block.

   2. When the flag is not set and the EnvGene image contains a default certificate, the logic validates and installs
      it as described in [Certificate validation and installation](#certificate-validation-and-installation).
      Otherwise the logic installs nothing.

   The logic adds every source whose condition is met. One source does not turn the others off. The default
   certificate is the exception: the logic adds it only when no earlier source was found.

| Source                    | Condition                                                     | Added to the trust store                                             |
| ------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------- |
| `SSL_CERTIFICATES_BUNDLE` | The variable is set                                           | The decoded bundle                                                   |
| `ca_bundle/`              | The directory contains at least one entry                     | Each file directly in the directory. An empty directory adds no file |
| `configuration/certs/`    | The directory contains at least one entry                     | Each file directly in the directory. An empty directory adds no file |
| Default certificate       | The variable is unset and neither directory contains an entry | The certificate from the image, when the image has one               |

## Certificate validation and installation

Blocks 3 to 6 handle every source with the same procedure.

1. The logic splits the source into PEM blocks. A block starts with line `-----BEGIN CERTIFICATE-----` and ends with
   line `-----END CERTIFICATE-----`. Text outside blocks is ignored.

2. For each PEM block, the logic checks that the block is a readable X.509 certificate and is not expired at the time
   of the run. When the check fails, the logic checks the next block.

3. When the source holds no PEM block, the check for this source fails.

4. When any block failed in substep 2, or the source holds no PEM block, the logic fails. The source is not
   installed.

5. The logic adds all certificates of the source to the trust store of the job.

6. The trust store keeps one entry per file name without extension. When two sources have the same file name without
   extension, for example `ca_bundle/root.pem` and `configuration/certs/root.crt`, the source installed later replaces
   the earlier one.

## Result

1. The job trusts every certificate installed in blocks 3 to 6, in addition to the public CA certificates of the
   image.

2. When `CI_SERVER_TLS_CA_FILE` is set, Git in the job trusts the GitLab server.

3. Repository files are unchanged.

## Error handling

The logic never writes to the repository. A failure stops the job before its own work.

**1a.** The logic fails when the CI system does not provide the repository root directory.

**3a.** The logic fails when `SSL_CERTIFICATES_BUNDLE` contains raw PEM text instead of base64.

**3b.** The logic fails when `SSL_CERTIFICATES_BUNDLE` is not valid base64.

**3c.** The logic fails when the decoded `SSL_CERTIFICATES_BUNDLE` does not pass validation.

**4a.** The logic fails when a file in `ca_bundle/` holds an expired or unreadable certificate, or no PEM block at all.
An empty file or a file that is not a certificate, such as a readme, fails the same way.

**5a.** The logic fails when a file in `configuration/certs/` fails the same check as in 4a.

**6a.** The logic fails when the default certificate of the image fails the same check as in 4a.

The logic does not continue after a failed check.

## Related documentation

- [System certificate configuration](/docs/features/system-certificate.md)
- [Configure system certificates](/docs/how-to/configure-system-certificates.md)
- [`SSL_CERTIFICATES_BUNDLE`](/docs/envgene-repository-variables.md#ssl_certificates_bundle)
- [`cert_apply` in Instance pipeline flow](/docs/technical-design/instance-pipeline/flow.md#11-step-preprocess-to-be-implemented-not-implemented-yet)
