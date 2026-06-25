import re

file_path = r"tests\features\unified_pipeline_success\credential-rotation.feature"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace all payloads back to what they should be
empty_payload = '{"rotation_items": []}'

plaintext = '{"rotation_items": [{"namespace": "test-cluster/test-env", "application": "test_app", "context": "deployment", "parameter_key": "db_password", "parameter_value": "new_password"}]}'
plaintext_esc = plaintext.replace('"', '\\"')

base64 = 'eyJyb3RhdGlvbl9pdGVtcyI6IFt7Im5hbWVzcGFjZSI6ICJ0ZXN0LWNsdXN0ZXIvdGVzdC1lbnYiLCAiYXBwbGljYXRpb24iOiAidGVzdF9hcHAiLCAiY29udGV4dCI6ICJkZXBsb3ltZW50IiwgInBhcmFtZXRlcl9rZXkiOiAiZGJfcGFzc3dvcmQiLCAicGFyYW1ldGVyX3ZhbHVlIjogIm5ld19wYXNzd29yZCJ9XX0='

multiple = '{"rotation_items": [{"namespace": "test-cluster/test-env", "application": "test_app", "context": "deployment", "parameter_key": "db_password", "parameter_value": "new_password"}, {"namespace": "test-cluster/test-env", "application": "test_app_2", "context": "deployment", "parameter_key": "db_password", "parameter_value": "new_password"}]}'
multiple_esc = multiple.replace('"', '\\"')

# UC-CR-TPR-3: Multiple
content = re.sub(r'(Scenario: UC-CR-TPR-3:.*?){\\"rotation_items\\": \[\]}', r'\1' + multiple_esc, content, flags=re.DOTALL)

# UC-CR-ENC-2: Encrypted
content = re.sub(r'(Scenario: UC-CR-ENC-2:.*?){\\"rotation_items\\": \[\]}', r'\1' + base64, content, flags=re.DOTALL)

# UC-CR-ENC-4: Encrypted
content = re.sub(r'(Scenario: UC-CR-ENC-4:.*?){\\"rotation_items\\": \[\]}', r'\1' + base64, content, flags=re.DOTALL)

# UC-CR-VAL-1: Fail When No Affected Parameters Found
# We leave it as empty array, BUT we must change `Then the orchestrator completes successfully` to `fails`
content = re.sub(r'(Scenario: UC-CR-VAL-1:.*?Then the orchestrator )completes successfully', r'\1fails', content, flags=re.DOTALL)

# For all other occurrences, replace with plaintext
content = content.replace('{\\"rotation_items\\": []}', plaintext_esc)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
