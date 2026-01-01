Erstelle den Dokumenten-Parser für Format "$ARGUMENTS" gemäß Konzept Sektion 3.4.

**Pfad:** `apps/backend/app/services/development/parsers/$ARGUMENTS_parser.py`

**Unterstützte Formate:**
- `pdf` - pdfplumber + Tesseract OCR
- `docx` - python-docx
- `docm` - python-docx + oletools (VBA extrahieren!)
- `xlsx` - openpyxl
- `xlsm` - openpyxl + oletools (VBA extrahieren!)
- `image` - pytesseract + PIL

**Schritte:**
1. Lies Konzept Sektion 3.4 "Dokumenten-Parsing"
2. Implementiere die `parse_$ARGUMENTS()` Methode
3. Erstelle `ParseResult` mit:
   - content: str (Markdown-formatiert)
   - tables: list[dict]
   - metadata: dict
   - security_warnings: list[str]
4. Für Makro-Dateien (.docm, .xlsm):
   - VBA NUR extrahieren, NIEMALS ausführen
   - Sicherheitswarnung hinzufügen
5. Schreibe Tests mit Beispiel-Dateien
6. Führe Tests aus

**Dependencies prüfen:**
```bash
pip install pdfplumber python-docx openpyxl oletools pytesseract pillow
```
