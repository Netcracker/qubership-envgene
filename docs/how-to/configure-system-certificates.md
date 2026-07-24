# Configure system certificates

This guide shows how to provide CA certificates so that EnvGene trusts internal registries and TLS services during
pipeline execution. EnvGene merges certificates from every non-empty configured source: the `SSL_CERTIFICATES_BUNDLE`
CI/CD variable, the `/ca_bundle` folder, and `/configuration/certs`. The guide also covers how to obtain certificates
and how to verify them before use.

For background on the mechanism and the merge rules, see
[System certificate configuration](/docs/features/system-certificate.md).

- [Configure system certificates](#configure-system-certificates)
  - [Prerequisites](#prerequisites)
  - [Provide certificates in a repository folder](#provide-certificates-in-a-repository-folder)
  - [Provide certificates through `SSL_CERTIFICATES_BUNDLE`](#provide-certificates-through-ssl_certificates_bundle)
    - [Encode the bundle](#encode-the-bundle)
    - [Create the variable in GitLab](#create-the-variable-in-gitlab)
    - [Create the variable in GitHub](#create-the-variable-in-github)
    - [Verify certificate loading](#verify-certificate-loading)
  - [Obtain the required certificates](#obtain-the-required-certificates)
    - [Retrieve server certificates with OpenSSL](#retrieve-server-certificates-with-openssl)
    - [Extract individual certificates from a chain](#extract-individual-certificates-from-a-chain)
    - [Export certificates from a browser](#export-certificates-from-a-browser)
  - [Build a certificate chain file](#build-a-certificate-chain-file)
  - [Verify a certificate](#verify-a-certificate)
    - [Check that the file parses](#check-that-the-file-parses)
    - [Check that the chain validates the host](#check-that-the-chain-validates-the-host)
    - [Check that a client trusts the host](#check-that-a-client-trusts-the-host)
  - [Usage examples](#usage-examples)
    - [Secure artifact repositories](#secure-artifact-repositories)
    - [Internal services with self-signed certificates](#internal-services-with-self-signed-certificates)
  - [Troubleshooting](#troubleshooting)

## Prerequisites

- Write access to the environment instance repository.
- For the CI/CD variable source: Maintainer access to the GitLab project, or admin access to the GitHub repository.
- The CA certificate, or full certificate chain, of each target service in PEM format.
- OpenSSL and cURL available locally for the verification steps.

## Provide certificates in a repository folder

1. Create a certificate folder in your environment instance repository. EnvGene reads both locations:

   ```text
   /ca_bundle
     ca-chain-internal.pem
   /configuration
     /certs
       your-ca-cert.pem
   ```

2. Place your CA certificate files in the folder. Each file must be PEM-encoded. The filename and extension do not
   matter, EnvGene detects certificates by content.
3. Commit and push the changes to your repository.
4. Run the pipeline. EnvGene loads the certificates and rebuilds the runner trust store before the other steps run.

## Provide certificates through `SSL_CERTIFICATES_BUNDLE`

Use the CI/CD variable when storing certificate files in the repository is restricted by security policies. If
`SSL_CERTIFICATES_BUNDLE` is set but invalid, the job fails. See
[Certificate validation](/docs/features/system-certificate.md#certificate-validation).

> [!WARNING]
> GitLab limits a CI/CD variable value to 10,000 characters. A GitHub secret is limited to 48 KB. For larger
> bundles, use a repository folder instead (see
> [Provide certificates in a repository folder](#provide-certificates-in-a-repository-folder)).

### Encode the bundle

Encode the PEM file as a single line with no line breaks, then check the length. On Linux (GNU `base64`):

```bash
base64 -w 0 ca-bundle.pem
base64 -w 0 ca-bundle.pem | wc -c
```

On macOS:

```bash
base64 -i ca-bundle.pem | tr -d '\n'
base64 -i ca-bundle.pem | tr -d '\n' | wc -c
```

Copy the full output of the first command. You use it as the variable value in the next step. For GitLab, the
character count must be 10,000 or less.

> [!WARNING]
> Do not add quotes, newlines, or spaces around the encoded string. Extra characters cause base64 decoding to fail
> and the pipeline job aborts.

### Create the variable in GitLab

1. Open the GitLab project of the instance repository.
2. Go to **Settings** → **CI/CD** → **Variables** and select **Add variable**.
3. Set **Key** to `SSL_CERTIFICATES_BUNDLE` and **Value** to the encoded string. Keep **Type** as Variable. Masking
   is recommended.
4. Save the variable and confirm it appears in the project CI/CD variable list.

> [!NOTE]
> GitLab may refuse to mask values that do not meet masking rules. If masking fails, save the variable unmasked and
> restrict project access instead.

### Create the variable in GitHub

GitHub Actions does not inject repository variables and secrets into jobs automatically. Map the value in the
instance repository workflow:

1. Open the instance repository on GitHub.
2. Go to **Settings** → **Secrets and variables** → **Actions** and create a secret named `SSL_CERTIFICATES_BUNDLE`
   with the encoded string as the value.
3. In the instance pipeline workflow (`.github/workflows/Envgene.yml`), map the secret into the job environment,
   following the existing pattern for other secrets:

   ```yaml
   env:
     SSL_CERTIFICATES_BUNDLE: ${{ secrets.SSL_CERTIFICATES_BUNDLE }}
   ```

The workflow passes its environment into the EnvGene container.

### Verify certificate loading

Trigger the instance pipeline and open the log of a job that loads certificates: `env-prepare` or `cmdb_import`.

Confirm the log shows certificates loaded from `SSL_CERTIFICATES_BUNDLE` and contains a successful import message,
for example `certs from … added to trusted root`. Confirm the job exits with success.

## Obtain the required certificates

Before adding certificates, identify and retrieve them from your target services.

### Retrieve server certificates with OpenSSL

For an HTTPS service:

```bash
# Print the certificate chain presented by a server
openssl s_client -connect your-site.com:443 -servername your-site.com -showcerts

# Save the server certificate to a file
openssl s_client -connect your-site.com:443 -servername your-site.com < /dev/null 2>/dev/null \
  | openssl x509 -outform PEM > server-cert.pem
```

For a service on a custom port, replace the host and port:

```bash
openssl s_client -connect internal-service.company.com:8443 -showcerts
```

### Extract individual certificates from a chain

When you run `openssl s_client -showcerts`, the output lists each certificate in the chain:

```text
-----BEGIN CERTIFICATE-----
[Certificate 1 - the server certificate]
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
[Certificate 2 - intermediate CA]
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
[Certificate 3 - root CA]
-----END CERTIFICATE-----
```

Copy the CA certificates (intermediate and root) into a single file to use as the chain.

### Export certificates from a browser

For a web service you can also export the chain from a browser:

1. Open the site in your browser.
2. Select the lock icon in the address bar.
3. Open the certificate details.
4. Export the certificate chain.
5. Convert it to PEM format if the export is in a different encoding.

## Build a certificate chain file

You can combine several PEM certificates into one file. Place the root CA first, then any intermediate CAs:

```text
-----BEGIN CERTIFICATE-----
[Root CA certificate]
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
[Intermediate CA certificate]
-----END CERTIFICATE-----
```

> [!NOTE]
> For trust-store installation the order inside the file does not change the result, because each CA is trusted
> independently. A consistent order keeps the file readable and matches the order a server uses when it serves a
> chain.

Keep separate chains in separate files, for example `ca-chain-internal.pem` and `ca-chain-external.pem`.

## Verify a certificate

Verify a certificate before you commit it. Set the variables once:

```bash
CERT=configuration/certs/ca-chain.pem
HOST=artifactory.company.com
PORT=443
```

### Check that the file parses

Confirm the file is a valid PEM certificate and read its subject, issuer, and validity dates:

```bash
openssl x509 -in "$CERT" -noout -subject -issuer -dates
```

For a file that holds several certificates, `openssl x509` reads only the first one. To confirm that every block
parses, list them all:

```bash
openssl crl2pkcs7 -nocrl -certfile "$CERT" | openssl pkcs7 -print_certs -noout
```

Any error at this step, for example `Could not find certificate from <file>` or `unable to load certificate`,
means the file is not a valid PEM certificate.

### Check that the chain validates the host

Confirm that the CA in `$CERT` is enough to validate the TLS connection to the host. Look for
`Verify return code: 0 (ok)`:

```bash
echo | openssl s_client -connect "$HOST:$PORT" -servername "$HOST" -CAfile "$CERT" 2>&1 \
  | grep -E "Verify return code|verify error"
```

- `0 (ok)`: the chain in `$CERT` is sufficient.
- `20 (unable to get local issuer certificate)`: a root or intermediate certificate is missing from the file.

### Check that a client trusts the host

Confirm that a real client trusts the host with this CA. The command exits with `curl OK` on success:

```bash
curl --cacert "$CERT" -sSf "https://$HOST:$PORT" -o /dev/null && echo "curl OK"
```

> [!NOTE]
> Verify the chain with the CA certificates, not the server leaf certificate. A client trusts a certificate that
> is present in the CA file directly, so testing with the leaf hides a missing issuer.

## Usage examples

### Secure artifact repositories

**Scenario**: EnvGene needs to connect to an artifact repository exposed over TLS with a private CA.

**Steps**:

1. Obtain the CA certificate, or chain, of the repository.
2. Place the file in the `configuration/certs/` directory:

   ```text
   /configuration
     /certs
       ca-artifactory.pem
   ```

3. Verify the certificate with the steps in [Verify a certificate](#verify-a-certificate).
4. Commit and push. The next pipeline run trusts the repository.

### Internal services with self-signed certificates

**Scenario**: EnvGene needs to reach an internal service that uses a self-signed certificate.

**Steps**:

1. Obtain the self-signed certificate of the internal service.
2. Place the certificate in the `configuration/certs/` directory:

   ```text
   /configuration
     /certs
       ca-internal-service.pem
   ```

3. Commit and push. The next pipeline run adds the certificate to the trust store.

## Troubleshooting

| Symptom                    | Check                                             |
|----------------------------|---------------------------------------------------|
| Certificate not recognized | PEM encoding, file present in a configured source |
| Connection failures        | Certificate not expired, chain complete           |
| Pipeline failures          | Pipeline logs show certificate loading errors     |

To check expiry and chain completeness, rerun the commands in [Verify a certificate](#verify-a-certificate)
against the target host from the runner.
