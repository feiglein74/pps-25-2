#!/usr/bin/env python3
"""Phase 2a: Inkrement-Befehle V+/V-/C+/C-.
Vor jedem Test: setze 5V/1A. Vorher *VSET?/*ISET? abfragen, Befehl, dann nochmal abfragen."""
import serial, time

ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=0.4)
ser.dtr = False; ser.rts = False
time.sleep(0.3); ser.reset_input_buffer()

def send(cmd, wait=0.4):
    ser.reset_input_buffer()
    ser.write(cmd); ser.flush()
    time.sleep(wait)
    return ser.read(ser.in_waiting) if ser.in_waiting else b""

def last_line(b):
    s = b.decode('ascii', errors='replace').replace('\r','')
    parts = [p for p in s.split('\n') if p]
    return parts[-1] if parts else "(none)"

def reset_state():
    send(b"*VSET050\r"); time.sleep(0.3)
    send(b"*ISET100\r"); time.sleep(0.3)

def vset_iset():
    v = last_line(send(b"*VSET?\r")); time.sleep(0.2)
    i = last_line(send(b"*ISET?\r")); time.sleep(0.2)
    return f"VSET={v} ISET={i}"

TESTS = [
    b"V+\r",
    b"V-\r",
    b"V+005\r",
    b"V-005\r",
    b"V+255\r",   # max +n - was passiert mit overflow?
    b"V-255\r",   # max -n - underflow
    b"C+\r",
    b"C-\r",
    b"C+010\r",
    b"C-010\r",
]

print(f"{'Befehl':<10} | {'Vorher':<24} | {'Antwort':<35} | {'Nachher':<24}")
print("-" * 105)

for cmd in TESTS:
    reset_state()
    before = vset_iset()
    response = send(cmd)
    cmd_str = cmd.decode('ascii').replace('\r', '\\r')
    resp_str = last_line(response)[:35]
    time.sleep(0.2)
    after = vset_iset()
    print(f"{cmd_str:<10} | {before:<24} | {resp_str:<35} | {after:<24}")

# Final reset
reset_state()
print(f"\nReset: {vset_iset()}")
ser.close()
