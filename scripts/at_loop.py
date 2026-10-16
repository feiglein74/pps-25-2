#!/usr/bin/env python3
"""@ command test - aktiviert Loop, sammelt Bytes, deaktiviert."""
import serial, time

ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=0.1)
ser.dtr = False; ser.rts = False
time.sleep(0.3); ser.reset_input_buffer()

def listen(seconds, label):
    """Lausche für N Sekunden, sammle alles und gib aus."""
    print(f"  [{label}] lausche {seconds}s...")
    deadline = time.time() + seconds
    buf = bytearray()
    while time.time() < deadline:
        n = ser.in_waiting
        if n: buf.extend(ser.read(n))
        time.sleep(0.05)
    if buf:
        s = "".join(chr(c) if 32<=c<127 else "." for c in buf)
        print(f"  empfangen ({len(buf)} bytes):")
        print(f"    hex: {buf.hex(' ')[:200]}{'...' if len(buf)>50 else ''}")
        print(f"    asc: {s[:200]!r}")
    else:
        print(f"  (nichts empfangen)")
    return buf

print("@ raus (Loop start)")
ser.write(b'@\r'); ser.flush()
buf1 = listen(5, "während @ Loop")

print("\n@ raus (Loop stop, weil toggle)")
ser.write(b'@\r'); ser.flush()
buf2 = listen(2, "nach Stop")

ser.close()
