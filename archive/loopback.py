#!/usr/bin/env python3
"""
Live-Loopback-Test. Sendet alle 500ms ein Testpaket und zeigt sofort an,
ob/was zurückkommt. Brücke an Pin 2/3 (DB-25-Ende) setzen oder lösen
- Ausgabe ändert sich live.

Drei Modi pro Zyklus:
  1. RTS aus, kein Handshake
  2. RTS ein, kein Handshake
  3. RTS ein, rtscts=True
Damit sehen wir, ob der Adapter Handshake-blockiert ist.

Strg-C zum Beenden.
"""
import time, serial, sys

PORT = "/dev/ttyUSB0"
BAUD = 9600

def hex_(b):
    if not b: return "(nichts)"
    p = "".join(chr(c) if 32<=c<127 else "." for c in b)
    return f"{b.hex(' ')} | {p!r}"

print("Loopback-Live-Test. Strg-C zum Beenden.")
print("Setz/lös die Brücke Pin 2<->3 am DB-25, beobachte 'resp'-Spalte.")
print("-" * 78)

cycle = 0
while True:
    cycle += 1
    # Kombinationen rotieren
    mode = cycle % 3
    if mode == 0:
        cfg = "RTS=0  hwflow=0"
        ser = serial.Serial(PORT, BAUD, timeout=0.3, rtscts=False)
        ser.rts = False; ser.dtr = False
    elif mode == 1:
        cfg = "RTS=1  hwflow=0"
        ser = serial.Serial(PORT, BAUD, timeout=0.3, rtscts=False)
        ser.rts = True; ser.dtr = True
    else:
        cfg = "RTS=1  hwflow=1"
        ser = serial.Serial(PORT, BAUD, timeout=0.3, rtscts=True)
        ser.rts = True; ser.dtr = True

    payload = f"PING{cycle:03d}\r\n".encode()
    try:
        ser.reset_input_buffer()
        # CTS-Zustand abfragen falls möglich
        try:
            cts = ser.cts
        except Exception:
            cts = None
        ser.write(payload); ser.flush()
        time.sleep(0.4)
        resp = ser.read(ser.in_waiting) if ser.in_waiting else b""
        match = "MATCH " if payload in resp else ""
        print(f"#{cycle:03d} {cfg}  CTS={cts}  send={payload.strip()!r:18s}  "
              f"resp={hex_(resp):40s} {match}")
    finally:
        ser.close()
    time.sleep(0.3)
