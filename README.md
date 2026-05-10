# Roth PPS 25/2 — Reverse Engineering & Repair

Complete teardown, firmware dump, RS-232 protocol decode, ESD-damage diagnosis and
repair guide for the **Roth PPS 25/2 Labornetzteil** (German lab power supply, 0–25 V /
0–2.5 A) from 1991 with the optional **PPS24 RS-232 interface card**.

If you've inherited or found one of these and want to use it via RS-232, this repo
gives you the full command set, hardware overview, and repair history.

## What it is

A linear bench power supply, 1991, made by *Roth Hardware + Software, 8082 Grafrath*.
Two 3-digit 7-segment displays (V and I), 10 illuminated push-buttons (memory recall,
parameter selection), 3-board sandwich (display / logic / analog) plus separate transformer
and rear linear power stage.

| Spec | Value |
|---|---|
| Output range | 0–25.5 V / 0–2.55 A (8-bit DAC, 0.1 V / 0.01 A per step) |
| Accuracy | < 0.3 % (verified: VSET=075 → 7.518 V on Brymen multimeter) |
| Output capacitor | 470 µF |
| Primary filter | 4700 µF |
| Memory slots | 8 (V/I pairs in NOVRAM, ~6 normally used) |
| Interfaces | Front panel + RS-232 (PPS24 card) |
| Firmware | "PPS-25/2 V1.1 91.10.20" |

## Hardware architecture

3-board sandwich behind the front panel + transformer + rear analog/power stage.

```
[Display board] — [Logic board] — [Analog buffer board]   |  [Transformer]  |  [Power stage + heatsink]
   10 buttons        MC6803            LM324                  primary +         2× LM324, 4700 µF,
   2× 3-digit        + EPROM           buffer for             aux winding       longitudinal transistors
   7-seg, LEDs       + VIA + ADC       TLC7524 DACs                             7805 for logic 5V
                     + GAL + 2×        + level shifting
                     74LS373/etc       to power stage
                     + X2444 NOVRAM
```

### Logic board (the brain)

| Chip | Role |
|---|---|
| Motorola **MC6803P** | 8-bit MCU, 4 MHz crystal (E = 1 MHz), Mode 2 (Expanded Multiplexed) |
| TI **TMS27C64-2JL** | 8 KB EPROM with firmware |
| Rockwell **R6522P** | VIA — display multiplexing, key matrix scan, X2444 bit-banging |
| Lattice **GAL16V8-25QNC** | Address decoder for `$6000-$6500` chip selects |
| 2× **SN74LS373N** | Address-demux latch (lower) + key-input latch (upper, **see repair below**) |
| **74LS133, 74LS273, 74LS14N** | Glue logic for key scanning + IRQ + reset |
| NEC **µPD7004C** | 4-channel 10-bit ADC (V/I measurement) |
| 2× **TLC7524CN** | 8-bit multiplying DACs for V/I setpoints |
| **X2444P** (Xicor) | 256-bit NOVRAM — holds the 8 memory presets across power cycles |

### PPS24 RS-232 card

| Chip | Role |
|---|---|
| Intersil **ICL232CPE** | RS-232 line driver/receiver (TTL ↔ ±10 V) |
| Motorola **MC14060BCP** + 2.4576 MHz crystal | 14-stage divider for baud rate clock |

The 4060 jumper at Q5 outputs 76,800 Hz, which the 6803 SCI uses as external clock.
Per MC6801 spec the bit rate is **clock / 8 = 9600 baud**.

### Power stage

| Component | Role |
|---|---|
| 2× **LM324N** | 8 op-amps for CV/CC loops, sense, comparator (CC kicks in at ~300 ms — slow regulation loop) |
| Bridge rectifier + heatsink | longitudinal pass transistors |
| 4700 µF | primary filter cap |
| 470 µF | output cap |
| Trim pots | per-channel calibration |

### Memory map

| Address | Function |
|---|---|
| `$0000-$007F` | MC6803 internal RAM |
| `$0080-$008F` | RAM image of X2444 NOVRAM (8× 16-bit memory presets) |
| `$6000-$600F` | R6522 VIA |
| `$6014` | Bit 1 = X2444 SK clock |
| `$6100` | Key-matrix latch (74LS373 upper) |
| `$6300/$6301` | µPD7004C ADC |
| `$6400` | TLC7524 — voltage DAC |
| `$6500` | TLC7524 — current DAC |
| `$E000-$FFFF` | EPROM firmware |

## Operating principle

1. MCU writes 8-bit value to TLC7524 at `$6400` (V) or `$6500` (I).
2. DAC produces analog setpoint, buffered by LM324 on the analog board.
3. Setpoint goes to power stage — CV-loop holds output until CC limit kicks in.
4. ADC samples actual V and I via mux, presents back at MV/MC commands.
5. Memory presets: NOVRAM (X2444) holds 8 V/I pairs, recalled into RAM at `$0080+` on
   boot, written back on user "Memory Store" key press.

## RS-232 protocol

**9600 8N1, no flow control.** All commands end with `\r` (0x0D).

