"""User-space I2C driver for the AMS AS5601 magnetic rotary position sensor.

``AS5601Driver`` is the primary interface: it owns the I2C connection and
reads the device's angle registers.

Modules:

- ``driver``: the synchronous driver (angle reads)
- ``registers``: name -> ``Field`` table and register access classification
- ``field``: the ``Field`` bit-field type
- ``constants``: I2C protocol constants from the datasheet
- ``errors``: exception hierarchy (``AS5601Error`` base)
"""

from as5601.constants import ANGLE_STEPS, DEGREES_PER_STEP, SLAVE_ADDRESS
from as5601.driver import AS5601Driver
from as5601.errors import (
    AS5601Error,
    AS5601IOError,
    NotWritableError,
    UnknownFieldError,
    ValueRangeError,
)

__all__ = [
    "ANGLE_STEPS",
    "DEGREES_PER_STEP",
    "SLAVE_ADDRESS",
    "AS5601Driver",
    "AS5601Error",
    "AS5601IOError",
    "NotWritableError",
    "UnknownFieldError",
    "ValueRangeError",
]
