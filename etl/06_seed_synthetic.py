"""
Script : 06_seed_synthetic.py
But : Générer et insérer des données synthétiques réalistes
Tables : fait_ventes, fait_trafic, fait_trends
Compatible : SQLAlchemy 2.x
"""

import os
import random
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Charger config
load_dotenv("config/.env")
DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL, future=True)

# ================================
# 1. Dimensions fixes
# ================================
dim_marque = [
    ("LV", "Louis Vuitton", "LVMH", "Maroquinerie"),
    ("DIOR", "Dior", "LVMH", "Couture/Parfums"),
    ("HERMES", "Hermès", "Indépendant", "Maroquinerie"),
    ("GUCCI", "Gucci", "Kering", "Couture/Luxe"),
]

dim_pays = [
    ("FR", "France", "EMEA"),
    ("US", "United States", "AMER"),
    ("CN", "China", "APAC"),
    ("JP", "Japan", "APAC"),
]

dim_categorie = [
    ("BAG", "Sacs"),
    ("SHOES", "Chaussures"),
    ("BEAUTY", "Parfums & Beauté"),
    ("WATCH", "Montres"),
]

dim_canal = [
    ("ONLINE", "E-commerce"),
    ("OFFLINE", "Boutiques"),
    ("MARKET", "Marketplaces"),
]

dim_devise = [
    ("EUR", "Euro", 1.0),
    ("USD", "US Dollar", 0.9),
    ("CNY", "Yuan Renminbi", 0.13),
    ("JPY", "Yen", 0.007),
]

# ================================
# 2. Générateurs de données
# ================================
def generate_sales(n=500, start="2018-01-01", end="2024-12-31"):
    dates = pd.date_range(start=start, end=end, freq="D")
    ventes = []
    for _ in range(n):
        ventes.append({
            "date_key": random.choice(dates).date(),
            "marque_code": random.choice(dim_marque)[0],
            "pays_iso2": random.choice(dim_pays)[0],
            "categorie_code": random.choice(dim_categorie)[0],
            "canal_code": random.choice(dim_canal)[0],
            "devise_code": random.choice(dim_devise)[0],
            "unites": random.randint(1, 50),
            "ca": random.randint(500, 5000) * random.randint(1, 10),
            "remise": random.choice([0, 0, 100, 200, 500]),
            "marge_pct": round(random.uniform(40, 70), 2),
        })
    return pd.DataFrame(ventes)

def generate_trafic(n=500, start="2018-01-01", end="2024-12-31"):
    dates = pd.date_range(start=start, end=end, freq="D")
    trafic = []
    for _ in range(n):
        visites = random.randint(100, 10000)
        taux_conversion = round(random.uniform(0.01, 0.2), 4)  # entre 1% et 20%
        trafic.append({
            "date_key": random.choice(dates).date(),
            "marque_code": random.choice(dim_marque)[0],
            "pays_iso2": random.choice(dim_pays)[0],
            "canal_code": random.choice(dim_canal)[0],
            "visites": visites,
            "taux_conversion": taux_conversion,
        })
    return pd.DataFrame(trafic)

def generate_trends(n=500, start="2018-01-01", end="2024-12-31"):
    dates = pd.date_range(start=start, end=end, freq="W")  # hebdomadaire
    trends = []
    for _ in range(n):
        trends.append({
            "date_key": random.choice(dates).date(),
            "marque_code": random.choice(dim_marque)[0],
            "pays_iso2": random.choice(dim_pays)[0],
            "indice_trends": random.randint(20, 100),  # entre 20 et 100
        })
    return pd.DataFrame(trends)

