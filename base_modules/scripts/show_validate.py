#!/usr/bin/env python3

import yaml
import glob
import argparse
from prettytable import PrettyTable, ALL

parser = argparse.ArgumentParser(description="Get variables from repository")
parser.add_argument("-p", "--path", dest="dest_dir", type=str, help='Path to folder validation')
parser.add_argument("-n", "--name", dest="place_validation", type=str, help='Module name')
args = parser.parse_args()


header = ['Module name', 'Place of validation', 'Validation status']
table = PrettyTable(header, align='l')
table._max_width = {'Module name' : 20, 'Place of validation' : 20, 'Validation status' : 90}
table.hrules = ALL
yaml_file = []
if args.place_validation:
    with open(f"{args.dest_dir}/{args.place_validation}_validation.yaml", "r") as report:
    #with open(f"dvm_validation.yaml", "r") as file:
        yaml_file = yaml.safe_load(report)
    for module in yaml_file:
        table.add_row([module['module_name'], module['place_of_validation'], module['validation_status']])
else:
    file_list = glob.glob(f"{args.dest_dir}/*_validation.yaml")
    for file in file_list:
        with open(file, "r") as report:
            yaml_content = yaml.safe_load(report)
            for module in yaml_content:
                yaml_file.append(module)
    for module in yaml_file:
        if len(module['validation_status'].split("\n"))>1:
            messages = ''
            for error in module['validation_status'].split("\n")[1:]:
                if error:
                    messages = messages + "\n\033[33m"+error.split(':')[0]+":\033[39m"+":".join(error.split(':')[1:])
            module['validation_status'] = module['validation_status'].split("\n")[0] + messages
        table.add_row([module['module_name'], module['place_of_validation'], module['validation_status']])
print(table)

