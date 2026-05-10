#!/usr/bin/env python3
"""Sender + Listener kombiniert.
Schickt alle 1s einen Befehl, gibt sofort aus was reinkommt."""
import serial, time, sys
PORT = "/dev/ttyUSB0"
BAUD = int(sys.argv[1]) if len(sys.argv)>1 else 4800

ser = serial.Serial(PORT, BAUD, timeout=0.05)
ser.dtr = False; ser.rts = False
print(f"TALK @ {BAUD}. Sende U\\r jede Sekunde. Strg-C zum Stop.\n", flush=True)

def emit(line):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {line}", flush=True)

last_send = 0
n = 0
while True:
    # RX prüfen
    avail = ser.in_waiting
    if avail:
        data = ser.read(avail)
        printable = "".join(chr(c) if 32<=c<127 else "." for c in data)
        emit(f"<<< {len(data)}B: {data.hex(' ')} | {printable!r}")
    # alle 1s senden
    if time.time() - last_send > 1.0:
        ser.write(b"U\r")
        n += 1
        emit(f">>> U\\r  (#{n})")
        last_send = time.time()
    time.sleep(0.02)
