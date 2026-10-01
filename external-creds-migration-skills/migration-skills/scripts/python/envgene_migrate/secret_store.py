"""Re-export for documented import path (logic lives in instance.secret_store)."""

from .instance.secret_store import (  # noqa: F401
    SecretStoreError,
    read_secret_stores,
    write_secret_stores,
)

__all__ = ("SecretStoreError", "read_secret_stores", "write_secret_stores")
