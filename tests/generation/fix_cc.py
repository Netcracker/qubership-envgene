import os
import yaml

base_dir = "/workspace/test_data/e2e"

scenarios = {
    "base": {},
    "uc-cc-dp-1": {},
    "uc-cc-dp-2": {},
    "uc-cc-dp-3": {},
    "uc-cc-dp-4": {},
    "uc-cc-mr-1": {
        "cloud": {
            "deployParameters": {"server_port": 8080, "app_version": "3.0", "ssl_enabled": True, "debug_mode": "true"},
            "e2eParameters": {},
            "technicalConfigurationParameters": {}
        },
        "namespace": {
            "deployParameters": {"api_port": "${server_port}", "service_version": "${app_version}", "use_ssl": "${ssl_enabled}", "log_level": "${debug_mode}"},
            "e2eParameters": {},
            "technicalConfigurationParameters": {}
        }
    },
    "uc-cc-mr-2": {
        "cloud": {
            "deployParameters": {
                "database_config": {"connection": {"host": "db.example.com", "port": 5432}},
                "yaml_template": "services:\n  api:\n    image: api:latest\n    ports:\n      - 8080:8080\n"
            },
            "e2eParameters": {},
            "technicalConfigurationParameters": {}
        },
        "namespace": {
            "deployParameters": {"api_config": "${database_config}", "rendered_template": "${yaml_template}"},
            "e2eParameters": {},
            "technicalConfigurationParameters": {}
        }
    },
    "uc-cc-hr-1": {
        "cloud": {
            "deployParameters": {"cloud_api_url": "https://api.example.com"},
            "e2eParameters": {"cloud_test_url": "https://test.example.com"},
            "technicalConfigurationParameters": {"cloud_config_url": "https://config.example.com"}
        },
        "namespace": {
            "deployParameters": {"service_url": "${cloud_api_url}"},
            "e2eParameters": {"test_endpoint": "${cloud_test_url}"},
            "technicalConfigurationParameters": {"config_endpoint": "${cloud_config_url}"}
        }
    },
    "uc-cc-hr-2": {
        "tenant": {
            "deployParameters": {"tenant_id": "acme-corp"},
            "e2eParameters": {"tenant_test_id": "acme-test"},
            "technicalConfigurationParameters": {"tenant_config_id": "acme-config"}
        },
        "namespace": {
            "deployParameters": {"organization": "${tenant_id}"},
            "e2eParameters": {"test_org": "${tenant_test_id}"},
            "technicalConfigurationParameters": {"config_org": "${tenant_config_id}"}
        }
    },
    "uc-cc-hr-3": {
        "tenant": {
            "deployParameters": {"tenant_name": "acme-corp"},
            "e2eParameters": {"tenant_test_name": "acme-test"},
            "technicalConfigurationParameters": {"tenant_config_name": "acme-config"}
        },
        "cloud": {
            "deployParameters": {"cloud_label": "${tenant.tenant_name}"},
            "e2eParameters": {"cloud_test_label": "${tenant.e2e.tenant_test_name}"},
            "technicalConfigurationParameters": {"cloud_config_label": "${tenant.config-server.tenant_config_name}"}
        }
    },
    "uc-cc-hr-4": {
        "namespace": {
            "deployParameters": {"namespace_db_url": "db.acme.com"},
            "e2eParameters": {"namespace_test_url": "test.acme.com"},
            "technicalConfigurationParameters": {"namespace_config_url": "config.acme.com"}
        },
        "cloud": {
            "deployParameters": {"cloud_config": "\\${namespace_db_url}"},
            "e2eParameters": {"cloud_test_config": "\\${namespace_test_url}"},
            "technicalConfigurationParameters": {"cloud_config_param": "\\${namespace_config_url}"}
        }
    },
    "uc-cc-hr-5": {
        "cloud": {
            "deployParameters": {"cloud_region": "us-east-1"},
            "e2eParameters": {"cloud_test_region": "us-west-1"},
            "technicalConfigurationParameters": {"cloud_config_region": "eu-central-1"}
        },
        "tenant": {
            "deployParameters": {"tenant_config": "${cloud_region}"},
            "e2eParameters": {"tenant_test_config": "${cloud_test_region}"},
            "technicalConfigurationParameters": {"tenant_config_param": "${cloud_config_region}"}
        }
    },
    "uc-cc-hr-6": {
        "namespace": {
            "deployParameters": {"namespace_name": "core"},
            "e2eParameters": {"namespace_test_name": "test-core"},
            "technicalConfigurationParameters": {"namespace_config_name": "config-core"}
        },
        "tenant": {
            "deployParameters": {"tenant_label": "${namespace_name}"},
            "e2eParameters": {"tenant_test_label": "${namespace_test_name}"},
            "technicalConfigurationParameters": {"tenant_config_label": "${namespace_config_name}"}
        }
    },
    "uc-cc-cr-1": {
        "namespace": {
            "e2eParameters": {"test_url": "https://test.example.com"},
            "deployParameters": {"service_url": "${test_url}"}
        }
    },
    "uc-cc-cr-2": {
        "namespace": {
            "technicalConfigurationParameters": {"config_url": "https://config.example.com"},
            "deployParameters": {"service_config": "${config_url}"}
        }
    },
    "uc-cc-cr-3": {
        "namespace": {
            "deployParameters": {"api_url": "https://api.example.com"},
            "e2eParameters": {"test_endpoint": "${api_url}"}
        }
    },
    "uc-cc-cr-4": {
        "namespace": {
            "technicalConfigurationParameters": {"config_endpoint": "https://config.example.com"},
            "e2eParameters": {"test_config": "${config_endpoint}"}
        }
    },
    "uc-cc-cr-5": {
        "namespace": {
            "deployParameters": {"deploy_url": "https://deploy.example.com"},
            "technicalConfigurationParameters": {"runtime_config": "${deploy_url}"}
        }
    },
    "uc-cc-cr-6": {
        "namespace": {
            "e2eParameters": {"e2e_endpoint": "https://e2e.example.com"},
            "technicalConfigurationParameters": {"runtime_endpoint": "${e2e_endpoint}"}
        }
    }
}

