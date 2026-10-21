import inspect
import os
from unittest.mock import Mock

os.environ.setdefault("ENVIRONMENT_NAME", "test-env")
os.environ.setdefault("CLUSTER_NAME", "test-cluster")
os.environ.setdefault("CI_PROJECT_DIR", os.path.dirname(__file__))


def _patch_client_response_for_aiohttp_314() -> None:
    """aioresponses 0.7.8 builds ClientResponse without stream_writer.

    aiohttp 3.14 made that argument required. The mock only reads
    stream_writer.output_size when the request writer is already finished.
    """
    from aiohttp.client_reqrep import ClientResponse

    if "stream_writer" not in inspect.signature(ClientResponse.__init__).parameters:
        return
    original = ClientResponse.__init__

    def _init(self, *args, **kwargs):
        kwargs.setdefault("stream_writer", Mock(output_size=0))
        return original(self, *args, **kwargs)

    ClientResponse.__init__ = _init


_patch_client_response_for_aiohttp_314()
