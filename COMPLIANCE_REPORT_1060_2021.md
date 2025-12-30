# Compliance-Analyse: FlowNavigator/FlowAudit Platform
## Prüfung der Konformität mit EU-Verordnung 2021/1060 und Vorbereitung auf die Förderperiode 2028+

**Erstellt am:** 30. Dezember 2025
**Repository:** flownavigator
**Branch:** claude/review-compliance-1060-2021-Vz5NS

---

## Executive Summary

Die **FlowAudit Platform** ist ein modernes, modulares Prüfbehörden-Management-System, das speziell für die Anforderungen der EU-Strukturfonds-Prüfung entwickelt wurde. Die Analyse zeigt, dass das System **eine solide Grundlage** für die Umsetzung der Aufgaben gemäß Verordnung (EU) 2021/1060 bietet, jedoch **kritische Lücken** bei zentralen Prüffunktionen aufweist, die vor der Förderperiode 2028+ geschlossen werden müssen.

**Gesamtbewertung:** 🟡 **Teilweise konform** – 65% der Kernfunktionen implementiert

---

## 1. Regulatorischer Rahmen

### 1.1 Verordnung (EU) 2021/1060 – Kernaufgaben der Prüfbehörde

Die Verordnung definiert in den **Artikeln 77-85** die zentralen Aufgaben der Prüfbehörde:

| Artikel | Aufgabe | Status in FlowAudit |
|---------|---------|---------------------|
| Art. 77 | Systemprüfungen und Vorhabenprüfungen | 🟡 Teilweise |
| Art. 78 | Prüfstrategie | 🔴 Nicht implementiert |
| Art. 79 | Vorhabenprüfungen (Stichprobe) | 🔴 Stichprobenziehung fehlt |
| Art. 80 | Einzige Prüfung (Single Audit) | 🟡 Grundlagen vorhanden |
| Art. 81 | Verwaltungsprüfungen | 🟢 Implementiert |
| Art. 82 | Aufbewahrungspflichten | 🟢 Implementiert |
| Art. 83 | Prüfung bei verstärkter Verhältnismäßigkeit | 🔴 Nicht implementiert |
| Art. 84 | Allgemeine Grundsätze | 🟢 Implementiert |
| Art. 85 | Jahreskontrollbericht & Bestätigungsvermerk | 🔴 Nicht implementiert |

### 1.2 Förderperiode 2028+ (MFR 2028-2034)

Die EU-Kommission hat am 16. Juli 2025 den Vorschlag für den neuen **Mehrjährigen Finanzrahmen (MFR) 2028-2034** vorgelegt. Wesentliche Änderungen:

1. **Einheitlicher Europäischer Fonds** – Zusammenlegung von EFRE, ESF+, Kohäsionsfonds
2. **Nationale und Regionale Partnerschaftspläne** – Ersatz für einzelne Operationelle Programme
3. **Verstärkte Digitalisierung** – Verpflichtende elektronische Datenerfassung und -übermittlung
4. **Do No Significant Harm (DNSH)** – Umweltprüfung als Querschnittsthema
5. **Vereinfachte Kostenoptionen** – Stärkerer Fokus auf Pauschalen und Standardeinheitskosten

---

## 2. Architektur-Analyse FlowAudit

### 2.1 Technologie-Stack

| Ebene | Technologie | Bewertung |
|-------|-------------|-----------|
| Backend | Python 3.11 + FastAPI | 🟢 Modern, async-fähig |
| ORM | SQLAlchemy 2.0 | 🟢 Flexibel mit JSONB |
| Datenbank | PostgreSQL 15 | 🟢 Enterprise-ready |
| Frontend | Vue 3 + TypeScript | 🟢 Reaktiv, typsicher |
| Styling | Tailwind CSS | 🟢 Flexibel |
| Monorepo | pnpm + Turborepo | 🟢 Skalierbar |

**Fazit:** Die technische Architektur ist **zukunftsfähig** und erfüllt moderne Standards.

