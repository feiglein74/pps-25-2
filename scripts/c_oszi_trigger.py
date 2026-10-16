#!/usr/bin/env python3
"""Erzeugt einen einzelnen sauberen CC-Trigger für Oszi-Beobachtung.
Reset → warten → C038 (Trigger) → warten → C100 (Recovery)."""
import serial, time

ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=0.4)
ser.dtr = False; ser.rts = False
time.sleep(0.3); ser.reset_input_buffer()

def send(c):
    ser.reset_input_buffer()
    ser.write(c); ser.flush(); time.sleep(0.3)
    return ser.read(ser.in_waiting) if ser.in_waiting else b""

# Reset zu definiertem state
send(b"*VSET050\r"); time.sleep(0.3)
send(b"*ISET100\r"); time.sleep(0.5)

print("State 5V/1A — gleich kommt Trigger. Oszi armieren!")
print("3...")
time.sleep(1)
print("2...")
time.sleep(1)
print("1...")
time.sleep(1)

t0 = time.time()
print(f"\n[{time.time()-t0:.3f}s] TRIGGER: C038")
send(b"C038\r")
time.sleep(5)

print(f"[{time.time()-t0:.3f}s] RECOVERY: C100")
send(b"C100\r")
time.sleep(5)

print(f"[{time.time()-t0:.3f}s] fertig")
ser.close()
