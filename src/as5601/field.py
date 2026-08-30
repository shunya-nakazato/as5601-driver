"""The ``Field`` bit-field type used by the AS5601 register table.

Vocabulary: ``register_bits`` = the content of the ``length`` registers the
field spans, concatenated MSB-first; ``raw_value`` = the field's own bits as an
unscaled int; ``physical_value`` = the converted quantity (equals the raw_value
when the field carries no conversion).

The AS5601 has an 8-bit register space in which 12-bit values (angle, zero
position, magnitude) occupy two consecutive registers, so a field spans
``length`` registers rather than exactly one.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from as5601.constants import MAX_FIELD_LENGTH, MAX_REGISTER_ADDRESS, REGISTER_WIDTH
from as5601.errors import ValueRangeError

__all__ = ["Field"]


@dataclass(frozen=True)
class Field:
    """A bit field [msb:lsb] within ``length`` consecutive registers.

    The field's name lives in the ``REGISTERS`` table key, not here. Bit
    positions are relative to the MSB-first concatenation of those registers,
    so a 12-bit angle at registers 0x0C-0x0D is ``[11:0]`` with ``length=2``.
    ``raw_to_physical`` converts a raw value (``None`` = used raw), and
    ``physical_type`` is the Python type a decode yields.
    """

    register: int
    msb: int
    lsb: int
    length: int = 1
    raw_to_physical: Callable[[int], int | float] | None = None
    physical_type: type[int | float] = int

    def __post_init__(self) -> None:
        if not 1 <= self.length <= MAX_FIELD_LENGTH:
            raise ValueError(f"length {self.length} out of range 1..{MAX_FIELD_LENGTH}")
        if not 0 <= self.lsb <= self.msb <= self.bit_width - 1:
            raise ValueError(
                f"invalid bit range [{self.msb}:{self.lsb}] "
                f"(must satisfy 0 <= lsb <= msb <= {self.bit_width - 1})"
            )
        if not 0 <= self.register <= MAX_REGISTER_ADDRESS:
            raise ValueError(f"register {self.register} out of range 0..{MAX_REGISTER_ADDRESS}")
        if self.last_register > MAX_REGISTER_ADDRESS:
            raise ValueError(
                f"field spans past the register space "
                f"(0x{self.register:02X} + {self.length} registers)"
            )

    @property
    def bit_width(self) -> int:
        """Total number of bits the spanned registers hold."""
        return self.length * REGISTER_WIDTH

    @property
    def register_bits_mask(self) -> int:
        """Mask of every bit the spanned registers hold."""
        return (1 << self.bit_width) - 1

    @property
    def last_register(self) -> int:
        """Address of the final register this field spans."""
        return self.register + self.length - 1

    @property
    def registers(self) -> range:
        """Every register address this field spans."""
        return range(self.register, self.last_register + 1)

    @property
    def width(self) -> int:
        return self.msb - self.lsb + 1

    @property
    def max_raw_value(self) -> int:
        return (1 << self.width) - 1

    @property
    def mask(self) -> int:
        return self.max_raw_value << self.lsb

    def extract(self, register_bits: int) -> int:
        self._check_register_bits(register_bits)
        return (register_bits & self.mask) >> self.lsb

    def insert(self, register_bits: int, raw_value: int) -> int:
        """Replace only this field's bits; ValueRangeError for a bad ``raw_value``."""
        self._check_register_bits(register_bits)
        raw_value = self._check_raw_value(raw_value)
        return (register_bits & ~self.mask) | (raw_value << self.lsb)

    def decode(self, register_bits: int) -> int | float:
        """Decode ``register_bits`` into this field's physical value.

        The result is coerced to ``physical_type``, guaranteeing the return
        type regardless of the conversion's own arithmetic.
        """
        raw_value = self.extract(register_bits)
        if self.raw_to_physical is not None:
            physical_value = self.raw_to_physical(raw_value)
        else:
            physical_value = raw_value
        return self.physical_type(physical_value)

    def _check_raw_value(self, raw_value: object) -> int:
        # Non-int is a value error too, so every input failure stays inside
        # the AS5601Error hierarchy.
        if not isinstance(raw_value, int):
            raise ValueRangeError(f"raw value must be int, got {type(raw_value).__name__}")
        if not 0 <= raw_value <= self.max_raw_value:
            raise ValueRangeError(f"raw value {raw_value} out of range 0..{self.max_raw_value}")
        return raw_value

    def _check_register_bits(self, register_bits: int) -> None:
        if not 0 <= register_bits <= self.register_bits_mask:
            raise ValueRangeError(
                f"register bits {register_bits} out of range "
                f"0..0x{self.register_bits_mask:0{self.length * 2}X}"
            )
