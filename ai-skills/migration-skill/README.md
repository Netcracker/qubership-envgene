# EnvGene External Credentials Migration Skills

The skills guide the user through migration and each time suggest one next action.

## Main workflow

Run:

```text
/envgene-instance-external-credentials-migration
```

The skill:

1. analyses all Environment Instances;
2. suggests the first non-prod Environment Instance;
3. identifies Cloud Passport, Shared Credentials, and related Environment Instances;
4. directs you to the Template Repository;
5. guides you through Secret Store, Shared, Cloud Passport, and System Credentials;
6. checks matching `credId` values;
7. prepares TEMPORARY and PERSISTENT parameters;
8. never runs a pipeline or deployment on its own;
9. updates a short report and suggests one next action.

## Template Repository

Run:

```text
/envgene-template-external-credentials-migration
```

The skill:

- works with one Environment Template;
- determines the structure of each Credential from references;
- does not determine structure from the `credId` name;
- does not assign the same `properties` to all Credentials;
- does not duplicate Credentials from Cloud Passport or Shared Credentials;
- validates `credId` against the Secret Store type;
- creates one Credential Template;
- adds `external_credential_template`;
- replaces local references only in `deployParameters` and `e2eParameters`;
- keeps built-in references as strings;
- does not run publication on its own.

## Other skills

- `envgene-external-credentials-validator` - validates changes, TEMPORARY result, deployment, and PERSISTENT.
- `envgene-external-credentials-analyzer` - optional read-only overview of the Instance Repository.

## Working with Credential files

When changing Shared, Cloud Passport, and System Credential files, the skill:

- uses only `credId`, `type`, and field names;
- converts `usernamePassword` to an external Credential with `username`, `password`;
- converts `secret` to an external Credential without `properties`;
- removes `data`;
- does not output or copy values;
- does not add `create` for existing Credentials;
- does not edit generated `Credentials/credentials.yml`.

## Manual user actions

The user manually:

- confirms the first non-prod Environment Instance;
- chooses a resolution for Shared Credentials and Cloud Passports shared by multiple Environment Instances;
- specifies `remoteRefPath` if it is not yet agreed;
- confirms that secrets exist in the external store;
- runs the template build pipeline;
- runs TEMPORARY and PERSISTENT pipelines;
- performs a test deployment;
- reports the result or provides a link.

## Report

All skills use:

```text
external-credentials-migration-report.md
```

The report contains the selected group, a short checklist, only necessary questions, and one next action.
