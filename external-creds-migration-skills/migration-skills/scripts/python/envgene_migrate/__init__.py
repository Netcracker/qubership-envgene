"""EnvGene External Credentials migration CLI (kit-local package).

Run from this kit::

    set PYTHONPATH=<kit>/python
    python -m envgene_migrate plan --repo=template
    python -m envgene_migrate apply --repo=instance

Depends on envgenehelper (crypt, yaml) when available; falls back to ruyaml/stdlib.
Delegates Secret Store I/O to external-cred-provision (instance apply only).
"""

__version__ = "0.1.0"
