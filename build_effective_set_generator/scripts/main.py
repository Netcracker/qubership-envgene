import click
from envgenehelper import encrypt_all_cred_files_for_env, decrypt_all_cred_files_for_env


@click.group(chain=True)
def crypt_manager():
    pass


@crypt_manager.command("decrypt_cred_files")
def decrypt_cred_files():
    decrypt_all_cred_files_for_env()


@crypt_manager.command("encrypt_cred_files")
def encrypt_cred_files():
    encrypt_all_cred_files_for_env()


if __name__ == "__main__":
    crypt_manager()
