-- Propósito: Sharky.fi Fase 2B — para cada default de los últimos 6 meses, estimar el FLOOR
-- de su colección (orderbook) alrededor de la fecha del default y clasificar underwater.
-- Floor proxy = percentil bajo de las ventas (ME v2+v3 + Tensor v2) de los mints que Sharky
-- usó como colateral en ese orderbook, en ventana [-10d, +2d] respecto del default.
-- Enlaces idénticos a Fase 2A (foreclose->take->offer). Semi-join limita el escaneo a mints
-- que Sharky tocó (no todo Solana). Underwater se decide luego en pandas (principal vs floor).

WITH forecloses AS (
    SELECT account_loan, call_block_time AS default_time FROM sharky_solana.sharky_call_forecloseloan             WHERE call_block_time > now() - interval '6' month
    UNION ALL SELECT account_loan, call_block_time FROM sharky_solana.sharky_call_forecloseloanv3                 WHERE call_block_time > now() - interval '6' month
    UNION ALL SELECT account_loan, call_block_time FROM sharky_solana.sharky_call_forecloseloanv3compressed       WHERE call_block_time > now() - interval '6' month
    UNION ALL SELECT account_loan, call_block_time FROM sharky_solana.sharky_call_forecloseloanescrow             WHERE call_block_time > now() - interval '6' month
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
fc_take AS (
    SELECT f.account_loan, f.default_time, t.orderbook, t.mint, t.start_time,
           row_number() OVER (PARTITION BY f.account_loan, f.default_time ORDER BY t.start_time DESC) AS rn
    FROM forecloses f JOIN takes t ON t.account_loan = f.account_loan AND t.start_time < f.default_time
),
fc_take1 AS (SELECT * FROM fc_take WHERE rn = 1),
defaults AS (
    SELECT k.account_loan, k.default_time, k.orderbook, k.mint, k.start_time, o.principalLamports,
           row_number() OVER (PARTITION BY k.account_loan, k.default_time ORDER BY o.offer_time DESC) AS rp
    FROM fc_take1 k
    LEFT JOIN offers o ON o.account_loan = k.account_loan AND o.offer_time <= k.start_time
),
defaults1 AS (
    SELECT account_loan, default_time, orderbook, mint, principalLamports / 1e9 AS principal_sol
    FROM defaults WHERE rp = 1
),
-- universo de mints por orderbook (muestra de la colección)
ob_collateral AS (
    SELECT DISTINCT account_orderBook AS orderbook, account_collateralMint AS mint
    FROM sharky_solana.sharky_call_takeloan   WHERE call_block_time > now() - interval '13' month AND account_collateralMint IS NOT NULL
    UNION
    SELECT DISTINCT account_orderBook, account_collateralMint
    FROM sharky_solana.sharky_call_takeloanv3 WHERE call_block_time > now() - interval '13' month AND account_collateralMint IS NOT NULL
),
-- ventas de mints-colateral de Sharky (semi-join implícito via join a ob_collateral)
sales AS (
    SELECT account_mint AS mint, amount_original AS price_sol, block_time FROM magiceden_v2_solana.trades
      WHERE block_time > now() - interval '7' month AND blockchain='solana' AND account_mint IS NOT NULL AND currency_symbol='SOL' AND amount_original > 0
    UNION ALL
    SELECT account_mint, amount_original, block_time FROM magiceden_v3_solana.trades
      WHERE block_time > now() - interval '7' month AND blockchain='solana' AND account_mint IS NOT NULL AND currency_symbol='SOL' AND amount_original > 0
    UNION ALL
    SELECT account_mint, amount_original, block_time FROM tensorswap_v2_solana.trades
      WHERE block_time > now() - interval '7' month AND blockchain='solana' AND account_mint IS NOT NULL AND currency_symbol='SOL' AND amount_original > 0
),
ob_sales AS (
    SELECT c.orderbook, s.price_sol, s.block_time
    FROM sales s JOIN ob_collateral c ON c.mint = s.mint
)
SELECT d.account_loan, d.default_time, d.orderbook, d.principal_sol,
       count(os.price_sol)                        AS n_sales_window,
       approx_percentile(os.price_sol, 0.15)      AS floor_p15_sol,
       approx_percentile(os.price_sol, 0.50)      AS floor_median_sol
FROM defaults1 d
LEFT JOIN ob_sales os
       ON os.orderbook = d.orderbook
      AND os.block_time BETWEEN d.default_time - interval '10' day AND d.default_time + interval '2' day
GROUP BY 1, 2, 3, 4
