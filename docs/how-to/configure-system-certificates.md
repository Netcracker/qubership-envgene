# Configure system certificates

This guide shows how to set the `SSL_CERTIFICATES_BUNDLE` CI/CD variable so that EnvGene trusts internal
registries and TLS services during pipeline execution.

For background on the mechanism, see [System certificate configuration](/docs/features/system-certificate.md).

- [Configure system certificates](#configure-system-certificates)
  - [Prerequisites](#prerequisites)
  - [Obtain the CA certificate](#obtain-the-ca-certificate)
    - [Retrieve the chain with OpenSSL](#retrieve-the-chain-with-openssl)
    - [Copy the CA certificates into one file](#copy-the-ca-certificates-into-one-file)
    - [Export the chain from a browser](#export-the-chain-from-a-browser)
  - [Build a certificate chain file](#build-a-certificate-chain-file)
  - [Verify the CA certificate](#verify-the-ca-certificate)
    - [Check that the file parses](#check-that-the-file-parses)
    - [Check that the chain validates the host](#check-that-the-chain-validates-the-host)
    - [Check that a client trusts the host](#check-that-a-client-trusts-the-host)
  - [Set `SSL_CERTIFICATES_BUNDLE`](#set-ssl_certificates_bundle)
    - [Encode the bundle](#encode-the-bundle)
    - [Create the variable in GitLab](#create-the-variable-in-gitlab)
    - [Create the variable in GitHub](#create-the-variable-in-github)
    - [Confirm the certificate was installed](#confirm-the-certificate-was-installed)

## Prerequisites

- The CA certificate, or the intermediate and root certificates, of the target service in PEM format.
- OpenSSL and cURL for the verification steps.
- On GitLab: access to create a CI/CD variable in the instance repository project.
- On GitHub: access to Actions secrets and to `.github/workflows/Envgene.yml` in the instance repository.

## Obtain the CA certificate

The value you encode is the CA that signed the service, not the leaf certificate the server presents.

### Retrieve the chain with OpenSSL

For an HTTPS service:

```bash
openssl s_client -connect your-site.com:443 -servername your-site.com -showcerts
```

For a service on a custom port, replace the host and port:

```bash
openssl s_client -connect internal-service.company.com:8443 -showcerts
```

### Copy the CA certificates into one file

The `openssl s_client -showcerts` output lists each certificate in the chain. Copy the intermediate CA and
the root CA into `ca-bundle.pem`:

```text
-----BEGIN CERTIFICATE-----
[Intermediate CA]
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
[Root CA]
-----END CERTIFICATE-----
```

Do not copy the server certificate into this file.

### Export the chain from a browser

For a web service you can export the chain from a browser:

1. Open the site in your browser.
2. Select the lock icon in the address bar.
3. Open the certificate details.
4. Export the CA certificate, not the server certificate.

If the export is DER (often a `.cer` file), convert it to PEM:

```bash
openssl x509 -inform DER -in certificate.cer -out ca-bundle.pem
```

If the export is already PEM, save it as `ca-bundle.pem`.

## Build a certificate chain file

You can combine several PEM CA certificates into `ca-bundle.pem`. Place the root CA first, then any
intermediate CAs:

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

`SSL_CERTIFICATES_BUNDLE` carries one file. Put every CA for this variable in the same `ca-bundle.pem`.

## Verify the CA certificate

Verify `ca-bundle.pem` before you encode it. Set the variables once:

```bash
CERT=ca-bundle.pem
HOST=artifactory.company.com
PORT=443
```

### Check that the file parses

Confirm the file is a valid PEM certificate and read its subject, issuer, and validity dates:

```bash
openssl x509 -in "$CERT" -noout -subject -issuer -dates
```

If `notAfter` is already past, do not encode the file. The `env-prepare` job fails on an expired certificate.

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

## Set `SSL_CERTIFICATES_BUNDLE`

EnvGene base64-decodes `SSL_CERTIFICATES_BUNDLE` and installs it into the runner trust store at the start of the
`env-prepare` job. Paste the encoded string only. Do not add quotes, spaces, or line breaks around it.

### Encode the bundle

On Linux (GNU `base64`):

```bash
base64 -w 0 ca-bundle.pem
```

On macOS:

```bash
base64 -i ca-bundle.pem | tr -d '\n'
```

On Windows PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("ca-bundle.pem"))
```

### Create the variable in GitLab

1. Open the GitLab project of the instance repository.
2. Go to **Settings** → **CI/CD** → **Variables** and select **Add variable**.
3. Set **Key** to `SSL_CERTIFICATES_BUNDLE` and **Value** to the encoded string. Set **Type** to Variable, not File.
4. Save the variable.

> [!NOTE]
> Masking is optional. If GitLab refuses to mask the value, save the variable unmasked.

### Create the variable in GitHub

Creating a secret does not pass it into the EnvGene container. Map it in the instance repository workflow.

1. Open the instance repository on GitHub.
2. Go to **Settings** → **Secrets and variables** → **Actions** and create a secret named
   `SSL_CERTIFICATES_BUNDLE` with the encoded string as the value.
3. In `.github/workflows/Envgene.yml`, add the secret to the `env` block of the `env-prepare` job, next to the
   other secrets:

   ```yaml
   env:
     SSL_CERTIFICATES_BUNDLE: ${{ secrets.SSL_CERTIFICATES_BUNDLE }}
   ```

### Confirm the certificate was installed

Run the instance pipeline and open the log of the `env-prepare` job.

Confirm the log contains `certs from 'SSL_CERTIFICATES_BUNDLE' added to trusted root`.

If the log contains `SSL_CERTIFICATES_BUNDLE is not set, skipping`, the job did not receive the variable. On
GitHub, check the `env` mapping in the workflow.
