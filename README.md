# Roth PPS 25/2 — RS-232 command set, firmware & repair

Reverse-engineered documentation for the **Roth PPS 25/2** (PPS-25/2) linear lab power supply
(1991, 0–25.5 V / 0–2.55 A) with the optional **PPS24 RS-232 interface card**: full remote
command set, firmware dump and disassembly, hardware notes and an ESD repair log.
The original manufacturer manual appears to be lost — this is the replacement.

![License](https://img.shields.io/github/license/feiglein74/pps-25-2)
![Interface](https://img.shields.io/badge/interface-RS--232%209600%208N1-555)
![Device](https://img.shields.io/badge/device-Roth%20PPS%2025%2F2-2b6cb0)

```text
> *IDN?
PPS-25/2 V1.1 91.10.20
> *ISET100      (current limit 1.00 A)
> *VSET050      (output 5.0 V)
> MA
049 001         (measured: 4.9 V, 0.01 A)
```

## Quickstart

```bash
pip install pyserial
```

```python
import serial
ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)   # 8N1, no flow control
ser.write(b"*ISET100")   # set the current limit FIRST (1.00 A)
ser.write(b"*VSET050")   # then the voltage (5.0 V)
ser.write(b"MA"); print(ser.read(100))   # measured V and I
```

- The PPS-25/2 is a **DTE** — with a normal USB-RS-232 adapter you need a **null-modem adapter**.
- Without `*ISET` first, the output stays capped at ~2.2 V regardless of `*VSET`.
- `SL` (set local) leaves remote mode **and resets all setpoints to 0**.
- Don't hot-plug the RS-232 cable: an ESD spike killed a 74LS373 on the logic board.

> Detailed documentation is in German.

## Summary (English)

- **Device:** Roth Hardware + Software (Grafrath, Germany), PPS 25/2, firmware "V1.1 91.10.20".
  MC6803 CPU, 8 KB EPROM, R6522 VIA, µPD7004C ADC, 2× TLC7524 DAC (8 bit, 0.1 V / 0.01 A steps),
  X2444 NOVRAM for 8 memory slots.
- **State:** fully working after repair. Front panel, display, memories and RS-232 remote
  control verified; output accuracy < 0.3 %.
- **Command set:** `*VSET`/`*ISET` (setpoints), `*VOUT?`/`*IOUT?`, `MV`/`MC`/`MA` (measure),
  `*IDN?`, `Y` (display self test), `@` (UART 0x55 test stream), `DD`/`DE` (display off/on)
  and more — complete matrix with firmware addresses in [docs/COMMANDS.md](docs/COMMANDS.md).
- **Repair:** the upper 74LS373 (keypad latch) had D6 shorted to GND after an ESD event;
  replaced and socketed. Diagnosis log in [docs/TODO.md](docs/TODO.md).
- **Files:** firmware dumps and disassembly in [`firmware/`](firmware/), a custom
  6803 disassembler and test scripts in [`scripts/`](scripts/), scope captures in [`scope/`](scope/).
- **Website:** <https://feiglein74.github.io/pps-25-2/>

---

## Ausführliche Dokumentation (Deutsch)


Komplette Zerlegung, Firmware-Dump, RS-232-Protokoll-Decodierung, ESD-Schadens-Diagnose
und Reparatur-Anleitung für das **Roth PPS 25/2 Labornetzteil** (deutsches Labornetzteil
von 1991, 0–25 V / 0–2,5 A) mit der optionalen **PPS24 RS-232-Schnittstellenkarte**.

Wenn du eines geerbt oder gefunden hast und es per RS-232 ansteuern willst, hast du hier
den vollständigen Befehlssatz, die Hardware-Übersicht und die Reparatur-Historie.

## Was es ist

Ein lineares Labornetzteil von 1991, gebaut von *Roth Hardware + Software, 8082 Grafrath*.
Zwei dreistellige 7-Segment-Anzeigen (V und I), 10 beleuchtete Drucktaster (Memory-Recall,
Parameter-Auswahl), 3-Platinen-Sandwich (Display / Logik / Analog) plus separater
Ringkerntrafo und hintere lineare Endstufe.

| Spezifikation | Wert |
|---|---|
| Output-Range | 0–25,5 V / 0–2,55 A (8-Bit DAC, 0,1 V / 0,01 A pro Schritt) |
| Genauigkeit | < 0,3 % (verifiziert: VSET=075 → 7,518 V am Brymen-Multimeter) |
| Output-Elko | 470 µF |
| Primärer Sieb-Cap | 4700 µF |
| Memory-Speicher | 8 Plätze (V/I-Paare im NOVRAM, ~6 normalerweise genutzt) |
| Schnittstellen | Frontpanel + RS-232 (PPS24-Karte) |
| Firmware | "PPS-25/2 V1.1 91.10.20" |

## Hardware-Aufbau

3-Platinen-Sandwich hinter der Frontplatte + Trafo + hintere Analog-/Leistungs-Stufe.

```
[Display-Platine] — [Logik-Platine] — [Analog-Buffer-Platine]   |  [Trafo]  |  [Endstufe + Kühlkörper]
   10 Tasten           MC6803             LM324                     primär +    2× LM324, 4700 µF,
   2× 3-stelliges      + EPROM            Buffer für                Hilfs-      Längstransistoren
   7-Segment, LEDs     + VIA + ADC        TLC7524-DACs              wicklung    7805 für Logik-5V
                       + GAL + 2×         + Pegelwandlung
                       74LS373 etc.       zur Endstufe
                       + X2444 NOVRAM
```

### Logik-Platine (das Hirn)

| Chip | Funktion |
|---|---|
| Motorola **MC6803P** | 8-Bit-MCU, 4 MHz Quarz (E = 1 MHz), Mode 2 (Expanded Multiplexed) |
| TI **TMS27C64-2JL** | 8 KB EPROM mit Firmware |
| Rockwell **R6522P** | VIA — Display-Multiplexing, Tasten-Matrix-Scan, X2444-Bit-Banging |
| Lattice **GAL16V8-25QNC** | Adress-Decoder für `$6000-$6500` Chip-Selects |
| 2× **SN74LS373N** | Adress-Demux-Latch (unten) + Tasten-Eingangs-Latch (oben, **siehe Reparatur unten**) |
| **74LS133, 74LS273, 74LS14N** | Glue-Logic für Tasten-Scan + IRQ + Reset |
| NEC **µPD7004C** | 4-Kanal 10-Bit ADC (V/I-Messung) |
| 2× **TLC7524CN** | 8-Bit Multiplying-DACs für V/I-Setpoints |
| **X2444P** (Xicor) | 256-Bit NOVRAM — speichert die 8 Memory-Plätze über Stromausfall |

### PPS24 RS-232-Karte

| Chip | Funktion |
|---|---|
| Intersil **ICL232CPE** | RS-232-Pegelwandler (TTL ↔ ±10 V) |
| Motorola **MC14060BCP** + 2,4576 MHz Quarz | 14-stufiger Teiler für Baudraten-Takt |

Der 4060-Jumper bei Q5 liefert 76.800 Hz, die der 6803 SCI als externen Takt verwendet.
Per MC6801-Spec ist die Bit-Rate **Takt / 8 = 9600 Baud**.

### Endstufe

| Komponente | Funktion |
|---|---|
| 2× **LM324N** | 8 Op-Amps für CV/CC-Loops, Mess-Verstärker, Schutz-Komparator (CC reagiert in ~300 ms — gemütliche Regelschleife) |
| Brückengleichrichter + Kühlkörper | Längstransistoren |
| 4700 µF | primärer Sieb-Elko |
| 470 µF | Output-Elko |
| Trim-Potis | Kanal-Kalibrierung |

### Memory-Map

| Adresse | Funktion |
|---|---|
| `$0000-$007F` | MC6803 internes RAM |
| `$0080-$008F` | RAM-Image vom X2444 NOVRAM (8× 16-Bit Memory-Plätze) |
| `$6000-$600F` | R6522 VIA |
| `$6014` | Bit 1 = X2444 SK-Clock |
| `$6100` | Tasten-Matrix-Latch (oberer 74LS373) |
| `$6300/$6301` | µPD7004C ADC |
| `$6400` | TLC7524 — Voltage-DAC |
| `$6500` | TLC7524 — Current-DAC |
| `$E000-$FFFF` | EPROM-Firmware |

## Funktionsprinzip

1. MCU schreibt 8-Bit-Wert in TLC7524 bei `$6400` (V) bzw. `$6500` (I).
2. DAC erzeugt analogen Setpoint, gepuffert vom LM324 auf der Analog-Platine.
3. Setpoint geht zur Endstufe — CV-Loop hält Output bis CC-Limit greift.
4. ADC misst echtes V und I per Multiplexer, gibt's per `MV`/`MC`-Befehl zurück.
5. Memory-Plätze: NOVRAM (X2444) speichert 8 V/I-Paare, beim Boot ins RAM `$0080+`
   geladen, beim "Memory Store"-Tastendruck zurückgeschrieben.

## RS-232-Protokoll

**9600 8N1, kein Flow-Control.** Alle Befehle enden mit `\r` (0x0D).

**Kritisch:** PPS-25/2 ist DTE. Wenn dein USB-RS-232-Adapter auch DTE ist (üblich),
**brauchst du einen Null-Modem-Adapter** dazwischen — sonst senden beide auf den gleichen
Pin und du bekommst nur Garbage.

### Pflicht-Sequenz für Remote-Steuerung

```python
ser.write(b"*ISET100\r")   # Strom-Limit MUSS zuerst gesetzt werden
ser.write(b"*VSET050\r")   # dann Spannung (5,0 V hier)
```

Wenn du `*ISET<n>\r` weglässt, ist der Default-Stromlimit so niedrig, dass die Spannung
unabhängig von `*VSET<n>` bei ~2,2 V capped. Das war das mehrtägige Mysterium während
des Reverse Engineering — siehe [docs/TODO.md](docs/TODO.md) für die ganze Saga.

### Befehlssatz (Übersicht)

Vollständig in [docs/COMMANDS.md](docs/COMMANDS.md). Highlights:

| Befehl | Wirkung |
|---|---|
| `*VSET<nnn>\r` | Spannung setzen (000..255 → 0..25,5 V in 0,1-V-Schritten) |
| `*ISET<nnn>\r` | Strom-Limit setzen (000..255 → 0..2,55 A in 0,01-A-Schritten) |
| `*VSET?\r` / `*ISET?\r` | Setpoint lesen |
| `MV\r` / `MC\r` / `MA\r` | Spannung / Strom / beides messen |
| `*VOUT?\r` / `*IOUT?\r` | Wie MV/MC (echte ADC-Messung) |
| `*IDN?\r` / `U\r` | "PPS-25/2 V1.1 91.10.20" |
| `Y\r` | Service-Display-Selbsttest (LEDs zyklisch, 7-Seg zählt, DPs wandern) |
| `@\r` | UART-Test-Modus — toggelt kontinuierlichen 0x55-Stream (gut für Baud-Verifikation) |
| `SL\r` | ⚠ Set Local — verlässt Remote-Mode UND cleart alle Setpoints auf 0 |
| `DD\r` / `DE\r` | Display Disable / Enable |

### Quick-Test

```python
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("comserver.local", 8000))   # via W&T Com-Server mit Null-Modem-Adapter
s.send(b"*IDN?\r")
print(s.recv(100))   # → b'*IDN?\r\nPPS-25/2 V1.1 91.10.20\r\n'
```

Oder mit direktem USB-RS-232-Adapter (muss einen MAX232 oder echte RS-232-Pegel haben —
TTL-only-Adapter wie PL2303 treiben den ICL232 nicht richtig):

```python
import serial
ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
ser.write(b"*ISET100\r"); ser.read(100)
ser.write(b"*VSET050\r"); ser.read(100)
```

## ESD-Reparatur (Mai 2026)

Beim Versuch einen anderen RS-232-Adapter anzustecken hat ein ESD-Spike beim Hot-Plug
den **oberen 74LS373** (Tasten-Eingangs-Latch) zerschossen — Pin 14 (D6) war intern
mit Pin 10 (GND) kurzgeschlossen.

**Symptome:** Tasten reagierten nicht oder falsch zugeordnet (Memory 1 triggerte Memory 2),
Memory-2-LED ging nach paar Sekunden von selbst an, MCU crashte kurz danach.

**Diagnose:** RS-232 funktionierte noch über TTL-Direkt-Setup → MCU/SCI/EPROM alle OK;
`Y`-Selbsttest lief → Display + LED-Treiber OK; `*VSET050\r` + Multimeter zeigte
DAC + Output-Stage OK. Continuity-Test am abgesteckten Tasten-Pfostenstecker zeigte
Memory-2-Eingang zu GND auf der Platine selbst kurzgeschlossen → zurückverfolgt zu
74LS373 Pin 14/10 internem Short.

**Fix:** Pins einzeln abgeklippt (Chip war eh tot), Pad-Reste entfernt,
SN74LS373N **in einen frischen Sockel** eingelötet für künftigen einfachen Tausch.
Zeit von "was ist los?" bis "läuft wieder komplett": ein Nachmittag.

Vollständiger Diagnose-Verlauf + Methodik-Lessons in [docs/TODO.md](docs/TODO.md).

## Dateien

```
README.md            Diese Datei
docs/                Dokumentation
  COMMANDS.md          Vollständige RS-232-Befehlsmatrix
  TODO.md              RE-Historie, ESD-Schaden, Reparatur, Methodik
  SUMMARY.md           Frühere Hardware-Notizen (größtenteils durch README abgelöst)
firmware/            EPROM-Dumps und Disassembly
  firmware.bin         Original-Dump (8192 Bytes, MD5 803de2bfb2f56135aeacf3c0f987c47b)
  firmware2.bin        Verifikations-Dump (identisch)
  firmware_modified.bin  Gepatchte Variante ($26 statt $27 bei 0x10BF, "Plan B")
  chip_28c64a_backup.bin Dump eines 28C64A-EEPROMs (Inhalt weicht von firmware.bin ab)
  dis.lst              Disassembly (~1780 Instruktionen)
scripts/             Python-Werkzeuge
  dis6803.py           Eigener 6803-Disassembler mit Control-Flow-Following
  cmd_phase1.py        Befehlsmatrix-Verifikation
  cmd_phase2_inc.py    Befehlsmatrix-Verifikation (inkrementell)
  vset_full.py         DAC-Sweep mit Setpoint und ADC-Messung
  c_verify3.py         CC-Mode-Trigger-Charakterisierung mit kohärentem MA-Sampling
  at_loop.py           UART-Test-Mode-Validator
  c_oszi_trigger.py    Einzelner CC-Trigger für Oszilloskop-Analyse
  archive/             Frühere Erkundungs-Skripte (probe*.py, listen*.py, Baud-Sweeps etc.)
scope/               Oszilloskop-Captures
  scope.png, scope2.png
  messwert-nach-last-watchdog/  Tek TDS1002B Captures vom CC-Trigger
```

## Danksagung

Reverse-engineered zusammen mit Claude (Anthropic). Hardware-in-the-Loop-Exploration,
Firmware-Dump und Disassembly, RS-232-Protokoll-Decode, ESD-Schadens-Diagnose,
Single-Chip-Tausch.

Wer ein Roth PPS-25/2 hat und das nützlich findet, gerne ein Issue oder PR mit neuen
Erkenntnissen aufmachen. Die originale Hersteller-Dokumentation scheint verloren.
