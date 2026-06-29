import os
import shutil
import yaml

base_dir = "/workspace/test_data/e2e/base"
e2e_dir = "/workspace/test_data/e2e"

def copy_base(name):
    target = os.path.join(e2e_dir, name)
    if os.path.exists(target):
        shutil.rmtree(target)
    shutil.copytree(base_dir, target)
    return target

def write_yaml(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if 'version' not in data:
        data = {'version': '1.0', **data}
    if 'cloud' not in data:
        data['cloud'] = {}
        
    # Ensure all required keys for cloud_passport.py are present in cloud
    if 'cloud' in data:
        required_keys = [
            "CLOUD_API_HOST", "CLOUD_API_PORT", "CLOUD_PRIVATE_HOST", 
            "CLOUD_PUBLIC_HOST", "CLOUD_DASHBOARD_URL", "CLOUD_DEPLOY_TOKEN",
            "CLOUD_PROTOCOL", "PRODUCTION_MODE"
        ]
        for key in required_keys:
            if key not in data['cloud']:
                data['cloud'][key] = "dummy-value"
                
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False)
        
    # generate credentials file right next to it
    basename = os.path.basename(path)
    name_without_ext = os.path.splitext(basename)[0]
    dirname = os.path.dirname(path)
    creds_path = os.path.join(dirname, f"{name_without_ext}-creds.yml")
    with open(creds_path, 'w', encoding='utf-8') as f:
        yaml.dump({
            "dummy_cred": {
                "type": "usernamePassword",
                "data": {
                    "username": "foo",
                    "password": "bar"
                }
            }
        }, f, sort_keys=False)

def update_env_def(target_dir, cp_val=None):
    env_def_path = os.path.join(target_dir, "environments", "test-cluster", "test-env", "Inventory", "env_definition.yml")
    with open(env_def_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if cp_val:
        if 'inventory' not in data:
            data['inventory'] = {}
        data['inventory']['cloudPassport'] = cp_val
        
    with open(env_def_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False)

# uc_cp_1_base (Auto-inherit cluster passport)
t1 = copy_base("uc_cp_1_base")
write_yaml(os.path.join(t1, "environments", "test-cluster", "cloud-passport", "test-cluster.yml"), {
    "version": "1.5",
    "cloud": {"test_passport_key": "auto-inherited-value"}
})
update_env_def(t1) 

# uc_cp_2_base (Explicitly named passport)
t2 = copy_base("uc_cp_2_base")
write_yaml(os.path.join(t2, "environments", "test-cluster", "cloud-passport", "custom-passport.yml"), {
    "version": "2.0",
    "cloud": {"test_passport_key": "explicit-value"}
})
update_env_def(t2, "custom-passport")

# uc_cp_3_base (No passport exists)
t3 = copy_base("uc_cp_3_base")
update_env_def(t3)

# uc_cp_4_base (Custom location passport)
t4 = copy_base("uc_cp_4_base")
write_yaml(os.path.join(t4, "environments", "cloud-passports", "my-custom-passport.yml"), {
    "version": "1.1",
    "cloud": {"test_passport_key": "custom-location-value"}
})
update_env_def(t4, "my-custom-passport")

# uc_cp_6_base (Mixed cluster, business auto-associate)
t6 = copy_base("uc_cp_6_base")
write_yaml(os.path.join(t6, "environments", "test-cluster", "cloud-passport", "test-cluster.yml"), {
    "version": "1.0",
    "bss": {"some_key": "business-value"}
})
write_yaml(os.path.join(t6, "environments", "test-cluster", "cloud-passport", "test-cluster-infra.yml"), {
    "version": "1.0",
    "infra": {"some_key": "infra-value"}
})
update_env_def(t6)

# uc_cp_7_base (Mixed cluster, infra explicit)
t7 = copy_base("uc_cp_7_base")
write_yaml(os.path.join(t7, "environments", "test-cluster", "cloud-passport", "test-cluster.yml"), {
    "version": "1.0",
    "bss": {"some_key": "business-value"}
})
write_yaml(os.path.join(t7, "environments", "test-cluster", "cloud-passport", "test-cluster-infra.yml"), {
    "version": "1.0",
    "infra": {"some_key": "infra-value"}
})
update_env_def(t7, "test-cluster-infra")

# uc_cp_8_base (Mixed cluster, infra auto-associate fails)
t8 = copy_base("uc_cp_8_base")
write_yaml(os.path.join(t8, "environments", "test-cluster", "cloud-passport", "test-cluster.yml"), {
    "version": "1.0",
    "bss": {"some_key": "business-value-that-fails-infra"}
})
update_env_def(t8)

print("Test data created successfully.")