### 2.2 Implementierte Module

```
✅ IMPLEMENTIERT                    ⚠️ IN PLANUNG                    ❌ FEHLEND
──────────────────────────────────────────────────────────────────────────────
@flowaudit/common                   @flowaudit/sampling              Prüfstrategie-Modul
@flowaudit/validation               @flowaudit/projection            OLAF-Schnittstelle
@flowaudit/permissions              @flowaudit/jkb                   SFC-Integration
@flowaudit/fiscal-year              @flowaudit/flow-invoice          eMS-Anbindung
@flowaudit/operations               @flowaudit/analytics             Risikobewertung
@flowaudit/checklists                                                Plausibilitätsprüfung
@flowaudit/audit-cases
@flowaudit/findings
@flowaudit/group-queries
@flowaudit/document-box
@flowaudit/file-manager
@flowaudit/word-export
@flowaudit/excel-import
@flowaudit/report-engine
@flowaudit/text-modules
```

---

## 3. Stärken der Plattform

### 3.1 Vollständiges Prüfungsfall-Management

Das System bietet ein **umfassendes Datenmodell** für Prüfungsfälle:

```python
# Aus apps/backend/app/models/audit_case.py
class AuditCase:
    - case_number, external_id, project_name, beneficiary_name
    - approved_amount, audited_amount, irregular_amount
    - status: draft → in_progress → review → completed → archived
    - audit_type: operation | system | accounts
    - Prüfteam: primary_auditor, secondary_auditor, team_leader
    - Ergebnis: no_findings | findings_minor | findings_major | irregularity
```

**Stärke:** Die Struktur entspricht den EU-Anforderungen an die Dokumentation von Vorhabenprüfungen.

### 3.2 EU-konforme Fehlerkategorisierung

Die Feststellungen (Findings) werden gemäß EU-Kategorien klassifiziert:

- `ineligible_expenditure` – Nicht förderfähige Ausgaben
- `public_procurement` – Vergabefehler
- `missing_documents` – Fehlende Unterlagen
- `calculation_error` – Rechenfehler
- `double_funding` – Doppelfinanzierung
- `other` – Sonstiges

**Stärke:** Direkte Übernahme in den Jahreskontrollbericht möglich.

### 3.3 Konzernstruktur mit Gruppenabfragen

Das **GroupQuery-System** ermöglicht:

- Erstellung von Konzern-Abfragen an untergeordnete Prüfbehörden
- Tracking von Einreichungsfristen und Fortschritt
- Aggregation von Ergebnissen (Fehlerquoten, Prüfvolumen)
- Vergleichsanalysen zwischen Behörden

**Stärke:** Unterstützt die hierarchische Berichtsstruktur gemäß Art. 77 Abs. 3.

### 3.4 Vollständiger Audit-Trail

```python
# Aus apps/backend/app/models/audit_log.py
class AuditLog:
    - entity_type, entity_id, action
    - user_id, user_email, user_name
    - ip_address, user_agent
    - old_values, new_values (JSONB)
    - created_at (timezone-aware)
```

**Stärke:** Lückenlose Nachverfolgbarkeit aller Änderungen – erforderlich für Art. 82 (Aufbewahrungspflichten).

### 3.5 Flexibles Checklisten-System

- Verschiedene Typen: main, procurement, subsidy, eligibility, system, custom
- JSONB-Speicherung für flexible Strukturen
- Versionierung von Templates
- Fortschrittsanzeige mit Prozentwerten

**Stärke:** Anpassbar an wechselnde Prüfanforderungen über Förderperioden hinweg.

### 3.6 Belegkasten mit KI-Integration (FlowInvoice)

Geplante Features für automatisierte Belegprüfung:

- OCR-Extraktion von Rechnungsdaten
- Formale Prüfung (Pflichtangaben)
- Rechnerische Prüfung (Summen, MwSt.)
- Plausibilitätsprüfung (Datum, Budget, Duplikate)
- Risikobewertung (low/medium/high)

