# Roth PPS 25/2 + PPS24 RS232-Schnittstelle — Reverse Engineering Status

## Gerät
- **Modell:** Roth PPS 25/2 (Labornetzteil 0-25V/0-2A)
- **Hersteller:** Roth Hardware + Software, 8082 Grafrath (vor 1993)
- **Schnittstellen-Option:** PPS24 (RS232 ohne galvanische Trennung), aufrüstbar
- **Firmware-Datum:** 1991-10-20 (per IDN-String "PPS-25/2 V1.1 91.10.20")

## Hardware-Inventur (vollständig)

### CPU-Hauptplatine (sandwich-mounted, Bestückungsseite nicht zugänglich)
| Chip | Funktion |
|---|---|
| MC6803P | 8-Bit CPU mit on-chip SCI |
| TMS27C64-2JL | 8KB EPROM Firmware |
| R6522 | VIA (Tastatur/Display I/O) |
| GAL16V8 | Adressdekoder |
| SN74LS373 | Adress-Latch (AD0-7 Demux) |
| NEC µPD7004C | A/D-Wandler (V/I-Messung) |
| Quarz **4 MHz** | CPU-Takt (E = 1 MHz, **bestätigt mit Oszi auf 6803 Pin 39**) |

### PPS24-Schnittstellenplatine (3 Bauteile + Passive)
| Chip | Funktion |
|---|---|
| Intersil ICL232CPE | RS232-Pegelwandler (TTL ↔ ±10V) |
| Motorola MC14060BCP | 14-stufiger Binärteiler + Oszillator |
| Quarz **2,4576 MHz** | Für 4060-Takterzeugung |
| 6 Cs, 1 R | Charge-Pump-Caps am ICL232, Quarzbeschaltung |

### DB-25 Verkabelung (Gerät als DTE)
| DB-25 Pin | ICL232 | Funktion |
|---|---|---|
| 2 | Pin 14 (T1OUT) | Daten Karte → PC |
| 3 | Pin 13 (R1IN) | Daten PC → Karte |
| 4 | Pin 7 (T2OUT) | RTS Karte → PC |
| 5 | Pin 8 (R2IN) | CTS PC → Karte |
| 7 | Pin 15 (GND) | Masse |

### Pfostenstecker PPS24 ↔ CPU-Board (10-pin Flachband, alle verifiziert)
| Funktion | 6803-Pin | ICL232-Seite |
|---|---|---|
| **SCI-Clock** | Pin 10 (P22/TIN) | 4060 Q-Output via Jumper |
| **TTL-RX** zur CPU | Pin 11 (P23/RXD) | Pin 12 (R1OUT) |
| **TTL-TX** von CPU | Pin 12 (P24/TXD) | Pin 11 (T1IN) |
| **CTS-Input** | Pin 19 (P1.6) | Pin 9 (R2OUT) |
| **RTS-Output** | Pin 20 (P1.7) | Pin 10 (T2IN) |
| **PPS24-Detect** | Pin 13 (P1.0) | GND der PPS24 |
| VCC | — | Pin 16 |
| GND | — | Pin 15 |
| 2 unbenutzt | (P1.1, P1.2 - andere Interface-Optionen) | — |

### Mode-Pin-Setup (6803 Boot-Modus)
- Pin 8 (P20) und Pin 10 (P22) über Widerstände auf GND (Mode bits = 0)
- Pin 9 (P21) Teil des Reset-Netzwerks (RC + Pull-Up)
- Vermutlich **Mode 2** (Expanded Multiplexed) - Standard für externes EPROM

## 4060 Jumper-Block (5 Positionen für Baudraten-Wahl)
| Jumper-Pos | 4060-Pin/Output | Frequenz | Erwartete Baudrate |
|---|---|---|---|
| Q4 | Pin 7 | 153,6 kHz | 9600 (/16) oder 153600 (direkt) |
| Q5 | Pin 5 | 76,8 kHz | 4800 oder 76800 |
| Q6 | Pin 4 | 38,4 kHz | 2400 oder 38400 |
| Q7 | Pin 6 | 19,2 kHz | 1200 oder 19200 |
| Q8 | Pin 14 | 9,6 kHz | 600 oder 9600 |

## Firmware-Analyse

