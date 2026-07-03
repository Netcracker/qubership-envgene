import os
import glob

def replace_in_files(directory):
    for filepath in glob.glob(directory + '/**/*.yml', recursive=True) + glob.glob(directory + '/**/*.yaml', recursive=True):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'envgeneNullValue' in content:
            new_content = content.replace('"envgeneNullValue"', '"dummy-value"').replace('envgeneNullValue', 'dummy-value')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {filepath}")

replace_in_files('test_data')
