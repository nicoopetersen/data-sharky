# Diario de sesiones

> Log breve por sesión: fecha · qué se analizó · conclusión · próximo paso.

## 2026-07-10 — Setup inicial
- **Qué se hizo:** instalación de la skill `analista-cripto`, creación del cerebro, venv con `dune-client` + stack core, helper `scripts/dune_helper.py` con caché.
- **Estado del entorno:** ✅ `DUNE_API_KEY` en `.env` (gitignored), venv OK, API verificada end-to-end (round-trip real en cluster free).
- **Plan Dune:** Free → ejecución solo en cluster gratuito (ver aprendizajes.md). Helper adaptado a REST sin tier.
- **Perfil de inversor:** pendiente (Nicolás pospuso el cuestionario). Recordar completarlo.
- **Seguridad:** recordado a Nicolás **rotar la key** porque la compartió por chat.
- **Próximo paso:** definir primer token/protocolo a analizar y/o completar perfil.

## 2026-07-10 — Sharky.fi Fase 1 (conteos)
- **Analizado:** préstamos y defaults de Sharky.fi (Solana), últimos 6 meses, vía Dune `sharky_solana`.
- **Resultados:** 18.455 originaciones; 4.503 defaults en ventana; cohorte default rate 13,9% (piso). Ver tesis/sharky-defaults.md.
- **Query:** queries/sharky_fase1_conteos.sql · chart: reports/sharky_fase1_originaciones_vs_defaults.html
- **Decisiones de Nicolás:** quiere ambas vistas (actividad + cohorte) y underwater con floor de Dune.
- **Próximo paso:** Fase 2 — underwater (principal+interés vs floor de colección al default). Estimar créditos antes de correr.

## 2026-07-10 — Sharky.fi Fase 2 (underwater) — CERRADO
- **Método:** orderbook=colección; floor = p15 de ventas ME v2+v3 + Tensor de mints-colateral, ventana ±10d. Cobertura 95% a nivel colección.
- **Resultado:** 2.453 defaults priceables (54% de 4.503). deuda/floor mediano ≈1,02. 63% en la línea, 19% claramente underwater, 18% sanos. % underwater = rango 15-73% (sensible al interés); caso base 58,8%; ponderado por SOL 71%.
- **Conclusión:** defaults mayormente racionales (colateral ≈ deuda). Reporte: reports/sharky_analisis_defaults.md
- **Aprendizajes técnicos guardados** (NFT Solana en Dune, Tensor cNFT, orderbook-as-collection). Rate limit 429 del plan Free al crear muchas queries — bajar ritmo.
- **Pendiente Fase 3:** decodificar interés real (repagos) para colapsar la banda; sumar USDC + comprimidos.
