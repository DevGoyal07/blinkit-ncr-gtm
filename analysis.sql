-- ============================================================================
-- Zippy q-commerce | "Where do we launch dark store #7?"  --  SQL analysis
-- Dialect: SQLite (CTEs + window functions). Runs on the three CSVs loaded
-- as tables: areas, dark_stores, orders.
--
-- Recent quarter = 2026-03, 2026-04, 2026-05 (used for the scorecard).
-- "Demand attempt" = a delivered order OR an unserviceable demand signal
-- (we drop cancelled_other as noise). Unserviceable = customer wanted to
-- order but no store could serve in time -> unmet demand.
-- ============================================================================


-- @@QUERY: q1_city_trend -- City demand trend by month (sanity + growth)
SELECT
    order_month,
    COUNT(*) FILTER (WHERE status IN ('delivered','unserviceable'))           AS demand_attempts,
    COUNT(*) FILTER (WHERE status = 'delivered')                              AS delivered,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'unserviceable')
                / COUNT(*) FILTER (WHERE status IN ('delivered','unserviceable')), 1) AS unserviceable_pct
FROM orders
GROUP BY order_month
ORDER BY order_month;


-- @@QUERY: q2_area_scorecard -- Per-area demand + service profile (recent quarter)
WITH base AS (
    SELECT
        o.area_name,
        COUNT(*) FILTER (WHERE o.status IN ('delivered','unserviceable'))     AS attempts,
        COUNT(*) FILTER (WHERE o.status = 'delivered')                        AS delivered,
        COUNT(*) FILTER (WHERE o.status = 'unserviceable')                    AS unmet,
        ROUND(AVG(o.order_value), 0)                                          AS aov,
        ROUND(AVG(o.delivery_time_min), 1)                                    AS avg_delivery_min,
        ROUND(100.0 * COUNT(*) FILTER (WHERE o.delivery_time_min > o.promised_time_min)
                    / NULLIF(COUNT(*) FILTER (WHERE o.status='delivered'),0),1) AS sla_breach_pct
    FROM orders o
    WHERE o.order_month IN ('2026-03','2026-04','2026-05')
    GROUP BY o.area_name
)
SELECT
    a.area_name, a.zone, a.has_own_store,
    a.est_households, a.avg_income_index, a.competitor_count,
    a.dist_to_nearest_store_km AS dist_km,
    b.attempts, b.delivered, b.unmet,
    ROUND(100.0 * b.unmet / b.attempts, 1)                                    AS unserviceable_pct,
    ROUND(100.0 * b.delivered / b.attempts, 1)                                AS capture_pct,
    b.aov, b.avg_delivery_min, b.sla_breach_pct,
    ROUND(1000.0 * b.attempts / a.est_households, 1)                          AS demand_per_1k_hh
FROM areas a
JOIN base b ON b.area_name = a.area_name
ORDER BY b.attempts DESC;


-- @@QUERY: q3_growth -- Demand growth: last month vs first month of window, per area
WITH m AS (
    SELECT area_name,
           COUNT(*) FILTER (WHERE order_month='2025-12' AND status IN ('delivered','unserviceable')) AS m0,
           COUNT(*) FILTER (WHERE order_month='2026-05' AND status IN ('delivered','unserviceable')) AS m5
    FROM orders
    GROUP BY area_name
)
SELECT a.area_name, a.has_own_store, m.m0 AS dec_2025, m.m5 AS may_2026,
       ROUND(100.0 * (m.m5 - m.m0) / NULLIF(m.m0,0), 1) AS growth_pct_6mo
FROM m JOIN areas a ON a.area_name = m.area_name
ORDER BY growth_pct_6mo DESC;


-- @@QUERY: q4_opportunity -- Underserved-demand opportunity score (candidate areas only)
-- Each driver min-max normalised within the candidate set, then weighted:
--   demand 0.30 | density 0.20 | growth 0.25 | under-service 0.25
WITH q AS (
    SELECT area_name,
           COUNT(*) FILTER (WHERE status IN ('delivered','unserviceable'))    AS attempts,
           COUNT(*) FILTER (WHERE status = 'unserviceable')                   AS unmet,
           COUNT(*) FILTER (WHERE status = 'delivered')                       AS delivered
    FROM orders
    WHERE order_month IN ('2026-03','2026-04','2026-05')
    GROUP BY area_name
),
g AS (
    SELECT area_name,
           COUNT(*) FILTER (WHERE order_month='2025-12' AND status IN ('delivered','unserviceable')) AS m0,
           COUNT(*) FILTER (WHERE order_month='2026-05' AND status IN ('delivered','unserviceable')) AS m5
    FROM orders GROUP BY area_name
),
cand AS (
    SELECT a.area_name, a.est_households, a.competitor_count,
           a.dist_to_nearest_store_km AS dist_km,
           q.attempts,
           1.0 * q.unmet / q.attempts                       AS underservice_rate,
           1.0 * q.delivered / q.attempts                   AS capture_rate,
           1000.0 * q.attempts / a.est_households           AS density,
           1.0 * (g.m5 - g.m0) / NULLIF(g.m0,0)             AS growth
    FROM areas a
    JOIN q ON q.area_name = a.area_name
    JOIN g ON g.area_name = a.area_name
    WHERE a.has_own_store = 0
),
norm AS (
    SELECT *,
        1.0*(attempts      - MIN(attempts)          OVER()) / NULLIF(MAX(attempts)          OVER() - MIN(attempts)          OVER(),0) AS n_demand,
        (density           - MIN(density)           OVER()) / NULLIF(MAX(density)           OVER() - MIN(density)           OVER(),0) AS n_density,
        (growth            - MIN(growth)            OVER()) / NULLIF(MAX(growth)            OVER() - MIN(growth)            OVER(),0) AS n_growth,
        (underservice_rate - MIN(underservice_rate) OVER()) / NULLIF(MAX(underservice_rate) OVER() - MIN(underservice_rate) OVER(),0) AS n_under
    FROM cand
)
SELECT area_name, est_households AS households, competitor_count AS competitors, dist_km,
       ROUND(100*underservice_rate,1) AS unmet_pct,
       ROUND(100*capture_rate,1)      AS capture_pct,
       ROUND(100*growth,1)            AS growth_pct,
       ROUND(100 * (0.30*n_demand + 0.20*n_density + 0.25*n_growth + 0.25*n_under), 1) AS opportunity_score
