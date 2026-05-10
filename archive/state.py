#!/usr/bin/env python3
"""Halte serielle Leitungen statisch. Aufruf: state.py <RTS> <DTR>
RTS/DTR: 'h' = high (+10V) oder 'l' = low (-10V)"""
import serial, time, sys

rts = sys.argv[1].lower() == 'h' if len(sys.argv) > 1 else False
dtr = sys.argv[2].lower() == 'h' if len(sys.argv) > 2 else False

ser = serial.Serial('/dev/ttyUSB1', 4800, timeout=0.1)
ser.rts = rts
ser.dtr = dtr
print(f"RTS={'+10V' if rts else '-10V'}  DTR={'+10V' if dtr else '-10V'}  TX=idle(-10V)", flush=True)
while True:
    time.sleep(60)
