#!/usr/bin/env python3
"""
Probe für unbekanntes RS232-Labornetzteil (Roth PPS 25-2).
Erst passiv lauschen, dann aktiv mit gängigen Protokoll-Dialekten anpingen.
"""
import sys, time, serial

PORT = "/dev/ttyUSB0"
BAUDS = [9600, 19200, 4800, 38400, 2400, 1200, 57600, 115200]

# (Beschreibung, Bytes, Wartezeit nach Senden)
PROBES = [
    ("SCPI *IDN? (CRLF)",        b"*IDN?\r\n", 0.5),
    ("SCPI *IDN? (LF)",          b"*IDN?\n",   0.5),
    ("Manson GETD",              b"GETD\r",    0.5),
    ("Manson GMOD",              b"GMOD\r",    0.5),
    ("Korad *IDN? (kein Term.)", b"*IDN?",     0.5),
    ("Korad VOUT1?",             b"VOUT1?",    0.5),
    ("Einfaches CR",             b"\r",        0.3),
    ("Einfaches LF",             b"\n",        0.3),
    ("? + CR",                   b"?\r",       0.3),
    ("HELP + CR",                b"HELP\r",    0.5),
]

def hexdump(b: bytes) -> str:
    if not b:
        return "(leer)"
    printable = "".join(chr(c) if 32 <= c < 127 else "." for c in b)
    return f"{b.hex(' ')}  |  {printable!r}"

def listen(ser, seconds, label):
    """Passiv N Sekunden lauschen."""
    print(f"  [{label}] {seconds}s lauschen...", end="", flush=True)
    end = time.time() + seconds
    buf = b""
    while time.time() < end:
        n = ser.in_waiting
        if n:
            buf += ser.read(n)
        time.sleep(0.05)
    if buf:
        print(f" -> {len(buf)}B: {hexdump(buf)}")
    else:
        print(" stille.")
    return buf

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "scan"

    if mode == "listen":
        # Lange passiv lauschen bei einer Baudrate
        baud = int(sys.argv[2]) if len(sys.argv) > 2 else 9600
        with serial.Serial(PORT, baud, timeout=0.1) as ser:
            print(f"Lausche bei {baud} 8N1 für 15s. Drück jetzt Knöpfe am Gerät / schalte ein/aus...")
            listen(ser, 15, f"{baud}")
        return

    # Default: Vollständiger Scan
    for baud in BAUDS:
        print(f"\n=== {baud} 8N1 ===")
        try:
            with serial.Serial(PORT, baud, bytesize=8, parity="N",
                               stopbits=1, timeout=0.3) as ser:
                ser.reset_input_buffer()
                # 1) Passiv 1.5s lauschen
                listen(ser, 1.5, "passiv")
                # 2) Probes
                for desc, payload, wait in PROBES:
                    ser.reset_input_buffer()
                    ser.write(payload)
                    ser.flush()
                    time.sleep(wait)
                    buf = ser.read(ser.in_waiting or 1)
                    extra = ser.read(ser.in_waiting) if ser.in_waiting else b""
                    buf += extra
                    tag = "++" if buf else "  "
                    print(f"  {tag} {desc:32s} send={hexdump(payload):50s}  resp={hexdump(buf)}")
        except serial.SerialException as e:
            print(f"  Fehler: {e}")

if __name__ == "__main__":
    main()
