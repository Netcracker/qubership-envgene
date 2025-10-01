# Simple Template Creation Guide

## Description

This guide explains the process of setting up a simple template in the Template repository.

## Prerequisites

1. **Template Repository**  
   - The Template repository should already be created.

2. **Folder Structure**  
   - Ensure the following folder structure exists in the Template repository:

   ```plaintext
   ├── templates
   │   ├── env_templates
   ```

## Flow

1. **Create `simple_template.yaml` (template descriptor)**

Place this file inside the `/templates/env_templates` directory in the template repository with the following content:

**`simple_template.yaml`**

```yaml
tenant: "{{ templates_dir }}/env_templates/simple_template/tenant.yml.j2"
cloud: "{{ templates_dir }}/env_templates/simple_template/cloud.yml.j2"
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/simple_template/Namespaces/core.yml.j2"
```  

- This file describes the overall template structure: Tenant, Cloud, Namespaces, etc.

2. **Create a folder named `simple_template` inside `/templates/env_templates`**

   - Create the following `.yml.j2` files within it:
     - [`tenant.yml.j2`](../samples/templates/env_templates/composite/tenant.yml.j2)
     - [`cloud.yml.j2`](../samples/templates/env_templates/composite/cloud.yml.j2)

3. **Create a `Namespaces` folder inside `/templates/env_templates/simple_template`**

4. **Inside the `Namespaces` folder, create the following `.yml.j2` file:**

   - [`core.yml.j2`](../samples/templates/env_templates/composite/namespaces/core.yml.j2)

5. **Push changes to Git feature/simple-template branch**

### Results

Template repository has the following environment template structure:

```plaintext
/templates/env_templates/
       |_simple_template.yaml
       |_simple_template
              |_Namespaces
                     |_core.yml.j2
              |_cloud.yml.j2
              |_tenant.yml.j2
```

 The Simple Environment Template has been created and built. This means a zip archive containing the Environment Template is available in Artifactory, which can be used to create the Environment Inventory. [EnvGene][UC][EM] Creating Environment Inventory.

## Troubleshooting

### Common Issues

1. **Pipeline Fails with Authentication Error**
   - Verify that your GitLab token has the correct permissions.
   - Check that the token has not expired.

2. **Build failed due to pati_cred configuration missing**
   - Verify that the `PATI_USER` and `PATI_PASSWORD` are correctly configured in CI/CD variables.

### Getting Help

If you encounter issues not covered in this guide, check pipeline logs or contact the support team.
