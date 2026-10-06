import logging
import os
import secrets
import yaml

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from qubership_pipelines_common_library.v2.secret_manager.providers.multi_store_provider import MultiStoreProvider
from qubership_pipelines_common_library.v2.secret_manager.secret_manager import SecretManager
from qubership_pipelines_common_library.v2.sops.sops_client import SopsClient


logger = logging.getLogger(__name__)


class PasswordGenerator:
    CHARS = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "-_.:/()[]{}<>"
        "@#%+=,;~&*|^`?!"
    )
    DEFAULT_LENGTH = 16

    @classmethod
    def generate(cls, length=DEFAULT_LENGTH) -> str:
        return "".join(secrets.choice(cls.CHARS) for _ in range(length))


class Strategy(Enum):
    FAIL_IF_ABSENT    = "fail_if_absent"
    CREATE_IF_ABSENT  = "create_if_absent"
    OVERWRITE = "overwrite"


VALID_STRATEGIES = {st.value for st in Strategy}
WRITE_STRATEGIES = {Strategy.CREATE_IF_ABSENT.value, Strategy.OVERWRITE.value}


@dataclass
class CredentialEntry:
    id: str
    vals: str
    strategy: Strategy
    data: dict[str, str] | str | None
    provider_type: str
    store_id: str | None


@dataclass
class ProvisioningResult:
    created:      int = 0
    overwritten:  int = 0
    skipped:      int = 0
    verified:     int = 0
    failed:       int = 0
    dry_run_ok:   int = 0
    dry_run_fail: int = 0


