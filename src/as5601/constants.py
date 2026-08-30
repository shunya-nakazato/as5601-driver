"""AS5601 I2C protocol constants (datasheet)."""

from __future__ import annotations

SLAVE_ADDRESS: int = 0x36  # 7-bit I2C address (fixed; shared with the AS5600)

REGISTER_WIDTH: int = 8  # registers are 8-bit; wider values span consecutive registers
MAX_REGISTER_ADDRESS: int = 0xFF  # register addresses are a single byte (0..255)
MAX_FIELD_LENGTH: int = 2  # widest field spans two registers (the 12-bit angle values)

ANGLE_RESOLUTION_BITS: int = 12
ANGLE_STEPS: int = 1 << ANGLE_RESOLUTION_BITS  # 4096 steps per revolution
DEGREES_PER_STEP: float = 360.0 / ANGLE_STEPS
