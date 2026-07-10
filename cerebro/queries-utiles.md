# Queries útiles de Dune

> Índice de queries que ya funcionan, para reutilizar sin re-crear.
> Formato: ID/archivo · propósito · parámetros · costo aprox. en créditos · última ejecución.
> Última actualización: 2026-07-10

| Query ID | Archivo local | Propósito | Parámetros | Costo aprox. | Última corrida |
|----------|---------------|-----------|------------|--------------|----------------|
| (ad-hoc) | queries/sharky_fase1_conteos.sql | Sharky: originaciones + defaults mensuales + tasa default cohorte (6m) | ninguno (ventana fija 6m) | bajo (tablas call chicas) | 2026-07-10 |
| (ad-hoc) | queries/sharky_fase2a_defaults_enriquecidos.sql | Sharky: defaults 6m enriquecidos (orderbook+mint+principal_sol) | ventana fija | bajo (solo Sharky) | 2026-07-10 |
| (ad-hoc) | queries/sharky_fase2b_floor_underwater.sql | Sharky: floor por orderbook + underwater (join ME/Tensor, semi-join) | ventana fija | medio (~scan 7m ventas, ~40s) | 2026-07-10 |

## Referencia: modelo de datos Sharky.fi en Dune (schema `sharky_solana`) — 2026-07-10
Protocolo de préstamos NFT P2P en **Solana**. Ciclo de vida de un préstamo, enlazado por el PDA **`account_loan`**:
- **Oferta** (lender publica principal): `sharky_call_offerloan` → cols clave: `account_loan`, `account_orderBook`, `account_lender`, **`principalLamports`** (monto en lamports), `termsChoice`, `call_block_time`.
- **Originación** (borrower toma el préstamo, bloquea NFT): `sharky_call_takeloan` / `takeloanv3` / `takeloanv3compressed` → `account_loan`, `account_borrower`, `account_lender`, **`account_collateralMint`** (NFT), `account_orderBook`, `call_block_time` (= inicio del préstamo).
- **Repago**: `sharky_call_repayloan` / `repayloanv3` / `repayloanv3compressed` / `repayloanescrow`.
- **Default (foreclosure)**: `sharky_call_forecloseloan` / `forecloseloanv3` / `forecloseloanv3compressed` / `forecloseloanescrow` → `account_loan`, `account_borrower`, `account_lender`, `account_collateralMint`, `call_block_time` (= momento del default). **No trae principal ni orderBook** → hay que joinear por `account_loan` a la oferta/take.
- Tabla `sharky_solana.events` (Anchor events) puede tener montos estructurados — a explorar.
- ⚠️ **Cuidado:** hay múltiples versiones (v1/v3/escrow/compressed). Contar TODAS las variantes (UNION) o se subcuenta. El PDA `account_loan` puede reusarse entre préstamos → linkear foreclose↔take por el take más reciente ANTES del foreclose.
- Principal e interés: `principalLamports` (oferta) + interés según `termsChoice`/orderbook. "Underwater" = deuda (principal+interés) > floor de la colección al momento del default → requiere fuente de floor price de colecciones Solana (Dune NFT trades / API externa).
