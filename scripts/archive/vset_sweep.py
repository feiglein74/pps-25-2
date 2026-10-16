#!/usr/bin/env python3
"""Sweept *VSET<nnn> systematisch und ruft *VOUT? ab.
User beobachtet parallel mit Multimeter am Output.
Pause 3s pro Schritt - Zeit zum Notieren."""
import serial, time

PORT = "/dev/ttyUSB0"
BAUD = 9600

# Strategische Werte: 0, kleine, mittlere, große
TEST_VALUES = [0, 1, 5, 16, 32, 64, 100, 128, 160, 192, 224, 250, 255]

def hx(b):
    if not b: return "(leer)"
    p = "".join(chr(c) if 32<=c<127 else "." for c in b)
    return f"{b.hex(' ')[:30]} | {p!r}"

ser = serial.Serial(PORT, BAUD, timeout=0.3)
ser.dtr = False; ser.rts = False
time.sleep(0.3); ser.reset_input_buffer()

print(f"VSET-Sweep bei {BAUD} Baud. Pause 3s pro Wert.")
print(f"{'n':>4} | {'cmd':<14} | {'VOUT? response':<30}")
print("-" * 60)

for n in TEST_VALUES:
    cmd = f"*VSET{n:03d}\r".encode()
    ser.reset_input_buffer()
    ser.write(cmd); ser.flush()
    time.sleep(0.5)
    # echo verwerfen
    _ = ser.read(ser.in_waiting) if ser.in_waiting else b""
    # jetzt VOUT abrufen
    ser.write(b"*VOUT?\r"); ser.flush()
    time.sleep(0.5)
    r = ser.read(ser.in_waiting) if ser.in_waiting else b""
    print(f"{n:>4} | {cmd!r:<14} | {hx(r):<30}", flush=True)
    time.sleep(2.0)  # Zeit zum Multimeter ablesen

print("\nfertig. Falls Output zwischen Werten variiert -> n hat Wirkung.")
print("Falls überall ~1.6V -> n wird ignoriert oder gedeckelt.")
ser.close()
