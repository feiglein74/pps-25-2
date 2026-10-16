#!/usr/bin/env python3
"""Probe v6 - mit den AUS DEM 4MHz QUARZ ABGELEITETEN exakten Baudraten."""
import serial, time

PORT = "/dev/ttyUSB0"

CMDS = [
    ("?\\r",   b"?\r"),
    ("U\\r",   b"U\r"),
    ("Z\\r",   b"Z\r"),
    ("RC\\r",  b"RC\r"),
    ("RV\\r",  b"RV\r"),
    ("RS\\r",  b"RS\r"),
    ("V100\\r",b"V100\r"),
    ("@\\r",   b"@\r"),
]

def hx(b):
    if not b: return "(nichts)"
    p = "".join(chr(c) if 32<=c<127 else "." for c in b)
    return f"{b.hex(' ')} | {p!r}"

# Die zwei berechneten Raten + ein paar Sicherheitskandidaten
for baud in [7812, 62500, 9600, 4800]:
    print(f"\n=== Baud: {baud} ===")
    try:
        ser = serial.Serial(PORT, baud, timeout=1.0)
        ser.dtr = False; ser.rts = False
        time.sleep(0.3); ser.reset_input_buffer()
        for desc, payload in CMDS:
            ser.reset_input_buffer()
            ser.write(payload); ser.flush()
            time.sleep(1.0)
            r = ser.read(ser.in_waiting) if ser.in_waiting else b""
            mark = "++HIT" if (b"PPS" in r or len(r) > 2) else (" ·" if r else "  ")
            print(f"  {mark} {desc:8s} resp={hx(r)}")
        ser.close()
    except Exception as e:
        print(f"  err: {e}")
print("\nFertig.")
