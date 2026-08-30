"""Exception hierarchy for the AS5601 library.

Each class also subclasses the builtin (OSError / KeyError / ValueError) that
the wrapped operation would otherwise raise, so ``except OSError`` /
``except ValueError`` callers keep working.
"""

from __future__ import annotations

__all__ = [
    "AS5601Error",
    "AS5601IOError",
    "NotWritableError",
    "UnknownFieldError",
    "ValueRangeError",
]


class AS5601Error(Exception):
    """Base class for all AS5601 library errors."""


class AS5601IOError(AS5601Error, OSError):
    """An I2C transfer failed, or the driver's bus is already closed."""


class UnknownFieldError(AS5601Error, KeyError):
    """The field name is not in the register table."""


class NotWritableError(AS5601Error, ValueError):
    """The field's register is read-only or is the irreversible burn command."""


class ValueRangeError(AS5601Error, ValueError):
    """The value does not fit the field (bit width or register width)."""
