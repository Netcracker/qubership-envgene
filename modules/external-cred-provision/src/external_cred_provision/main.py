import logging
import sys
import click

from external_cred_provision.provisioner import ExternalCredProvisioner


def setup_logging(log_level: str = "INFO") -> None:
    from qubership_pipelines_common_library.v1.utils.utils_logging import ColoredFormatter

    level = getattr(logging, log_level.upper(), logging.INFO)
    full_log_format = '[%(asctime)s] [%(levelname)-5s] [class=%(filename)s:%(lineno)-3s] %(message)s'
    module_log_format = '[%(asctime)s] [%(levelname)-5s] %(message)s'

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(module_log_format))
    console_handler.setLevel(level)

    module_file_handler = logging.FileHandler("module.log", encoding="utf-8")
    module_file_handler.setFormatter(logging.Formatter(module_log_format))
    module_file_handler.setLevel(level)

    full_file_handler = logging.FileHandler("full.log", encoding="utf-8")
    full_file_handler.setFormatter(logging.Formatter(full_log_format))
    full_file_handler.setLevel(logging.DEBUG)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(full_file_handler)

    package_logger = logging.getLogger("external_cred_provision")
    package_logger.setLevel(level)
    package_logger.addHandler(console_handler)
    package_logger.addHandler(module_file_handler)


@click.command()
@click.argument("context_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--dry-run", is_flag=True, default=False, help="Validate without writing to any store.")
@click.option("--log-level", default="DEBUG", show_default=True,
              type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
              help="Log level for console and module.log (full.log is always DEBUG)")
def cli(context_file: str, dry_run: bool, log_level: str) -> None:
    """Provision external credentials defined in CONTEXT_FILE."""
    setup_logging(log_level=log_level)
    provider = ExternalCredProvisioner(context_path=context_file, dry_run=dry_run)
    raise SystemExit(provider.run())
