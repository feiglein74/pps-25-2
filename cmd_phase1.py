#!/usr/bin/env python3
"""Phase 1: Nur sichere Read-Only Befehle. Keine Side-Effects."""
import serial, time

ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=0.4)
ser.dtr = False; ser.rts = False
time.sleep(0.3); ser.reset_input_buffer()

def send(cmd, wait=0.4):
    ser.reset_input_buffer()
    ser.write(cmd); ser.flush()
    time.sleep(wait)
    return ser.read(ser.in_waiting) if ser.in_waiting else b""

def fmt(b):
    if not b: return "(no response)"
    s = "".join(chr(c) if 32<=c<127 else "." for c in b)
    return f"{b.hex(' '):<40} {s!r}"

# State herstellen für reproducible reads
print("Setup: *ISET100 / *VSET050 (1A / 5V)")
send(b"*ISET100\r"); time.sleep(0.3)
send(b"*VSET050\r"); time.sleep(0.5)

TESTS = [
    b"U\r",
    b"Z\r",
    b"*IDN?\r",
    b"*ICR?\r",
    b"MV\r",
    b"MC\r",
    b"MA\r",
    b"MX\r",
    b"MV?\r",
    b"RV\r",
    b"RC\r",
    b"RS\r",
    b"*VSET?\r",
    b"*ISET?\r",
    b"*VOUT?\r",
    b"*IOUT?\r",
    b"*CLS\r",
]

print(f"\n{'Befehl':<12} | Antwort")
print("-" * 90)
for cmd in TESTS:
    r = send(cmd)
    cmd_str = cmd.decode('ascii').replace('\r', '\\r')
    print(f"{cmd_str:<12} | {fmt(r)}")
    time.sleep(0.2)

# State final
print(f"\nState am Ende: ", end="")
mv = send(b"MV\r"); time.sleep(0.2)
mc = send(b"MC\r")
print(f"MV={fmt(mv)[:30]}  MC={fmt(mc)[:30]}")

ser.close()
