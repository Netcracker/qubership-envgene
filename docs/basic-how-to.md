# Basic How-To
1. Create your git for templates with structure
```
├── templates
│   ├── env_templates
│   │   ├── namespace1.yml.j2
│   │   ├── namespace2.yml.j2
│   │   ├── tenant1.yml.j2
│   │   ├── cloud1.yml.j2
│   │   ├── template_name1.yml
│   ├──parameters
│   │   ├── paramset1.yml
│   │   ├── paramset2.yml
│   │   ├── parameters_group1
│   │   │   ├── paramset3.yml
│   │   │   ├── paramset4.yml
│   ├──resource_profiles
│   │   ├── resource_profile1.yml
│   │   ├── resource_profile2.yml
```
2. Create your git for instances with structure
```
├── configuration
│   ├── credentials
│   │   ├── credentials.yml
│   ├── deployer.yml
│   ├── registry.yml
├── environments
│   ├── cluster_name1
│   │   ├── cloud-passport
│   │   │   ├── cloud_name1.yml
│   │   │   ├── cloud_name1-creds.yml
│   │   ├── env_name1
│   │   │   ├── Inventory
│   │   │   │   ├── inventory.yml
│   │   │   ├── parameters
│   │   │   │   ├── env_specific_paramset.yml
```

More details are available in samples [ReadME](../samples/README.md).