# Tests ausführen

Führe Tests für $ARGUMENTS aus.

## Anweisungen

1. Identifiziere welche Tests ausgeführt werden sollen
2. Führe die Tests aus
3. Analysiere Fehlermeldungen
4. Behebe gefundene Fehler
5. Führe Tests erneut aus bis sie bestehen

## Optionen

- **backend**: Alle Backend-Tests (`cd apps/backend && pytest`)
- **frontend**: Alle E2E-Tests (`cd apps/frontend && npm run test:e2e`)
- **vendor**: Vendor-spezifische Tests (`pytest -k vendor`)
- **layer**: Layer-spezifische Tests (`pytest -k layer`)
- **all**: Alle Tests

## Beispiel

`/run-tests backend` - Führt alle Backend-Tests aus
