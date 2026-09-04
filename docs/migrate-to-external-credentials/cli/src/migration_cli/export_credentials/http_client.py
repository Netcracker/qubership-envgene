"""Minimal HTTP client for Jenkins export (stdlib only)."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlencode

from migration_cli.errors import MigrationCliError
from migration_cli.export_credentials.auth import JenkinsAuth


class JenkinsHttpClient:
    def __init__(self, *, jenkins_url: str, auth: JenkinsAuth, insecure: bool = False) -> None:
        self._base = jenkins_url.rstrip("/")
        self._auth = auth
        self._insecure = insecure

    def _opener(self) -> urllib.request.OpenerDirector:
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self._base, self._auth.username, self._auth.token)
        handlers: list[urllib.request.BaseHandler] = [
            urllib.request.HTTPBasicAuthHandler(password_mgr),
        ]
        if self._insecure:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            handlers.append(urllib.request.HTTPSHandler(context=ctx))
        return urllib.request.build_opener(*handlers)

    def _request(
        self,
        *,
        method: str,
        path: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
    ) -> tuple[int, str]:
        url = f"{self._base}{path}"
        req_headers = dict(headers or {})
        opener = self._opener()

        request = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        try:
            with opener.open(request, timeout=120) as response:
                payload = response.read().decode("utf-8")
                return response.status, payload
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise MigrationCliError(f"HTTP {exc.code} from {url}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise MigrationCliError(f"Request failed for {url}: {exc.reason}") from exc

    def get_json_with_body(
        self,
        *,
        path: str,
        headers: dict[str, str],
        json_body: dict[str, Any],
    ) -> Any:
        """Replicate the CM API call (GET with JSON body) from the GitLab pipeline."""
        body = json.dumps(json_body).encode("utf-8")
        headers_with_length = {**headers, "Content-Length": str(len(body))}
        status, text = self._request(method="GET", path=path, headers=headers_with_length, body=body)
        if status != 200:
            raise MigrationCliError(f"Unexpected HTTP {status} from {path}: {text}")
        if not text.strip():
            return []
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise MigrationCliError(f"Invalid JSON from {path}: {exc}") from exc

    def post_form(self, *, path: str, form: dict[str, str]) -> str:
        body = urlencode(form).encode("utf-8")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        status, text = self._request(method="POST", path=path, headers=headers, body=body)
        if status != 200:
            raise MigrationCliError(f"Unexpected HTTP {status} from {path}: {text}")
        return text
