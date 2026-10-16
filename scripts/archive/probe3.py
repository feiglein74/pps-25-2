#!/usr/bin/env python3
"""Probe v3 — exakte Befehlsliste aus Disassembly + alle Flow-Control-Varianten."""
import time, serial

PORT = "/dev/ttyUSB0"

CMDS = [
    ("U  -> IDN",        b"U\r"),
    ("Z  -> Copyright",  b"Z\r"),
    ("V  -> Voltage?",   b"V\r"),
    ("S  -> Status?",    b"S\r"),
    ("D  -> Display?",   b"D\r"),
    ("M  -> Mode?",      b"M\r"),
    ("C  -> ?",          b"C\r"),
    ("R  -> ?",          b"R\r"),
    ("Y  -> ?",          b"Y\r"),
    # auch mit LF Terminierung
    ("U+LF",             b"U\n"),
    ("U+CRLF",           b"U\r\n"),
    ("U pur",            b"U"),
]

def hx(b):
    if not b: return "(nichts)"
    p = "".join(chr(c) if 32<=c<127 else "." for c in b)
    return f"{b.hex(' ')} | {p!r}"

# Wir fokussieren uns auf 9600 (häufigste Standardrate) und probieren alle DTR/RTS
for baud in [9600, 4800, 2400, 1200]:
    print(f"\n--- {baud} 8N1 ---")
    for dtr in [True, False]:
        for rts in [True, False]:
            try:
                ser = serial.Serial(PORT, baud, timeout=0.6)
                ser.dtr = dtr; ser.rts = rts
                time.sleep(0.2)
                # Passiv 0.5s lauschen — vielleicht jetzt was?
                ser.reset_input_buffer()
                time.sleep(0.5)
                pas = ser.read(ser.in_waiting) if ser.in_waiting else b""
                if pas:
                    print(f"  PASSIV baud={baud} dtr={int(dtr)} rts={int(rts)}: {hx(pas)}")
                for desc, payload in CMDS:
                    ser.reset_input_buffer()
                    ser.write(payload); ser.flush()
                    time.sleep(0.7)
                    r = ser.read(ser.in_waiting) if ser.in_waiting else b""
                    if r:
                        mark = "++ HIT" if (b"PPS" in r or b"yright" in r) else " *"
                        print(f"  {mark} baud={baud} dtr={int(dtr)} rts={int(rts)} "
                              f"{desc:20s} resp={hx(r)}")
                ser.close()
            except Exception as e:
                print(f"  err {baud}: {e}")
print("\nFertig.")
