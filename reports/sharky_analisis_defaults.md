# Sharky.fi — Préstamos NFT y defaults (últimos 6 meses)

**Fecha de ejecución:** 2026-07-10 · **Fuente:** Dune (`sharky_solana`, `magiceden_v2/v3_solana`, `tensorswap_v2_solana`) · **Chain:** Solana
**Frescura:** datos on-chain hasta 2026-07-10 (enero y julio parciales). *Esto no es asesoramiento financiero.*

---

## 1. Volumen de préstamos y defaults

| Métrica | Valor |
|---|---|
| **Préstamos originados (6m)** | **18.455** (~3.000/mes) |
| **Defaults ocurridos en la ventana** | **4.503** foreclosures |
| **Tasa de default de la cohorte** (originados en 6m que ya defaultearon) | **13,9%** (2.563 / 18.455) — *piso*, por censura a derecha |

Serie mensual (originaciones / defaults): ene 2254/449 · feb 2634/457 · mar 3224/939 · abr 3008/584 · may 3546/1103 · jun 2962/675 · jul(parcial) 827/296.
Pico de defaults en **mayo (1.103)**, coincidente con alta originación previa y probable caída de floors.

## 2. Underwater vs no-underwater

**Definición:** un default es *underwater* si la deuda (principal + interés) supera el floor de la colección al momento del default. Un default *no-underwater* implica que el borrower entregó un NFT que aún valía más que su deuda (default no estratégico: iliquidez, olvido, o incapacidad de repagar/vender a tiempo).

**Población analizada:** 2.453 defaults con floor estimable (de 4.503 totales = **54% de cobertura**; el resto son préstamos comprimidos, en USDC, o de colecciones sin ventas suficientes).

### Hallazgo central: los defaults se agrupan JUSTO en el floor
El ratio **deuda/floor mediano es ≈ 1,02**. Repartición:

| Zona (deuda/floor) | Interpretación | Defaults |
|---|---|---|
| < 0,9 | Claramente sano (NFT valía >10% más que la deuda) | **18%** |
| 0,9 – 1,1 | En la línea | **63%** |
| > 1,1 | Claramente underwater | **19%** |

**Lectura:** la mayoría de los defaults de Sharky son **económicamente racionales** — el borrower deja de pagar cuando el colateral vale aproximadamente lo mismo que la deuda. No son defaults "aleatorios": el 63% ocurre en la frontera exacta.

### El % underwater es un rango, no un número (depende del interés)
Como los defaults se apilan en deuda/floor≈1, el % underwater es muy sensible a los supuestos:

| Método de floor | Deuda = principal | + 5% interés | + 10% interés |
|---|---|---|---|
| Floor p15 (bajo) | 34,9% | **58,8%** | 73,4% |
| Floor mediana | 14,8% | 27,3% | 49,0% |

- **Caso base (floor p15, +5% interés): 58,8% underwater / 41,2% no-underwater.**
- **Ponderado por SOL de principal: 71% underwater** → los préstamos grandes tienden más a underwater que los chicos.

## 3. Metodología (reproducible)
1. Ciclo de vida por PDA `account_loan`: `offerloan` (principal) → `takeloan*` (NFT + inicio) → `forecloseloan*` (default). Se UNEN todas las variantes (v1/v3/compressed/escrow).
2. **Colección = orderbook de Sharky** (no hay etiqueta de colección en Dune para Solana). El floor se estima con el percentil bajo (p15) de las ventas en ME v2+v3 + Tensor v2 de los mints que Sharky usó como colateral en ese orderbook, en ventana [-10d, +2d] del default. Cobertura del método: 95% de los defaults matcheados.
3. Interés no decodificado (vive en `termsChoice`/orderbook) → se usa banda de sensibilidad ×1.05/×1.10.

Queries: `queries/sharky_fase1_conteos.sql`, `sharky_fase2a_defaults_enriquecidos.sql`, `sharky_fase2b_floor_underwater.sql`.
Charts: `reports/sharky_fase1_originaciones_vs_defaults.html`, `sharky_fase2_underwater.html`, `sharky_fase2_debt_to_floor.html`.

## 4. Nivel de confianza y limitaciones
- **Conteos de préstamos/defaults: ALTA.** Directo de instrucciones decodificadas.
- **Clasificación underwater: MEDIA-BAJA.** Sensible al supuesto de interés (lever dominante) y al método de floor. El hallazgo robusto es el *clustering* en deuda/floor≈1, no el % exacto.
- **Cobertura:** el underwater cubre 54% de los defaults (excluye comprimidos, USDC e iliquidez). Los conteos de la sección 1 sí son completos.
- **Censura a derecha:** cohortes de jun/jul aún no maduraron → la tasa de default final será algo mayor a 13,9%.
- **Floor por ventas (no listings):** aproximación; p15 de ventas ≈ floor pero con ruido.

## 5. Análisis complementario que tightening-earía el resultado
- **Decodificar el interés real** por orderbook (estimándolo de préstamos repagados: `repayloan.amount / principal`) → colapsa la banda de sensibilidad a un número.
- Incluir préstamos en **USDC** (`account_valueMint`) y **comprimidos** (via `tensor_cnft_solana`) para subir la cobertura del 54%.
- Cruzar con **caídas de floor** por colección para explicar el pico de defaults de mayo.
