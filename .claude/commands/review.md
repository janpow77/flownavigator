Führe ein Code-Review durch für: $ARGUMENTS

**Prüfpunkte:**

1. **Architektur-Konsistenz**
   - Pfade nach Projekt-Pattern? (apps/backend/app/, apps/frontend/src/)
   - Imports korrekt?
   - Keine `src/modules/` sondern `src/components/`

2. **Code-Qualität**
   - Typ-Annotationen vorhanden?
   - Docstrings?
   - Error-Handling?

3. **Sicherheit**
   - SQL-Injection möglich?
   - XSS-Risiken?
   - Secrets im Code?
   - VBA-Makros nur extrahiert, nie ausgeführt?

4. **Tests**
   - Ausreichende Testabdeckung?
   - Edge-Cases abgedeckt?

5. **Performance**
   - N+1 Queries?
   - Unnötige Loops?

**Ausgabe:**
- Liste der Findings (critical/warning/info)
- Vorgeschlagene Fixes
- Lob für gute Patterns