for d in os.listdir(base_dir):
    if d not in scenarios:
        continue
    
    env_dir = os.path.join(base_dir, d, "environments", "test-cluster", "test-env")
    if not os.path.exists(env_dir):
        os.makedirs(env_dir, exist_ok=True)
    
    cfg = scenarios[d]
    
    cloud_data = {
        "name": "test-cluster_test-env",
        "apiUrl": "api.test-cluster.qubership.org",
        "apiPort": "6443",
        "privateUrl": "cluster.qubership.org",
        "publicUrl": "cluster.qubership.org",
        "dashboardUrl": "https://dashboard.cluster.qubership.org",
        "labels": [],
        "defaultCredentialsId": "cloud-deploy-sa-token",
        "protocol": "https",
        "dbMode": "db",
        "databases": [],
        "productionMode": False,
        "maasConfig": {"enable": False, "maasUrl": "", "maasInternalAddress": "", "credentialsId": ""},
        "vaultConfig": {"enable": False, "url": "", "publicUrl": "", "credentialsId": ""},
        "consulConfig": {"enabled": False, "publicUrl": "", "internalUrl": "", "tokenSecret": ""},
        "deployParameters": cfg.get("cloud", {}).get("deployParameters", {}),
        "e2eParameters": cfg.get("cloud", {}).get("e2eParameters", {}),
        "technicalConfigurationParameters": cfg.get("cloud", {}).get("technicalConfigurationParameters", {})
    }
    with open(os.path.join(env_dir, "cloud.yml"), "w") as f:
        yaml.dump(cloud_data, f)
        
    tenant_data = {
        "name": "test-tenant",
        "registryName": "default",
        "description": "test",
        "owners": "test",
        "gitRepository": "",
        "defaultBranch": "",
        "credential": "",
        "labels": [],
        "deployParameters": cfg.get("tenant", {}).get("deployParameters", {}),
        "globalE2EParameters": {"environmentParameters": cfg.get("tenant", {}).get("e2eParameters", {})},
        "technicalConfigurationParameters": cfg.get("tenant", {}).get("technicalConfigurationParameters", {})
    }
    with open(os.path.join(env_dir, "tenant.yml"), "w") as f:
        yaml.dump(tenant_data, f)
        
    ns_dir = os.path.join(env_dir, "Namespaces", "test-namespace", "Applications")
    os.makedirs(ns_dir, exist_ok=True)
    
    ns_data = {
        "name": "cloud",
        "deployParameters": cfg.get("namespace", {}).get("deployParameters", {}),
        "e2eParameters": cfg.get("namespace", {}).get("e2eParameters", {}),
        "technicalConfigurationParameters": cfg.get("namespace", {}).get("technicalConfigurationParameters", {})
    }
    with open(os.path.join(ns_dir, "cloud.yml"), "w") as f:
        yaml.dump(ns_data, f)

print("Test data updated.")
