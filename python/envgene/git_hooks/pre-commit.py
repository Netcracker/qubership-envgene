#!/usr/bin/env python
from pathlib import Path
from os import getenv, environ
import subprocess
import sys
import logging
import click
logging.basicConfig(
    format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level=logging.INFO)

ENVGENE_AGE_PUBLIC_KEY_ID = "ENVGENE_AGE_PUBLIC_KEY"
ENVGENE_AGE_PRIVATE_KEY_ID = "ENVGENE_AGE_PRIVATE_KEY"
PUBLIC_AGE_KEYS_ID = "PUBLIC_AGE_KEYS"
SECRET_KEY_ID = "SECRET_KEY"


@click.group(chain=True)
def cli():
    pass


def get_file_content(path: Path):
    if path.exists():
        return path.read_text()
    logging.info(f'Couldn\'t find {path}')
    return ""


@cli.command('decrypt')
@click.option('--key_file_path', '-f', 'file_path', default="", help="Path to file with creds")
def decrypt_repo(file_path):
    environ[ENVGENE_AGE_PRIVATE_KEY_ID] = get_file_content(Path(file_path))
    environ[PUBLIC_AGE_KEYS_ID] = 'valueIsSet'
    environ[ENVGENE_AGE_PUBLIC_KEY_ID] = 'valueIsSet'
    environ[SECRET_KEY_ID] = get_file_content(
        Path('./.git/SECRET_KEY.txt'))
    import envgenehelper

    envgenehelper.crypt.decrypt_all_cred_files_for_env()


class PreCommit:
    # Init variables from files if exists
    @staticmethod
    def init_vars():
        if not getenv(SECRET_KEY_ID, ""):
            environ[SECRET_KEY_ID] = get_file_content(
                Path('./.git/SECRET_KEY.txt'))
        if not getenv(ENVGENE_AGE_PUBLIC_KEY_ID, ""):
            environ[PUBLIC_AGE_KEYS_ID] = get_file_content(
                Path('./.git/PUBLIC_AGE_KEYS.txt'))
        environ[ENVGENE_AGE_PUBLIC_KEY_ID] = 'valueIsSet'
        environ[ENVGENE_AGE_PRIVATE_KEY_ID] = 'valueIsSet'

    def encrypt_repo():
        PreCommit.init_vars()
        import envgenehelper
        try:
            envgenehelper.crypt.encrypt_all_cred_files_for_env()
        except Exception as e:
            print(e)


def main():
    if 'decrypt' in sys.argv:
        cli()
    else:
        PreCommit.encrypt_repo()
    subprocess.run('git add .')


if __name__ == "__main__":
    raise SystemExit(main())
