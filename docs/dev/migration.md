
TO DO:

1. What should the template descriptor be like to include SaaS best practices?
   1. Consult with Vitya/Ganesh.
2. Validate approach via migration a project
3. Validate blanks
   1. Import into CMDB should not fail
   2. Effective set generation should not fail
4. What do we do with dev/prod baselines?
   1. Make both versions at once
   2. Or
   3. Only dev, add prod later

OQ:

1. Should all environments of one project be in one instance repo, or split per region?
2. Should we change the naming pattern of namespaces if it's not the default one?
3. Do we use Cloud Passport in Phase 3 or 4?

Phase 1

Step 1

1. Get template, instance repos from `<these sources>`

Step 2 - Create template

1. Identify solution/env topology (could be more than one) [!!!] Is this too complex? **M**
   1. Topology = the list of namespaces that are part of the env
2. For each unique solution topology, create an env template that includes:
   1. Namespace template for each namespace - use `<this>` template as is
      1. Rename the template file (j2 file) to match deploy postfix
      2. Change the name to {env-name}-`<deployPostfix>` [!!!] What if another naming pattern is required?
      <!-- 3. Set resource profile baseline + an empty override [!!!] (this is a workaround for a bug) -->
   2. Cloud template - use `<this>` template as is
      1. Do not modify it
   3. Tenant template - use as is
      1. Do not modify it
   4. Template descriptor
      1. Write it like this `<principle>`
3. **App Reg def**

Step 3 - Create env inventory

1. Export configuration from CMDB Tenant via `<tool>`
2. Find env configurations in CMDB **M**
   1. For each cloud, list all namespaces under it
   2. Based on namespace list and topology, determine the number of envs
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
   1. **handle built-in creds**
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