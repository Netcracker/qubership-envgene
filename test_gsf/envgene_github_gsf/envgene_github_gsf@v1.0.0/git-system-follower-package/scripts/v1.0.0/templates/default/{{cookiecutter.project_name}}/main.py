#!/usr/bin/env python3
"""
{{cookiecutter.project_name}} - {{cookiecutter.project_description}}

Author: {{cookiecutter.author_name}} <{{cookiecutter.author_email}}>
"""

import sys
import os
from typing import Dict, Any
from datetime import datetime

# Configuration
CONFIG = {
    "project_name": "{{cookiecutter.project_name}}",
    "project_description": "{{cookiecutter.project_description}}",
    "author": "{{cookiecutter.author_name}}",
    "email": "{{cookiecutter.author_email}}",
    "python_version": "{{cookiecutter.python_version}}",
    "use_docker": {{cookiecutter.use_docker|title}},
    "use_tests": {{cookiecutter.use_tests|title}},
    "use_linting": {{cookiecutter.use_linting|title}},
    "docker_registry": "{{cookiecutter.docker_registry}}",
    "docker_username": "{{cookiecutter.docker_username}}",
    "github_org": "{{cookiecutter.github_org}}",
    "env_template_version": "{{cookiecutter.env_template_version}}",
    "env_builder": "{{cookiecutter.env_builder}}",
    "generate_effective_set": "{{cookiecutter.generate_effective_set}}",
    "get_passport": "{{cookiecutter.get_passport}}",
    "cmdb_import": "{{cookiecutter.cmdb_import}}"
}

def print_banner() -> None:
    """Print project banner"""
    print("=" * 70)
    print(f"🚀 {CONFIG['project_name']}")
    print(f"📝 {CONFIG['project_description']}")
    print("=" * 70)

def print_config() -> None:
    """Print project configuration"""
    print("\n📋 Project Configuration:")
    print("-" * 40)
    print(f"Author: {CONFIG['author']} <{CONFIG['email']}>")
    print(f"Python Version: {CONFIG['python_version']}")
    print(f"Docker: {CONFIG['use_docker']}")
    print(f"Tests: {CONFIG['use_tests']}")
    print(f"Linting: {CONFIG['use_linting']}")
    print(f"Docker Registry: {CONFIG['docker_registry']}")
    print(f"Docker Username: {CONFIG['docker_username']}")
    print(f"GitHub Org: {CONFIG['github_org']}")

def print_envgene_config() -> None:
    """Print EnvGene configuration"""
    print("\n🔧 EnvGene Configuration:")
    print("-" * 40)
    print(f"Env Template Version: {CONFIG['env_template_version']}")
    print(f"Env Builder: {CONFIG['env_builder']}")
    print(f"Generate Effective Set: {CONFIG['generate_effective_set']}")
    print(f"Get Passport: {CONFIG['get_passport']}")
    print(f"CMDB Import: {CONFIG['cmdb_import']}")

def print_workflows() -> None:
    """Print available GitHub Actions workflows"""
    print("\n📁 Available EnvGene Workflows:")
    print("-" * 40)
    print("1. .github/workflows/envgene.yml - EnvGene Execution")
    print("   • Environment generation and management")
    print("   • Credential rotation")
    print("   • CMDB integration")
    print("   • Effective set generation")
    print("   • Git commit automation")
    
    print("\n2. .github/workflows/pipeline-v1.yml - Pipeline v1")
    print("   • Advanced pipeline with API support")
    print("   • Multiple environment processing")
    print("   • Artifact management")
    print("   • Container-based execution")
    
    print("\n3. .github/actions/ - Custom Actions")
    print("   • load-env-files - Environment file loading")
    print("   • download_artifact - Artifact management")
    
    print("\n4. .github/scripts/ - Helper Scripts")
    print("   • Environment variable processing")
    print("   • Matrix generation")
    print("   • Variable collection")

def print_ci_status() -> None:
    """Print CI/CD pipeline status"""
    print("\n🔄 CI/CD Pipeline Features:")
    print("-" * 40)
    print("✅ EnvGene GitHub Actions workflows configured")
    print("✅ Environment generation and management")
    print("✅ Credential rotation support")
    print("✅ CMDB integration")
    print("✅ Effective set generation")
    print("✅ Git commit automation")
    print("✅ Artifact management")
    print("✅ Multi-environment processing")
    
    if CONFIG['use_docker']:
        print("✅ Docker image building and pushing")
        print(f"   Registry: {CONFIG['docker_registry']}/{CONFIG['docker_username']}/{CONFIG['project_name']}")

def print_usage_instructions() -> None:
    """Print usage instructions"""
    print("\n🚀 Usage Instructions:")
    print("-" * 40)
    print("1. Push your code to GitHub")
    print("2. Go to Actions tab in GitHub")
    print("3. Run 'EnvGene Execution' workflow manually")
    print("4. Configure environment parameters:")
    print("   • ENV_NAMES: List of environments to process")
    print("   • DEPLOYMENT_TICKET_ID: Jira ticket ID")
    print("   • ENV_TEMPLATE_VERSION: Template version")
    print("   • ENV_BUILDER: Enable environment building")
    print("   • GENERATE_EFFECTIVE_SET: Generate effective sets")
    print("   • GET_PASSPORT: Get cloud passport")
    print("   • CMDB_IMPORT: Import to CMDB")
    print("5. Monitor workflow execution and artifacts")

def main() -> None:
    """Main function"""
    print_banner()
    print_config()
    print_envgene_config()
    print_workflows()
    print_ci_status()
    print_usage_instructions()
    
    print(f"\n🎉 {CONFIG['project_name']} is ready!")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🔗 Next steps:")
    print("1. Configure GitHub secrets (SECRET_KEY, ENVGENE_AGE_*_KEY, etc.)")
    print("2. Set up environment variables in GitHub")
    print("3. Configure Docker registry access")
    print("4. Test EnvGene workflows with sample environments")

if __name__ == "__main__":
    main()
