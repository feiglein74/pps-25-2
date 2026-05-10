#!/usr/bin/env python3
"""Probe mit explizit gesetzten Handshake-Leitungen."""
import time, serial

PORT = "/dev/ttyUSB0"
BAUDS = [9600, 19200, 4800, 2400]
PROBES = [b"*IDN?\r\n", b"GETD\r", b"*IDN?", b"\r", b"V?\r"]

def hexdump(b):
    if not b: return "(leer)"
    p = "".join(chr(c) if 32 <= c < 127 else "." for c in b)
    return f"{b.hex(' ')}  |  {p!r}"

for baud in BAUDS:
    for dtr, rts in [(True, True), (True, False), (False, True), (False, False)]:
        for parity in ["N", "E"]:
            try:
                ser = serial.Serial(PORT, baud, bytesize=8, parity=parity,
                                    stopbits=1, timeout=0.4,
                                    dsrdtr=False, rtscts=False, xonxoff=False)
                ser.dtr = dtr
                ser.rts = rts
                time.sleep(0.1)
                ser.reset_input_buffer()
                # passiv 0.3s
                time.sleep(0.3)
                pas = ser.read(ser.in_waiting) if ser.in_waiting else b""
                # ein probe
                for p in PROBES:
                    ser.reset_input_buffer()
                    ser.write(p); ser.flush()
                    time.sleep(0.4)
                    r = ser.read(ser.in_waiting or 1)
                    r += ser.read(ser.in_waiting) if ser.in_waiting else b""
                    if r or pas:
                        print(f"baud={baud} par={parity} dtr={dtr} rts={rts} "
                              f"passiv={hexdump(pas)} probe={hexdump(p)} "
                              f"resp={hexdump(r)}")
                ser.close()
            except Exception as e:
                print(f"  err {baud}/{parity}: {e}")
print("Fertig. Wenn nichts ausgegeben wurde -> komplett stille Leitung.")
