#!/usr/bin/env python3
"""Systematischer Test aller bekannten PPS25/2 Befehle.

Strategie:
- Erst sicheren State herstellen (*ISET100, *VSET050 = 5V/1A)
- Jeden Befehl einzeln senden, raw-Antwort dokumentieren
- Vorsichtig bei Side-Effect-Befehlen (DD/DE/SL/Y/@)
- Nach potentiell gefährlichen Befehlen State prüfen mit MV/MC

Output: Markdown-tabelle für direkten Copy-Paste in COMMANDS.md
"""
import serial, time, sys

PORT = "/dev/ttyUSB0"
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=0.4)
ser.dtr = False; ser.rts = False
time.sleep(0.3); ser.reset_input_buffer()

def send(cmd_bytes, wait=0.4):
    """Send command, return raw response bytes."""
    ser.reset_input_buffer()
    ser.write(cmd_bytes); ser.flush()
    time.sleep(wait)
    r = ser.read(ser.in_waiting) if ser.in_waiting else b""
    return r

def fmt(b):
    """Format raw bytes for table."""
    if not b:
        return "(no response)"
    s = "".join(chr(c) if 32<=c<127 else "." for c in b)
    return f"`{b.hex(' ')}` `{s!r}`"

def state():
    """Liest aktuellen State (MV/MC)."""
    mv = send(b"MV\r"); time.sleep(0.2)
    mc = send(b"MC\r"); time.sleep(0.2)
    return f"MV={fmt(mv)[:40]}  MC={fmt(mc)[:40]}"

def safe_state():
    """Stelle sichere Konfiguration her: 5V/1A."""
    send(b"*ISET100\r"); time.sleep(0.3)
    send(b"*VSET050\r"); time.sleep(0.3)

# ===== Tests =====
results = []

print("=== State vor Test ===")
print(state())
print()
print("Stelle 5V/1A her")
safe_state()
print(state())
print()

# Liste: (cmd, beschreibung, side_effect)
TESTS = [
    # Sichere Read-only Befehle erst
    (b"U\r",         "U — IDN single letter",        False),
    (b"Z\r",         "Z — Copyright single letter",  False),
    (b"*IDN?\r",     "*IDN? — IDN string",           False),
    (b"*ICR?\r",     "*ICR? — Copyright string",     False),
    (b"MV\r",        "MV — Voltage measure",         False),
    (b"MC\r",        "MC — Current measure",         False),
    (b"MA\r",        "MA — V then C (both)",         False),
    (b"MX\r",        "MX — $B1 (unknown)",           False),
    (b"MV?\r",       "MV? — same as MV",             False),
    (b"RV\r",        "RV — read voltage setpoint",   False),
    (b"RC\r",        "RC — read current setpoint",   False),
    (b"RS\r",        "RS — read status?",            False),
    (b"*VSET?\r",    "*VSET? — query setpoint",      False),
    (b"*ISET?\r",    "*ISET? — query setpoint",      False),
    (b"*VOUT?\r",    "*VOUT? — measured V",          False),
    (b"*IOUT?\r",    "*IOUT? — measured I",          False),
    (b"*CLS\r",      "*CLS — clear status",          False),
    # Inkrement-Befehle (Side-Effect: ändern Setpoint)
    (b"V+\r",        "V+ — voltage += 1",             True),
    (b"V-\r",        "V- — voltage -= 1",             True),
    (b"V+005\r",     "V+005 — voltage += 5",          True),
    (b"V-005\r",     "V-005 — voltage -= 5",          True),
    (b"C+\r",        "C+ — current += 1",             True),
    (b"C-\r",        "C- — current -= 1",             True),
    # Status-Sub
    (b"SD\r",        "SD — clear bit 6 of $B5",       True),
    (b"SE\r",        "SE — set bit 6 of $B5",         True),
    # *S subcommands
    (b"*SR?\r",      "*SR? — status read?",           True),
    (b"*SET?\r",     "*SET? — ?",                     True),
]

print(f"{'Befehl':<14} | Antwort")
print("-" * 80)

for cmd, desc, side_effect in TESTS:
    response = send(cmd)
    cmd_str = cmd.decode('ascii').replace('\r', '\\r')
    print(f"{cmd_str:<14} | {fmt(response)}")
    results.append((cmd_str, desc, fmt(response), side_effect))
    if side_effect:
        # Nach side-effect kurz state prüfen
        st = state()
        print(f"{'  → state':<14} | {st}")
    time.sleep(0.3)

# Finaler state
print()
print("=== State nach Test ===")
print(state())

# Restore safe state
print("Restore: *VSET050 / *ISET100")
safe_state()
print(state())

ser.close()

# Markdown-Tabelle für copy-paste
print("\n\n=== MARKDOWN ===")
print("| Befehl | Antwort |")
print("|---|---|")
for cmd_str, desc, resp, _ in results:
    print(f"| `{cmd_str}` | {resp} |")
