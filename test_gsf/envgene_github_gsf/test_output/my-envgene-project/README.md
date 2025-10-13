# my-envgene-project

A project with EnvGene GitHub Actions workflows

## 🚀 Features

- **EnvGene Integration** - Full EnvGene workflow support
- **GitHub Actions** - Automated CI/CD with EnvGene workflows
- **Docker Support** - Containerized application deployment
- **Environment Management** - Automated environment generation and management
- **Security** - Credential rotation and CMDB integration

## 👨‍💻 Author

- **Name**: Developer
- **Email**: developer@example.com

## 🛠️ Tech Stack

- **Python**: 3.11
- **Docker**: Containerized deployment
- **EnvGene**: Environment management system
- **GitHub Actions**: CI/CD automation

## 📋 Prerequisites

- Python 3.11
- Docker
- GitHub Actions access
- EnvGene system access

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd my-envgene-project

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Docker

```bash
# Build the Docker image
docker build -t developer/my-envgene-project .

# Run the container
docker run -p 8000:8000 developer/my-envgene-project
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


```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html
```


## 🔧 Development

### Code Quality


```bash
# Lint code
flake8 .

# Format code
black .
```


## 🚀 CI/CD Pipeline

This project uses GitHub Actions with EnvGene integration:

### Workflow Configuration

- **Docker Registry**: ghcr.io/netcracker
- **Docker Username**: developer
- **GitHub Organization**: netcracker
- **Env Template Version**: latest

### EnvGene Parameters

- **Env Builder**: true
- **Generate Effective Set**: false
- **Get Passport**: false
- **CMDB Import**: false

## 📊 Project Status

![EnvGene](https://github.com/netcracker/my-envgene-project/workflows/EnvGene%20Execution/badge.svg)
![Pipeline](https://github.com/netcracker/my-envgene-project/workflows/Pipeline%20v1/badge.svg)

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