**Critical:** PPS-25/2 is a DTE. If your USB-RS232 adapter is also DTE (typical),
**you need a Null-Modem adapter** between the two — otherwise both send on the same
pin and you get pure garbage.

### Required command sequence for remote control

```python
ser.write(b"*ISET100\r")   # current limit MUST be set first
ser.write(b"*VSET050\r")   # then voltage (5.0 V here)
```

If you skip `*ISET<n>\r`, the default current limit is so low that voltage caps
at ~2.2 V regardless of `*VSET<n>`. This was the multi-day mystery during reverse
engineering — see [TODO.md](TODO.md) for the full saga.

### Command set (full reference)

See [COMMANDS.md](COMMANDS.md). Highlights:

| Command | Effect |
|---|---|
| `*VSET<nnn>\r` | Set voltage (000..255 → 0..25.5 V in 0.1 V steps) |
| `*ISET<nnn>\r` | Set current limit (000..255 → 0..2.55 A in 0.01 A steps) |
| `*VSET?\r` / `*ISET?\r` | Read setpoint |
| `MV\r` / `MC\r` / `MA\r` | Measure voltage / current / both |
| `*VOUT?\r` / `*IOUT?\r` | Same as MV/MC (real ADC reading) |
| `*IDN?\r` / `U\r` | "PPS-25/2 V1.1 91.10.20" |
| `Y\r` | Service display self-test (LEDs cycle, 7-seg counts, DPs walk) |
| `@\r` | UART test mode — toggles continuous 0x55 stream (handy for baud verification) |
| `SL\r` | ⚠ Set Local — exits remote mode AND clears all setpoints to 0 |
| `DD\r` / `DE\r` | Display Disable / Enable |

### Quick test

```python
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("10.0.0.66", 8000))   # via W&T Com-Server with Null-Modem adapter
s.send(b"*IDN?\r")
print(s.recv(100))   # → b'*IDN?\r\nPPS-25/2 V1.1 91.10.20\r\n'
```

Or with a direct USB-RS232 adapter (must include MAX232 or actual RS-232 levels — TTL-only
adapters like PL2303 won't drive the ICL232 properly):

```python
import serial
ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
ser.write(b"*ISET100\r"); ser.read(100)
ser.write(b"*VSET050\r"); ser.read(100)
```

## ESD repair (May 2026)

While trying a new RS-232 adapter, an ESD spike on hot-plug killed the **upper 74LS373**
(key-input latch) — Pin 14 (D6 input) shorted internally to Pin 10 (GND).

**Symptoms:** keys unresponsive or wrongly mapped (Memory 1 triggered Memory 2),
Memory-2 LED came on by itself after a few seconds, MCU crashed shortly after.

**Diagnosis:** RS-232 still worked over TTL-direct setup → MCU/SCI/EPROM all fine;
`Y` self-test ran → display + LED drivers fine; `*VSET050\r` + multimeter showed
DAC + output stage fine. Continuity test on the disconnected key header revealed
Memory-2 input was shorted to GND on the board itself → traced to 74LS373 Pin 14/10
internal short.

**Fix:** clipped pins individually (chip was dead anyway), removed pad residue,
soldered in a fresh SN74LS373N **into a new socket** for future easy swap.
Time from "what's wrong?" to "fully working again": one afternoon.

Full diagnosis log + methodology lessons in [TODO.md](TODO.md).

## Files

| File | Description |
|---|---|
| [README.md](README.md) | This file |
| [COMMANDS.md](COMMANDS.md) | Complete RS-232 command matrix |
| [TODO.md](TODO.md) | Reverse engineering history, ESD damage, repair, methodology |
| [SUMMARY.md](SUMMARY.md) | Earlier hardware notes (mostly superseded by README) |
| `firmware.bin` | Original EPROM dump (8192 bytes, MD5 803de2bfb2f56135aeacf3c0f987c47b) |
| `firmware2.bin` | Verification dump (identical) |
| `dis.lst` | Disassembly (~1780 instructions) |
| `dis6803.py` | Custom 6803 disassembler with control-flow following |
| `cmd_phase1.py` / `cmd_phase2_inc.py` | Command matrix verification scripts |
| `vset_full.py` | DAC sweep with both setpoint and ADC measurement |
| `c_verify3.py` | CC-mode trigger characterization with kohärente MA sampling |
| `at_loop.py` | UART test mode validator |
| `c_oszi_trigger.py` | Single CC trigger for oscilloscope analysis |
| `messwert-nach-last-watchdog/` | Tek TDS1002B oscilloscope captures of CC trigger |
| `archive/` | Earlier exploration scripts (probe*.py, listen*.py, baud sweeps, etc.) |

## Acknowledgements

Reverse engineered together with Claude (Anthropic). Hardware-in-the-loop exploration,
firmware dump and disassembly, RS-232 protocol decode, ESD damage diagnosis, single-chip
replacement.

If you have a Roth PPS-25/2 and find this useful, raise an issue or PR with whatever
new findings you make. The original manufacturer's documentation appears to be lost.