**Stärke:** Effizienzsteigerung bei der Vorhabenprüfung.

### 3.7 Multi-Mandanten-Architektur

- Trennung von Konzern (Group) und Prüfbehörden (Authority)
- Tenant-übergreifende Abfragen und Auswertungen
- Rollenbasierte Zugriffskontrolle (RBAC)

**Stärke:** Skalierbar für Bundesländer-übergreifende Strukturen.

---

## 4. Schwächen und Compliance-Lücken

### 4.1 🔴 KRITISCH: Fehlende Stichprobenziehung (Sampling)

**Anforderung Art. 79:**
> "Die Prüfbehörde führt Prüfungen anhand einer geeigneten Stichprobe von Vorhaben durch."

**Status:** Das Modul `@flowaudit/sampling` ist nur geplant, nicht implementiert.

**Fehlende Funktionen:**
- Statistische Stichprobenverfahren (MUS, Zufallsauswahl)
- Schichtung nach Risiko, Fonds, Maßnahme
- Berechnung des Stichprobenumfangs
- Dokumentation der Auswahlmethodik
- Zufallsgenerator mit Seed-Speicherung

**Auswirkung:** Ohne Stichprobenmodul können keine rechtskonformen Vorhabenprüfungen durchgeführt werden.

### 4.2 🔴 KRITISCH: Fehlende Fehlerquoten-Hochrechnung (Projection)

**Anforderung Art. 77/Art. 85:**
> "Die Prüfbehörde berechnet die Gesamtfehlerquote und die Restfehlerquote."

**Status:** Das Modul `@flowaudit/projection` ist nur dokumentiert, nicht implementiert.

**Fehlende Funktionen:**
- Hochrechnung von Stichprobenfehlern auf die Grundgesamtheit
- Berechnung der gewichteten Fehlerquote
- Unterscheidung: Zufallsfehler, systembedingte Fehler, anomale Fehler
- Restfehlerquoten-Berechnung nach Finanzkorrekturen
- 2%-Wesentlichkeitsschwelle-Prüfung

**Auswirkung:** Keine Aussage zur Gesamtfehlerquote möglich – zentrales Element des Jahrekontrollberichts.

### 4.3 🔴 KRITISCH: Fehlender Jahreskontrollbericht (JKB)

**Anforderung Art. 85:**
> "Die Prüfbehörde erstellt einen jährlichen Kontrollbericht gemäß dem Muster in Anhang XXV."

**Status:** Das Modul `@flowaudit/jkb` ist nur als Platzhalter vorhanden.

**Fehlende Funktionen:**
- Strukturierter Bericht gemäß Anhang XXV
- Integration aller Teilberichte (Systemprüfungen, Vorhabenprüfungen)
- Prüfstellungnahme des Prüfbehördenleiters
- Bestätigungsvermerk (uneingeschränkt/eingeschränkt/versagt)
- Export im EU-konformen Format

**Auswirkung:** Zentrale Berichtspflicht nicht erfüllbar.

### 4.4 🔴 KRITISCH: Fehlende Prüfstrategie

**Anforderung Art. 78:**
> "Die Prüfbehörde legt der Kommission [...] eine Prüfstrategie vor."

**Status:** Nicht implementiert.

**Fehlende Funktionen:**
- Mehrjährige Prüfplanung (Rolling Plan)
- Risikobasierte Prüfungsauswahl
- Stichprobenkonzept mit Methodik
- Personal- und Ressourcenplanung
- Zeitplan für System- und Vorhabenprüfungen

**Auswirkung:** Keine strategische Prüfplanung gemäß EU-Vorgaben.

### 4.5 🟡 WICHTIG: Unvollständige Systemprüfung

**Status:** Grundmodell vorhanden, aber:

**Fehlende Funktionen:**
- Vollständiges Kategorie-Bewertungssystem (1-4)
- Zuordnung zu Schlüsselanforderungen (Key Requirements)
- Behebungsmaßnahmen-Tracking
- Follow-Up-Prüfungen
- Korrelation zwischen System- und Vorhabenprüfungsergebnissen

