#!/usr/bin/env python3
"""
Toggelt eine einzelne Steuerleitung im Sekundentakt.
Damit identifizieren wir am Oszi welche RS232-Leitung am ICL232 ankommt.
Default: RTS toggle. Umschalten: Argument 'dtr' oder 'tx'.
"""
import time, serial, sys

PORT = "/dev/ttyUSB0"
mode = sys.argv[1] if len(sys.argv)>1 else "rts"

ser = serial.Serial(PORT, 4800, timeout=0.1)
print(f"Modus: {mode.upper()}-Toggle alle 1s. Strg-C zum Stoppen.")
print(f"  TX-Idle = -10V, TX-aktiv (sendet) = pulst")
print(f"  RTS=True = +10V (assertiert), RTS=False = -10V (negiert)")
print(f"  DTR analog zu RTS")

state = True
n = 0
try:
    while True:
        if mode == "rts":
            ser.rts = state
            ser.dtr = False
            label = f"RTS={'+' if state else '-'}"
        elif mode == "dtr":
            ser.dtr = state
            ser.rts = False
            label = f"DTR={'+' if state else '-'}"
        elif mode == "tx":
            ser.rts = False; ser.dtr = False
            ser.write(b"X" if state else b"\x00")
            label = f"TX-byte {'X' if state else 'NUL'}"
        elif mode == "break":
            if state:
                ser.send_break(0.5)
                label = "BREAK (+10V dauerhaft 500ms)"
            else:
                label = "idle (-10V)"
        else:
            print(f"unbekannt: {mode}"); break
        n += 1
        print(f"  #{n:3d}: {label}")
        time.sleep(1)
        state = not state
except KeyboardInterrupt:
    print("\nGestoppt.")
ser.close()
