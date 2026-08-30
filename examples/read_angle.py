"""Print the AS5601's angle every 200 ms until interrupted.

Run on the Raspberry Pi with the breakout board wired to I2C bus 1:

    uv run python examples/read_angle.py
"""

from __future__ import annotations

import time

from as5601 import DEGREES_PER_STEP, AS5601Driver

POLL_INTERVAL_S = 0.2


def main() -> None:
    with AS5601Driver(bus=1) as sensor:
        while True:
            # One read, both units: reading twice would sample two different
            # instants and print an inconsistent pair.
            raw_angle = sensor.read_raw_angle()
            print(f"raw angle = {raw_angle:4d}  ({raw_angle * DEGREES_PER_STEP:7.3f} deg)")
            time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
