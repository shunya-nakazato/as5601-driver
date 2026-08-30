# AS5601 — Python I2C Driver

A user-space Linux driver for the AMS **AS5601** magnetic rotary position sensor. It reads the sensor's 12-bit angle over `/dev/i2c-*` so a knob or shaft attached to a Raspberry Pi (or any Linux SBC) can be read from Python — no kernel module, no IIO setup.

- Product page: https://www.switch-science.com/products/3494
- Breakout board and reference samples: https://github.com/y2kblog/AS5601_BreakoutBoard_V1_0

---

## Target Hardware

The AS5601 is a Hall-based absolute rotary encoder: a diametrically magnetized magnet turns above the chip, and the die measures its field angle. It exposes both an I2C interface and an A/B quadrature output.

| Item | Details |
|---|---|
| Resolution | 4096 steps per revolution (12-bit absolute) |
| Sampling time | 150 µs |
| I2C address | `0x36` (fixed) |
| Supply | 3.3 V or 5 V |
| Interfaces | I2C, A/B incremental output (8–2048 ppr), PUSH pin |

This library targets the **I2C interface**. The A/B incremental output is a hardware signal read by counting edges on GPIO, which is outside this library's scope.

## Status

This is the first stage of the driver: **reading the angle**. Multi-turn tracking and the magnet-status registers are planned next (see [Roadmap](#roadmap)).

## Requirements

- Linux with I2C enabled (`raspi-config` → Interface Options → I2C on Raspberry Pi OS)
- Python 3.12 or newer
- Read/write access to the I2C device node (add your user to the `i2c` group)

Verify the sensor is visible before using the library:

```console
$ i2cdetect -y 1
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
30: -- -- -- -- -- -- 36 -- -- -- -- -- -- -- -- --
```

## Installation

```console
$ pip install git+https://github.com/shunya-nakazato/as5601-driver.git
```

## Quick Start

```python
from as5601 import AS5601Driver

with AS5601Driver(bus=1) as sensor:
    print(sensor.read_raw_angle())  # 0..4095
    print(sensor.read_raw_angle_degrees())  # 0.0 <= angle < 360.0
```

The driver owns the bus, so use it as a context manager (or call `close()`) to release the file descriptor. It is thread-safe: concurrent reads are serialized internally.

A runnable version is in [`examples/read_angle.py`](examples/read_angle.py).

## API

| Method | Returns | Description |
|---|---|---|
| `read_raw_angle()` | `int` | `RAW_ANGLE` register (0x0C), 0–4095, unaffected by the device's zero position |
| `read_raw_angle_degrees()` | `float` | The same reading in degrees |
| `read_angle()` | `int` | `ANGLE` register (0x0E), 0–4095, with the device's `ZPOS` applied |
| `read_angle_degrees()` | `float` | The same reading in degrees |

Every read fetches both bytes of a 12-bit value in a **single I2C transaction** (a repeated start). The device updates the angle every 150 µs, so bytes read in separate transactions could come from different samples and produce a torn value.

Failures raise exceptions from a single hierarchy rooted at `AS5601Error`; `AS5601IOError` also subclasses `OSError`, so existing `except OSError` code keeps working.

## I2C Bus Speed

The default bus speed on Raspberry Pi OS is 100 kHz, which puts one angle read at roughly 0.4 ms — slower than the sensor's 150 µs sampling time. For fast rotation, raise the bus to 400 kHz (the speed the board's reference sample uses) by adding this to `/boot/firmware/config.txt` and rebooting:

```
dtparam=i2c_arm_baudrate=400000
```

Bus speed is a system setting, not something this library can configure.

## Known Limitations

- **No push-button detection.** The AS5601 has a PUSH output, but on this breakout board that pin is not connected, so it cannot be read.
- **Single-turn readings only.** The angle wraps from 4095 back to 0 once per revolution. Accumulating turns is the caller's job until the tracker lands.
- **Magnet status is not exposed yet.** A missing or badly positioned magnet still yields a plausible-looking angle. The `STATUS` (MD/ML/MH), `AGC`, and `MAGNITUDE` registers are defined in the register table but have no public read method yet.
- **Read-only.** The driver never writes to the device. Configuration registers (`CONF`, `ABN`, `ZPOS`, `PUSHTHR`) and the irreversible `BURN` command are out of reach by design.

## Roadmap

- Multi-turn tracking (cumulative angle and rotation direction)
- `STATUS` / `AGC` / `MAGNITUDE` reads for magnet health
- An asyncio facade mirroring the synchronous driver

## Development

```console
$ uv sync
$ uv run ruff check . && uv run ruff format --check .
$ uv run pytest --cov=as5601
```

Test files use the `*.spec.py` suffix and are intentionally not committed; they are local specs.

## License

MIT — see [LICENSE](LICENSE).
