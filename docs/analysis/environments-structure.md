
# Environments Structure

- [Environments Structure](#environments-structure)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Option A. Consumer Calculated Environment List](#option-a-consumer-calculated-environment-list)
      - [\[Option A\] Use Cases](#option-a-use-cases)
        - [\[Option A\] `app:ver` Deploy](#option-a-appver-deploy)
        - [\[Option A\] SD Deploy](#option-a-sd-deploy)
    - [Option B. Environments Structure as Separate Object](#option-b-environments-structure-as-separate-object)
      - [\[Option B\] Environments Structure Generation](#option-b-environments-structure-generation)
        - [Generation Option 1](#generation-option-1)
        - [Generation Option 2](#generation-option-2)
        - [On commit Environments Structure generation](#on-commit-environments-structure-generation)
      - [\[Option B\] Use Cases](#option-b-use-cases)
        - [\[Option B\] On-commit Environments Structure generation. New Environment. No artifact download](#option-b-on-commit-environments-structure-generation-new-environment-no-artifact-download)
        - [\[Option B\] On-commit Environments Structure generation. New Environment. Artifact download](#option-b-on-commit-environments-structure-generation-new-environment-artifact-download)
        - [\[Option B\] On-commit Environments Structure generation. Template version change/SNAPSHOT version](#option-b-on-commit-environments-structure-generation-template-version-changesnapshot-version)
        - [\[Option B\] `app:ver` Deploy](#option-b-appver-deploy)
        - [\[Option B\] SD Deploy](#option-b-sd-deploy)
    - [Options Comparison](#options-comparison)

## Problem Statement

The EnvGene Instance repository keeps information about:

- Site structure: which Environments exist in the site
- Environment structure: which namespaces are in each Environment and what roles (deployPostfix) they have

External systems need this information, for example, to show a list of available Environments in a UI so a user can start operations on them.

EnvGene is the main source of this information and must provide it.

Getting this information should not require specifying a particular Environment name.

## Proposed Approach

### Option A. Consumer Calculated Environment List

**The list of environments** in the site (Instance repository) is calculated by the EnvGene consumer system. It determines the list by scanning the folder names where inventory files are located, using a command like:

`find . -type f -name 'env_definition.yml' | sed 's|.*/environments/\(.*\)/Inventory/env_definition\.yml|\1|'`

**The mapping of namespace name to deploy postfix** is stored in the Effective Set of a specific Environment, in the [`environments`](/docs/calculator-cli.md#version-20topology-context-environments-example) variable of the [topology](/docs/calculator-cli.md#version-20-topology-context) context.

#### [Option A] Use Cases

##### [Option A] `app:ver` Deploy

   1. The user opens the Environment selection view in the orchestrating deploy pipeline
   2. The orchestrating deploy pipeline retrieves the list of Environments in EnvGene Instance repository:
      1. Searches for the list of Environments using the file structure pattern:  
         `find . -type f -name 'env_definition.yml' | sed 's|.*/environments/\(.*\)/Inventory/env_definition\.yml|\1|'`
   3. The Environment selection view displays the full list of Environments
   4. The user selects an Environment
   5. The user specifies:
      1. Namespace
      2. `app:ver` of Application
   6. The orchestrating deploy pipeline generates [useDeployPostfixAsNamespace SD](https://github.com/Netcracker/qubership-envgene/blob/feature/deploypostfix-as-sd/docs/sd-processing.md#usedeploypostfixasnamespace-handling)
   7. The orchestrating deploy pipeline triggers EnvGene to calculate the Effective Set
      1. Passing useDeployPostfixAsNamespace SD
   8. EnvGene generates the Environment Instance
   9. EnvGene [transforms](https://github.com/Netcracker/qubership-envgene/blob/feature/deploypostfix-as-sd/docs/sd-processing.md#usedeploypostfixasnamespace-handling) useDeployPostfixAsNamespace SD into a SD with deployPostfix
   10. EnvGene generates the Effective Set (including the [`environments`](/docs/calculator-cli.md#version-20topology-context-environments-example) variable as part of the pipeline context)
   11. The orchestrating deploy pipeline retrieves the Effective Set
   12. The orchestrating deploy pipeline generates the deploy SD (deploy-sd calculates deployment waves for deploy-app)

##### [Option A] SD Deploy

   1. The user opens the Environment selection view in the orchestrating deploy pipeline
   2. The orchestrating deploy pipeline retrieves the list of Environments in EnvGene Instance repository:
      1. Searches for the list of Environments using the file structure pattern:  
         `find . -type f -name 'env_definition.yml' | sed 's|.*/environments/\(.*\)/Inventory/env_definition\.yml|\1|'`
   3. The Environment selection view displays the full list of Environments
   4. The user selects an Environment
   5. The user specifies:
      1. SD
   6. The orchestrating deploy pipeline triggers EnvGene to calculate the effective set,
      1. Passing SD with deployPostfix
   7. EnvGene generates the Environment Instance
   8. EnvGene generates the Effective Set (including the [`environments`](/docs/calculator-cli.md#version-20topology-context-environments-example) variable as part of the pipeline context)
   9. The orchestrating deploy pipeline retrieves the Effective Set
   10. The orchestrating deploy pipeline generates the deploy SD (deploy-sd calculates deployment waves for deploy-app)

### Option B. Environments Structure as Separate Object

The Instance repository contains the Environments Structure object, which describes all Environments in the site. For each Environment, it lists the namespaces, and for each namespace, it shows the deploy postfix.

The Environments Structure is stored in the Instance repository at `/environments/environment-structure.yml`.

The structure of the object is as follows (each field is mandatory):

```yaml
environments:
  <cluster-name>/<environment-name>:
    namespaces:
      <namespace-name>:
        deployPostfix: <deploy-postfix>
```

Example:

```yaml
environments:
  cluster-01/env-1:
    namespaces:
      env-1-core:
        deployPostfix: core
      env-1-bss:
        deployPostfix: bss
  cluster-01/env-2:
    namespaces:
      env-2-core:
        deployPostfix: core
      env-2-bss:
        deployPostfix: bss
  cluster-02/env-1:
    namespaces:
      core:
        deployPostfix: core
      oss:
        deployPostfix: oss
```

#### [Option B] Environments Structure Generation

For each Environment in the repository, the Environments Structure object enumerates the namespaces, and for each namespace, specifies the deploy postfix.

- The namespace name is derived from the `name` attribute of the Namespace object within the Environment Instance.
- The deploy postfix is determined by the name of the namespace folder in the Environment Instance.

Triggers for initiating the Environment Structure generation:

   1. Upon a commit to the EnvGene Instance repository
   2. As part of the Environment Instance generation process, at its conclusion

##### Generation Option 1

1. Identify the list of Environments that match the following conditions:

   a. The Environment Inventory exists, but there are no namespace folders  
   b. The Environment Inventory exists, and the `artifact` field contains `-SNAPSHOT`  
   c. The Environment Inventory exists, there are namespace folders, and the template version has changed (compare `generateEnvironmentLatestVersion` and `artifact`)  
   d. All other cases

2. For these Environments, perform the following actions:

   a. For such an Environment, download the template artifact and extract the namespaces and deploy postfixes  
   b. For such an Environment, download the template artifact and extract the namespaces and deploy postfixes  
   c. For such an Environment, resolve the SNAPSHOT, download the template artifact, and extract the namespaces and deploy postfixes  
   d. For such an Environment, do nothing

3. Using the information from step 2, generate the complete Environments Structure

##### Generation Option 2

   1. Identify the list of Environments that match the following conditions:

       a. The Environment Inventory exists, but there are no namespace folders
       c. The Environment Inventory exists, and namespace folders exist

   2. For these Environments, perform the following actions:

       a. For such an Environment, generate an incomplete Environments Structure:

        ```yaml
        environments:
          cluster-01/env-1:
            namespaces: {}
        ```

       c. For such an Environment, generate a complete Environments Structure:

        ```yaml
        environments:
          cluster-01/env-1:
            namespaces:
              env-1-core:
                deployPostfix: core
              env-1-bss:
                deployPostfix: bss
        ```

##### On commit Environments Structure generation

The Environments Structure is generated by the Instance on-commit pipeline. This pipeline runs automatically on every push to the remote repository. It does not require any extra actions from the user or external systems, and does not need extra configuration.

During this pipeline, the generated object is saved by committing it to the Instance repository. On each new generation, the previous Environments Structure is replaced with the new one.

#### [Option B] Use Cases

##### [Option B] On-commit Environments Structure generation. New Environment. No artifact download

   1. User creates Environment Inventory for a new Environment (optional)
   2. User pushes changes to the EnvGene Instance repository
   3. [On-commit pipeline](#on-commit-environments-structure-generation) regenerates the Environments Structure
      1. For the new Environment (Inventory exists, but no namespace folders), the Environments Structure will NOT contain namespaces:

          ```yaml
          environments:
            cluster-01/env-1:
              namespaces: {}
          ```

      2. For already generated Environments, the Environments Structure will contain namespaces:

          ```yaml
          environments:
            cluster-01/env-1:
              namespaces:
                env-1-core:
                  deployPostfix: core
                env-1-bss:
                  deployPostfix: bss
          ```

##### [Option B] On-commit Environments Structure generation. New Environment. Artifact download

   1. User creates Environment Inventory for a new Environment (optional)
   2. User pushes changes to the EnvGene Instance repository
   3. On-commit pipeline regenerates the Environments Structure
      1. For the new Environment (Inventory exists, but no namespace folders)
         1. Pipeline downloads the template artifact and reads namespaces from it (does not generate the Environment, just reads from the template)
      2. Generates a complete Environments Structure for all Environments, including the new one

##### [Option B] On-commit Environments Structure generation. Template version change/SNAPSHOT version

   1. User changes the number of namespaces or `deployPostfix` in the template
   2. User pushes changes to the EnvGene Instance repository (sets new template version)
   3. On-commit pipeline regenerates the Environments Structure
      1. For all Environments where the template version changed or is a SNAPSHOT
         1. Pipeline downloads the template artifact and reads namespaces from it (does not generate the Environment, just reads from the template)
      2. Generates a complete Environments Structure for all Environments

##### [Option B] `app:ver` Deploy

   1. The user opens the Environment selection view in the orchestrating deploy pipeline
   2. The orchestrating deploy pipeline retrieves the list of Environments in EnvGene Instance repository:
      1. Gets `/environments/environment-structure.yml`
   3. The Environment selection view displays the full list of Environments
   4. User selects an Environment
      1. Если для этого энва сгенерировалась complete Environments Structure, то неймспейс можно выбрать из списка
   5. User specifies:
      1. Namespace
      2. `app:ver` of Application
   6. The orchestrating deploy pipeline generates [useDeployPostfixAsNamespace SD](https://github.com/Netcracker/qubership-envgene/blob/feature/deploypostfix-as-sd/docs/sd-processing.md#usedeploypostfixasnamespace-handling)
   7. The orchestrating deploy pipeline triggers EnvGene to calculate the Effective Set
      1. Passing useDeployPostfixAsNamespace SD
   8. EnvGene generates the Environment Instance
   9. EnvGene [transforms](https://github.com/Netcracker/qubership-envgene/blob/feature/deploypostfix-as-sd/docs/sd-processing.md#usedeploypostfixasnamespace-handling) useDeployPostfixAsNamespace SD into a SD with deployPostfix
   10. EnvGene generates the Effective Set (including the [`environments`](/docs/calculator-cli.md#version-20topology-context-environments-example) variable as part of the pipeline context)
   11. The orchestrating deploy pipeline retrieves the Effective Set
   12. The orchestrating deploy pipeline generates the deploy SD (deploy-sd calculates deployment waves for deploy-app)

##### [Option B] SD Deploy

   1. The user opens the Environment selection view in the orchestrating deploy pipeline
   2. The orchestrating deploy pipeline retrieves the list of Environments in EnvGene Instance repository:
      1. Gets `/environments/environment-structure.yml`
   3. The Environment selection view displays the full list of Environments
   4. User selects an Environment
   5. The user specifies:
      1. SD
   6. The orchestrating deploy pipeline triggers EnvGene to calculate the effective set,
      1. Passing SD with deployPostfix
   7. EnvGene generates the Environment Instance
   8. EnvGene generates the Effective Set (including the [`environments`](/docs/calculator-cli.md#version-20topology-context-environments-example) variable as part of the pipeline context)
   9. The orchestrating deploy pipeline retrieves the Effective Set
   10. The orchestrating deploy pipeline generates the deploy SD (deploy-sd calculates deployment waves for deploy-app)

### Options Comparison

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A**  | Fast, simple, but no mapping for UI | - Does not increase the execution time of the Instance repository pipeline<br>- Does not require any implementation in EnvGene | - Does not allow the user to see the current mapping of namespace to deployPostfix |
| **B1** | Not always up-to-date mapping for UI |  | - Increases the execution time of **each** pipeline run:<br> • to spawning a job (~10-15 seconds)<br> • calculating the structure (~1 second)<br>- Does not allow the user to see the current mapping of namespace to deployPostfix for:<br> • new Environments<br> • Environments where the template structure has changed<br>- Requires implementation in EnvGene |
| **B2** | Always up-to-date mapping for UI. Most complete, but slowest | - Allows the user to see the current mapping of namespace to deployPostfix | - Increases the execution time of **each** pipeline run:<br> • to spawning a job (~10-15 seconds)<br> • downloading each SNAPSHOT or changed artifact (up to 5 seconds per artifact)<br> • calculating the structure (~1 second)<br>- Requires implementation in EnvGene |
