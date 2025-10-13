# {{cookiecutter.project_name}}

{{cookiecutter.project_description}}

## 🚀 Features

- **EnvGene Integration** - Full EnvGene workflow support
- **GitHub Actions** - Automated CI/CD with EnvGene workflows
- **Docker Support** - Containerized application deployment
- **Environment Management** - Automated environment generation and management
- **Security** - Credential rotation and CMDB integration

## 👨‍💻 Author

- **Name**: {{cookiecutter.author_name}}
- **Email**: {{cookiecutter.author_email}}

## 🛠️ Tech Stack

- **Python**: {{cookiecutter.python_version}}
- **Docker**: Containerized deployment
- **EnvGene**: Environment management system
- **GitHub Actions**: CI/CD automation

## 📋 Prerequisites

- Python {{cookiecutter.python_version}}
- Docker
- GitHub Actions access
- EnvGene system access

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd {{cookiecutter.project_name}}

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Docker

```bash
# Build the Docker image
docker build -t {{cookiecutter.docker_username}}/{{cookiecutter.project_name}} .

# Run the container
docker run -p 8000:8000 {{cookiecutter.docker_username}}/{{cookiecutter.project_name}}
```

## 🔄 EnvGene Workflows

This project includes EnvGene GitHub Actions workflows:

### Available Workflows

1. **EnvGene Execution** (`.github/workflows/envgene.yml`)
   - Environment generation and management
   - Credential rotation
   - CMDB integration
   - Effective set generation

2. **Pipeline v1** (`.github/workflows/pipeline-v1.yml`)
   - Advanced pipeline with API support
   - Multiple environment processing
   - Artifact management

### Workflow Features

- **Environment Management**: Generate and manage multiple environments
- **Credential Rotation**: Automated credential updates
- **CMDB Integration**: Configuration management database integration
- **Effective Set Generation**: Generate effective configuration sets
- **Git Integration**: Automated git commits and artifact management

## 🧪 Testing

{% if cookiecutter.use_tests == "true" %}
```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html
```
{% endif %}

## 🔧 Development

### Code Quality

{% if cookiecutter.use_linting == "true" %}
```bash
# Lint code
flake8 .

# Format code
black .
```
{% endif %}

## 🚀 CI/CD Pipeline

This project uses GitHub Actions with EnvGene integration:

### Workflow Configuration

- **Docker Registry**: {{cookiecutter.docker_registry}}
- **Docker Username**: {{cookiecutter.docker_username}}
- **GitHub Organization**: {{cookiecutter.github_org}}
- **Env Template Version**: {{cookiecutter.env_template_version}}

### EnvGene Parameters

- **Env Builder**: {{cookiecutter.env_builder}}
- **Generate Effective Set**: {{cookiecutter.generate_effective_set}}
- **Get Passport**: {{cookiecutter.get_passport}}
- **CMDB Import**: {{cookiecutter.cmdb_import}}

## 📊 Project Status

![EnvGene](https://github.com/{{cookiecutter.github_org}}/{{cookiecutter.project_name}}/workflows/EnvGene%20Execution/badge.svg)
![Pipeline](https://github.com/{{cookiecutter.github_org}}/{{cookiecutter.project_name}}/workflows/Pipeline%20v1/badge.svg)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📚 EnvGene Documentation

For more information about EnvGene workflows and configuration, see:
- [EnvGene Documentation](https://docs.envgene.com)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