class ExternalCredProvisioner:

    GENERATE_MARKER      = "_generateValue"
    _DEFAULT_STORE_LABEL = "default-store"  # used only in log messages; it has NO effect on env-var prefix
    _DICT_ONLY_STORES    = frozenset({"vault", "openbao"})

    def __init__(self, context_path: str, dry_run: bool = False) -> None:
        self.context_path = context_path
        self.dry_run = dry_run
        self._credentials: list[CredentialEntry] = []
        self._stores: dict[tuple[str, str], str] = {}
        self._provider: MultiStoreProvider | None = None
        self._manager: SecretManager | None = None

    def run(self) -> int:
        mode = "DRY-RUN" if self.dry_run else "APPLY"
        logger.info(f"Starting {mode} provisioning from '{self.context_path}'")

        try:
            self._load_context()
        except Exception as exc:
            logger.error(f"Failed to load context: {exc}")
            return 1

        if not self._preflight():
            return 1

        result = self._dry_run_phase() if self.dry_run else self._processing_phase()
        self._print_summary(result)

        if self.dry_run:
            return 0 if result.dry_run_fail == 0 else 1
        return 0 if result.failed == 0 else 1

    def _load_context(self) -> None:
        with open(self.context_path) as fh:
            ctx = yaml.safe_load(fh)

        if not ctx or not isinstance(ctx, dict):
            raise ValueError(f"Invalid context file: {self.context_path}")

        if SopsClient.is_encrypted(ctx):
            ctx = self._decrypt_context()

        errors: list[str] = []
        for cred_id, entry in (ctx.get("credentials") or {}).items():
            cred, cred_errors = self._parse_credential(cred_id, entry)
            if cred_errors:
                errors.extend(cred_errors)
                continue
            label = cred.store_id or self._DEFAULT_STORE_LABEL
            self._stores.setdefault((cred.provider_type, label), cred.vals)
            self._credentials.append(cred)

        if errors:
            raise ValueError("Invalid credential entries in context file:\n" + "\n".join(errors))
        logger.info(f"Loaded {len(self._credentials)} credential(s)")

    def _decrypt_context(self) -> dict:
        age_key = os.environ.get("SOPS_AGE_KEY")
        if not age_key:
            raise ValueError("Context file is SOPS-encrypted but SOPS_AGE_KEY for decryption is not set")
        logger.info(f"Context file '{self.context_path}' is SOPS-encrypted, decrypting...")
        client = SopsClient(sops_artifact_configs_folder_path=None)
        decrypted = client.get_decrypted_content_by_path(
            age_private_key=age_key,
            source_file_path_to_decrypt=Path(self.context_path),
        )
        if not decrypted:
            raise ValueError(f"SOPS decryption failed for '{self.context_path}'")
        result = yaml.safe_load(decrypted)
        if not result or not isinstance(result, dict):
            raise ValueError(f"Decrypted content of '{self.context_path}' is not a valid YAML mapping")
        return result

    @staticmethod
    def _parse_credential(cred_id: str, entry: dict) -> tuple[CredentialEntry | None, list[str]]:
        errors: list[str] = []
        provider_type, store_id = None, None
        if "vals" not in entry:
            errors.append(f"  [{cred_id}] missing required field 'vals'")
        else:
            try:
                provider_type, store_id = MultiStoreProvider.parse_provider_type(entry["vals"])
            except ValueError as exc:
                errors.append(f"  [{cred_id}] invalid 'vals': {exc}")
        if "strategy" not in entry:
            errors.append(f"  [{cred_id}] missing required field 'strategy'")
        elif entry["strategy"] not in VALID_STRATEGIES:
            errors.append(f"  [{cred_id}] unknown strategy '{entry['strategy']}'")
        if "data" not in entry:
            if entry.get("strategy") in WRITE_STRATEGIES:
                errors.append(f"  [{cred_id}] missing required field 'data'")
        elif isinstance(entry["data"], str) and provider_type in ExternalCredProvisioner._DICT_ONLY_STORES:
            errors.append(f"  [{cred_id}] plain-string data is not supported for '{provider_type}' - use named fields instead")
        elif not isinstance(entry["data"], (str, dict)):
            errors.append(f"  [{cred_id}] 'data' must be a string or a dict, got {type(entry['data']).__name__!r}")
        if errors:
            return None, errors
        return CredentialEntry(
            id=cred_id,
            vals=entry["vals"],
            strategy=Strategy(entry["strategy"]),
            data=entry.get("data"),
            provider_type=provider_type,
            store_id=store_id,
        ), []

    def _preflight(self) -> bool:
        logger.info("Pre-flight: authenticating to stores...")
        try:
            self._provider = MultiStoreProvider()
            self._manager = SecretManager(secret_provider=self._provider)
        except Exception as exc:
            logger.error(f"Pre-flight: failed to initialise provider: {exc}")
            return False

        ok = True
        for (provider_type, store_label), sample_path in self._stores.items():
            try:
                self._provider.with_provider(sample_path)
                logger.info(f"  + '{store_label}' ({provider_type})")
            except Exception as exc:
                logger.error(f"  x '{store_label}' ({provider_type}): {exc}")
                ok = False
        return ok

    def _processing_phase(self) -> ProvisioningResult:
        result = ProvisioningResult()
        for cred in self._credentials:
            try:
                outcome = self._apply_credential(cred)
                logger.info(f"[{cred.id}] {outcome}")
                match outcome:
                    case "created":     result.created += 1
                    case "overwritten": result.overwritten += 1
                    case "skipped":     result.skipped += 1
                    case "verified":    result.verified += 1
            except Exception as exc:
                logger.error(f"[{cred.id}] FAILED: {type(exc).__name__}: {exc}")
                result.failed += 1
        return result

    def _apply_credential(self, cred: CredentialEntry) -> str:
        exists = self._secret_exists(cred.vals)

        match cred.strategy:
            case Strategy.FAIL_IF_ABSENT:
                if not exists:
                    raise RuntimeError(f"absent at '{cred.vals}'")
                return "verified"

            case Strategy.CREATE_IF_ABSENT:
                if exists:
                    return "skipped"
                self._write_secret(cred, overwrite=False)
                return "created"

            case Strategy.OVERWRITE:
                if exists:
                    self._write_secret(cred, overwrite=True)
                    return "overwritten"
                self._write_secret(cred, overwrite=False)
                return "created"

    def _dry_run_phase(self) -> ProvisioningResult:
        result = ProvisioningResult()
        for cred in self._credentials:
            try:
                self._check_credential_dry_run(cred)
                logger.info(f"[{cred.id}] dry_run_ok")
                result.dry_run_ok += 1
            except Exception as exc:
                logger.error(f"[{cred.id}] dry_run_fail: {type(exc).__name__}: {exc}")
                result.dry_run_fail += 1
        return result

    def _check_credential_dry_run(self, cred: CredentialEntry) -> None:
        exists = self._secret_exists(cred.vals)  # raises on auth/connectivity errors for all strategies

        match cred.strategy:
            case Strategy.FAIL_IF_ABSENT:
                if not exists:
                    raise RuntimeError(f"absent at '{cred.vals}' (required by fail_if_absent)")

            case Strategy.CREATE_IF_ABSENT | Strategy.OVERWRITE:
                # The exists call above is sufficient as a connectivity/auth check
                # Currently, no reliable way to check specific path's write permission across all providers
                pass

    def _secret_exists(self, path: str) -> bool:
        return self._manager.secret_exists(path=path)

    def _write_secret(self, cred: CredentialEntry, overwrite: bool) -> None:
        payload = self._resolve_data(cred.data)
        if overwrite:
            self._manager.update_secret(path=cred.vals, data=payload)
        else:
            self._manager.create_secret(path=cred.vals, data=payload)

    def _print_summary(self, result: ProvisioningResult) -> None:
        if self.dry_run:
            logger.info(
                "Summary (dry-run): "
                f"dry_run_ok={result.dry_run_ok}, "
                f"dry_run_fail={result.dry_run_fail}"
            )
        else:
            logger.info(
                "Summary: "
                f"created={result.created}, "
                f"overwritten={result.overwritten}, "
                f"skipped={result.skipped}, "
                f"verified={result.verified}, "
                f"failed={result.failed}"
            )

    def _resolve_data(self, data: dict[str, str] | str) -> dict[str, str] | str:
        if isinstance(data, str):
            return PasswordGenerator.generate() if data == self.GENERATE_MARKER else data
        return {
            key: PasswordGenerator.generate() if val == self.GENERATE_MARKER else val
            for key, val in data.items()
        }
