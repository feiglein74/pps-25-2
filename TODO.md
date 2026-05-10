# PPS 25/2 — Offene Punkte

## Stand 2026-05-03 (Hardware-Schaden + Reparatur)

### Schaden
ESD-Spike beim Hot-Plug eines RS232-Adapters (BP6 oder W&T) hat den **oberen 74LS373** (Tasten-Eingangs-Latch, NICHT der Adress-Demux-Latch) zerschossen. Konkret war **Pin 14 (D6 input) intern mit Pin 10 (GND) kurzgeschlossen**.

### Symptom-Bild
- Tasten reagierten gar nicht oder falsch (Memory 1 → triggert Memory 2)
- Memory-2-LED ging "von selbst" nach Wartezeit/Mehrfachdruck an
- Karte crashte nach LED-Trigger → Power-Cycle nötig
- RS232 funktionierte anfangs, hängte dann nach Tasten-Activity
- Output-Pfad und SCI komplett OK (TTL-Direkt-Test)
- Y-Selbsttest, MV/MC/MA, *VSET/*ISET alle funktionierten

### Diagnose-Pfad (was funktioniert hat)
1. **Differential-Test mit IDN-Befehl** über TTL-Direkt → MCU + SCI + EPROM OK
2. **Y-Selbsttest** → Display und LED-Treiber-Pfad OK
3. **`*VSET050` + Multimeter** → DAC + Output-Stage komplett OK
4. **Continuity mit abgestecktem Memory-2-Switch** → Pin am Pfostenstecker zeigt Verbindung zu GND und mehreren Chip-Pins. Da der Switch physisch getrennt war, muss der Short auf der Platine sein
5. **Pin-Trace zur Latch-Hardware** → Memory-2-Eingangsleitung führte zu 74LS373 Pin 14 (D6). Auf demselben Chip Pin 10 = GND. → Chip ist intern shorted

### Reparatur
- **T74LS373B1** (SGS-Thomson) Pin-für-Pin abgeklippt (Chip war eh tot)
- Pad-Reste mit Lötkolben entfernt
- **SN74LS373N** (Texas Instruments) eingelötet (drop-in kompatibel)
- Karte komplett funktional nach Reparatur — alle Tasten gehen, kein Crash mehr, RS232 sauber

### Restarbeit
- **Memory-2 hat einen Pad-Schaden** vom Auslöten — muss mit Drahtbrücke oder sauberer Lötstelle nachgezogen werden. Andere Tasten und Funktionen alle OK.

### Finale Bonus-Reparatur
- **74LS373 ist jetzt gesockelt** — beim nächsten ESD-Schaden ist Tausch in Sekunden möglich.

### Methodik-Lessons
- **NIE RS232 hot-pluggen** an Vintage-Geräten. ESD-Spike beim Massenanschluss kann durch ICL232-Schutzdioden bis zu Logik-Chips dahinter durchschlagen.
- **Differential-Test mit kontrollierten Befehlen** (IDN, Y, *VSET) ist sehr effektiv um zu zeigen welche Pfade gesund sind und welche nicht
- **Continuity bei abgesteckter Tasten-Hardware** ist der entscheidende Test für Latch-Schaden: wenn die Verbindung zur GND auch ohne Switch besteht, ist der Latch intern hin
- **DTE/DCE-Mismatch nicht unterschätzen:** PPS-25/2 ist DTE, W&T Com-Server ist auch DTE → ohne Null-Modem-Adapter senden beide auf TX-Pin = TX-Kollision = nur Garbage. Die "0xFC"-Antworten beim ersten W&T-Versuch waren keine kaputte Hardware sondern Verkabelungsfehler. Mit Null-Modem-Adapter dazwischen läuft's sauber.

### W&T-Setup (für künftige Sessions)
- IP 10.0.0.66, Port 8000 (Daten), Port 80 (Web-Config), Port 23 (Telnet-Banner)
- UART-Settings: 9600, 8N1, no flow control (Standard)
- **Null-Modem-Adapter zwischen W&T und PPS24-DB-25 erforderlich** (beide sind DTE)
- W&T hat Single-Connection-Mode auf Port 8000 — alte TCP-Verbindung muss sauber geschlossen werden bevor neue connect, sonst "Connection refused"

### Adapter-Test (offen)
Es gibt mehrere RS232-Adapter im Setup. Einer davon "mag uns nicht" — funktioniert nicht zuverlässig. In künftiger Session systematisch durchprobieren welcher welche Eigenschaften hat (1:1 vs Crossover, DTE/DCE-Pinning, ggf. RTS/CTS-Handling).

## Stand 2026-05-03 (ZIEL ERREICHT)

**Vollständige Remote-Control funktioniert** — Sequenz:
1. Erst `*ISET255\r` (Strom-Limit auf Maximum öffnen)
2. Dann `*VSET<n>\r` mit n=0..255 → linear 0..25,5 V (0,1 V/Schritt)

**Erkenntnis:** Der vorher beobachtete "Bruch bei n=24..32" war kein DAC- oder Firmware-Limit, sondern **interne Strom-Limitierung**. Default-Stromsetpoint nach Reset ist niedrig → Voltage-Loop begrenzt → Spannung capped bei ~2,2 V. Mit `*ISET255` zuerst kommt die volle Range.

**Verifiziert (am Multimeter):**
- n=0 → 0 V
- n=128 → ~12,6 V
- n=248 → ~24,5 V
- Linear durch die ganze Range mit ~3 Counts ADC-Drift (Linearitätsfehler)

**Befehlsskala:**
- `*VSET<n>`: 0..25,5 V in 0,1 V Schritten
- `*ISET<n>`: 0..2,55 A in 0,01 A Schritten
- = passt zum Geräte-Label PPS-25/2 (25 V / 2,5 A)

## Offen

### Bruchpunkt n=25..32 genau lokalisieren
1er-Schritte sweepen (n=20..40 mit ~1s Pause), sehen wo genau der Übergang ist. Vermutung: harte Schwelle (z.B. n=25 oder n=31) statt graduell.

### Bruch verstehen
- Hypothese A: Hardware-Schutz triggert ab Output > X Volt (z.B. ~2,5 V) → DAC wird zurückgesetzt
- Hypothese B: DAC ist intern nur N Bit, bei N+1 Bit-Wert läuft was über
- Hypothese C: Code-Pfad mit Range-Check den wir noch nicht gefunden haben

Strategie: vor jedem Test 1er-Schritt-Sweep aus 0 hoch — wenn Bruch immer beim gleichen n → Hardware oder fixer Schwellwert. Wenn variabel → Slew-Rate / Sequenz-Effekt.

### Volle Range trotz Bruch erreichen?
Mögliche Ansätze:
- Vor `*VSET<n>` mit hohem n erst `*VSET000` schicken (Reset des DAC?)
- Anderes Befehl-Format ausprobieren (es gibt 'V' single-letter mit V+ und V- für relative Änderungen — vielleicht umgeht das den Trigger)

### `*ISET` genauso verifizieren
Analoger Test mit Strombefehl. Bisher angenommen aber nicht gemessen.

### `*VOUT?` ist NICHT die Output-Messung
Korrektur zur SUMMARY: `*VOUT?` liest `$B8` (Setpoint-Echo), durch BCD-Konvertierung in `$F63C`. Echte Messung kommt aus `MV` (liest `$91` = ADC-Wert). SUMMARY entsprechend korrigieren.

### Mapping DAC-Wert → Volt
Bei n=17 ergibt es ~1,7 V. Linear extrapoliert: n=255 → ~25,5 V. Passt zu Vollausschlag, also ist DAC vermutlich linear über die ganze Range. Aber: muss bei höheren Werten noch verifiziert werden.

### `*VOUT?`-Konvertierung in `$F63C`
Einfache Binary-to-BCD (Double-Dabble) — formatiert Setpoint als 4-Digit BCD. Kein Scaling, also `*VOUT?` antwortet eigentlich exakt was `*VSET` setzte (mit kleiner Abweichung wegen Skalierungs-Code davor). Niedrige Priorität.

### Logic Analyzer Setup
Für tieferes Debug (Adress-Bus + Daten-Bus + Read/Write) wäre nützlich, ist aber jetzt nicht mehr blockierend, weil Remote-Control funktioniert.

### Code-Pfad sauber durcharbeiten
Mit dem neuen Wissen (`*VSET` wirkt!) ist die Hauptschleife `$F037-$F068` neu zu interpretieren. Vermutlich:
- `$A2 = 0` ist der NORMALE Zustand, nicht "idle"
- `$F045: JSR $F52F` läuft normalerweise NICHT permanent
- Es gibt einen Trigger der den DAC-Wert von `$6400` regelmäßig zum echten DAC schickt

### Methodik-Hinweis: ADC vs. Oszi

**ADC-Messungen via `MV`/`MC`/`MA` zeigen die echte Dynamik NICHT.** Die Sample-Rate plus die Mess-Latenz sind zu langsam für schnelle Übergänge (CC-Trigger, Last-Schaltvorgänge etc.). Was im ADC als "Sanftabschalt" oder "graduelles Ansteigen" aussieht ist meistens:
- Entladung des Ausgangs-Elkos (~13 mF geschätzt) über die Last
- ADC-Mittelung über die Sample-Zeit
- Latenz zwischen ADC-Trigger und ADC-Lesung

**Konsequenz:** Für jede Aussage über transientes Verhalten am Ausgang Oszi nutzen, nicht ADC. ADC nur für stabile Werte mit reproduzierbar erreichten Endzuständen.

### Vergangene Bewertungen neu prüfen mit Methodik-Wissen

Mit der "ADC zu langsam"-Erkenntnis sind diese Befunde aus dieser und früheren Sessions zu hinterfragen:

- **C-Verifikation Phase 2 (heute):** Aussagen wie "CC-Mode kicked bei C038, Spannung sackt auf 1,0V" sind vermutlich falsch — das ist Kondensator-Entladung, nicht der echte CC-Schaltzeitpunkt. Echter Trigger könnte deutlich früher liegen.
- **"Bruch bei n=24..32" früher (Session vor heute):** wir hatten DAC-Linearität via MV gemessen. Bei n=32+ → MV festgenagelt 014. Das war Strom-Limit, das wissen wir jetzt. Aber wenn man genauer hinschaut: die ADC-Werte könnten auch hier Mess-Artefakte enthalten haben.
- **`*VOUT?` als "echte Messung":** liest tatsächlich `$91` (ADC-Wert). Aber wegen ADC-Sample-Rate ist das ein Mittelwert über einige ms. Für stabile Werte OK, für Transienten unbrauchbar.
- **Last-Recovery-Zeiten:** "30 Sekunden bis Last wieder zieht" — das ist dein Watchdog, nicht das Netzteil. Bestätigt durch mehrfache Messungen.

### Hardware katalogisieren und verfolgen
Bisher haben wir das Gerät nur aus der RS232/Software-Sicht analysiert. Jetzt:
- Welche Leitungen gehen wo hin? Komplette Pin-für-Pin-Verfolgung der Boards.
- Speziell: was hängt an **6522 PA7 (Pin 9)** = Bit 7 von `$6001`? Vermutlich Hardware-Schutzsignal (Temperatursensor / Übertemperatur / Überstrom).
- Memory-Map vollständig dokumentieren: was sitzt bei `$6000`-`$6017` (VIA), `$6100` (Tastatur), `$6200` (?), `$6300` (?), `$6400`/`$6500` (DAC), `$6014` (?).
- GAL16V8 Adress-Decoder: was decodiert er? (würde die Memory-Map endgültig klären — evtl. mit gal-Reader auslesen oder per Pin-Tracing reverse-engineeren)
- Temperatursensor: welcher Chip, wo angeschlossen, wie gelesen?

### Aufräumen
- 30+ Test-Skripte im Projektverzeichnis (probe*.py, listen*.py etc.) — die meisten obsolet
- SUMMARY.md auf neuen Stand bringen

### RS232 wieder regulär aufbauen (morgen, 2026-05-04)
- ICL232CPE wieder einlöten
- P1.6-Brücke zu GND entfernen (CTS sollte regulär laufen)
- Über DB-25 mit Waveshare RS232-Adapter (echter Pegelwandler) verbinden
- Gleiche Befehlssequenz wie heute testen (`*ISET100\r` → `*VSET050\r` → `MV\r`/`MC\r`)
- Sollte regulär funktionieren — die ganzen Timing-Theorien waren irrelevant