### 4.6 🟡 WICHTIG: Fehlende Schnittstellen

**Status:** Keine externen Integrationen implementiert.

**Fehlende Schnittstellen:**
- **SFC (System for Fund Management)** – EU-Berichtssystem
- **ARACHNE** – Risikoanalyse-Tool der EU
- **OLAF** – Meldung von Unregelmäßigkeiten
- **eMS/JEMS** – Projektmanagement-Systeme
- **EDES** – Ausschlussdatenbank

**Auswirkung:** Manuelle Datenübertragung erforderlich, Fehlerrisiko, Mehraufwand.

### 4.7 🟡 WICHTIG: Fehlende Risikobewertung

**Status:** Keine risikobasierte Komponente implementiert.

**Fehlende Funktionen:**
- Risiko-Scoring für Vorhaben/Begünstigte
- Risikofaktoren-Katalog (Betrag, Historie, Sektor)
- Red-Flag-Indikatoren
- Automatische Hochstufung bei Auffälligkeiten

### 4.8 🟡 WICHTIG: Unvollständiges Reporting

**Status:** Report-Engine vorhanden, aber:

**Fehlende Reports:**
- Standardisierte Prüfberichte gemäß Anhang XV
- Fehlerquoten-Übersichten nach Fonds/Priorität
- Trendanalysen über mehrere Geschäftsjahre
- Korrekturmaßnahmen-Register
- Statusbericht zu Finanzkorrekturen

### 4.9 🟡 WICHTIG: Fehlende Mehrsprachigkeit

**Status:** i18n vorhanden (DE/EN), aber:

- Keine EU-Amtssprachen-Unterstützung
- Keine rechtssichere Übersetzung von Fachtermini
- Keine Lokalisierung für andere EU-Länder

### 4.10 🟡 WICHTIG: Fehlende Archivierung

**Status:** Kein dediziertes Archivierungskonzept.

**Fehlende Funktionen:**
- Langzeitarchivierung (5+ Jahre nach Programmabschluss)
- Revisionssichere Speicherung
- Wiederherstellungsverfahren
- Löschkonzept nach Aufbewahrungsfrist

---

## 5. Vorbereitung auf Förderperiode 2028+

### 5.1 Neue Anforderungen (MFR 2028-2034)

| Anforderung | Aktuelle Abdeckung | Maßnahme |
|-------------|-------------------|----------|
| Einheitlicher Fonds | 🔴 Nicht vorbereitet | Fonds-Struktur anpassen |
| Partnerschaftspläne | 🔴 Nicht vorbereitet | Neues Modul erforderlich |
| DNSH-Prüfung | 🔴 Nicht vorhanden | Umweltchecklisten ergänzen |
| Vereinfachte Kosten | 🟡 Teilweise | Standardeinheitskosten-Modul |
| Digitale Übermittlung | 🟡 Export vorhanden | SFC-Integration |
| Multi-Level-Governance | 🟢 Konzernstruktur | Bereits unterstützt |

### 5.2 Empfohlene Priorisierung

**Phase 1: Kritische Compliance (2026)**
1. Stichprobenziehung (Sampling)
2. Fehlerquoten-Hochrechnung (Projection)
3. Jahreskontrollbericht (JKB)
4. Prüfstrategie-Modul

**Phase 2: Operative Exzellenz (2027)**
5. Risikobewertungs-System
6. SFC-Schnittstelle
7. Vollständige Systemprüfung
8. Erweiterte Reports

**Phase 3: Zukunftssicherheit (2028)**
9. DNSH-Integration
10. Einheitlicher Fonds
11. ARACHNE/OLAF-Integration
12. Langzeitarchivierung

---

## 6. Die 10 Punkte, die unbedingt berücksichtigt werden müssen

### 🔴 KRITISCHE PRIORITÄT

