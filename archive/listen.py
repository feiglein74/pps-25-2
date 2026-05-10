#!/usr/bin/env python3
"""Permanenter RX-Listener. Zeigt alles was reinkommt sofort an."""
import serial, time, sys
PORT = "/dev/ttyUSB0"
BAUD = int(sys.argv[1]) if len(sys.argv)>1 else 4800

ser = serial.Serial(PORT, BAUD, timeout=0.05)
ser.dtr = True; ser.rts = True
print(f"LISTEN bei {BAUD} Baud. Strg-C oder timeout zum Beenden.")
print("Drück Knöpfe am Gerät, schick gleich Probebytes...\n")

# Nach 2s Stille schicken wir einmal "U\r"
last_send = time.time()
while True:
    n = ser.in_waiting
    if n:
        data = ser.read(n)
        ts = time.strftime("%H:%M:%S")
        printable = "".join(chr(c) if 32<=c<127 else "." for c in data)
        print(f"[{ts}] {n}B: {data.hex(' ')} | {printable!r}", flush=True)
    else:
        time.sleep(0.05)
    if time.time() - last_send > 3:
        ser.write(b"U\r")
        print(f"  -> sent U\\r", flush=True)
        last_send = time.time()
