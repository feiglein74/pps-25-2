# PPS 25/2 — Befehlsmatrix

Aus Disassembly extrahiert. **Alle Befehle enden mit `\r` (0x0D).**

## Single-Letter Befehle (Dispatch ab $E16D)

| Befehl | Adresse | Funktion (aus Code) | Test |
|---|---|---|---|
| `@` | $E1A3 | **UART-Test-Modus (Toggle)** — 1× `@` startet kontinuierlichen Stream von `0x55` ('U' = `01010101` Bit-Pattern für Baud/Timing-Validierung). 2× `@` toggelt wieder aus. Output bleibt unbeeinflusst. Diagnose-Pattern für Baudraten-Test, Oszi-Timing oder UART-Loopback. | ✅ |
| `C<n>` | $E43C | Set current setpoint ($B9 ← n, $6500 ← n), n=3 ASCII Digits 000..255 → 0,00..2,55 A. Hardware verifiziert: bei 0,4A Last triggert CC-Mode bei C038. Oszi-Messung zeigt Spannungs-Einbruch über ~300 ms — verursacht durch **langsame CC-Regelschleife** des Netzteils (NICHT Cap-Entladung; Cap ist nur 470 µF und würde in <6 ms entladen). | ✅ |
| `C+<d>` | $E43C | Current += d (1 Digit 0..9), clamp 255 | ✅ |
| `C-<d>` | $E43C | Current -= d (1 Digit 0..9), clamp 0 | ✅ |
| `C+` | $E43C | Current += 1 (default) | ✅ |
| `C-` | $E43C | Current -= 1 (default) | ✅ |
| `D` | $E48E | Display dispatch: |  |
| `DD` | $E48E | **Display Disable** — schaltet Display aus (im Remote-Mode bereits aus, daher silent). Cleart $B5 Bit 7. | ✅ |
| `DE` | $E48E | **Display Enable** — schaltet Display AN. Setzt $B5 Bit 7. Output bleibt unbeeinflusst. | ✅ |
| `M` | $E4C4 | Measure dispatch: |  |
| `MV` / `MV?` | $E4C4 | Voltage-ADC ($91), Antwort "049" bei 5V | ✅ |
| `MC` / `MC?` | $E4C4 | Current-ADC ($94), Antwort "001" bei 0A Last | ✅ |
| `MA` / `MA?` | $E4C4 | V then C, Antwort "049 001" (space-getrennt) | ✅ |
| `MX` / `MX?` | $E4C4 | RAW Voltage-ADC ($B1, 10-bit). Antwort "0<6" = `$00C6` = 198 (raw). $91/MV ist die skalierte BCD-Form davon. | ✅ |
| `R` | $E361 | Read setpoints: RV/RC/RS | ✅ |
| `RV` | $E361 | Read voltage setpoint $B8, Antwort "050" | ✅ |
| `RC` | $E361 | Read current setpoint $B9, Antwort "100" | ✅ |
| `RS` | $E361 | Read status: liest $6001, LSR×3, AND $11. Antwort "017" = bit 7+3 von $6001 = OK-Flag + bit 3. Bei Emergency wäre Antwort "001". | ✅ |
| `S` | $E1C1 | Status: SL/SD/SE | ⚠ |
| `SL` | $E1C1 | **Set LOCAL** — schaltet aus Remote-Mode zurück in Local: Display an, Knöpfe aktiv, Setpoints auf 0 gecleared. Sets bit 5 of $6001 (= Hardware-Trigger für Local-Mode). Nach SL ist die Remote-Session quasi beendet — neue Befehle werden zwar noch verarbeitet, aber Display/Knöpfe sind aktiv. ⚠ aufpassen: nicht versehentlich senden. | ✅⚠ |
| `SD` | $E1C1 | Clears bit 6 of $B5 — async-status-marker DISABLE. Silent | ✅ |
| `SE` | $E1C1 | Sets bit 6 of $B5 — async-status-marker ENABLE. Wenn aktiv und HW-Status ändert sich, wird Status-Byte mit `$C0\|status` über RS232 gesendet (statt `$80\|status`). Silent bestätigt | ✅ |
| `U` | $E356 | IDN string | ✅ |
| `V<n>` | $E3E7 | Set voltage ($B8, $6400), n=3 ASCII Digits 000..255 | ✅ |
| `V+<d>` | $E3E7 | Voltage += d (1 Digit 0..9!), clamp 255. **Achtung:** mehr Digits → Müll | ✅ |
| `V-<d>` | $E3E7 | Voltage -= d (1 Digit 0..9), clamp 0 | ✅ |
| `V+` / `V-` | $E3E7 | Voltage ±1 (default ohne Digit) | ✅ |
| `Y` | $E201 | **Qualitäts-/Troubleshooting-Test der Anzeige** — Produktions-/Service-Diagnose, läuft nicht beim Power-On. Komplette Anzeige-Sequenz: (1) alle LED-Tasten + CNV/CV/CC/RMT-LEDs blinken nacheinander, (2) alle 7-Segment-Stellen zählen 1..0, (3) Dezimalpunkte wandern rechts→links. Funktioniert unabhängig von DD/DE (schaltet Display temporär an). Output bleibt unbeeinflusst. | ✅ |
| `Z` | $E351 | Copyright string | ✅ |

## *X Subcommand-Befehle (Dispatch ab $E5DB)

