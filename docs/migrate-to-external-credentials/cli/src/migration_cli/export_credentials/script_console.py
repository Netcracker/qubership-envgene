"""Jenkins Script Console client — fetch plaintext credential values."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from migration_cli.errors import MigrationCliError
from migration_cli.export_credentials.http_client import JenkinsHttpClient

log = logging.getLogger(__name__)

CredentialType = Literal["usernamePassword", "secret"]


@dataclass(frozen=True)
class UsernamePasswordValue:
    username: str
    password: str


@dataclass(frozen=True)
class SecretValue:
    secret: str


def _groovy_username_password(cred_id: str) -> str:
    return f"""\
import jenkins.model.Jenkins
import com.cloudbees.plugins.credentials.CredentialsProvider
import com.cloudbees.plugins.credentials.common.StandardCredentials
import com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl
import hudson.util.Secret

def credentialId = "{cred_id}"

def allCreds = CredentialsProvider.lookupCredentials(
    StandardCredentials.class,
    Jenkins.instance,
    null,
    null
)

def found = allCreds.find {{ it.id == credentialId }}

if (found && found instanceof UsernamePasswordCredentialsImpl) {{
    println "USERNAME:" + found.username
    println "PASSWORD:" + Secret.toString(found.password)
}} else if (found) {{
    println "ERROR:wrong_type"
}} else {{
    println "ERROR:not_found"
}}
"""


def _groovy_secret(cred_id: str) -> str:
    return f"""\
import jenkins.model.Jenkins
import com.cloudbees.plugins.credentials.CredentialsProvider
import com.cloudbees.plugins.credentials.common.StandardCredentials
import org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl
import hudson.util.Secret

def credentialId = "{cred_id}"

def allCreds = CredentialsProvider.lookupCredentials(
    StandardCredentials.class,
    Jenkins.instance,
    null,
    null
)

def found = allCreds.find {{ it.id == credentialId }}

if (found && found instanceof StringCredentialsImpl) {{
    println "SECRET:" + Secret.toString(found.secret)
}} else if (found) {{
    println "ERROR:wrong_type"
}} else {{
    println "ERROR:not_found"
}}
"""


def _parse_script_output(text: str) -> dict[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    parsed: dict[str, str] = {}
    for line in lines:
        if line.startswith("ERROR:"):
            parsed["error"] = line.removeprefix("ERROR:")
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        parsed[key] = value
    return parsed


def fetch_credential_value(
    *,
    client: JenkinsHttpClient,
    cred_id: str,
    cred_type: CredentialType,
) -> UsernamePasswordValue | SecretValue:
    if cred_type == "usernamePassword":
        script = _groovy_username_password(cred_id)
    else:
        script = _groovy_secret(cred_id)

    log.debug("Fetching %r via Script Console.", cred_id)
    output = client.post_form(path="/scriptText", form={"script": script})
    parsed = _parse_script_output(output)

    if "error" in parsed:
        raise MigrationCliError(f"Failed to fetch {cred_id!r}: ERROR:{parsed['error']}")

    if cred_type == "usernamePassword":
        if "USERNAME" not in parsed or "PASSWORD" not in parsed:
            raise MigrationCliError(
                f"Unexpected Script Console output for {cred_id!r}: {output!r}"
            )
        return UsernamePasswordValue(username=parsed["USERNAME"], password=parsed["PASSWORD"])

    if "SECRET" not in parsed:
        raise MigrationCliError(f"Unexpected Script Console output for {cred_id!r}: {output!r}")
    return SecretValue(secret=parsed["SECRET"])


def credential_entry_payload(
    cred_type: CredentialType,
    value: UsernamePasswordValue | SecretValue,
) -> dict[str, object]:
    if cred_type == "usernamePassword":
        assert isinstance(value, UsernamePasswordValue)
        return {
            "type": "usernamePassword",
            "data": {
                "username": value.username,
                "password": value.password,
            },
        }
    assert isinstance(value, SecretValue)
    return {
        "type": "secret",
        "data": {
            "secret": value.secret,
        },
    }
