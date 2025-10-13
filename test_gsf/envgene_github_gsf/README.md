# 🚀 EnvGene GitHub GSF Package

GSF package for creating projects with EnvGene GitHub Actions workflows integration.

## 📋 Description

This GSF package creates projects with full EnvGene system integration, including:

- **EnvGene GitHub Actions workflows** - automated environment management processes
- **Credential rotation** - automatic credential updates
- **CMDB integration** - configuration management database integration
- **Environment generation** - environment generation and management
- **Effective set generation** - creation of effective configuration sets
- **Git automation** - git operations automation

## 🏗️ Package Structure

```
envgene_github_gsf@v1.0.0/
├── git-system-follower-package/
│   ├── package.yaml
│   └── scripts/
│       └── v1.0.0/
│           ├── init.py
│           ├── update.py
│           ├── delete.py
│           └── templates/
│               └── default/
│                   ├── cookiecutter.json
│                   └── {{cookiecutter.project_name}}/
│                       ├── .github/          # GitHub Actions workflows
│                       │   ├── workflows/
│                       │   │   ├── envgene.yml
│                       │   │   └── pipeline-v1.yml
│                       │   ├── actions/
│                       │   ├── scripts/
│                       │   └── configuration/
│                       ├── main.py
│                       ├── README.md
│                       ├── requirements.txt
│                       └── Dockerfile
```

## 🎯 Features

### EnvGene Workflows

1. **EnvGene Execution** (`.github/workflows/envgene.yml`)
   - Environment generation and management
   - Credential rotation
   - CMDB integration
   - Effective set generation
   - Git operations automation

2. **Pipeline v1** (`.github/workflows/pipeline-v1.yml`)
   - Advanced pipeline with API support
   - Multiple environment processing
   - Artifact management
   - Container-based execution

### Cookiecutter Variables

```json
{
    "project_name": "my-envgene-project",
    "project_description": "A project with EnvGene GitHub Actions workflows",
    "author_name": "Developer",
    "author_email": "developer@example.com",
    "python_version": "3.11",
    "use_docker": "true",
    "use_tests": "true",
    "use_linting": "true",
    "docker_registry": "ghcr.io/netcracker",
    "docker_username": "developer",
    "github_org": "netcracker",
    "env_template_version": "latest",
    "env_builder": "true",
    "generate_effective_set": "false",
    "get_passport": "false",
    "cmdb_import": "false"
}
```

## 🚀 Usage

### 1. Project Creation

```bash
# Using cookiecutter directly
cookiecutter ./envgene_github_gsf@v1.0.0/git-system-follower-package/scripts/v1.0.0/templates/default/ --output-dir my-project

# Or using GSF system
gsf init envgene_github_gsf@v1.0.0 --project-name my-envgene-project
```

### 2. GitHub Setup

After creating the project, you need to configure:

#### GitHub Secrets
- `SECRET_KEY` - secret key for EnvGene
- `ENVGENE_AGE_PUBLIC_KEY` - Age public key
- `ENVGENE_AGE_PRIVATE_KEY` - Age private key
- `GH_ACCESS_TOKEN` - GitHub access token

#### GitHub Variables
- `DOCKER_REGISTRY` - Docker registry (default: ghcr.io/netcracker)
- `GH_RUNNER_TAG_NAME` - runner tag (default: ubuntu-22.04)

### 3. Running Workflows

1. Go to **Actions** section in GitHub
2. Select **EnvGene Execution** workflow
3. Click **Run workflow**
4. Fill in parameters:
   - `ENV_NAMES` - list of environments to process
   - `DEPLOYMENT_TICKET_ID` - Jira ticket ID
   - `ENV_TEMPLATE_VERSION` - environment template version
   - `ENV_BUILDER` - enable environment building
   - `GENERATE_EFFECTIVE_SET` - generate effective sets
   - `GET_PASSPORT` - get cloud passport
   - `CMDB_IMPORT` - import to CMDB

## 🔧 Development

### Local Development

```bash
cd my-envgene-project

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py

# Testing
pytest

# Linting
flake8 .
black .
```

### Docker

```bash
# Build image
docker build -t my-envgene-project .

# Run container
docker run -p 8000:8000 my-envgene-project
```

## 📊 Monitoring

### Workflow Status

- **EnvGene Execution**: Main workflow for environment management
- **Pipeline v1**: Advanced pipeline with API support

### Artifacts

Workflows create the following artifacts:
- `generate_inventory_*` - environment inventory
- `credential_rotation_*` - credential rotation
- `env_build_*` - environment building
- `generate_effective_set_*` - effective sets
- `git_commit_*` - git commits

## 🛠️ Configuration

### Changing Configuration

1. Edit `.github/configuration/config.env`
2. Update `.github/pipeline_vars.env`
3. Configure variables in GitHub

### Customizing Workflows

1. Edit `.github/workflows/envgene.yml`
2. Modify `.github/workflows/pipeline-v1.yml`
3. Add new actions in `.github/actions/`

## 📚 Documentation

- [EnvGene Documentation](https://docs.envgene.com)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com)

## 🤝 Support

For support:
1. Create an issue in the repository
2. Contact the EnvGene team
3. Check GitHub Actions documentation

## 📄 License

This package is part of the EnvGene system and follows Netcracker corporate standards.
