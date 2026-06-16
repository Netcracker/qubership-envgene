import logging

import pytest


@pytest.fixture(autouse=True)
def capture_envgene_logger(caplog):
    """Attach caplog handler directly to the 'envgene' logger.

    The envgene logger sets propagate=False, so caplog's default hook on the
    root logger never receives its records. This fixture adds caplog.handler
    to the envgene logger for the duration of each test and removes it after.
    """
    envgene_logger = logging.getLogger("envgene")
    envgene_logger.addHandler(caplog.handler)
    yield
    envgene_logger.removeHandler(caplog.handler)
