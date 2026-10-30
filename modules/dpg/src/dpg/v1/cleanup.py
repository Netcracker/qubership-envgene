import base64
import logging
import os
import re
import shutil
import tempfile
from pathlib import Path

import yaml
from git import Actor, Repo
from qubership_pipelines_common_library.v1.execution.exec_command import ExecutionCommand
from qubership_pipelines_common_library.v2.secret_manager.providers.multi_store_provider import MultiStoreProvider
from qubership_pipelines_common_library.v2.sops.sops_client import SopsClient


CONTEXTS = ("deployment", "runtime")


def clean_namespaces(effective_set: Path, namespace_names: str = "") -> None:
    mappings = {}
    for context in CONTEXTS:
        mapping_path = effective_set / context / "mapping.yaml"
        mappings[context] = yaml.safe_load(mapping_path.read_text()) if mapping_path.is_file() else {}
        mappings[context] = mappings[context] or {}
    namespaces = list(dict.fromkeys(filter(None, re.split(r"[;,\s]+", namespace_names))))
    if not namespaces:
        namespaces = sorted(set().union(*(mapping.keys() for mapping in mappings.values())))

    for namespace in namespaces:
        found = False
        for context, mapping in mappings.items():
            if namespace not in mapping:
                continue
            found = True
            # Mapping values use repository paths; namespace folders can differ from their names.
            folder = Path(mapping[namespace]).name
            context_dir = effective_set / context
            namespace_dir = context_dir / folder
            if (not folder or folder in (".", "..") or namespace_dir.is_symlink()
                    or not namespace_dir.resolve().is_relative_to(context_dir.resolve())):
                raise ValueError(f"Invalid effective set mapping for namespace '{namespace}'")
            if not namespace_dir.is_dir():
                logging.warning("Namespace '%s' is absent from effective set context '%s'", namespace, context)
                continue
            marker = namespace_dir / ".cleaned"
            if marker.exists():
                logging.warning("Namespace '%s' is already cleaned in context '%s'", namespace, context)
            for application in namespace_dir.iterdir():
                if application.is_dir() and not application.is_symlink():
                    for content in application.iterdir():
                        if content.is_dir() and not content.is_symlink():
                            shutil.rmtree(content)
                        else:
                            content.unlink()
                    # Git needs a tracked file to preserve the application directory.
                    (application / ".gitkeep").touch()
                else:
                    application.unlink()
            marker.touch()
        if not found:
            logging.warning("Namespace '%s' is absent from the effective set", namespace)

    cleanup_context = effective_set / "cleanup"
    if cleanup_context.is_dir() and not cleanup_context.is_symlink():
        shutil.rmtree(cleanup_context)
    else:
        cleanup_context.unlink(missing_ok=True)


def read_repository_config(rootdir: Path, environment_id: str) -> dict:
    effective_set = rootdir / "environments" / environment_id / "effective-set"
    params = {}
    secure_params = {}
    for context in ("pipeline", "topology"):
        context_dir = effective_set / context
        params_path = context_dir / "parameters.yaml"
        if params_path.is_file():
            params.update(yaml.safe_load(params_path.read_text()) or {})
        credentials_path = context_dir / "credentials.yaml"
        if credentials_path.is_file():
            credentials = yaml.safe_load(credentials_path.read_text()) or {}
            if "sops" in credentials:
                credentials = SopsClient(rootdir).get_decrypted_content_by_path(
                    os.getenv("ENVGENE_AGE_PRIVATE_KEY", ""), credentials_path)
                if isinstance(credentials, str):
                    credentials = yaml.safe_load(credentials)
                if not credentials or "sops" in credentials:
                    raise ValueError(f"Cannot decrypt {credentials_path}")
            secure_params.update(credentials)
    for name in ("DCL_CONFIG_GITLAB_USER", "DCL_CONFIG_GITLAB_TOKEN"):
        value = secure_params.get(name) or params.get(name)
        if isinstance(value, str) and value.startswith("ref+"):
            value = MultiStoreProvider().read_secret(value)
        params[name] = value
    for name in ("DCL_GIT_URL", "DCL_GIT_BRANCH"):
        if not params.get(name):
            raise ValueError(f"{name} is required in the committed effective set")
    return params


