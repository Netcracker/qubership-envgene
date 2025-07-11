# Configuration Files

System-wide configuration files that define how EnvGene connects to external systems and manages integrations.

## Registry Configuration

Defines Maven and Docker registries for template artifacts:

```yaml title="registry.yml"
--8<-- "samples/configuration/registry.yml"
```

## Integration Configuration

Configures integration with discovery repositories and Git operations:

```yaml title="integration.yml"
--8<-- "samples/configuration/integration.yml"
```

## Configuration File Purposes

### Registry Configuration
- **Username/Password**: Authentication credentials for artifact repositories
- **Repository URLs**: Different repository types (release, snapshot, staging, proxy)
- **Docker Registries**: Container image repository configurations
- **Maven Repositories**: JAR/WAR artifact repository configurations

### Integration Configuration
- **Discovery Repository**: Integration with external service discovery
- **Git Configuration**: Repository access and commit settings
- **API Tokens**: Authentication for external service integrations

## Security Considerations

Configuration files often contain sensitive information:

- Use credential references (`envgen.creds.get()`) instead of plain text passwords
- Store actual credentials in encrypted credential files
- Follow the principle of least privilege for service accounts
- Regularly rotate API tokens and passwords

## Configuration Validation

EnvGene validates configuration files against JSON schemas to ensure:

- Required fields are present
- Data types are correct
- URLs are properly formatted
- Credential references are valid 
