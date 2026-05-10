#!/usr/bin/env python3
"""Karte ist im @-Lock-Modus, sendet kontinuierlich 'U' (0x55).
Lausche bei mehreren Baudraten 5s, gucke welche die meisten 0x55 liefert."""
import serial, time, sys

PORT = "/dev/ttyUSB0"

# Kandidaten - 62500 berechnet, drumrum probieren
BAUDS = [62500, 56000, 57600, 60000, 64000, 65536, 50000, 55000, 70000]

def hx(b):
    if not b: return "(leer)"
    return b.hex(' ')[:60] + ("..." if len(b)>20 else "")

for baud in BAUDS:
    try:
        ser = serial.Serial(PORT, baud, timeout=0.05)
        ser.dtr = False; ser.rts = False
        time.sleep(0.2); ser.reset_input_buffer()
        # 3s lauschen
        deadline = time.time() + 3.0
        buf = bytearray()
        while time.time() < deadline:
            n = ser.in_waiting
            if n: buf.extend(ser.read(n))
            time.sleep(0.01)
        # Statistik
        if buf:
            from collections import Counter
            c = Counter(buf)
            top = c.most_common(3)
            top_str = " ".join(f"{v:02X}*{n}" for v,n in top)
            score = c.get(0x55, 0)
            print(f"  baud={baud:6d}  bytes={len(buf):4d}  top: {top_str}  0x55-count={score}")
        else:
            print(f"  baud={baud:6d}  STILLE")
        ser.close()
    except Exception as e:
        print(f"  baud={baud:6d}  err: {e}")
print("\nWenn ein Baud viele 0x55 zeigt → das ist die richtige Rate.")
