#!/usr/bin/env python3
"""Sendet kontinuierlich U\\r mit RTS=False/DTR=False."""
import serial, time
ser = serial.Serial('/dev/ttyUSB0', 4800, timeout=0.1)
ser.rts = False
ser.dtr = False
print('RTS=False, DTR=False. Sende U alle 200ms...', flush=True)
n = 0
while True:
    ser.write(b'U\r')
    n += 1
    if n % 25 == 0:
        r = ser.read(ser.in_waiting) if ser.in_waiting else b''
        print(f'#{n} resp={r!r}', flush=True)
    time.sleep(0.2)
