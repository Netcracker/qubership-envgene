from .duration import Duration
from .retry import RetryPolicy, parse_duration, retry_call

# Default policy aligned with espusher.internal.git.GitUtils.retry_policy
GIT_RETRY_POLICY = RetryPolicy(
    limit=10,
    backoff_duration=parse_duration("0.3s"),
    backoff_factor=2,
    backoff_max_duration=parse_duration("5s"),
)

__all__ = [
    "Duration",
    "GIT_RETRY_POLICY",
    "RetryPolicy",
    "parse_duration",
    "retry_call",
]
