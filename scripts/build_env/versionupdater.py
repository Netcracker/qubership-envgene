import argparse
from envgenehelper import beautifyYaml, openYaml, writeYamlToFile, logger

def update_version(env_definition_path, version_to_add):
    logger.info(f"Started version update to {version_to_add} in {env_definition_path}.")
    data = openYaml(env_definition_path)

    if ":" in version_to_add:
        if 'envTemplate' in data:
            if 'templateArtifact' in data['envTemplate']:
                del data['envTemplate']['templateArtifact']
            data['envTemplate']['artifact'] = version_to_add
        else:
            logger.error(f"Bad env_definition structure in file {env_definition_path}.")
            raise ReferenceError(f"Can't update version in {env_definition_path}. See logs above.")
    else:
        if 'envTemplate' in data and 'templateArtifact' in data['envTemplate'] and 'artifact' in data['envTemplate']['templateArtifact']:
            oldVersion = "undefined"
            if 'version' in data['envTemplate']['templateArtifact']['artifact']:
                oldVersion = data['envTemplate']['templateArtifact']['artifact']['version']
            data['envTemplate']['templateArtifact']['artifact']['version'] = version_to_add
            logger.info(f"Succesfully updated version from {oldVersion} to {version_to_add} in {env_definition_path}")
        else:
            logger.error(f"Bad env_definition structure in file {env_definition_path}.")
            raise ReferenceError(f"Can't update version in {env_definition_path}. See logs above.")
    writeYamlToFile(env_definition_path, data)
    beautifyYaml(env_definition_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--env_definition_path', help="Path to env definition file", type=str)
    parser.add_argument('--version_to_add', help="New version to set", type=str)
    args = parser.parse_args()
    update_version(args.env_definition_path, args.version_to_add)
