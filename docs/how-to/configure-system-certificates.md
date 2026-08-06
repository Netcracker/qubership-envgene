# Configure system certificates

This guide shows how to add CA certificates to an environment instance repository so that EnvGene trusts internal
registries and TLS services during pipeline execution. It also covers how to obtain certificates and how to verify
them before use.

For background on the mechanism, see [System certificate configuration](/docs/features/system-certificate.md).

- [Configure system certificates](#configure-system-certificates)
  - [Prerequisites](#prerequisites)
  - [Steps](#steps)
  - [Use a CI/CD variable instead of committed files](#use-a-cicd-variable-instead-of-committed-files)
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

## Prerequisites

- Write access to the environment instance repository.
- The CA certificate, or full certificate chain, of each target service in PEM format.
- OpenSSL and cURL available locally for the verification steps.

## Steps

1. Create a `certs` directory inside the `configuration` folder of your environment instance repository:

   ```text
   /configuration
     /certs
       your-ca-cert.pem
       ca-chain-internal.pem
   ```

2. Place your CA certificate files in this directory. Each file must be PEM-encoded and use a `.crt` or `.pem`
   extension.
3. Commit and push the changes to your repository.
4. Run the pipeline. EnvGene loads the certificates and rebuilds the runner trust store before the other steps run.

## Use a CI/CD variable instead of committed files

To keep certificate files out of the repository, store the base64-encoded PEM bundle in the
`SSL_CERTIFICATES_BUNDLE` CI/CD variable. EnvGene decodes the value and installs it into the runner trust store
before the other steps run.

1. Verify the PEM bundle with the steps in [Verify a certificate](#verify-a-certificate).
2. base64-encode the file as a single line:

   ```bash
   base64 -w 0 ca-bundle.pem
   ```

   On macOS, use `base64 -i ca-bundle.pem | tr -d '\n'`.

3. Create a CI/CD variable named `SSL_CERTIFICATES_BUNDLE` with the encoded string as its value. Mask the
   variable when your CI/CD platform allows it.
4. Run the pipeline.

> [!IMPORTANT]
> The value must be valid base64 of PEM content. If decoding fails, the job stops with an explicit error.

`SSL_CERTIFICATES_BUNDLE` and `configuration/certs/` can be used together. EnvGene installs certificates from
both sources. For a bundle that exceeds your CI/CD platform's variable size limit, use `configuration/certs/`
instead. See [Certificate sources](/docs/features/system-certificate.md#certificate-sources).

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
