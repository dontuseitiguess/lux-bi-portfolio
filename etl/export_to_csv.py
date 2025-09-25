import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv("config/.env")
DB_URL = os.getenv("DB_URL")

engine = create_engine(DB_URL, future=True)

OUT_DIR = "data/processed"
os.makedirs(OUT_DIR, exist_ok=True)
OUT_CSV = os.path.join(OUT_DIR, "mv_month_brand_country.csv")

sql = """
SELECT
  month_key, marque_key, pays_key,
  ca, unites, aov, marge_pct_avg, ca_online, ca_offline
FROM mv_month_brand_country
ORDER BY month_key, marque_key, pays_key
"""

with engine.begin() as con:
    df = pd.read_sql(text(sql), con)

df.to_csv(OUT_CSV, index=False)
print("✅ Exporté :", OUT_CSV, "| lignes:", len(df))