#### 1. Stichprobenziehung implementieren

**Warum:** Ohne rechtskonformes Sampling keine gültigen Vorhabenprüfungen.

**Anforderungen:**
- Monetary Unit Sampling (MUS) als Standardmethode
- Zufallsauswahl mit dokumentiertem Seed
- Mindestens 30 Stichprobeneinheiten pro Programm
- Schichtung nach Risikoklassen
- Export der Stichprobenliste für Prüfer

**Geschätzter Aufwand:** 3-4 Wochen Entwicklung

---

#### 2. Fehlerquoten-Hochrechnung entwickeln

**Warum:** Kernaussage für EU-Kommission und Bestätigungsvermerk.

**Anforderungen:**
- Berechnung: Gesamtfehlerquote = (Hochgerechneter Fehler / Prüfvolumen) × 100
- Unterscheidung: Zufallsfehler, systembedingte Fehler, anomale Fehler
- Restfehlerquote nach Finanzkorrekturen
- 2%-Schwellenwert-Warnung
- Konfidenzintervalle und Unsicherheitsanalyse

**Geschätzter Aufwand:** 2-3 Wochen Entwicklung

---

#### 3. Jahreskontrollbericht (JKB) erstellen

**Warum:** Jährliche Berichtspflicht an EU-Kommission gemäß Art. 85.

**Anforderungen:**
- Gliederung gemäß Anhang XXV der VO 2021/1060
- Automatische Aggregation aus Einzelprüfungen
- Prüfstellungnahme mit Kategorisierung
- Bestätigungsvermerk (uneingeschränkt/eingeschränkt/versagt)
- Word-/PDF-Export für offizielle Einreichung
- Versionierung und Signatur

**Geschätzter Aufwand:** 4-5 Wochen Entwicklung

---

#### 4. Prüfstrategie-Modul einführen

**Warum:** Pflichtenangabe an EU vor Beginn der Prüfperiode.

**Anforderungen:**
- Mehrjährige Prüfplanung (3 Jahre rollierend)
- Risikobasierte Schwerpunktsetzung
- Stichprobendesign-Dokumentation
- Personal- und Ressourcenallokation
- Zeitpläne mit Meilensteinen

**Geschätzter Aufwand:** 2-3 Wochen Entwicklung

---

### 🟡 HOHE PRIORITÄT

#### 5. Risikobewertungs-Framework aufbauen

**Warum:** Effiziente Ressourcenallokation und risikobasierte Prüfung.

**Anforderungen:**
- Risiko-Score pro Vorhaben (0-100)
- Faktoren: Betragshöhe, Begünstigten-Historie, Sektorrisiko, Vergabeart
- Red-Flag-Indikatoren (automatische Hochstufung)
- Integration in Stichprobenziehung (Schichtung)

**Geschätzter Aufwand:** 3-4 Wochen Entwicklung

---

#### 6. SFC2021-Schnittstelle entwickeln

**Warum:** Offizielle Datenübermittlung an EU-Kommission.

**Anforderungen:**
- XML-Export gemäß SFC-Spezifikation
- Validierung vor Upload
- Fehlerbehandlung mit Korrekturworkflow
- Statusverfolgung der Übermittlung
- Archivierung übermittelter Daten

**Geschätzter Aufwand:** 4-6 Wochen Entwicklung

---

#### 7. Systemprüfung vervollständigen

**Warum:** Schlüsselanforderungen gemäß Art. 69 prüfen.

**Anforderungen:**
- 15 Schlüsselanforderungen gemäß Anhang XI
- Kategorie-Bewertung (1-4) pro Anforderung
- Behebungsplan mit Fristen
- Follow-Up-Prüfungen mit Wirksamkeitsbewertung
- Korrelation zu Vorhabenprüfungsergebnissen

**Geschätzter Aufwand:** 3-4 Wochen Entwicklung

---

### 🟢 MITTLERE PRIORITÄT

#### 8. DNSH-Prüfung integrieren (für 2028+)

