#!/usr/bin/env python3
"""VSET<n> setzen, VOUT? (Setpoint-Echo) und MV (echte ADC-Messung) abrufen."""
import serial, time

ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=0.3)
ser.dtr = False; ser.rts = False
time.sleep(0.3); ser.reset_input_buffer()

def query(cmd):
    ser.reset_input_buffer()
    ser.write(cmd); ser.flush()
    time.sleep(0.4)
    r = ser.read(ser.in_waiting) if ser.in_waiting else b""
    s = r.decode("ascii", errors="replace")
    # die letzte Zeile (nach allen \r\n) ist die Antwort
    parts = [p for p in s.replace("\r","").split("\n") if p]
    return parts[-1] if parts else ""

print(f"{'n':>3} | {'VOUT?':>6} | {'MV':>10}")
print("-" * 30)
for n in [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 15, 16, 17, 18, 20, 32, 64, 128, 200, 255]:
    query(f"*VSET{n:03d}\r".encode())
    vout = query(b"*VOUT?\r")
    mv   = query(b"MV\r")
    print(f"{n:3d} | {vout:>6} | {mv:>10}")
ser.close()
