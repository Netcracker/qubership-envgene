from os import getenv

DEFAULT_REQUEST_TIMEOUT = float(getenv("DEFAULT_REQUEST_TIMEOUT", 30))

TCP_CONNECTION_LIMIT = int(getenv("TCP_CONNECTION_LIMIT", 100))

METADATA_XML = "maven-metadata.xml"

# HTTP debug tracing configuration used by aiohttp.ClientSession trace_configs.
HTTP_SECRET_HEADERS = {"authorization", "proxy-authorization", "cookie", "set-cookie"}
HTTP_LOGGED_RESPONSE_TYPES = {"application/xml", "application/json"}
HTTP_MAX_LOGGED_BODY_BYTES = 4096
