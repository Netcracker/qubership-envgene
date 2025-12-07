# Migrating Dot-Notation Parameters to Nested Object Format

- [Migrating Dot-Notation Parameters to Nested Object Format](#migrating-dot-notation-parameters-to-nested-object-format)
  - [Problem](#problem)
  - [Migration Steps](#migration-steps)
  - [Example Migration](#example-migration)

This guide explains how to migrate parameters in [EnvGene objects](/docs/envgene-objects.md) that have a dot (`.`) in their key to a normalized YAML format.

## Problem

Some parameters use dots in their names (e.g., `database.url`) to describe complex parameters. Not all consumers of such parameters can process them correctly, which can cause issues in processing.

## Migration Steps

1. **Identify parameters with dots in their names**

     ```yaml
     parameters:
       database.url: jdbc:mysql://host/db
       service.port: 8080
     ```

2. **Convert each dotted key into nested YAML objects**

     ```yaml
     parameters:
       database:
         url: jdbc:mysql://host/db
       service:
         port: 8080
     ```

3. **Apply the same change in all relevant places**

## Example Migration

Given this original file:

```yaml
parameters:
  app.env: prod
  logging.level: INFO
```

Migrate to:

```yaml
parameters:
  app:
    env: prod
  logging:
    level: INFO
```

Keep the structure simple. Use nested keys instead of dot-notation.
