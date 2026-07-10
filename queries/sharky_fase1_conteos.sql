-- Propósito: Sharky.fi (Solana) — conteos base de préstamos y defaults, últimos 6 meses.
-- Devuelve: originaciones y defaults por mes (actividad en ventana) + tasa de default de
-- la cohorte de préstamos originados en la ventana (linkeando take -> primer foreclose del
-- mismo ciclo del PDA account_loan, acotado por la siguiente toma para evitar reuse del PDA).
-- Fuente: schema decodificado sharky_solana. Enlace de ciclo de vida: account_loan.
-- Nota de completitud: se UNEN todas las variantes (v1 / v3 / compressed / escrow).

WITH takes AS (
    SELECT account_loan, call_block_time AS start_time
    FROM sharky_solana.sharky_call_takeloan
    WHERE call_block_time > now() - interval '6' month
    UNION ALL
    SELECT account_loan, call_block_time
    FROM sharky_solana.sharky_call_takeloanv3
    WHERE call_block_time > now() - interval '6' month
    UNION ALL
    SELECT account_loan, call_block_time
    FROM sharky_solana.sharky_call_takeloanv3compressed
    WHERE call_block_time > now() - interval '6' month
),
-- Todas las tomas (sin filtro de fecha en el borde) para calcular "siguiente toma" del PDA
takes_all AS (
    SELECT account_loan, call_block_time AS start_time
    FROM sharky_solana.sharky_call_takeloan
    WHERE call_block_time > now() - interval '9' month
    UNION ALL
    SELECT account_loan, call_block_time
    FROM sharky_solana.sharky_call_takeloanv3
    WHERE call_block_time > now() - interval '9' month
    UNION ALL
    SELECT account_loan, call_block_time
    FROM sharky_solana.sharky_call_takeloanv3compressed
    WHERE call_block_time > now() - interval '9' month
),
forecloses AS (
    SELECT account_loan, call_block_time AS default_time
    FROM sharky_solana.sharky_call_forecloseloan
    WHERE call_block_time > now() - interval '9' month
    UNION ALL
    SELECT account_loan, call_block_time
    FROM sharky_solana.sharky_call_forecloseloanv3
    WHERE call_block_time > now() - interval '9' month
    UNION ALL
    SELECT account_loan, call_block_time
    FROM sharky_solana.sharky_call_forecloseloanv3compressed
    WHERE call_block_time > now() - interval '9' month
    UNION ALL
    SELECT account_loan, call_block_time
    FROM sharky_solana.sharky_call_forecloseloanescrow
    WHERE call_block_time > now() - interval '9' month
),
-- Ciclo por toma: start_time y next_take_time del mismo account_loan
cycles AS (
    SELECT account_loan, start_time,
           lead(start_time) OVER (PARTITION BY account_loan ORDER BY start_time) AS next_take_time
    FROM takes_all
),
-- Marca defaulted = existe un foreclose entre esta toma y la siguiente toma del PDA
cohort AS (
    SELECT c.account_loan, c.start_time,
           CASE WHEN EXISTS (
               SELECT 1 FROM forecloses f
               WHERE f.account_loan = c.account_loan
                 AND f.default_time > c.start_time
                 AND (c.next_take_time IS NULL OR f.default_time < c.next_take_time)
           ) THEN 1 ELSE 0 END AS defaulted
    FROM cycles c
    WHERE c.start_time > now() - interval '6' month   -- solo cohorte de la ventana de 6m
)
SELECT
    'ORIGINACIONES_POR_MES'                        AS metric,
    cast(date_trunc('month', start_time) AS date)  AS mes,
    count(*)                                        AS n
FROM takes GROUP BY 2
UNION ALL
SELECT 'DEFAULTS_POR_MES',
       cast(date_trunc('month', default_time) AS date),
       count(*)
FROM forecloses WHERE default_time > now() - interval '6' month GROUP BY 2
UNION ALL
SELECT 'COHORTE_TOTAL', NULL, count(*) FROM cohort
UNION ALL
SELECT 'COHORTE_DEFAULTEADOS', NULL, sum(defaulted) FROM cohort
ORDER BY 1, 2
