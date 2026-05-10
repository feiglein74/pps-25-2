#!/usr/bin/env python3
"""
Probe v2 — basierend auf Firmware-Analyse.
Wir wissen jetzt:
  - '?' + CR  -> sollte IDN-String "PPS-25/2 V1.1 91.10.20\r\n" liefern
  - '*X' + CR -> Subcommand-Schema (z.B. *C, *H)
  - case-insensitive ASCII, CR-terminiert

P1.6 muss HIGH sein, sonst sendet die Karte nicht (Hardware-Wartebedingung).
Wir testen alle Kombinationen aus DTR/RTS und Baudrate, mit hwflow=False.
"""
import time, serial, sys

PORT = "/dev/ttyUSB0"

def hx(b):
    if not b: return "(nichts)"
    p = "".join(chr(c) if 32<=c<127 else "." for c in b)
    return f"{b.hex(' ')} | {p!r}"

# Hauptkandidat: '?' für IDN
PROBES = [
    ("?    -> IDN?",    b"?\r"),
    ("?    -> nur ?",   b"?"),
    ("?\\n -> IDN?",    b"?\n"),
    ("*C   -> sub-cmd", b"*C\r"),
    ("*H   -> sub-cmd", b"*H\r"),
    ("ID   -> ?",       b"ID\r"),
    ("V    -> Volt?",   b"V\r"),
    ("I    -> Strom?",  b"I\r"),
]

for baud in [9600, 4800, 2400, 1200]:
    print(f"\n=== {baud} 8N1 ===")
    for dtr in [True, False]:
        for rts in [True, False]:
            ser = serial.Serial(PORT, baud, bytesize=8, parity="N",
                                stopbits=1, timeout=0.5,
                                rtscts=False, dsrdtr=False, xonxoff=False)
            ser.dtr = dtr
            ser.rts = rts
            time.sleep(0.15)
            for desc, payload in PROBES:
                ser.reset_input_buffer()
                ser.write(payload); ser.flush()
                time.sleep(0.7)  # warten - die Karte hat 300ms Timeout falls P1.6 low
                resp = ser.read(ser.in_waiting) if ser.in_waiting else b""
                if resp:
                    mark = "++" if b"PPS" in resp else " *"
                    print(f"  {mark} baud={baud} dtr={int(dtr)} rts={int(rts)}  "
                          f"{desc:25s}  resp={hx(resp)}")
            ser.close()
print("\nFertig. Nach 'PPS' oben suchen — das wäre der IDN-Treffer.")
