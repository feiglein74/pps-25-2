#!/usr/bin/env python3
"""
Endlos-Sendeschleife für Oszi-Diagnose.
Schickt alle 100ms 'U\\r' raus. Triggern auf fallende Flanke an irgendeinem Messpunkt.
Mit Strg-C beenden.
"""
import time, serial, sys

PORT = "/dev/ttyUSB0"  # FTDI Waveshare
BAUD = int(sys.argv[1]) if len(sys.argv) > 1 else 4800
ser = serial.Serial(PORT, BAUD, timeout=0.1)
ser.dtr = True; ser.rts = True
print(f"Sende 'U\\r' alle 200ms bei {BAUD} Baud. Strg-C zum Stoppen.")
print(f"  -> 'U' = 0x55 = 01010101  (perfekt für Oszi!)")
print(f"  -> Bei {BAUD} Baud: 1 Bit = {1e6/BAUD:.0f} µs, 'U\\r' Frame = ~{20*1e6/BAUD:.0f} µs")
n = 0
try:
    while True:
        ser.write(b"U\r")
        n += 1
        if n % 50 == 0:
            r = ser.read(ser.in_waiting) if ser.in_waiting else b""
            if r:
                print(f"  RESPONSE: {r!r}")
            else:
                print(f"  ({n} bytes gesendet, weiterhin still)")
        time.sleep(0.2)
except KeyboardInterrupt:
    print(f"\nGestoppt nach {n} Sendungen.")
    ser.close()
