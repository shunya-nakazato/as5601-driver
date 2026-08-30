"""Synchronous AS5601 driver that owns a real I2C connection (smbus2)."""

from __future__ import annotations

import logging
import threading

from smbus2 import SMBus, i2c_msg

from as5601.constants import DEGREES_PER_STEP, SLAVE_ADDRESS
from as5601.errors import AS5601IOError
from as5601.field import Field
from as5601.registers import REGISTERS

__all__ = ["AS5601Driver"]

logger = logging.getLogger(__name__)


class AS5601Driver:
    """Reads AS5601 angle registers over a real I2C bus (smbus2).

    Thread-safe; owns the bus (close via :meth:`close` or context manager).
    Read-only: the configuration and burn registers are in the register table
    but no write path is exposed, so this driver cannot alter the device.

    Each read returns an instantaneous single-turn angle. Tracking rotation
    across the 4095 -> 0 wrap is the caller's (later, the tracker's) job.
    """

    def __init__(self, bus: int = 1, *, address: int = SLAVE_ADDRESS) -> None:
        self._address = address
        self._lock = threading.Lock()
        self._bus: SMBus | None = SMBus(bus)

    def close(self) -> None:
        """Release the I2C bus (idempotent); any later access raises AS5601IOError."""
        with self._lock:
            if self._bus is not None:
                self._bus.close()
                self._bus = None

    def __enter__(self) -> AS5601Driver:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def read_raw_angle(self) -> int:
        """RAW_ANGLE as a 0..4095 step count, unmodified by ZPOS."""
        return self._read_field("RAW_ANGLE")

    def read_raw_angle_degrees(self) -> float:
        """RAW_ANGLE in degrees: 0.0 <= angle < 360.0."""
        return self.read_raw_angle() * DEGREES_PER_STEP

    def read_angle(self) -> int:
        """ANGLE as a 0..4095 step count, with the device's ZPOS applied."""
        return self._read_field("ANGLE")

    def read_angle_degrees(self) -> float:
        """ANGLE in degrees: 0.0 <= angle < 360.0."""
        return self.read_angle() * DEGREES_PER_STEP

    def _read_field(self, name: str) -> int:
        field = REGISTERS[name]
        return int(field.decode(self._read_register_bits(field)))

    def _read_register_bits(self, field: Field) -> int:
        """Read the field's registers MSB-first and return their concatenation.

        The bytes are fetched in one transaction (a repeated start, as in the
        breakout board's reference sample) rather than one transaction per
        register: the device updates the angle every 150 us, so bytes read in
        separate transactions could come from different samples and tear.
        """
        write_msg = i2c_msg.write(self._address, [field.register])
        read_msg = i2c_msg.read(self._address, field.length)
        with self._lock:
            if self._bus is None:
                raise AS5601IOError("driver is closed")
            try:
                self._bus.i2c_rdwr(write_msg, read_msg)
            except OSError as exc:
                raise AS5601IOError(
                    f"I2C read failed at register 0x{field.register:02X}: {exc}"
                ) from exc
        register_bits = 0
        for byte in list(read_msg):
            register_bits = (register_bits << 8) | byte
        return register_bits
