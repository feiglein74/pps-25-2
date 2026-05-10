#!/usr/bin/env python3
"""Sendet alle 500ms *VOUT?\\r bei 76800 Baud, zum Beobachten der RMT-LED."""
import serial, time
ser = serial.Serial('/dev/ttyUSB0', 76800, timeout=0.05)
ser.dtr=False; ser.rts=False
time.sleep(0.3); ser.reset_input_buffer()
print('Sende *VOUT?\\r alle 500ms bei 76800 Baud. Strg-C zum Beenden.', flush=True)
n = 0
while True:
    ser.write(b'*VOUT?\r'); ser.flush()
    n += 1
    if n % 10 == 0:
        r = ser.read(ser.in_waiting) if ser.in_waiting else b''
        if r:
            p = ''.join(chr(c) if 32<=c<127 else '.' for c in r)
            print(f'#{n}: {len(r)}B {r.hex(" ")} | {p!r}', flush=True)
        else:
            print(f'#{n}: still kein RX', flush=True)
    time.sleep(0.5)
