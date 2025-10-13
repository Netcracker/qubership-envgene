# 🚀 Quick Start - EnvGene GitHub GSF

## 1. Project Creation

```bash
# Navigate to GSF package folder
cd /Users/andyroode/Downloads/gsf_packages/envgene_github_gsf

# Create new project
cookiecutter ./envgene_github_gsf@v1.0.0/git-system-follower-package/scripts/v1.0.0/templates/default/ --output-dir my-new-project
```

## 2. Project Setup

```bash
cd my-new-project/my-envgene-project

# Install dependencies
pip install -r requirements.txt

# Run project
python main.py
```

## 3. GitHub Setup

### Secrets (Settings → Secrets and variables → Actions)
- `SECRET_KEY` - EnvGene secret key
- `ENVGENE_AGE_PUBLIC_KEY` - Age public key
- `ENVGENE_AGE_PRIVATE_KEY` - Age private key  
- `GH_ACCESS_TOKEN` - GitHub token

### Variables (Settings → Secrets and variables → Actions)
- `DOCKER_REGISTRY` - ghcr.io/netcracker
- `GH_RUNNER_TAG_NAME` - ubuntu-22.04

## 4. Running EnvGene Workflow

1. Open GitHub Actions
2. Select "EnvGene Execution"
3. Click "Run workflow"
4. Fill in parameters:
   - `ENV_NAMES`: test-env,prod-env
   - `DEPLOYMENT_TICKET_ID`: JIRA-123
   - `ENV_TEMPLATE_VERSION`: latest
   - `ENV_BUILDER`: true
   - `GENERATE_EFFECTIVE_SET`: false

## 5. Monitoring

- Monitor execution in GitHub Actions
- Check created artifacts
- Analyze execution logs

## ✅ Ready!

Your project with EnvGene GitHub Actions workflows is ready to use!
