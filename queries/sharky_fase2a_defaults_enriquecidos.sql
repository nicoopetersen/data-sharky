-- Propósito: Sharky.fi Fase 2A — defaults (foreclosures) de los últimos 6 meses enriquecidos
-- con su orderbook (=colección), el mint del colateral y el principal (en SOL).
-- Linkeo: foreclose -> take del mismo ciclo (última toma del account_loan antes del default)
--         take -> offer (última oferta del account_loan antes de la toma) para el principal.
-- Sólo columnas seguras: de foreclose sólo account_loan + time; mint/orderbook vienen del take.

WITH forecloses AS (
    SELECT account_loan, call_block_time AS default_time
    FROM sharky_solana.sharky_call_forecloseloan       WHERE call_block_time > now() - interval '6' month
    UNION ALL
    SELECT account_loan, call_block_time FROM sharky_solana.sharky_call_forecloseloanv3           WHERE call_block_time > now() - interval '6' month
    UNION ALL
    SELECT account_loan, call_block_time FROM sharky_solana.sharky_call_forecloseloanv3compressed WHERE call_block_time > now() - interval '6' month
    UNION ALL
    SELECT account_loan, call_block_time FROM sharky_solana.sharky_call_forecloseloanescrow       WHERE call_block_time > now() - interval '6' month
),
takes AS (
    SELECT account_loan, account_orderBook AS orderbook, account_collateralMint AS mint, call_block_time AS start_time
    FROM sharky_solana.sharky_call_takeloan   WHERE call_block_time > now() - interval '13' month
    UNION ALL
    SELECT account_loan, account_orderBook, account_collateralMint, call_block_time
    FROM sharky_solana.sharky_call_takeloanv3 WHERE call_block_time > now() - interval '13' month
),
offers AS (
    SELECT account_loan, principalLamports, call_block_time AS offer_time
    FROM sharky_solana.sharky_call_offerloan  WHERE call_block_time > now() - interval '13' month
),
-- foreclose -> take del mismo ciclo (última toma antes del default)
fc_take AS (
    SELECT f.account_loan, f.default_time, t.orderbook, t.mint, t.start_time,
           row_number() OVER (PARTITION BY f.account_loan, f.default_time ORDER BY t.start_time DESC) AS rn
    FROM forecloses f
    JOIN takes t ON t.account_loan = f.account_loan AND t.start_time < f.default_time
),
fc_take1 AS (SELECT * FROM fc_take WHERE rn = 1),
-- take -> offer (última oferta antes de la toma) para principal
fc_prin AS (
    SELECT k.account_loan, k.default_time, k.orderbook, k.mint, k.start_time,
           o.principalLamports,
           row_number() OVER (PARTITION BY k.account_loan, k.default_time ORDER BY o.offer_time DESC) AS rp
    FROM fc_take1 k
    LEFT JOIN offers o ON o.account_loan = k.account_loan AND o.offer_time <= k.start_time
)
SELECT account_loan, orderbook, mint, start_time, default_time,
       principalLamports / 1e9 AS principal_sol
FROM fc_prin
WHERE rp = 1
