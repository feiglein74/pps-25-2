#!/usr/bin/env python3
"""Voller DAC-Sweep n=0..255 in 8er-Schritten, mit 500ms Pausen.
Zeigt n und echte ADC-Messung MV nebeneinander."""
import serial, time

ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=0.3)
ser.dtr = False; ser.rts = False
time.sleep(0.3); ser.reset_input_buffer()

def query(cmd):
    ser.reset_input_buffer()
    ser.write(cmd); ser.flush()
    time.sleep(0.3)
    r = ser.read(ser.in_waiting) if ser.in_waiting else b""
    s = r.decode("ascii", errors="replace").replace("\r","")
    parts = [p for p in s.split("\n") if p]
    return parts[-1] if parts else ""

print(f"{'n':>3} | {'MV':>6}")
print("-" * 14)
for n in range(0, 256, 8):
    query(f"*VSET{n:03d}\r".encode())
    time.sleep(0.3)
    mv = query(b"MV\r")
    print(f"{n:>3} | {mv:>6}", flush=True)
    time.sleep(0.2)

# Zum Schluss zurück auf 0
query(b"*VSET000\r")
ser.close()
