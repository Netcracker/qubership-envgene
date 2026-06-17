
TO DO:

1. **Describe how to export credentials from JCS** T
2. **Validate approach via migration a project** T
3. **Describe deploycli usage for export**
4. **How to export RP via deploycli**
5. **Add information about how to map an environment to a region**
   1. Pavel Karpievich
6. **Create Application Definitions for templates automatically** E
   1. Sergei Yashin
7. **What should the template descriptor be like to include SaaS best practices?**

OQ:

1. Should all environments of one project be in one instance repo, or split per region?
2. Should we change the naming pattern of namespaces if it's not the default one?
3. What do we do with dev/prod baselines?
   1. Make both versions at once
   2. Or
   3. Only dev, add prod later
4. Как в автоматизации обработать "ненужные" сущности CMDB **E**
5. **JOB-IMPORT** Читана проверит
6. ресурс профайл оверрайд Читана проверит
7. композит стракча
8. бг домен
9. апликейшен, под клаудом и нс
10. что с маасом/дбаасом

Phase 1

Step 1

1. Get template, instance repos from `<these sources>`

Step 2 - Create template

1. Identify environments from the Solution Descriptors (could be more than one) **M**
   1. An environment = the set of namespaces (deployPostfix) that one Solution Descriptor deploys into
2. For each unique set of deploy postfixes, create an env template that includes:
   1. Namespace template for each namespace - use `<this>` template as is
      1. Rename the template file (j2 file) to match deploy postfix
      2. Change the name to {env-name}-`<deployPostfix>` [!!!] What if another naming pattern is required?
   2. Cloud template - use `<this>` template as is
      1. Do not modify it
   3. Tenant template - use as is
      1. Do not modify it
   4. Template descriptor
      1. Write it like this `<principle>`
3. Copy from central git app and reg def by SD
   1. Transform them according to [doc](https://github.com/Netcracker/qubership-envgene/blob/main/docs/how-to/app-reg-defs-add-to-template.md)
4. In the cloud CMDB, create an Application Definition for the env-template artifact, so the cloud can resolve and download the template

Step 3 - Create env inventory

1. Export configuration from CMDB Tenant via `<tool>`
2. Find env configurations in CMDB **M**
   1. For each cloud, list all namespaces under it
   2. One Solution Descriptor = one env; group by deployPostfix set to determine the number of envs
3. For each identified env
   1. Create env_definition at `<this path>` with `<this content>`
   2. If there are deployment/e2e/technical parameters for the cloud:
      1. Put them into param sets (one per context) `<here>`, link them in env_definition `<like this>`
   3. If a resource profile override is linked to the cloud:
      1. Put it in the repo `<here>`, link it in env_definition `<like this>`
   4. If param sets are linked to the cloud:
      1. Put them in the repo `<here>`, link them in env_definition `<like this>`
   5. Take `<these>` parameters from the cloud and put in the cloud passport [!!!] Controversial, maybe in phase 2
   6. For each namespace in the env:
      1. If namespace has deployment/e2e/technical parameters
         1. Put them into param sets (one per context) `<here>`, link them in env_definition `<like this>`
      2. If resource profile override is linked to the namespace
         1. Put it in the repo `<here>`, link it in env_definition `<like this>`
      3. If param sets are linked to the namespace
          1. Put them in the repo `<here>`, link them in env_definition `<like this>`
4. Export creds from tenant `<like this>`, put `<here>`, link them in env_definition `<like this>`
5. Put SD into the repo `<here>`

Step 4 - Test

1. Run effective set generation to check everything with `<parameters>`
2. ...

Phase 2 - Refactor parameters [!!!] Do later

1. Replace multiline strings with YAML
2. Find all cloud passport parameters in param sets and move them to the cloud passport
3. Review parameters in param sets and divide into groups:
   1. Template ones - common for all environments, for onsite and offsite - move them to template param set
   2. Env-specific on repo/cluster/env level
4. Describe sensitive parameters using envgene cred macros
5. ...
6. TBD