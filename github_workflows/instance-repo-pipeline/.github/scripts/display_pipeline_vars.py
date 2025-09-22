#!/usr/bin/env python3
"""
Dynamic pipeline variables display script.
Reads all variables from GITHUB_ENV and displays non-empty pipeline-related variables.
"""
import os
import sys


def get_pipeline_variables():
    """
    Read all variables from GITHUB_ENV file or environment variables.
    Returns a dictionary of non-empty pipeline variables.
    """
    variables = {}
    
    # First, try to read from GITHUB_ENV file
    github_env_file = os.getenv("GITHUB_ENV")
    if github_env_file:
        try:
            with open(github_env_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and "=" in line and not line.startswith("#"):
                        try:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Only include non-empty values
                            if value:
                                variables[key] = value
                        except ValueError:
                            print(f"⚠️  Warning: Skipping malformed line {line_num}: {line}")
                            continue
        except FileNotFoundError:
            print(f"⚠️  GITHUB_ENV file not found: {github_env_file}")
        except Exception as e:
            print(f"⚠️  Error reading GITHUB_ENV file: {e}")
    
    # If no variables from file, fall back to environment variables
    if not variables:
        # Get all environment variables
        for key, value in os.environ.items():
            if value and is_pipeline_variable(key):
                variables[key] = value
    
    return variables


def is_pipeline_variable(key):
    """
    Determine if a variable should be displayed.
    Exclude only system/CI variables, include everything else.
    """
    # System variables to exclude (secrets, CI internals, etc.)
    system_vars = {
        # Secrets and credentials
        'SECRET_KEY', 'GITHUB_TOKEN', 'ENVGENE_AGE_PUBLIC_KEY', 'ENVGENE_AGE_PRIVATE_KEY',
        'GH_ACCESS_TOKEN', 'PUBLIC_AGE_KEYS', 'GPG_KEY',
        
        # GitHub Actions internal variables
        'GITHUB_ENV', 'GITHUB_OUTPUT', 'GITHUB_WORKSPACE', 'GITHUB_REPOSITORY', 
        'GITHUB_SHA', 'GITHUB_REF', 'GITHUB_ACTIONS', 'GITHUB_REF_NAME',
        'GITHUB_EVENT_NAME', 'GITHUB_EVENT_PATH', 'GITHUB_HEAD_REF', 'GITHUB_BASE_REF',
        'GITHUB_SERVER_URL', 'GITHUB_API_URL', 'GITHUB_GRAPHQL_URL',
        'GITHUB_USER_EMAIL', 'GITHUB_USER_NAME',
        
        # Runner system variables
        'RUNNER_OS', 'RUNNER_ARCH', 'RUNNER_NAME', 'RUNNER_ENVIRONMENT', 'RUNNER_TOOL_CACHE',
        'RUNNER_TEMP', 'RUNNER_WORKSPACE', 'RUNNER_PERFLOG', 'RUNNER_TRACKING_ID',
        
        # CI system variables
        'CI_COMMIT_REF_NAME', 'CI_PROJECT_DIR',
        
        # Container and system paths
        'HOME', 'PATH', 'SHELL', 'USER', 'LANG', 'PWD', 'OLDPWD',
        'TERM', 'HOSTNAME', 'HOSTTYPE', 'MACHTYPE', 'OSTYPE',
        
        # Python/Node environment
        'PYTHONPATH', 'PYTHON_VERSION', 'NODE_VERSION', 'NPM_VERSION',
        'PIP_CACHE_DIR', 'PIPENV_CACHE_DIR', 'PYTHONDONTWRITEBYTECODE', 
        'PYTHONUNBUFFERED', 'PYTHON_SHA256',
        
        # Common system environment variables
        'DEBIAN_FRONTEND', 'ACCEPT_EULA', 'DOTNET_SKIP_FIRST_TIME_EXPERIENCE',
        'POWERSHELL_DISTRIBUTION_CHANNEL', 'TZ', 'LANG', 'LC_ALL',
        
        # Android development
        'ANDROID_HOME', 'ANDROID_NDK', 'ANDROID_NDK_HOME', 'ANDROID_NDK_LATEST_HOME',
        'ANDROID_NDK_ROOT', 'ANDROID_SDK_ROOT',
        
        # Build tools and development environments
        'ANT_HOME', 'GRADLE_HOME', 'MAVEN_HOME', 'SBT_HOME', 'LEIN_HOME', 'LEIN_JAR',
        'SWIFT_PATH', 'VCPKG_INSTALLATION_ROOT', 'NVM_DIR',
        
        # Java environments
        'JAVA_HOME', 'JAVA_HOME_8_X64', 'JAVA_HOME_11_X64', 'JAVA_HOME_17_X64', 'JAVA_HOME_21_X64',
        
        # Go environments
        'GOROOT_1_22_X64', 'GOROOT_1_23_X64', 'GOROOT_1_24_X64',
        
        # Web drivers and browsers
        'CHROMEWEBDRIVER', 'CHROME_BIN', 'EDGEWEBDRIVER', 'GECKOWEBDRIVER',
        'SELENIUM_JAR_PATH',
        
        # Cloud and Azure
        'AZURE_EXTENSION_DIR',
        
        # System and runtime
        'CI', 'CONDA', 'LOGNAME', 'SHLVL', 'SGX_AESM_ADDR', 'SYSTEMD_EXEC_PID',
        'XDG_CONFIG_HOME', 'XDG_RUNTIME_DIR', 'JOURNAL_STREAM', 'INVOCATION_ID',
        
        # .NET and other development
        'DOTNET_MULTILEVEL_LOOKUP', 'DOTNET_NOLOGO', 'ENABLE_RUNNER_TRACING',
        
        # Package managers
        'PIPX_BIN_DIR', 'PIPX_HOME',
        
        # Homebrew
        'HOMEBREW_CLEANUP_PERIODIC_FULL_DAYS', 'HOMEBREW_NO_AUTO_UPDATE',
        
        # Haskell
        'BOOTSTRAP_HASKELL_NONINTERACTIVE', 'GHCUP_INSTALL_BASE_PREFIX'
    }
    
    # Exclude system/secret variables
    if key in system_vars:
        return False
    
    # Exclude system variable prefixes (but allow specific pipeline ones)
    pipeline_exceptions = {'GITHUB_PIPELINE_API_INPUT'}
    
    if key.startswith(('RUNNER_', 'GITHUB_')) and key not in pipeline_exceptions:
        return False
    
    # Exclude other common system prefixes
    system_prefixes = (
        'ACTIONS_', 'INPUT_', 'ImageOS', 'ImageVersion', 'AGENT_',
        'ANDROID_', 'JAVA_HOME_', 'GOROOT_', 'HOMEBREW_', 'XDG_',
        'DOTNET_', 'PIPX_', 'GHCUP_'
    )
    
    if key.startswith(system_prefixes):
        return False
    
    # Include everything else - this is the dynamic approach!
    return True


def display_variables(show_docker=True, show_pipeline=True):
    """
    Display pipeline variables in organized sections.
    """
    variables = get_pipeline_variables()
    
    if not variables:
        print("No variables found in GITHUB_ENV")
        return
    
    # Separate variables into categories dynamically
    docker_vars = {}
    pipeline_vars = {}
    
    for key, value in variables.items():
        if not is_pipeline_variable(key):
            continue
            
        if key.startswith('DOCKER_IMAGE_') or key == 'DOCKER_REGISTRY':
            docker_vars[key] = value
        else:
            # Everything else goes to pipeline vars - fully dynamic!
            pipeline_vars[key] = value
    
    # Display Docker Images section
    if show_docker and docker_vars:
        print("=== Docker Images ===")
        for key in sorted(docker_vars.keys()):
            print(f"{key} = {docker_vars[key]}")
        print("")
    
    # Display Pipeline Configuration section
    if show_pipeline and pipeline_vars:
        print("=== Pipeline Configuration (All non-empty variables) ===")
        for key in sorted(pipeline_vars.keys()):
            print(f"{key} = {pipeline_vars[key]}")
        print("")
    
    total_count = len(docker_vars) + len(pipeline_vars)
    
    if total_count == 0:
        print("ℹ️  No pipeline variables found to display")
        print("   This could mean:")
        print("   - Variables are not set yet")
        print("   - GITHUB_ENV file is empty or doesn't exist")
        print("   - All variables have empty values")
    # No additional statistics or source information displayed


def main():
    """
    Main function for command-line usage.
    """
    # Parse command line arguments
    show_docker = True
    show_pipeline = True
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--no-docker":
            show_docker = False
        elif sys.argv[1] == "--only-pipeline":
            show_docker = False
        elif sys.argv[1] == "--only-docker":
            show_pipeline = False
        elif sys.argv[1] == "--help":
            print("Usage: python display_pipeline_vars.py [--no-docker|--only-pipeline|--only-docker]")
            print("  --no-docker     : Don't show Docker image variables")
            print("  --only-pipeline : Show only pipeline configuration variables")
            print("  --only-docker   : Show only Docker image variables")
            return
    
    display_variables(show_docker=show_docker, show_pipeline=show_pipeline)


if __name__ == "__main__":
    main()
