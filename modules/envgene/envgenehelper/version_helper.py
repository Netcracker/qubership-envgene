import os


UNKNOWN_VERSION = "UNKNOWN"


def resolve_envgene_version() -> str:
    image = os.getenv("envgen_image", "").strip()
    if image:
        image_name, digest_separator, digest = image.partition("@")
        _, tag_separator, tag = image_name.rsplit("/", 1)[-1].partition(":")
        if tag_separator and tag:
            return tag
        if digest_separator and digest:
            return digest
        return "latest"

    for key in ("ENVGENE_VERSION", "CI_COMMIT_TAG", "CI_COMMIT_SHORT_SHA", "CI_COMMIT_SHA"):
        value = os.getenv(key, "").strip()
        if value:
            return value
    return UNKNOWN_VERSION
