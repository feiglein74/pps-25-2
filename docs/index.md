---
title: Roth PPS 25/2 — RS-232 command set & repair
---

# Roth PPS 25/2 lab power supply

Reverse-engineered documentation for the **Roth PPS 25/2** (PPS-25/2), a linear lab power
supply from 1991 (0–25.5 V / 0–2.55 A) built by *Roth Hardware + Software, Grafrath, Germany*,
with the optional **PPS24 RS-232 interface card**. The original manual appears to be lost.

Source, firmware dump and scripts: [github.com/feiglein74/pps-25-2](https://github.com/feiglein74/pps-25-2)

## RS-232 remote control

**9600 baud, 8N1, no flow control.** Every command ends with `\r` (0x0D).
The PPS-25/2 is a **DTE** — use a **null-modem adapter** with a normal USB-RS-232 adapter.

```python
import serial
ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
ser.write(b"*ISET100\r")   # current limit FIRST (1.00 A)
ser.write(b"*VSET050\r")   # then voltage (5.0 V)
ser.write(b"MA\r"); print(ser.read(100))   # measured V and I
```

Without `*ISET` first, the output stays capped at about 2.2 V.

| Command | Effect |
|---|---|
| `*VSET<nnn>` | Set voltage, 000..255 → 0..25.5 V (0.1 V steps) |
| `*ISET<nnn>` | Set current limit, 000..255 → 0..2.55 A (0.01 A steps) |
| `*VSET?` / `*ISET?` | Read setpoint |
| `MV` / `MC` / `MA` | Measure voltage / current / both |
| `*VOUT?` / `*IOUT?` | Same as MV / MC |
| `*IDN?` / `U` | Identification: `PPS-25/2 V1.1 91.10.20` |
| `Y` | Display self test |
| `@` | UART test mode: continuous 0x55 stream (toggle) |
| `DD` / `DE` | Display off / on |
| `SL` | Set local — leaves remote mode **and resets all setpoints to 0** |

## Hardware

MC6803 CPU (4 MHz crystal, mode 2), TMS27C64 8 KB EPROM, R6522 VIA (display and keypad),
GAL16V8 address decoder, µPD7004C 10-bit ADC, 2× TLC7524 8-bit DAC for the V/I setpoints,
X2444 NOVRAM for 8 memory slots. The PPS24 card uses an ICL232 and an MC14060 with a
2.4576 MHz crystal as baud clock.

## Repair

After an ESD event while hot-plugging an RS-232 adapter, the upper 74LS373 (keypad input
latch) had pin 14 (D6) shorted internally to GND: keys mapped wrongly, memory LEDs lit up by
themselves, then the CPU crashed. Replaced with a new SN74LS373N in a socket.

## Detailed documentation (German)

- [Command matrix with firmware addresses](COMMANDS.md)
- [Reverse-engineering log, damage diagnosis and repair](TODO.md)
- [Early hardware notes](SUMMARY.md)
- [Full README (English summary + German details)](https://github.com/feiglein74/pps-25-2#readme)
