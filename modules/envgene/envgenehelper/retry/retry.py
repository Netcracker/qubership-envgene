import time
from dataclasses import dataclass
from datetime import timedelta
from typing import Callable, Iterable, Type, TypeVar

from .duration import Duration

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    limit: int
    backoff_duration: timedelta
    backoff_factor: int
    backoff_max_duration: timedelta


def parse_duration(value: str) -> Duration:
    return Duration.from_string(value)


def retry_call(
    policy,
    fn: Callable[..., T],
    *args,
    retry_on: Iterable[Type[Exception]] = (Exception,),
    no_retry_on: Iterable[Type[Exception]] = (),
    **kwargs,
) -> T:
    if policy is None:
        return fn(*args, **kwargs)

    retry_on_t = tuple(retry_on)
    no_retry_on_t = tuple(no_retry_on)
    delay = policy.backoff_duration

    for attempt in range(1, policy.limit + 1):
        try:
            return fn(*args, **kwargs)
        except no_retry_on_t:
            raise
        except retry_on_t:
            if attempt >= policy.limit:
                raise

            time.sleep(delay.total_seconds())

            delay = min(
                delay * policy.backoff_factor,
                policy.backoff_max_duration,
            )