### Speicher
- EPROM gemappt bei $E000-$FFFF
- Internal RAM bei $0000-$007F
- Vector-Table @ $FFF0-$FFFF
  - SCI-IRQ → $E000
  - Reset → $F000

### SCI-Initialisierung (Boot @ $F0AD-$F0CB)
```
P1DDR = $86 (P1.1, P1.2, P1.7 Output; Rest Input)
P2DDR = $03 (P2.0, P2.1 Output)

Lesen P1.0:
  P1.0 = LOW (PPS24 angeschlossen) → RMCR = $0C
  P1.0 = HIGH (kein PPS24)         → RMCR = $05

TRCSR = $1A (TE + RE + RIE)
```

### RMCR-Bit-Bedeutung (aus Datenblatt)
- **CC1:CC0 = 11** = NRZ, ClockSource External, P22=Input
- **RMCR = $0C** → External Clock vom 4060 wird verwendet
- Bit Rate vom externen Takt am Pin 10 abhängig

### Befehlssatz (aus Disassembly)
- Top-Level Parser bei $E145, Dispatch-Tabelle $E16D (single-letter)
- `*X`-Subkommandos bei $E5BE, Subtabelle $E5DB
- Gültige Kommandos:
  - `*CLS\r` (Clear Status — silent)
  - `*ISET<n>\r` / `*ISET?\r` (Strom setzen/abfragen, n=0..255 → DAC $6500)
  - `*VSET<n>\r` / `*VSET?\r` (Spannung setzen/abfragen, n=0..255 → DAC $6400)
  - `*VOUT?\r` (gemessene Spannung abfragen, von $91)
  - `*S<x>\r` (Status-Subkommandos: SR, SET)
  - Number-Format: **EXAKT 3 ASCII-Ziffern** (z.B. `*VSET050\r`)

## Beobachtetes Verhalten (was funktioniert / nicht)
- **HW-Pfade:** Komplett verifiziert, Loopback OK, Pegel OK
- **Bei 76800 oder 153600 Baud:** Karte zeigt Reaktion (RMT-LED an, Display aus, Output 0V) → SCI empfängt Bytes
- **Aber:** Antworten sind 1-Byte-Garbage (0xe0 / 0x80), keine ASCII-Strings
- **Spannung ändert sich nie** trotz `*VSET<n>` Befehlen
- **Probleme:** Vermutlich Bit-Phase-Drift weil unser FT232 + ICL232-Pfad nicht synchron mit dem 4060-Takt der SCI

## Plan A (NÄCHSTER TEST): TTL-Direktanschluss
PPS24 + ICL232 komplett umgehen. PL2303-TTL-Adapter direkt an Ribbon:
- TX → Pin der zu 6803 Pin 11 (RXD) führt
- RX ← Pin der von 6803 Pin 12 (TXD) kommt
- GND → CPU-Board GND
- 4060-Takt-Pin lassen (das ist die SCI-Clock-Quelle, am 6803 Pin 10)

Damit sind alle ICL232-bedingten Timing-Probleme weg. SCI sieht TTL-Signal direkt.

Baudrate: aktuell Jumper auf 153,6 kHz → testen mit 153600 Baud (direkt) und 9600 (/16).

## Plan B: Firmware-Mod (Backup wenn Plan A scheitert)
Modifizierte Firmware (`firmware_modified.bin`) mit Byte $26 statt $27 bei Offset 0x10BF.
Kehrt die P1.0-Polarität um → erzwingt RMCR=$05 (= internal clock) statt $0C (external).
Brennen auf blanken 27C64 mit TL866II+.

## Wichtige Dateien
- `/home/feig/pps-25-2/firmware.bin` — Original-Dump (MD5: 803de2bfb2f56135aeacf3c0f987c47b)
- `/home/feig/pps-25-2/firmware2.bin` — Verifikations-Dump (identisch)
- `/home/feig/pps-25-2/firmware_modified.bin` — Mod für Plan B
- `/home/feig/pps-25-2/dis.lst` — Disassembly (1780 Instruktionen)
- `/home/feig/pps-25-2/dis6803.py` — eigener 6803-Disassembler
- `/home/feig/pps-25-2/probe*.py` — diverse Test-Skripte
