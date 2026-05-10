#!/usr/bin/env python3
"""C-Befehl Hardware-Verifikation:
Sweep C von 100 abwärts. Beobachte MC. Wenn MC abfällt = Last hat getriggert (Spannung gesackt).
Dann einen Schritt höher, 30s warten, MC erneut lesen → muss recovered sein."""
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

def state():
    return f"VSET={last(send(b'*VSET?\r'))} ISET={last(send(b'*ISET?\r'))} MV={last(send(b'MV\r'))} MC={last(send(b'MC\r'))}"

print(f"Baseline: {state()}")
print()

# Sweep C abwärts
sweep = [100, 80, 60, 50, 40, 35, 30, 25, 20]
trigger_at = None
prev_c = sweep[0]

for c in sweep:
    send(f"C{c:03d}\r".encode())
    time.sleep(0.5)
    mc = last(send(b"MC\r"))
    mv = last(send(b"MV\r"))
    print(f"C{c:03d}  →  MV={mv}  MC={mc}", flush=True)
    # MC sollte um 040 liegen wenn alles ok. Wenn unter 030 → Last hat getriggert
    try:
        mc_int = int(mc)
        if mc_int < 30:
            print(f"  ⚠ Last hat getriggert (MC={mc} unter erwartung)")
            trigger_at = c
            break
    except ValueError:
        print(f"  Antwort nicht numerisch: {mc}")
    time.sleep(0.5)

if trigger_at:
    # Einen Schritt höher
    recovery_c = sweep[sweep.index(trigger_at) - 1]
    print(f"\nSetze C{recovery_c:03d} (= ein Schritt höher) für Recovery")
    send(f"C{recovery_c:03d}\r".encode())
    print("Warte 30s auf Recovery...")
    time.sleep(30)
    print(f"Nach 30s: {state()}")
else:
    print("\nKein Trigger im Sweep beobachtet")

# Cleanup: C100 zurück
print("\nReset zu C100")
send(b"C100\r")
time.sleep(0.5)
print(f"Final: {state()}")
ser.close()
