from os import getenv

DEFAULT_REQUEST_TIMEOUT = float(getenv("DEFAULT_REQUEST_TIMEOUT", 30))

TCP_CONNECTION_LIMIT = int(getenv("TCP_CONNECTION_LIMIT", 100))

METADATA_XML = "maven-metadata.xml"
