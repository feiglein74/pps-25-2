#!/usr/bin/env python3
"""Multi-baud send + passive listen."""
import serial, time
PORT = '/dev/ttyUSB0'

def hx(b):
    if not b: return '(nichts)'
    return b.hex(' ') + ' | ' + repr(''.join(chr(c) if 32<=c<127 else '.' for c in b))

print('Multi-Baud Send/Listen', flush=True)
for baud in [4800, 9600, 2400, 1200, 600, 300, 19200, 38400]:
    print(f'\n=== {baud} ===', flush=True)
    try:
        ser = serial.Serial(PORT, baud, timeout=0.5)
        ser.dtr = False; ser.rts = False
        time.sleep(0.2)
        ser.reset_input_buffer()
        # passiv 1s
        time.sleep(1.0)
        pas = ser.read(ser.in_waiting) if ser.in_waiting else b''
        if pas:
            print(f'  passiv: {hx(pas)}', flush=True)
        for c in ['U','Z','V','S','?','D','M']:
            ser.reset_input_buffer()
            ser.write(c.encode()+b'\r')
            ser.flush()
            time.sleep(1.5)
            r = ser.read(ser.in_waiting) if ser.in_waiting else b''
            if r:
                print(f'  ++ {c!r} -> {hx(r)}', flush=True)
        ser.close()
    except Exception as e:
        print(f'  ERR {baud}: {e}', flush=True)
print('\nFertig.', flush=True)
