#!/usr/bin/env python3
"""Probe v7 — bei 62500 Baud, lange Wartezeit, mit Live-Output."""
import serial, time

PORT = "/dev/ttyUSB0"
BAUD = 62500

def hx(b):
    if not b: return "(nichts)"
    p = "".join(chr(c) if 32<=c<127 else "." for c in b)
    return f"{b.hex(' ')} | {p!r}"

CMDS = [
    b"?\r", b"U\r", b"Z\r", b"RV\r", b"RC\r", b"RS\r", b"V100\r", b"@\r"
]

ser = serial.Serial(PORT, BAUD, timeout=0.05)
ser.dtr = False; ser.rts = False
time.sleep(0.3); ser.reset_input_buffer()

for c in CMDS:
    ser.reset_input_buffer()
    ser.write(c); ser.flush()
    # Sammle 3 Sekunden lang
    deadline = time.time() + 3.0
    buf = bytearray()
    while time.time() < deadline:
        n = ser.in_waiting
        if n:
            buf.extend(ser.read(n))
        time.sleep(0.02)
    print(f"  send={c!r:14s} bytes={len(buf):3d}  {hx(bytes(buf))}")
ser.close()