# ================================
# 3. Insertions
# ================================
def seed_dimensions(conn):
    conn.execute(text("TRUNCATE dim_marque, dim_pays, dim_categorie, dim_canal, dim_devise RESTART IDENTITY CASCADE;"))
    for m in dim_marque:
        conn.execute(text("INSERT INTO dim_marque (marque_code, marque_nom, groupe, segment) VALUES (:c1,:c2,:c3,:c4)"),
                     {"c1": m[0], "c2": m[1], "c3": m[2], "c4": m[3]})
    for p in dim_pays:
        conn.execute(text("INSERT INTO dim_pays (iso2, pays_lib, region) VALUES (:c1,:c2,:c3)"),
                     {"c1": p[0], "c2": p[1], "c3": p[2]})
    for c in dim_categorie:
        conn.execute(text("INSERT INTO dim_categorie (categorie_code, categorie_lib) VALUES (:c1,:c2)"),
                     {"c1": c[0], "c2": c[1]})
    for ca in dim_canal:
        conn.execute(text("INSERT INTO dim_canal (canal_code, canal_lib) VALUES (:c1,:c2)"),
                     {"c1": ca[0], "c2": ca[1]})
    for d in dim_devise:
        conn.execute(text("INSERT INTO dim_devise (code, libelle, taux_eur) VALUES (:c1,:c2,:c3)"),
                     {"c1": d[0], "c2": d[1], "c3": d[2]})
    print("✅ Dimensions insérées")

def seed_fait_ventes(conn, ventes_df):
    conn.execute(text("TRUNCATE fait_ventes RESTART IDENTITY CASCADE;"))
    for _, row in ventes_df.iterrows():
        conn.execute(text("""
            INSERT INTO fait_ventes
            (date_key, marque_key, pays_key, categorie_key, canal_key, devise_key, unites, ca, remise, marge_pct)
            VALUES (
              :date_key,
              (SELECT marque_key FROM dim_marque WHERE marque_code=:marque_code),
              (SELECT pays_key FROM dim_pays WHERE iso2=:pays_iso2),
              (SELECT categorie_key FROM dim_categorie WHERE categorie_code=:categorie_code),
              (SELECT canal_key FROM dim_canal WHERE canal_code=:canal_code),
              (SELECT devise_key FROM dim_devise WHERE code=:devise_code),
              :unites, :ca, :remise, :marge_pct
            )
        """), row.to_dict())
    print(f"✅ {len(ventes_df)} ventes insérées dans fait_ventes")

def seed_fait_trafic(conn, trafic_df):
    conn.execute(text("TRUNCATE fait_trafic RESTART IDENTITY CASCADE;"))
    for _, row in trafic_df.iterrows():
        conn.execute(text("""
            INSERT INTO fait_trafic
            (date_key, marque_key, pays_key, canal_key, visites, taux_conversion)
            VALUES (
              :date_key,
              (SELECT marque_key FROM dim_marque WHERE marque_code=:marque_code),
              (SELECT pays_key FROM dim_pays WHERE iso2=:pays_iso2),
              (SELECT canal_key FROM dim_canal WHERE canal_code=:canal_code),
              :visites, :taux_conversion
            )
        """), row.to_dict())
    print(f"✅ {len(trafic_df)} lignes insérées dans fait_trafic")

def seed_fait_trends(conn, trends_df):
    conn.execute(text("TRUNCATE fait_trends RESTART IDENTITY CASCADE;"))
    for _, row in trends_df.iterrows():
        conn.execute(text("""
            INSERT INTO fait_trends
            (date_key, marque_key, pays_key, indice_trends)
            VALUES (
              :date_key,
              (SELECT marque_key FROM dim_marque WHERE marque_code=:marque_code),
              (SELECT pays_key FROM dim_pays WHERE iso2=:pays_iso2),
              :indice_trends
            )
        """), row.to_dict())
    print(f"✅ {len(trends_df)} lignes insérées dans fait_trends")

# ================================
# 4. Main
# ================================
if __name__ == "__main__":
    ventes_df = generate_sales(n=500)
    trafic_df = generate_trafic(n=500)
    trends_df = generate_trends(n=500)

    with engine.begin() as conn:
        seed_dimensions(conn)
        seed_fait_ventes(conn, ventes_df)
        seed_fait_trafic(conn, trafic_df)
        seed_fait_trends(conn, trends_df)

    print("🎉 Seed terminé avec succès (ventes + trafic + trends) !")