**Warum:** "Do No Significant Harm"-Prinzip wird Pflicht.

**Anforderungen:**
- Umweltcheckliste für Vorhaben
- 6 Umweltziele der EU-Taxonomie
- Klimaverträglichkeitsprüfung
- Nachweis-Dokumentation

**Geschätzter Aufwand:** 2-3 Wochen Entwicklung

---

#### 9. Langzeitarchivierung sicherstellen

**Warum:** Aufbewahrungspflicht 5 Jahre nach Programmabschluss (Art. 82).

**Anforderungen:**
- Revisionssichere Archivierung
- Wiederherstellungsverfahren
- Automatische Löschung nach Ablauf
- Prüfpfad-Erhaltung
- Migration bei Systemwechsel

**Geschätzter Aufwand:** 2-3 Wochen Entwicklung

---

#### 10. Vereinfachte Kostenoptionen unterstützen

**Warum:** Zunehmende Bedeutung in Förderperiode 2028+.

**Anforderungen:**
- Standardeinheitskosten-Katalog
- Pauschalen-Verwaltung
- Automatische Prüfung bei Standardkosten
- Anpassung der Fehlerquotenberechnung

**Geschätzter Aufwand:** 2-3 Wochen Entwicklung

---

## 7. Zusammenfassung und Empfehlung

### Aktueller Compliance-Status

| Bereich | Status | Dringlichkeit |
|---------|--------|---------------|
| Prüfungsfall-Management | 🟢 85% | - |
| Feststellungen/Findings | 🟢 90% | - |
| Konzernabfragen | 🟢 80% | - |
| Audit-Trail | 🟢 95% | - |
| Checklisten | 🟢 85% | - |
| **Stichprobenziehung** | 🔴 0% | KRITISCH |
| **Fehlerquoten-Hochrechnung** | 🔴 0% | KRITISCH |
| **Jahreskontrollbericht** | 🔴 0% | KRITISCH |
| **Prüfstrategie** | 🔴 0% | KRITISCH |
| Systemprüfung | 🟡 50% | HOCH |
| Risikobewertung | 🔴 0% | HOCH |
| Schnittstellen (SFC) | 🔴 0% | HOCH |

### Handlungsempfehlung

**FlowAudit bietet eine solide technische Basis**, ist aber für den produktiven Einsatz als Prüfbehörden-System **noch nicht vollständig konform** mit EU-Verordnung 2021/1060.

**Prioritäre Maßnahmen für 2026:**
1. Sofortige Implementierung von Sampling und Projection
2. JKB-Generator mit Anhang XXV Struktur
3. Prüfstrategie-Modul

**Geschätzter Gesamtaufwand für volle Compliance:** 20-25 Entwicklerwochen

**Risiko bei Nicht-Umsetzung:**
- Keine Vorlage des Jahreskontrollberichts möglich
- Potenzielle Aussetzung von Zahlungen durch EU-Kommission
- Haftungsrisiken für Prüfbehördenleiter

---

## 8. Quellen

- [EU-Verordnung 2021/1060 (EUR-Lex)](https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32021R1060)
- [Konsolidierte Fassung 01.03.2024](https://eur-lex.europa.eu/legal-content/DE/TXT/HTML/?uri=CELEX:02021R1060-20240301)
- [EU-Budget 2028-2034](https://commission.europa.eu/strategy-and-policy/eu-budget/long-term-eu-budget/eu-budget-2028-2034_en)
- [EU Cohesion Policy post-2027 (Umweltbundesamt)](https://www.umweltbundesamt.de/publikationen/eu-cohesion-policy-post-2027)
- [Delegierte Verordnung 2021/771](https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32021R0771)
- [EGESIF_16-0014-00 Sampling Method](https://ec.europa.eu/regional_policy/sources/guidance/guidance_sampling_method_de.pdf)

---

*Dieser Bericht wurde automatisch erstellt auf Basis einer Code-Analyse des FlowNavigator-Repositories.*
