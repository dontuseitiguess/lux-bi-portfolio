
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_month_brand_country AS
SELECT
  DATE_TRUNC('month', v.date_key)::date AS month_key,
  v.marque_key,
  v.pays_key,
  SUM(v.ca) AS ca,
  SUM(v.unites) AS unites,
  CASE WHEN SUM(v.unites) > 0 THEN SUM(v.ca)::numeric / SUM(v.unites) ELSE 0 END AS aov,
  AVG(v.marge_pct) AS marge_pct_avg,
  SUM(CASE WHEN c.canal_code = 'ONLINE'  THEN v.ca ELSE 0 END) AS ca_online,
  SUM(CASE WHEN c.canal_code = 'OFFLINE' THEN v.ca ELSE 0 END) AS ca_offline
FROM fait_ventes v
JOIN dim_canal c ON c.canal_key = v.canal_key
GROUP BY 1,2,3;

-- Index pour accélérer les filtres (période, marque, pays)
CREATE INDEX IF NOT EXISTS idx_mv_mbc
  ON mv_month_brand_country(month_key, marque_key, pays_key);
