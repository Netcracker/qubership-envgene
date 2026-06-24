import ruyaml
yaml = ruyaml.main.YAML()
result = yaml.load("")
print("Result of empty load:", repr(result))
print("Type of result:", type(result))
