"""AS5601 register table and access classification.

Names follow the datasheet, which is also the source of the per-field
descriptions in the trailing comments. Each comment starts with the value
domain the API speaks for that field: "raw:" means the raw register value is
used as-is. Angle fields deliberately carry no conversion: both the raw step
count and the angle in degrees are wanted, so the unit is chosen by the
driver method the caller picks, not fixed here.
"""

from __future__ import annotations

from as5601.field import Field

__all__ = [
    "BURN_REGISTER",
    "CONFIG_REGISTERS",
    "OUTPUT_REGISTERS",
    "REGISTERS",
    "STATUS_REGISTERS",
    "WRITABLE_REGISTERS",
]

# name -> Field. The AS5601 register space is 8-bit; 12-bit values occupy two
# consecutive registers, MSB-first (length=2).
REGISTERS: dict[str, Field] = {
    # Configuration registers (0x00-0x0A)
    "ZMCO": Field(0x00, 1, 0),  # raw: number of times ZPOS has been burned
    "ZPOS": Field(0x01, 11, 0, length=2),  # raw: zero position
    # raw: configuration word. Kept as a single field until the per-bit layout
    # (PM / HYST / ...) is confirmed against the datasheet; defining subfields
    # from guesswork would risk writing unintended settings once write lands.
    "CONF": Field(0x07, 13, 0, length=2),
    "ABN": Field(0x09, 3, 0),  # raw: incremental (A/B) output resolution
    "PUSHTHR": Field(0x0A, 7, 0),  # raw: push-detection threshold
    # Status registers (0x0B, 0x1A-0x1C)
    "MH": Field(0x0B, 3, 3),  # raw: AGC minimum gain overflow (magnet too strong)
    "ML": Field(0x0B, 4, 4),  # raw: AGC maximum gain overflow (magnet too weak)
    "MD": Field(0x0B, 5, 5),  # raw: magnet detected
    "AGC": Field(0x1A, 7, 0),  # raw: automatic gain control value
    "MAGNITUDE": Field(0x1B, 11, 0, length=2),  # raw: CORDIC magnitude
    # Output registers (0x0C-0x0F)
    "RAW_ANGLE": Field(0x0C, 11, 0, length=2),  # raw: unmodified angle, 0..4095
    "ANGLE": Field(0x0E, 11, 0, length=2),  # raw: angle after ZPOS, 0..4095
    # Burn command (0xFF)
    "BURN": Field(0xFF, 7, 0),  # raw: irreversible OTP programming command
}

# Register-level access classification (datasheet). Kept next to the table so
# adding a register means classifying it here; the table spec below enforces
# that every register above belongs to exactly one class.
CONFIG_REGISTERS = frozenset(range(0x00, 0x0B))  # ZMCO, ZPOS, CONF, ABN, PUSHTHR
OUTPUT_REGISTERS = frozenset(range(0x0C, 0x10))  # RAW ANGLE, ANGLE
STATUS_REGISTERS = frozenset({0x0B}) | frozenset(range(0x1A, 0x1D))  # STATUS, AGC, MAGNITUDE
BURN_REGISTER = 0xFF

# ZMCO counts burns performed and is read-only. BURN is excluded because
# programming the OTP is irreversible and limited in count: it must never be
# reachable through a generic write.
_READ_ONLY_CONFIG_REGISTERS = frozenset({0x00})
WRITABLE_REGISTERS: frozenset[int] = CONFIG_REGISTERS - _READ_ONLY_CONFIG_REGISTERS

# Table spec, checked at import: every field must sit in exactly one access
# class, so a newly added register cannot silently escape classification.
_CLASSES = (CONFIG_REGISTERS, OUTPUT_REGISTERS, STATUS_REGISTERS, frozenset({BURN_REGISTER}))
for _name, _field in REGISTERS.items():
    for _register in _field.registers:
        if sum(_register in _class for _class in _CLASSES) != 1:
            raise AssertionError(
                f"{_name}: register 0x{_register:02X} is not classified exactly once"
            )
del _name, _field, _register
