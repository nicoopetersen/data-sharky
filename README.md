# data-sharky

Análisis on-chain de **Sharky.fi** (protocolo de préstamos NFT peer-to-peer en Solana) con datos de Dune Analytics.

## Qué contiene
- **`queries/`** — SQL DuneSQL (Trino) reproducibles:
  - `sharky_fase1_conteos.sql` — originaciones, defaults mensuales y tasa de default de cohorte (6m).
  - `sharky_fase2a_defaults_enriquecidos.sql` — defaults enriquecidos con orderbook + principal.
  - `sharky_fase2b_floor_underwater.sql` — floor por colección + clasificación underwater.
- **`scripts/`** — helper de Dune con caché (`dune_helper.py`) y scripts de análisis/visualización.
- **`reports/`** — análisis final en markdown ([`sharky_analisis_defaults.md`](reports/sharky_analisis_defaults.md)).
- **`cerebro/`** — memoria del proyecto (metodología, aprendizajes, tesis).

## Hallazgos (2026-07-10)
- 18.455 préstamos originados en 6 meses; 4.503 defaults; tasa de default de cohorte ~13,9%.
- Los defaults se agrupan **justo en el floor** (deuda/floor mediano ≈ 1,02) → mayormente racionales.
- % underwater = rango 15–73% según supuestos de interés (caso base ~59%).

## Uso
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # y poné tu DUNE_API_KEY
python scripts/dune_helper.py   # smoke test
```

## Notas
- Requiere `DUNE_API_KEY` (nunca commiteada; `.env` está en `.gitignore`).
- Metodología y limitaciones detalladas en el reporte. **No es asesoramiento financiero.**