def cleanup_repository(rootdir: Path, environment_id: str, namespace_names: str, commit_message: str) -> None:
    _update_repository(rootdir, environment_id, commit_message,
                       lambda effective_set: clean_namespaces(effective_set, namespace_names), mirror=True)


def remove_cleaned_markers(effective_set: Path, namespaces: set[str]) -> None:
    for context in CONTEXTS:
        remote_mapping_file = effective_set / context / "mapping.yaml"
        if not remote_mapping_file.is_file():
            continue
        remote_mapping = yaml.safe_load(remote_mapping_file.read_text()) or {}
        for namespace in namespaces & remote_mapping.keys():
            folder = Path(remote_mapping[namespace]).name
            if not folder or folder in (".", ".."):
                raise ValueError(f"Invalid effective set mapping for namespace '{namespace}'")
            remote_dir = effective_set / context / folder
            if not (remote_dir / ".cleaned").is_file():
                continue
            if (remote_dir.is_symlink() or not remote_dir.resolve().is_relative_to(
                    (effective_set / context).resolve())):
                raise ValueError(f"Invalid effective set mapping for namespace '{namespace}'")
            if not any(path.is_file() and path.name not in (".cleaned", ".gitkeep")
                       for path in remote_dir.rglob("*")):
                raise ValueError(f"No published application content for previously cleaned namespace '{namespace}'")
            (remote_dir / ".cleaned").unlink()


def finalize_deployment(rootdir: Path, environment_id: str, namespaces: set[str]) -> None:
    if not namespaces:
        return

    # The publisher has already written the application content. Only its cleanup signal changes here.
    _update_repository(rootdir, environment_id, f"Finalize deployed namespaces for {environment_id}",
                       lambda effective_set: remove_cleaned_markers(effective_set, namespaces))


def _update_repository(rootdir, environment_id, commit_message, update, mirror=False):
    config = read_repository_config(rootdir, environment_id)
    url = config["DCL_GIT_URL"]
    branch = config["DCL_GIT_BRANCH"]
    git_env = {"GIT_TERMINAL_PROMPT": "0"}
    token = config.get("DCL_CONFIG_GITLAB_TOKEN")
    if token:
        username = config.get("DCL_CONFIG_GITLAB_USER") or "oauth2"
        auth = base64.b64encode(f"{username}:{token}".encode()).decode()
        git_env.update({
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": f"http.{url}.extraHeader",
            "GIT_CONFIG_VALUE_0": f"Authorization: Basic {auth}",
        })
    relative_es = Path("environments") / environment_id / "effective-set"
    with tempfile.TemporaryDirectory(prefix="es-cleanup-") as checkout:
        with Repo.clone_from(url, checkout, branch=branch, depth=1, single_branch=True, env=git_env) as repo:
            effective_set = Path(checkout) / relative_es
            update(effective_set)
            if effective_set.is_dir():
                repo.git.add("--all", "--", relative_es.as_posix())
            if repo.index.diff("HEAD"):
                actor = Actor(os.getenv("GITLAB_USER_NAME") or os.getenv("GITHUB_ACTOR") or "EnvGene",
                              os.getenv("GITLAB_USER_EMAIL") or os.getenv("GITHUB_USER_EMAIL") or "envgene@localhost")
                repo.index.commit(commit_message, author=actor, committer=actor)
                with repo.git.custom_environment(**git_env):
                    repo.remote().push(f"HEAD:refs/heads/{branch}").raise_if_error()
            # Keep local artifacts aligned with the remote ES without replacing pipeline configuration.
            for context in (*CONTEXTS, "cleanup") if mirror else ():
                source = effective_set / context
                destination = rootdir / relative_es / context
                if destination.exists():
                    shutil.rmtree(destination)
                if source.is_dir():
                    shutil.copytree(source, destination)


class CleanupStructure(ExecutionCommand):
    def _validate(self):
        return self.context.validate(["params.environment_id", "params.commit_message"])

    def _execute(self):
        environment_id = self.context.input_param_get("params.environment_id")
        if (Path(environment_id).is_absolute() or len(Path(environment_id).parts) != 2
                or any(part in (".", "..") for part in Path(environment_id).parts)):
            raise ValueError(f"Invalid environment ID '{environment_id}'")
        cleanup_repository(
            Path(self.context.input_param_get("params.rootdir", os.getcwd())),
            environment_id,
            self.context.input_param_get("params.namespace_names", ""),
            self.context.input_param_get("params.commit_message"),
        )
