pipeline {
    agent {
        docker {
            image 'ghcr.io/netcracker/qubership-envgene:latest'
            args '-u root'
        }
    }
    
    environment {
        ENV_TEMPLATES_REPO = 'https://github.com/your-org/env-templates.git'
        ENV_INSTANCES_REPO = 'https://github.com/your-org/env-instances.git'
        
        // Use credentials for private repositories
        // GIT_AUTH_CREDS = credentials('github-auth-token')
        
        BDD_DATA_DIR = "${env.WORKSPACE}/test_data"
        PYTHONPATH = "${env.WORKSPACE}"
    }
    
    stages {
        stage('Prepare Test Data') {
            steps {
                sh '''
                    echo "Preparing test data directories..."
                    mkdir -p $BDD_DATA_DIR/templates $BDD_DATA_DIR/instances
                    
                    # Example for Private Repository with credentials:
                    # git clone https://${GIT_AUTH_CREDS_USR}:${GIT_AUTH_CREDS_PSW}@github.com/your-org/env-templates.git $BDD_DATA_DIR/templates
                    
                    # Example for Public Repository:
                    git clone $ENV_TEMPLATES_REPO $BDD_DATA_DIR/templates
                    git clone $ENV_INSTANCES_REPO $BDD_DATA_DIR/instances
                '''
            }
        }
        
        stage('Run All Pytest Scenarios') {
            steps {
                sh '''
                    pytest tests/ -v -s --junitxml=reports/all_tests.xml
                '''
            }
            post {
                always {
                    junit 'reports/*.xml'
                }
            }
        }
    }
}
