import re

file_path = r"tests\features\unified_pipeline_success\credential-rotation.feature"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('"namespace": "test-cluster/test-env"', '"namespace": "test-env-namespace"')
content = content.replace('\"namespace\": \"test-cluster/test-env\"', '\"namespace\": \"test-env-namespace\"')

# Also for base64:
import base64
plaintext = '{"rotation_items": [{"namespace": "test-env-namespace", "application": "test_app", "context": "deployment", "parameter_key": "db_password", "parameter_value": "new_password"}]}'
base64_str = base64.b64encode(plaintext.encode()).decode()

# Replace the old base64
old_base64 = 'eyJyb3RhdGlvbl9pdGVtcyI6IFt7Im5hbWVzcGFjZSI6ICJ0ZXN0LWNsdXN0ZXIvdGVzdC1lbnYiLCAiYXBwbGljYXRpb24iOiAidGVzdF9hcHAiLCAiY29udGV4dCI6ICJkZXBsb3ltZW50IiwgInBhcmFtZXRlcl9rZXkiOiAiZGJfcGFzc3dvcmQiLCAicGFyYW1ldGVyX3ZhbHVlIjogIm5ld19wYXNzd29yZCJ9XX0='

content = content.replace(old_base64, base64_str)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
