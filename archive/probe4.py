#!/usr/bin/env python3
"""Probe v4 — alles, was wir aus dem EPROM wissen, gegen die nun korrekt verkabelte Karte."""
import time, serial

PORT = "/dev/ttyUSB0"

# Kompletter Satz: alle aus dem Disassembly bekannten Befehle + ein paar Kandidaten
CMDS = [
    ("?  -> IDN (E789)",  b"?\r"),
    ("U  -> IDN (E356)",  b"U\r"),
    ("Z  -> Copyright",   b"Z\r"),
    ("V  -> Voltage",     b"V\r"),
    ("S  -> ?",           b"S\r"),
    ("D  -> ?",           b"D\r"),
    ("M  -> ?",           b"M\r"),
    ("C  -> ?",           b"C\r"),
    ("R  -> ?",           b"R\r"),
    ("Y  -> ?",           b"Y\r"),
    ("*C -> sub",         b"*C\r"),
    ("CRLF leer",         b"\r\n"),
]

def hx(b):
    if not b: return "(nichts)"
    p = "".join(chr(c) if 32<=c<127 else "." for c in b)
    return f"{b.hex(' ')} | {p!r}"

# Erst lange passiv lauschen bei jeder Baudrate
print("=== PASSIV (5s je Baudrate, jetzt am Gerät rumdrücken!) ===")
for baud in [9600, 4800, 2400, 1200, 600, 300]:
    ser = serial.Serial(PORT, baud, timeout=0.1)
    ser.dtr = True; ser.rts = True
    time.sleep(0.2); ser.reset_input_buffer()
    time.sleep(5)
    pas = ser.read(ser.in_waiting) if ser.in_waiting else b""
    if pas:
        print(f"  ++ {baud}: {hx(pas)}")
    ser.close()

# Jetzt aktiv probieren
print("\n=== AKTIV ===")
for baud in [9600, 4800, 2400, 1200, 600, 300]:
    print(f"\n--- {baud} ---")
    for rts in [True, False]:
        for dtr in [True, False]:
            ser = serial.Serial(PORT, baud, timeout=1.0)
            ser.dtr = dtr; ser.rts = rts
            time.sleep(0.1)
            for desc, payload in CMDS:
                ser.reset_input_buffer()
                ser.write(payload); ser.flush()
                time.sleep(1.0)
                r = ser.read(ser.in_waiting) if ser.in_waiting else b""
                if r:
                    mark = "++HIT" if (b"PPS" in r or b"yright" in r) else "  *  "
                    print(f"  {mark} baud={baud} dtr={int(dtr)} rts={int(rts)} "
                          f"{desc:20s} resp={hx(r)}")
            ser.close()
print("\nFertig.")
