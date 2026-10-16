#!/usr/bin/env python3
"""C-Sweep mit ECHTER Beobachtung: pro Wert mehrere MA-Samples, Sample-Verlauf zeigen.
Ziel: sehen wo es zerbricht, wie schnell, ob es stabilisiert oder oszilliert."""
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

def ma():
    """Single MA query, returns (V, I) as ints, or (None, None)."""
    r = last(send(b"MA\r"))
    try:
        v, i = r.split()
        return int(v), int(i), r
    except (ValueError, AttributeError):
        return None, None, r

# Reset zu definiertem state
print("Setup: VSET050, ISET100")
send(b"*VSET050\r"); time.sleep(0.3)
send(b"*ISET100\r"); time.sleep(0.5)

# Baseline: 5 MA-Samples
print(f"\nBaseline samples (5x):")
for i in range(5):
    v, c, raw = ma()
    print(f"  {i+1}: {raw}", flush=True)
    time.sleep(0.3)

# Sweep
sweep = [50, 45, 42, 40, 38, 36, 34, 32, 30]
print(f"\nSweep mit jeweils 5 MA-Samples (200ms Pause):")
print(f"{'C':>4} | {'sample 1':>10} {'sample 2':>10} {'sample 3':>10} {'sample 4':>10} {'sample 5':>10}")
print("-" * 70)

trigger_at = None
for c in sweep:
    send(f"C{c:03d}\r".encode())
    time.sleep(0.5)
    samples = []
    for _ in range(5):
        _, _, raw = ma()
        samples.append(raw)
        time.sleep(0.2)
    print(f"C{c:03d} | " + "  ".join(f"{s:>10}" for s in samples), flush=True)
    # Trigger detection: wenn V im letzten Sample < 30 oder I < 5
    try:
        v_last, i_last = samples[-1].split()
        v_last, i_last = int(v_last), int(i_last)
        if v_last < 30 or i_last < 5:
            trigger_at = c
            print(f"  ⚠ Trigger erkannt bei C{c:03d}")
            break
    except ValueError:
        pass

# Nach Trigger: längere Beobachtung
if trigger_at:
    print(f"\nNach Trigger - 10 weitere Samples mit 1s Pause (sehen wie es weiter geht):")
    for i in range(10):
        _, _, raw = ma()
        print(f"  +{i+1}s: {raw}", flush=True)
        time.sleep(1.0)

    # Recovery: zurück auf C100, dann 60s warten, dann beobachten
    print(f"\nRecovery: C100 setzen, dann 60s warten und beobachten alle 5s:")
    send(b"C100\r"); time.sleep(0.5)
    for i in range(12):
        _, _, raw = ma()
        print(f"  Recovery +{(i+1)*5}s: {raw}", flush=True)
        time.sleep(5)

print(f"\nFinal: MA={last(send(b'MA\r'))}")
ser.close()
