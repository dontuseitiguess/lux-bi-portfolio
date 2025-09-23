-- =========================
-- Schéma étoile Luxe BI
-- =========================

-- Dimensions
CREATE TABLE IF NOT EXISTS dim_date (
  date_key        DATE PRIMARY KEY,
  year            INT NOT NULL,
  quarter         INT CHECK (quarter BETWEEN 1 AND 4),
  month           INT CHECK (month BETWEEN 1 AND 12),
  month_name      TEXT,
  week            INT,
  day             INT,
  is_weekend      BOOLEAN
);

CREATE TABLE IF NOT EXISTS dim_marque (
  marque_key      SERIAL PRIMARY KEY,
  marque_code     TEXT UNIQUE NOT NULL,   -- ex: LV, DIOR, HERMES, GUCCI
  marque_nom      TEXT NOT NULL,
  groupe          TEXT,                   -- ex: LVMH, Kering
  segment         TEXT                    -- ex: maroquinerie, couture, joaillerie
);

CREATE TABLE IF NOT EXISTS dim_pays (
  pays_key        SERIAL PRIMARY KEY,
  iso2            CHAR(2) UNIQUE NOT NULL,
  pays_lib        TEXT NOT NULL,
  region          TEXT                     -- ex: EMEA, APAC, AMER
);

CREATE TABLE IF NOT EXISTS dim_categorie (
  categorie_key   SERIAL PRIMARY KEY,
  categorie_code  TEXT UNIQUE NOT NULL,    -- ex: BAG, SHOES, BEAUTY
  categorie_lib   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_canal (
  canal_key       SERIAL PRIMARY KEY,
  canal_code      TEXT UNIQUE NOT NULL,    -- ONLINE, OFFLINE, MARKETPLACE
  canal_lib       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_devise (
  devise_key      SERIAL PRIMARY KEY,
  code            CHAR(3) UNIQUE NOT NULL, -- EUR, USD, JPY...
  libelle         TEXT,
  taux_eur        NUMERIC(18,6)            -- taux moyen vers EUR (facultatif)
);

-- Faits
CREATE TABLE IF NOT EXISTS fait_ventes (
  vente_id        BIGSERIAL PRIMARY KEY,
  date_key        DATE NOT NULL REFERENCES dim_date(date_key),
  marque_key      INT NOT NULL REFERENCES dim_marque(marque_key),
  pays_key        INT NOT NULL REFERENCES dim_pays(pays_key),
  categorie_key   INT NOT NULL REFERENCES dim_categorie(categorie_key),
  canal_key       INT NOT NULL REFERENCES dim_canal(canal_key),
  devise_key      INT NOT NULL REFERENCES dim_devise(devise_key),
  unites          INT CHECK (unites >= 0),
  ca              NUMERIC(18,2) CHECK (ca >= 0),
  remise          NUMERIC(18,2) DEFAULT 0 CHECK (remise >= 0),
  marge_pct       NUMERIC(5,2) CHECK (marge_pct BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS fait_trafic (
  trafic_id       BIGSERIAL PRIMARY KEY,
  date_key        DATE NOT NULL REFERENCES dim_date(date_key),
  pays_key        INT NOT NULL REFERENCES dim_pays(pays_key),
  canal_key       INT NOT NULL REFERENCES dim_canal(canal_key),
  visites         INT CHECK (visites >= 0),
  taux_conversion NUMERIC(6,4) CHECK (taux_conversion BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS fait_trends (
  trends_id       BIGSERIAL PRIMARY KEY,
  date_key        DATE NOT NULL REFERENCES dim_date(date_key),
  pays_key        INT NOT NULL REFERENCES dim_pays(pays_key),
  marque_key      INT NOT NULL REFERENCES dim_marque(marque_key),
  indice_trends   INT CHECK (indice_trends BETWEEN 0 AND 100)
);

-- Index
CREATE INDEX IF NOT EXISTS idx_ventes_date ON fait_ventes(date_key);
CREATE INDEX IF NOT EXISTS idx_ventes_pays ON fait_ventes(pays_key);
CREATE INDEX IF NOT EXISTS idx_ventes_marque ON fait_ventes(marque_key);
CREATE INDEX IF NOT EXISTS idx_trafic_date_pays ON fait_trafic(date_key, pays_key);
CREATE INDEX IF NOT EXISTS idx_trends_date_marque ON fait_trends(date_key, marque_key);
