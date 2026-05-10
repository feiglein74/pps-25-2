#!/usr/bin/env python3
"""5,0 V / 1,00 A einstellen, kurz verifizieren."""
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

query(b"*ISET100\r")   # 1,00 A
time.sleep(0.3)
query(b"*VSET050\r")   # 5,0 V
time.sleep(0.5)

mv = query(b"MV\r")
mc = query(b"MC\r")
print(f"Gesetzt: 5,0 V / 1,00 A")
print(f"Gemessen: MV={mv}  MC={mc}")
ser.close()
