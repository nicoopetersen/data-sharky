# Tesis: Sharky.fi — calidad de cartera de préstamos NFT (defaults / underwater)

- **Estado:** abierta (recolectando evidencia)
- **Creada:** 2026-07-10
- **Última actualización:** 2026-07-10
- **Nivel de confianza actual:** medio (Fase 1 con datos duros; underwater pendiente)

## Pregunta de análisis
Medir el volumen de préstamos y la tasa de default de Sharky.fi en los últimos 6 meses, y
separar los defaults "underwater" (deuda > floor de la colección al default) de los que no.

## Evidencia (Fase 1 — 2026-07-10, fuente Dune sharky_solana, datos hasta 2026-07-10)
- **Originaciones últimos 6m:** 18.455 préstamos (~3.000/mes; ene y jul parciales).
- **Defaults ocurridos en la ventana:** 4.503 foreclosures.
- **Cohorte (originados en 6m que YA defaultearon):** 2.563 / 18.455 = **13,9%** (piso, por censura a derecha en cohortes de jun/jul).
- Serie mensual originaciones: ene 2254, feb 2634, mar 3224, abr 3008, may 3546, jun 2962, jul(parcial) 827.
- Serie mensual defaults: ene 449, feb 457, mar 939, abr 584, may 1103, jun 675, jul 296.
- Report: reports/sharky_fase1_originaciones_vs_defaults.html

## Fase 2 — underwater (2026-07-10) ✅
- Población: 2.453 defaults con floor estimable (54% de los 4.503; excluye comprimidos/USDC/iliquidez).
- **Hallazgo central:** deuda/floor mediano ≈ **1,02**. Los defaults se agrupan JUSTO en el floor: 18% claramente sanos, **63% en la línea (0.9-1.1)**, 19% claramente underwater. → defaults económicamente racionales, no aleatorios.
- % underwater es un RANGO (sensible al interés, lever dominante): 15%-73% según supuestos. Caso base (floor p15, +5% int) = **58,8% underwater**; ponderado por SOL = **71%** (préstamos grandes más underwater).
- Método floor: orderbook = colección; p15 de ventas ME v2+v3 + Tensor v2 de mints-colateral en ventana [-10d,+2d]. Cobertura 95% de matcheados.
- Reporte completo: reports/sharky_analisis_defaults.md

## Pendiente (Fase 3 — para tightening)
- Decodificar interés real por orderbook (de repagos: repayloan.amount/principal) → colapsa la banda de sensibilidad a un número.
- Sumar préstamos USDC (`account_valueMint`) y comprimidos (`tensor_cnft_solana`) para subir cobertura del 54%.

## Riesgos / caveats metodológicos
- Censura a derecha: cohortes recientes (jun/jul) aún no maduraron → 13,9% subestima el default rate final.
- PDA `account_loan` reusable → cohorte linkeada por primer foreclose antes de la siguiente toma.
- Posibles préstamos en USDC (no solo SOL) via `account_valueMint` — verificar en Fase 2.

## Conclusión / decisión
Sharky tiene un default rate de cohorte de ~14% (piso) y la mayoría de sus defaults son racionales
(el colateral vale ≈ la deuda al momento de default). La cartera no muestra defaults "irracionales"
masivos. Para una tesis sobre el token/protocolo faltaría cruzar con ingresos por intereses del lado
lender y salud de los lenders. Estado: análisis de calidad de cartera cerrado; tesis de inversión abierta.
(Recordatorio: esto no es asesoramiento financiero.)
