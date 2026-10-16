#!/usr/bin/env python3
"""Systematischer SCPI-Befehlstest. Eine Reihe Befehle nacheinander."""
import serial, time

PORT = "/dev/ttyUSB0"
BAUD = 57600

CMDS = [
    # Standard SCPI Common Commands
    b"*IDN?\r",   # identification query
    b"*RST\r",    # reset
    b"*OPC?\r",   # operation complete query
    b"*ESR?\r",   # event status register
    b"*STB?\r",   # status byte query
    b"*TST?\r",   # self-test query
    # Aus Disassembly bekannte gültige Subkommandos
    b"*CLS\r",    # clear status (bestätigt gültig)
    b"*ISET?\r",  # current set query
    b"*VSET?\r",  # voltage set query
    b"*SLS\r",    # *S sub - vielleicht status?
    b"*VLS\r",    # *V sub
    # Single-letter aus Hauptdispatch-Tabelle
    b"V?\r",      # voltage query (single letter dispatch)
    b"I?\r",      # current query
    b"R?\r",      # read?
    b"S?\r",      # status?
]

def hx(b):
    if not b: return "(nichts)"
    p = "".join(chr(c) if 32<=c<127 else "." for c in b)
    return f"{b.hex(' ')} | {p!r}"

ser = serial.Serial(PORT, BAUD, timeout=0.2)
ser.dtr=False; ser.rts=False
time.sleep(0.3); ser.reset_input_buffer()
print(f"Sequenztest bei {BAUD} Baud:")
for cmd in CMDS:
    ser.reset_input_buffer()
    ser.write(cmd); ser.flush()
    time.sleep(1.5)
    r = ser.read(ser.in_waiting) if ser.in_waiting else b""
    print(f"  send={cmd!r:18s} resp({len(r)}B)={hx(r)}")
ser.close()
