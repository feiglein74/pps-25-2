#!/usr/bin/env python3
"""Probe v5 - Befehle aus vollständigem Disassembly."""
import serial, time

PORT = "/dev/ttyUSB0"

CMDS = [
    # Single-letter aus Dispatch-Tabelle bei $E16D
    ("U  -> Print IDN",        b"U\r"),
    ("Z  -> Print Copyright",  b"Z\r"),
    # R<X> Read-Befehle
    ("RC -> Read $B9 (I?)",    b"RC\r"),
    ("RV -> Read $B8 (V?)",    b"RV\r"),
    ("RS -> Read S setting",   b"RS\r"),
    # S<X> Set-Befehle
    ("SL -> Set bit $6001",    b"SL\r"),
    ("SD -> Clr bit $B5",      b"SD\r"),
    # V<num> Set Voltage
    ("V100 -> set V=100",      b"V100\r"),
    ("V0   -> set V=0",        b"V0\r"),
    # * Sub-Befehle
    ("*C   -> sub C",          b"*C\r"),
    ("*H   -> sub H",          b"*H\r"),
    # Andere Single-Letter
    ("C    -> ?",              b"C\r"),
    ("D    -> ?",              b"D\r"),
    ("M    -> ?",              b"M\r"),
    ("Y    -> ?",              b"Y\r"),
    # Mit @ (offset 0 in Tabelle, hat Handler $E1A3)
    ("@    -> Handler $E1A3",  b"@\r"),
]

def hx(b):
    if not b: return "(nichts)"
    p = "".join(chr(c) if 32<=c<127 else "." for c in b)
    return f"{b.hex(' ')} | {p!r}"

print(f"Probe v5 — vollständiger Disassembly-Befehlssatz")
print(f"Port: {PORT}, Baud: 600, RTS/DTR egal (Waveshare hat keine)\n")

ser = serial.Serial(PORT, 600, timeout=4.0)
ser.dtr = False; ser.rts = False
time.sleep(0.3); ser.reset_input_buffer()

for desc, payload in CMDS:
    ser.reset_input_buffer()
    ser.write(payload); ser.flush()
    time.sleep(2.5)  # bei 600 Baud längere Wartezeit für längere Antworten
    r = ser.read(ser.in_waiting) if ser.in_waiting else b""
    mark = "++ HIT!" if (b"PPS" in r or b"yright" in r or len(r) > 1) else ("·" if r else " ")
    print(f"  {mark}  send={payload!r:18s}  resp={hx(r)}")
ser.close()
print("\nFertig.")
