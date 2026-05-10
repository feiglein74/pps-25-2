#!/usr/bin/env python3
"""C-Befehl Übergangs-Test mit MA (kohärente V+C Messung).
Sweep C runter um den Übergangspunkt sauber zu sehen."""
import serial, time

ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=0.4)
ser.dtr = False; ser.rts = False
time.sleep(0.3); ser.reset_input_buffer()

def send(c):
    ser.reset_input_buffer()
    ser.write(c); ser.flush(); time.sleep(0.3)
    return ser.read(ser.in_waiting) if ser.in_waiting else b""

def last(b):
    s = b.decode('ascii', errors='replace').replace('\r','').split('\n')
    return [p for p in s if p][-1] if s else "(none)"

# Erst sauber auf 5V/1A
send(b"*VSET050\r"); time.sleep(0.3)
send(b"*ISET100\r"); time.sleep(0.5)
print(f"Baseline: MA={last(send(b'MA\r'))}")
print()

# Sweep C runter um Übergangspunkt
sweep = [80, 60, 50, 45, 40, 38, 35, 32, 30, 25, 20]
trigger_at = None

for c in sweep:
    send(f"C{c:03d}\r".encode())
    time.sleep(0.6)   # Last Zeit zum Reagieren geben
    ma = last(send(b"MA\r"))
    print(f"C{c:03d}  →  MA={ma}", flush=True)
    # MA Format: "VVV CCC" - parse
    try:
        v, i = ma.split()
        v, i = int(v), int(i)
        # Trigger wenn V deutlich gesackt ODER MC nahe 0
        if v < 30 or i < 3:
            print(f"  ⚠ Übergang erreicht (V={v} I={i})")
            trigger_at = c
            break
    except (ValueError, AttributeError):
        print(f"  Antwort nicht parsbar: {ma!r}")
    time.sleep(0.5)

if trigger_at:
    # Recover
    rec = sweep[sweep.index(trigger_at) - 1] if sweep.index(trigger_at) > 0 else 100
    print(f"\nRecovery: C{rec:03d}, warte 30s...")
    send(f"C{rec:03d}\r".encode())
    time.sleep(30)
    print(f"Nach 30s: MA={last(send(b'MA\r'))}")

# Cleanup
print("\nReset zu C100")
send(b"C100\r")
time.sleep(0.5)
print(f"Final: MA={last(send(b'MA\r'))}")
ser.close()
