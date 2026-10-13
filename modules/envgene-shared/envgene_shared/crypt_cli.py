import os
import click

from envgene_shared.crypto.crypt import encrypt_file, decrypt_file, encrypt_all_cred_files_for_env, \
    decrypt_all_cred_files_for_env


@click.group()
def cli():
    """Credential encryption/decryption CLI."""
    pass


@cli.command("decrypt_cred_file")
@click.option("-f", "--file", "file_path", required=True, 
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    help="Path to the credential file to decrypt.")
@click.option("-s", "--secret-key", default=None, envvar="SECRET_KEY",
    help="Secret key. Defaults to the SECRET_KEY environment variable.")
@click.option("-k", "--age-private-key", default=None, envvar="ENVGENE_AGE_PRIVATE_KEY",
    help="Age private key. Defaults to the ENVGENE_AGE_PRIVATE_KEY environment variable.")
@click.option("-p", "--age-public-key", default=None, envvar="PUBLIC_AGE_KEYS",
    help="Age public key. Defaults to the PUBLIC_AGE_KEYS environment variable.")
def decrypt_cred_file(file_path, secret_key, age_private_key, age_public_key):
    set_crypto_env_vars(secret_key, age_private_key, age_public_key)
    decrypt_file(file_path)


@cli.command("encrypt_cred_file")
@click.option("-f", "--file", "file_path", required=True, 
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    help="Path to the credential file to decrypt.")
@click.option("-s", "--secret-key", default=None, envvar="SECRET_KEY",
    help="Secret key. Defaults to the SECRET_KEY environment variable.")
@click.option("-k", "--age-private-key", default=None, envvar="ENVGENE_AGE_PRIVATE_KEY",
    help="Age private key. Defaults to the ENVGENE_AGE_PRIVATE_KEY environment variable.")
@click.option("-p", "--age-public-key", default=None, envvar="PUBLIC_AGE_KEYS",
    help="Age public key. Defaults to the PUBLIC_AGE_KEYS environment variable.")
@click.option("-jsd", "--json-schemas-dir", "json_schemas_dir", default=None, envvar="JSON_SCHEMAS_DIR",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=str),
    help="Path to the JSON schemas directory. Defaults to the JSON_SCHEMAS_DIR environment variable.")
def encrypt_cred_file(file_path, secret_key, age_private_key, age_public_key, json_schemas_dir):
    set_crypto_env_vars(secret_key, age_private_key, age_public_key, json_schemas_dir)
    encrypt_file(file_path)


@cli.command("decrypt_all")
@click.option("-s", "--secret-key", default=None, envvar="SECRET_KEY",
    help="Secret key. Defaults to the SECRET_KEY environment variable.")
@click.option("-k", "--age-private-key", default=None, envvar="ENVGENE_AGE_PRIVATE_KEY",
    help="Age private key. Defaults to the ENVGENE_AGE_PRIVATE_KEY environment variable.")
@click.option("-p", "--age-public-key", default=None, envvar="PUBLIC_AGE_KEYS",
    help="Age public key. Defaults to the PUBLIC_AGE_KEYS environment variable.")
def decrypt_all(secret_key, age_private_key, age_public_key):
    set_crypto_env_vars(secret_key, age_private_key, age_public_key)
    decrypt_all_cred_files_for_env()


@cli.command("encrypt_all")
@click.option("-s", "--secret-key", default=None, envvar="SECRET_KEY",
    help="Secret key. Defaults to the SECRET_KEY environment variable.")
@click.option("-k", "--age-private-key", default=None, envvar="ENVGENE_AGE_PRIVATE_KEY",
    help="Age private key. Defaults to the ENVGENE_AGE_PRIVATE_KEY environment variable.")
@click.option("-p", "--age-public-key", default=None, envvar="PUBLIC_AGE_KEYS",
    help="Age public key. Defaults to the PUBLIC_AGE_KEYS environment variable.")
@click.option("-jsd", "--json-schemas-dir", "json_schemas_dir", default=None, envvar="JSON_SCHEMAS_DIR",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=str),
    help="Path to the JSON schemas directory. Defaults to the JSON_SCHEMAS_DIR environment variable.")
def encrypt_all(secret_key, age_private_key, age_public_key, json_schemas_dir):
    set_crypto_env_vars(secret_key, age_private_key, age_public_key, json_schemas_dir)
    encrypt_all_cred_files_for_env()

def set_crypto_env_vars(secret_key, age_private_key, age_public_key, json_schemas_dir=None):
    if secret_key is not None:
        os.environ["SECRET_KEY"] = secret_key
    if age_private_key is not None:
        os.environ["ENVGENE_AGE_PRIVATE_KEY"] = age_private_key
    if age_public_key is not None:
        os.environ["PUBLIC_AGE_KEYS"] = age_public_key
    if json_schemas_dir is not None:
        os.environ["JSON_SCHEMAS_DIR"] = json_schemas_dir

if __name__ == "__main__":
    cli()