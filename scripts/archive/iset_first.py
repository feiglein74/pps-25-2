#!/usr/bin/env python3
"""Erst Strom-Setpoint auf MAX, dann Voltage rampen.
Wenn der Bruch wegfällt -> war Strom-Limit. Wenn er bleibt -> andere Ursache."""
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

# Strom-Setpoint hochsetzen
print("Erst *ISET255 (Strom-Limit auf Max)")
query(b"*ISET255\r")
time.sleep(0.5)

# Dann Voltage rampen
print(f"\n{'n':>3} | {'MV':>6} | {'MC':>6}")
print("-" * 22)
for n in range(0, 256, 8):
    query(f"*VSET{n:03d}\r".encode())
    time.sleep(0.3)
    mv = query(b"MV\r")
    mc = query(b"MC\r")
    print(f"{n:>3} | {mv:>6} | {mc:>6}", flush=True)
    time.sleep(0.2)

# Sauber zurück
query(b"*VSET000\r")
ser.close()