| Befehl | Adresse | Funktion (aus Code) | Test |
|---|---|---|---|
| `*CLS` | $E64C | Clear status (silent) | ✅ |
| `*ICR?` | $E759 | Copyright string ($E334), wie `Z` | ✅ |
| `*IDN?` | $E772 | IDN string ($E31B = "PPS-25/2 V1.1 91.10.20"), wie `U` | ✅ |
| `*IOUT?` | $E66E | Measured Current ($94), Antwort "001" | ✅ |
| `*ISET<n>` | $E6C0 | Set current setpoint | ✅ |
| `*ISET?` | $E6C0 | Query current setpoint ($B9), Antwort "100" | ✅ |
| `*S<sub>` | $E611 | Status sub (SR / SET / ...) | ❓ |
| `*VOUT?` | $E79B | Measured Voltage ($91), Antwort "049" | ✅ |
| `*VSET<n>` | $E7CD | Set voltage setpoint | ✅ |
| `*VSET?` | $E7CD | Query voltage setpoint ($B8), Antwort "050" | ✅ |

**Legende:** ✅ = funktioniert, ❌ = fehler, ⚠ = vorsichtig (Side-Effect), ❓ = noch zu testen

## Wichtige Beobachtungen / Falsifikations-Tricks

### Default-State nach Power-On (= "leerer" Ausgangszustand)
- `$B5` Bit 0 = 0 → `@`-Loop AUS
- `$B5` Bit 6 = 0 → async-status DISABLED
- `$B5` Bit 7 = 0 → Display AUS
- DACs = 0, Setpoints `$B8`/`$B9` = 0 → Output 0 V
- Im Remote-Mode (RMT-LED an), Knöpfe deaktiviert

### Befehle die als ERSTER Befehl silent sind (= Default-State macht sie wirkungslos)

| Befehl | Warum silent | Entdeckungs-Trick |
|---|---|---|
| `DD` | Display ist Default schon aus | Erst `DE` schicken, dann `DD` — Display geht aus = sichtbar |
| `SD` ≡ `*CLS` | Bit 6 ist Default schon 0 | Erst `SE`, dann `SD` — aber Wirkung sowieso nur bei HW-Status-Trigger erkennbar |
| `SE` ≡ `*SRE` | Setzt Bit 6, aber sichtbar erst wenn HW-Status sich ändert (Async-Byte) | Emergency provozieren (Übertemp/Überlast) und erwarten dass Status-Byte mit `$C0\|status` kommt |
| `*ST?` | No-op laut Code | Nie sichtbar |

### Befehle die silent wirken weil **Voraussetzung fehlt**

| Befehl | Was passiert | Warum nicht (voll) sichtbar |
|---|---|---|
| `*VSET<n>` ohne vorheriges `*ISET` | DAC bekommt Wert, aber CC-Limit greift | Output capped bei ~2,2 V (= Default-Stromlimit). Erst-Lösung beim Reverse Engineering: `*ISET255` zuerst |
| `*VSET<n>` mit n > 255 | $A3 (high byte) ≠ 0 → Reject | Range-Check `$E56D`: BCS Error |
| `C+`/`C-`/`V+`/`V-` mit n>1 Digit | Nur erste Ziffer wird genommen | Restliche Digits gehen als ungültiger Befehl an den Top-Level-Parser |
| `*CLS` als "alle Errors clearen" | Cleart NUR Bit 6 von $B5 | Standard-SCPI-Bedeutung trifft nicht zu — kein generelles Error-Register sichtbar |

### Befehle die nur **toggle**-sichtbar sind (= 2× = wieder Ausgangszustand)

| Befehl | Toggle-Verhalten |
|---|---|
| `@` | 1× = UART-Test-Loop start, 2× = stop |
| `DD`/`DE` | Doppelt-Schicken hat keine Wirkung; nur Wechsel sichtbar |
| `SD`/`SE` | Toggle Bit 6 von $B5 — silent solange kein Status-Trigger |

### Methodik: ADC zu langsam für Transienten

ADC-Messungen via `MV`/`MC`/`MA` haben Sample-Rate + Latenz die transiente Übergänge nicht auflösen kann. Was im ADC als "graduell" oder "Sanftabschalt" erscheint ist meistens:
- Langsame CC-Regelschleife des Netzteils (~300 ms Bandbreite)
- ADC-Mittelung über Sample-Zeit
- NICHT Cap-Entladung (Ausgangs-Elko 470 µF entlädt in <6 ms bei 0,4 A Last)

**Konsequenz:** Für Transienten-Bewertungen Oszi nutzen, ADC nur für stabile Endzustände.

### Last-Verhalten (im aktuellen Test-Setup)

- Externe elektronische Last hat Watchdog der bei Spannungseinbruch (~< 4 V) die Stromaufnahme abschaltet
- **Recovery: ~25 s scharf** nach Setzen einer ausreichend hohen Strom-Limit (Sprung, kein graduelles Anlaufen)
- Im Recovery-Fenster zieht die Last nur Mess-Strom (~0,01 A)

### Noch offen / weiter zu erforschen

- **`SE` Async-Status real provozieren:** durch HW-Trigger (Übertemperatur, Überlast, Versorgungsfehler) den Pfad `$E3B3` auslösen und das Async-Byte `$C0|status` mitschneiden
- **Hardware-Schutzpfad:** Bit 7 von `$6001` (= 6522 PA7) physisch verfolgen — was hängt da dran (siehe TODO)
- **`MX` (raw ADC `$B1`)** im Stress-Test: ist das wirklich nur die Voltage-ADC-Rohversion oder gibt es einen weiteren Sample-Pfad?
