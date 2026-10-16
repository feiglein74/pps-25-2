#!/usr/bin/env python3
"""Stress-Test: schnell zwischen Werten um den Bruchpunkt wechseln, MV abfragen.
Sehen ob der Bruch bei n=18 konsistent ist oder schwankt."""
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

# 5 Runden um den Bruchpunkt herum
print(f"{'iter':>4} | {'n':>3} | {'MV':>6}")
print("-" * 25)
for run in range(5):
    for n in [16, 17, 18, 19, 20]:
        query(f"*VSET{n:03d}\r".encode())
        time.sleep(0.2)
        mv = query(b"MV\r")
        print(f"{run:>4} | {n:>3} | {mv:>6}")
    print("-" * 25)
ser.close()
