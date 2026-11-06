import logging

import aiohttp

from artifact_searcher.utils.constants import (
    HTTP_LOGGED_RESPONSE_TYPES,
    HTTP_MAX_LOGGED_BODY_BYTES,
    HTTP_SECRET_HEADERS,
)
from envgene_shared.utils.logger import logger


def _headers_for_log(headers) -> dict:
    return {
        key: "***" if key.lower() in HTTP_SECRET_HEADERS else value
        for key, value in headers.items()
    }


def _should_log_response_body(response) -> bool:
    if response.status >= 400:
        return True
    content_type = response.content_type
    return content_type.startswith("text/") or content_type in HTTP_LOGGED_RESPONSE_TYPES


def _http_debug_enabled() -> bool:
    return logger.isEnabledFor(logging.DEBUG)


async def _on_request_start(session, context, params):
    if not _http_debug_enabled():
        return
    logger.debug(
        "HTTP request %s %s\nheaders: %s",
        params.method, params.url, _headers_for_log(params.headers),
    )


async def _on_request_end(session, context, params):
    if not _http_debug_enabled():
        return
    response = params.response
    logger.debug(
        "HTTP response %s %s -> %s\nheaders: %s",
        params.method, params.url, response.status, _headers_for_log(response.headers),
    )
    if _should_log_response_body(response):
        body = await response.read()
        logged = body[:HTTP_MAX_LOGGED_BODY_BYTES].decode("utf-8", errors="replace")
        if len(body) > HTTP_MAX_LOGGED_BODY_BYTES:
            logged += f"\n... truncated, {len(body)} bytes total"
        logger.debug("HTTP response body: %s", logged)


async def _on_request_exception(session, context, params):
    if not _http_debug_enabled():
        return
    logger.debug(
        "HTTP %s %s failed: %s\nheaders: %s",
        params.method, params.url, params.exception, _headers_for_log(params.headers),
    )


def http_trace_configs() -> list[aiohttp.TraceConfig]:
    if not _http_debug_enabled():
        return []
    trace = aiohttp.TraceConfig()
    trace.on_request_start.append(_on_request_start)
    trace.on_request_end.append(_on_request_end)
    trace.on_request_exception.append(_on_request_exception)
    return [trace]
