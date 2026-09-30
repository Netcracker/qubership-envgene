# Configure system certificates

This guide shows how to add CA certificates to an environment instance repository so that EnvGene trusts internal
registries and TLS services during pipeline execution. It also covers how to obtain certificates and how to verify
them before use.

For background on the mechanism, see [System certificate configuration](/docs/features/system-certificate.md).

- [Configure system certificates](#configure-system-certificates)
  - [Running this guide](#running-this-guide)
  - [Prerequisites](#prerequisites)
  - [Required Environment Variables](#required-environment-variables)
  - [Steps](#steps)
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

## Running this guide

**No installation needed** — run with `npx`. Fill in your values using the template in [Required Inputs](#required-inputs), save to any file (e.g. `my-inputs.txt`), then run:

`(set -a; source my-inputs.txt; npx runme run --all --filename configure-system-certificates.md)`

See [How to run guides with runme](/docs/how-to/how-to-run-guides-with-runme.md) for full CLI, VS Code, pipeline, and AI agent instructions.

Steps marked **Manual step — cannot be automated** are blockquotes — runme skips them automatically.

## Prerequisites

- Write access to the environment instance repository, cloned locally.
- The CA certificate, or full certificate chain, of each target service in PEM format.
- OpenSSL, cURL, and Node.js (v16+) available locally.

Verify tools are available:

```bash
openssl version
# Expected: OpenSSL 1.x.x or 3.x.x

curl --version | head -1
# Expected: curl x.x.x ...

node --version
# Expected: v16.x.x or higher
```

## Required Inputs

Create a file with your values (any filename, e.g. `my-inputs.txt`) and load it with `source` before running.

| Variable | Required | Example | Description |
|---|---|---|---|
| `CERT` | Yes | `configuration/certs/ca-chain.pem` | Path to the CA cert file, relative to repo root |
| `HOST` | Yes | `artifactory.company.com` | Hostname of the TLS service to trust |
| `PORT` | No | `443` | Port of the TLS service (default: `443`) |

**Template** — copy, fill in your values, save as any filename:

```bash {"excludeFromRunAll":true,"name":"input-template"}
CERT=configuration/certs/ca-chain.pem
HOST=artifactory.company.com
PORT=443
```

Validate inputs (first runnable cell — fails immediately if a required variable is missing):

```bash
# validate-inputs
: "${CERT:?CERT is required — see Required Inputs section}"
: "${HOST:?HOST is required — see Required Inputs section}"
PORT="${PORT:-443}"
echo "Inputs OK: CERT=$CERT  HOST=$HOST  PORT=$PORT"
```

## Steps

These steps assume you have already cloned your instance repository locally and are running commands from its root.

1. **Create the `certs` directory:**

   ```bash
   mkdir -p configuration/certs
   ```

   Verify:

   ```bash
   ls -d configuration/certs
   # Expected: configuration/certs
   ```

   Expected directory layout after adding your certificate files:

   ```text
   /configuration
     /certs
       your-ca-cert.pem
       ca-chain-internal.pem
   ```

2. **Place your CA certificate files in `configuration/certs/`.**

   > **Manual step — cannot be automated:** Certificate files must be obtained from the target services
   > (see [Obtain the required certificates](#obtain-the-required-certificates)) and copied into place manually.
   > Each file must be PEM-encoded and use a `.crt` or `.pem` extension.
   >
   > Verify: run the [Check that the file parses](#check-that-the-file-parses) commands against each file before committing.

3. **Commit and push the changes:**

   > **Note:** Run these from the root of your cloned instance repository.

   ```bash {"excludeFromRunAll":true}
   git add configuration/certs/
   git commit -m "Add CA certificates for internal services"
   git push
   ```

   Verify:

   ```bash {"excludeFromRunAll":true}
   git log --oneline -1
   # Expected: commit message matching what you entered above
   ```

4. **Run the pipeline.**

   > **Manual step — cannot be automated:** Pipeline execution requires GitLab CI access. Trigger the pipeline
   > from the GitLab UI or via the API. EnvGene loads the certificates and rebuilds the runner trust store
   > before the other steps run.

## Obtain the required certificates

Before adding certificates, identify and retrieve them from your target services.

### Retrieve server certificates with OpenSSL

Print the full certificate chain presented by a server:

```bash {"excludeFromRunAll":true}
openssl s_client -connect "$HOST:$PORT" -servername "$HOST" -showcerts
```

Save the server certificate to a file:

```bash {"excludeFromRunAll":true}
openssl s_client -connect "$HOST:$PORT" -servername "$HOST" < /dev/null 2>/dev/null \
  | openssl x509 -outform PEM > server-cert.pem
```

Verify the saved file parsed correctly:

```bash {"excludeFromRunAll":true}
openssl x509 -in server-cert.pem -noout -subject -issuer -dates
# Expected: subject, issuer, and validity date lines with no error
```

For a service on a custom port, set `$HOST` and `$PORT` accordingly before running the commands above.

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

Copy the CA certificates (intermediate and root) into a single file to use as the chain. The server leaf
certificate is not needed for trust-store installation.

### Export certificates from a browser

> **Manual step — cannot be automated:** Certificate export from a browser requires a GUI browser session.

1. Open the site in your browser.
2. Select the lock icon in the address bar.
3. Open the certificate details.
4. Export the certificate chain.
5. Convert it to PEM format if the export is in a different encoding.

## Build a certificate chain file

Combine several PEM certificates into one file using `cat`. Place the root CA first, then any intermediate CAs:

```bash {"excludeFromRunAll":true}
cat root-ca.pem intermediate-ca.pem > configuration/certs/ca-chain.pem
```

Verify the combined file lists all expected certificates:

```bash {"excludeFromRunAll":true}
openssl crl2pkcs7 -nocrl -certfile configuration/certs/ca-chain.pem \
  | openssl pkcs7 -print_certs -noout
# Expected: one Subject/Issuer block per certificate in the file
```

> [!NOTE]
> For trust-store installation the order inside the file does not change the result, because each CA is trusted
> independently. A consistent order keeps the file readable and matches the order a server uses when it serves a
> chain.

Keep separate chains in separate files, for example `ca-chain-internal.pem` and `ca-chain-external.pem`.

## Verify a certificate

Verify a certificate before you commit it. Ensure `$CERT`, `$HOST`, and `$PORT` are set from the
[Required Environment Variables](#required-environment-variables) section.

### Check that the file parses

Confirm the file is a valid PEM certificate and read its subject, issuer, and validity dates:

```bash {"excludeFromRunAll":true}
openssl x509 -in "$CERT" -noout -subject -issuer -dates
# Expected: subject, issuer, and validity date lines — no error
```

For a file that holds several certificates, `openssl x509` reads only the first one. To confirm that every block
parses, list them all:

```bash {"excludeFromRunAll":true}
openssl crl2pkcs7 -nocrl -certfile "$CERT" | openssl pkcs7 -print_certs -noout
```

Any error at this step, for example `Could not find certificate from <file>` or `unable to load certificate`,
means the file is not a valid PEM certificate.

### Check that the chain validates the host

Confirm that the CA in `$CERT` is enough to validate the TLS connection to the host. Look for
`Verify return code: 0 (ok)`:

```bash {"excludeFromRunAll":true}
echo | openssl s_client -connect "$HOST:$PORT" -servername "$HOST" -CAfile "$CERT" 2>&1 \
  | grep -E "Verify return code|verify error"
```

- `0 (ok)`: the chain in `$CERT` is sufficient.
- `20 (unable to get local issuer certificate)`: a root or intermediate certificate is missing from the file.

### Check that a client trusts the host

Confirm that a real client trusts the host with this CA. The command exits with `curl OK` on success:

```bash {"excludeFromRunAll":true}
curl --cacert "$CERT" -sSf "https://$HOST:$PORT" -o /dev/null && echo "curl OK"
```

> [!NOTE]
> Verify the chain with the CA certificates, not the server leaf certificate. A client trusts a certificate that
> is present in the CA file directly, so testing with the leaf hides a missing issuer.

## Usage examples

### Secure artifact repositories

**Scenario**: EnvGene needs to connect to an artifact repository exposed over TLS with a private CA.

Create the directory and copy the certificate:

```bash {"excludeFromRunAll":true}
mkdir -p configuration/certs
cp ca-artifactory.pem configuration/certs/ca-artifactory.pem
```

Verify the certificate is valid before committing:

```bash {"excludeFromRunAll":true}
CERT="configuration/certs/ca-artifactory.pem"
openssl x509 -in "$CERT" -noout -subject -issuer -dates
```

Expected layout:

```text
/configuration
  /certs
    ca-artifactory.pem
```

Commit and push. The next pipeline run trusts the repository.

### Internal services with self-signed certificates

**Scenario**: EnvGene needs to reach an internal service that uses a self-signed certificate.

Create the directory and copy the certificate:

```bash {"excludeFromRunAll":true}
mkdir -p configuration/certs
cp ca-internal-service.pem configuration/certs/ca-internal-service.pem
```

Verify:

```bash {"excludeFromRunAll":true}
CERT="configuration/certs/ca-internal-service.pem"
openssl x509 -in "$CERT" -noout -subject -issuer -dates
```

Expected layout:

```text
/configuration
  /certs
    ca-internal-service.pem
```

Commit and push. The next pipeline run adds the certificate to the trust store.

## Troubleshooting

| Symptom                    | Check                                                       |
|----------------------------|-------------------------------------------------------------|
| Certificate not recognized | PEM encoding, `.crt` or `.pem` extension, correct directory |
| Connection failures        | Certificate not expired, chain complete                     |
| Pipeline failures          | Pipeline logs show certificate loading errors               |

To check expiry and chain completeness, rerun the commands in [Verify a certificate](#verify-a-certificate)
against the target host from the runner.