FROM norm
ORDER BY opportunity_score DESC;


-- @@QUERY: q5_decision -- Combine opportunity score + cannibalisation + feasibility into the call
WITH q AS (
    SELECT area_name,
           COUNT(*) FILTER (WHERE status IN ('delivered','unserviceable')) AS attempts,
           COUNT(*) FILTER (WHERE status = 'unserviceable')                AS unmet,
           COUNT(*) FILTER (WHERE status = 'delivered')                    AS delivered
    FROM orders WHERE order_month IN ('2026-03','2026-04','2026-05')
    GROUP BY area_name
),
g AS (
    SELECT area_name,
           COUNT(*) FILTER (WHERE order_month='2025-12' AND status IN ('delivered','unserviceable')) AS m0,
           COUNT(*) FILTER (WHERE order_month='2026-05' AND status IN ('delivered','unserviceable')) AS m5
    FROM orders GROUP BY area_name
),
cand AS (
    SELECT a.area_name, a.est_households AS hh, a.competitor_count AS comp,
           a.dist_to_nearest_store_km AS dist_km,
           q.attempts,
           1.0*q.unmet/q.attempts                  AS unmet_rate,
           1.0*q.delivered/q.attempts              AS capture_rate,
           1000.0*q.attempts/a.est_households       AS density,
           1.0*(g.m5-g.m0)/NULLIF(g.m0,0)           AS growth
    FROM areas a JOIN q ON q.area_name=a.area_name JOIN g ON g.area_name=a.area_name
    WHERE a.has_own_store = 0
),
norm AS (
    SELECT *,
        100*(0.30*(1.0*(attempts -MIN(attempts)     OVER())/NULLIF(MAX(attempts)     OVER()-MIN(attempts)     OVER(),0))
           + 0.20*((density      -MIN(density)      OVER())/NULLIF(MAX(density)      OVER()-MIN(density)      OVER(),0))
           + 0.25*((growth       -MIN(growth)       OVER())/NULLIF(MAX(growth)       OVER()-MIN(growth)       OVER(),0))
           + 0.25*((unmet_rate   -MIN(unmet_rate)   OVER())/NULLIF(MAX(unmet_rate)   OVER()-MIN(unmet_rate)   OVER(),0))) AS opportunity
    FROM cand
)
SELECT area_name, hh AS households, comp AS competitors, dist_km,
       ROUND(100*unmet_rate,1)   AS unmet_pct,
       ROUND(100*capture_rate,1) AS capture_pct,
       ROUND(100*growth,1)       AS growth_pct,
       ROUND(opportunity,1)      AS opp_score,
       CASE
         WHEN hh < 40000                   THEN '4 DONT  (sub-scale: catchment too small for a store)'
         WHEN capture_rate >= 0.90         THEN '3 DONT  (already served -> ~pure cannibalisation)'
         WHEN opportunity   >= 80          THEN '1 LAUNCH (clear standout: large + underserved + low cannibalisation)'
         ELSE                                   '2 PHASE (real opportunity; revisit - cannibalisation/competition/scale)'
       END AS decision
FROM norm
ORDER BY decision, opportunity DESC;


-- @@QUERY: q6_densify -- Capacity strain in MATURE (served) zones -> densification candidates
-- A market leader's "next store" can also be a 2nd store to relieve an
-- over-capacity catchment. Flag served zones whose service is degrading.
WITH s AS (
    SELECT o.area_name,
           COUNT(*) FILTER (WHERE o.status IN ('delivered','unserviceable'))  AS attempts,
           ROUND(100.0*COUNT(*) FILTER (WHERE o.status='unserviceable')
                     /COUNT(*) FILTER (WHERE o.status IN ('delivered','unserviceable')),1) AS unserviceable_pct,
           ROUND(AVG(o.delivery_time_min),1) AS avg_delivery_min,
           ROUND(100.0*COUNT(*) FILTER (WHERE o.delivery_time_min>o.promised_time_min)
                     /NULLIF(COUNT(*) FILTER (WHERE o.status='delivered'),0),1) AS sla_breach_pct
    FROM orders o
    WHERE o.order_month IN ('2026-03','2026-04','2026-05')
    GROUP BY o.area_name
)
SELECT a.area_name, a.zone, a.nearest_store_id AS store, s.attempts,
       s.unserviceable_pct, s.avg_delivery_min, s.sla_breach_pct,
       CASE WHEN s.avg_delivery_min > 14 OR s.sla_breach_pct > 25
            THEN 'DENSIFY - add relief store' ELSE 'healthy' END AS flag
FROM areas a JOIN s ON s.area_name=a.area_name
WHERE a.has_own_store = 1
ORDER BY s.avg_delivery_min DESC;
