import re
from datetime import timedelta


class Duration:
    _RE = re.compile(r"(\d+)\s*(h|m|s)", re.IGNORECASE)

    def __init__(self, value: timedelta):
        if not isinstance(value, timedelta):
            raise TypeError("Duration expects datetime.timedelta")
        self._value = value

    @classmethod
    def from_string(cls, value: str) -> "Duration":
        total_seconds = 0

        for amount, unit in cls._RE.findall(value):
            amount = int(amount)
            unit = unit.lower()

            if unit == "h":
                total_seconds += amount * 3600
            elif unit == "m":
                total_seconds += amount * 60
            elif unit == "s":
                total_seconds += amount

        if total_seconds == 0:
            raise ValueError(f"Invalid duration: {value}")

        return cls(timedelta(seconds=total_seconds))

    @classmethod
    def from_seconds(cls, seconds: int | float) -> "Duration":
        return cls(timedelta(seconds=seconds))

    def to_timedelta(self) -> timedelta:
        return self._value

    def total_seconds(self) -> float:
        return self._value.total_seconds()

    def __str__(self) -> str:
        seconds = int(self._value.total_seconds())

        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)

        parts = []
        if h:
            parts.append(f"{h}h")
        if m:
            parts.append(f"{m}m")
        if s or not parts:
            parts.append(f"{s}s")

        return " ".join(parts)

    def __mul__(self, factor: int | float) -> "Duration":
        return Duration.from_seconds(self.total_seconds() * factor)

    def __rmul__(self, factor: int | float) -> "Duration":
        return self.__mul__(factor)

    def __lt__(self, other: "Duration") -> bool:
        return self._value < other._value

    def __le__(self, other: "Duration") -> bool:
        return self._value <= other._value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            return False
        return self._value == other._value

    def __repr__(self) -> str:
        return f"Duration('{self}')"
