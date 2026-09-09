"""Resolve Jenkins basic-auth credentials from environment or CLI overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass

from migration_cli.errors import ValidationError

DEFAULT_JENKINS_URL = "https://jenkins.example.com"


@dataclass(frozen=True)
class JenkinsAuth:
    username: str
    token: str


def normalize_jenkins_url(url: str) -> str:
    return url.rstrip("/")


def is_default_jenkins_url(url: str) -> bool:
    return normalize_jenkins_url(url) == DEFAULT_JENKINS_URL


def resolve_jenkins_auth(
    *,
    jenkins_url: str,
    username: str | None = None,
    token: str | None = None,
    username_env: str | None = None,
    token_env: str | None = None,
) -> JenkinsAuth:
    """Resolve username and token for Jenkins API calls.

    When ``jenkins_url`` is the default URL (``DEFAULT_JENKINS_URL``), ``CLOUD_USERNAME``
    and ``CLOUD_TOKEN`` are used unless explicit overrides are supplied.

    For any other URL, ``JENKINS_USERNAME`` and ``JENKINS_TOKEN`` are required unless
    explicit overrides or ``*_env`` names are supplied.
    """
    if username is not None and token is not None:
        return JenkinsAuth(username=username, token=token)

    if is_default_jenkins_url(jenkins_url):
        user_var = username_env or "CLOUD_USERNAME"
        token_var = token_env or "CLOUD_TOKEN"
        resolved_user = username or os.environ.get(user_var)
        resolved_token = token or os.environ.get(token_var)
        if not resolved_user:
            raise ValidationError(
                f"{user_var} is not set. Add it in CI/CD variables or pass --username."
            )
        if not resolved_token:
            raise ValidationError(
                f"{token_var} is not set. Add it in CI/CD variables or pass --token."
            )
        return JenkinsAuth(username=resolved_user, token=resolved_token)

    user_var = username_env or "JENKINS_USERNAME"
    token_var = token_env or "JENKINS_TOKEN"
    resolved_user = username or os.environ.get(user_var)
    resolved_token = token or os.environ.get(token_var)
    if not resolved_user:
        raise ValidationError(
            f"Jenkins URL is non-default ({jenkins_url!r}). "
            f"Set {user_var} or pass --username."
        )
    if not resolved_token:
        raise ValidationError(
            f"Jenkins URL is non-default ({jenkins_url!r}). "
            f"Set {token_var} or pass --token."
        )
    return JenkinsAuth(username=resolved_user, token=resolved_token)
