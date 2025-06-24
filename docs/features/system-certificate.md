# System Certificate Configuration

- [System Certificate Configuration](#system-certificate-configuration)
  - [Problem Statement](#problem-statement)
  - [Approach](#approach)
    - [Certificate Management Process](#certificate-management-process)
    - [Supported Certificate Types](#supported-certificate-types)
  - [Usage Examples](#usage-examples)
    - [Secure Artifact Repositories](#secure-artifact-repositories)
    - [Internal Services with Self-Signed Certificates](#internal-services-with-self-signed-certificates)

## Problem Statement

When deploying environments in enterprise settings, teams face several certificate-related challenges:

1. Secure Communication Barriers:
   1. Internal services use self-signed certificates not trusted by default
   2. Artifact repositories require client certificate authentication

2. Manual Certificate Management:
   1. Manually installing certificates on build agents is error-prone
   2. Certificate updates require manual intervention
   3. Different environments may require different certificates

Goals:

1. Provide a consistent way to manage certificates across all environments
2. Automate certificate installation during pipeline execution
3. Support various certificate types and authentication methods
4. Eliminate manual certificate management on build agents

## Approach

EnvGene provides a built-in mechanism for managing system certificates through a dedicated directory in the environment instance repository. Certificates placed in this directory are automatically loaded and configured during pipeline execution.

### Certificate Management Process

The system certificate configuration feature in EnvGene automatically handles certificates placed in the `configuration/certs/` directory of your environment instance repository. During pipeline execution:

1. EnvGene checks for certificate files in the `configuration/certs/` directory
2. Detected certificates are loaded into the runner environment
3. CA certificates are added to the system's trusted root certificate store
4. Environment variables are set to ensure tools and libraries use the certificates
5. EnvGene uses these certificates for secure communication with external systems

```mermaid
flowchart TD
    A[Place certificates in configuration/certs/] --> B[Pipeline execution begins]
    B --> C[Certificate detection]
    C --> D[Certificates loaded into runner environment]
    D --> E[CA certificates added to trusted root store]
    E --> F[Environment variables set for secure communication]
    F --> G[EnvGene uses certificates for secure connections]
```

To use this feature:

1. Create a `certs` directory within the `configuration` folder of your environment instance repository:

```
/configuration
  /certs
    your-ca-cert.pem
    your-client-cert.p12
```

2. Place your certificate files in this directory
3. Commit and push these changes to your repository
4. When the pipeline runs, these certificates will be automatically loaded and used

### Supported Certificate Types

The system supports various certificate types:

- **CA Certificates** (`.crt`, `.pem`): Root or intermediate certificates used to validate server certificates
- **Client Certificates** (`.p12`, `.pfx`): Used for client authentication when connecting to external systems

While the system will load all certificates in the directory, following these naming conventions can help with organization:

- `ca-*.pem` or `ca-*.crt` for CA certificates
- `client-*.p12` or `client-*.pfx` for client certificates

## Usage Examples

### Secure Artifact Repositories

**Scenario**: EnvGene needs to connect to secure artifact repositories that require certificate-based authentication.

**Implementation**:

1. Obtain the client certificate for the artifact repository
2. Place the files in the `configuration/certs/` directory:

```
/configuration
  /certs
    ca.pem          # CA certificate
    client-artifactory.p12    # Client certificate for Artifactory
```

3. The certificate will be automatically used for authentication during pipeline execution

```mermaid
sequenceDiagram
    participant EnvGene
    participant SecureRepo
    
    EnvGene->>SecureRepo: Request with client certificate
    SecureRepo->>EnvGene: Authenticate and respond
```

### Internal Services with Self-Signed Certificates

**Scenario**: EnvGene needs to communicate with internal services that use self-signed certificates.

**Implementation**:

1. Obtain the self-signed certificate used by the internal service
2. Place the certificate in the `configuration/certs/` directory:

```
/configuration
  /certs
    ca-internal-service.pem  # Self-signed certificate
```

3. The certificate will be automatically added to the trusted root store during pipeline execution

## Technical Implementation

Under the hood, EnvGene uses a certificate handling script that:

1. Detects the operating system of the runner
2. Copies certificates to the appropriate system location based on the OS:
   - Debian/Ubuntu: `/usr/local/share/ca-certificates/`
   - CentOS/Red Hat: `/etc/pki/ca-trust/source/anchors/`
   - Alpine: appends to `/etc/ssl/certs/ca-certificates.crt`
3. Updates the CA trust store using the appropriate command for the OS:
   - Debian/Ubuntu: `update-ca-certificates --fresh`
   - CentOS/Red Hat: `update-ca-trust`
4. Sets environment variables like `REQUESTS_CA_BUNDLE` for Python-based tools

## Troubleshooting

### Common Issues

1. **Certificate not recognized**:
   - Ensure the certificate is in the correct format
   - Check that the certificate is placed in the correct directory

2. **Connection failures**:
   - Verify that the certificate is not expired
   - Ensure the certificate is trusted by the target system

3. **Pipeline failures**:
   - Check pipeline logs for certificate loading errors
   - Verify that the certificate files have the correct permissions

### Debugging Tips

To debug certificate issues:

1. Check the pipeline logs for certificate loading messages
2. Verify that environment variables like `REQUESTS_CA_BUNDLE` are set correctly
3. Use tools like `openssl` to validate certificate chains
