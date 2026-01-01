# Akzeptanzkriterien prüfen

Prüfe Akzeptanzkriterien für Feature $ARGUMENTS.

## Anweisungen

1. Lies `docs/07_UMSETZUNG_MIT_CLAUDE_CLI.md`
2. Finde alle AC-x.x.x Kriterien für das angegebene Feature
3. Prüfe für jedes Kriterium:
   - Ist der Code implementiert?
   - Existiert ein Test dafür?
   - Besteht der Test?
4. Erstelle einen Bericht:

```
## AC-Prüfung Feature X

| AC-ID | Beschreibung | Implementiert | Test | Status |
|-------|--------------|---------------|------|--------|
| AC-x.x.x | ... | ✅/❌ | ✅/❌ | PASS/FAIL |
```

## Features

- **1**: Layer 0 (AC-1.x.x)
- **2**: Layer 1 (AC-2.x.x)
- **3**: Layer 2 (AC-3.x.x)
- **4**: Layer-Dashboard (AC-4.x.x)
- **5**: UI Enhancements (AC-5.x.x)
- **6**: Modul-Distribution (AC-6.x.x)
- **7**: Workflow-Historisierung (AC-7.x.x)

## Beispiel

`/check-ac 1` - Prüft alle Akzeptanzkriterien für Feature 1
