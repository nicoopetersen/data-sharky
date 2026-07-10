# Aprendizajes

> Lecciones acumuladas: qué análisis funcionaron, qué señales resultaron falsas, errores a no repetir.
> Última actualización: 2026-07-10

## Metodología
- _(vacío)_

## Señales que resultaron falsas
- _(vacío)_

## Errores a no repetir (técnicos y de criterio)
- Verificar decimales de tokens (6 vs 18) antes de reportar montos.
- Cuidado con double-counts en DEX aggregators.
- Chequear frescura de datos en Dune (lag variable) antes de concluir.

## Entorno / Dune API (2026-07-10)
- La cuenta de Dune es **plan Free**: la API permite EJECUTAR en el **cluster gratuito**
  (omitiendo `performance`) y LEER resultados cacheados. Los tiers `medium`/`large`
  devuelven `Invalid performance tier` (HTTP 400).
- ⚠️ El SDK `dune-client` (`run_query_dataframe`) fuerza el cluster `medium` aunque la
  firma diga `performance=None` → falla en Free. **Por eso el proyecto ejecuta vía REST
  omitiendo el tier** (ver `scripts/dune_helper.py`: `execute_query`, `run_sql`).
- Preferir `latest_result(query_id)` (lee cacheado, no gasta créditos de ejecución)
  sobre `execute_query()` cuando la query ya corrió.
- Créditos de ejecución del plan Free son limitados: estimar antes de correr y cachear en `./data/`.

## Qué funcionó bien
- **NFTs Solana en Dune (2026-07-10):** NO existe `nft.trades`/`nft.lending` para Solana (son EVM-only). Ventas de NFTs Solana están en `magiceden_v2_solana.trades`, `magiceden_v3_solana.trades`, `tensorswap_v2_solana.trades` (curadas). Columnas útiles: `account_mint`, `amount_original` (SOL), `block_time`, `blockchain='solana'`.
- ⚠️ **Tensor v2 en Dune es mayormente cNFT** (`account_mint` NULL, usa `account_merkle_tree`+`leaf_id`). Magic Eden v2/v3 sí trae mints reales. Para pricing por mint, ME es la fuente principal.
- **NO hay etiqueta de colección** en las trades de Solana en Dune. Truco que funcionó: usar el **orderbook del protocolo de lending como proxy de colección** y estimar floor con el percentil bajo de ventas de los mints-colateral. Cobertura 95% a nivel colección aunque sólo 29% a nivel mint individual.
- **Floor proxy robusto:** p15 de ventas en ventana [-10d,+2d]. El caso Sharky mostró defaults agrupados en deuda/floor≈1 → cuando pasa esto, reportar RANGO + el clustering, no un único %.
- Direcciones Solana en Dune = base58 string (no varbinary hex como EVM).
