# etl/04_quality_checks_ge.py
# Rapport Qualité (HTML) – contrôles équivalents GE, version robuste en pandas

import os
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

# -----------------------------
# Config / Connexion
# -----------------------------
load_dotenv("config/.env")
DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL, future=True)

REPORT_DIR = "docs/quality"
FAIL_DIR = "docs/quality/failing_rows"
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(FAIL_DIR, exist_ok=True)

# Période attendue (cohérente avec ta dim_date)
DATE_MIN = pd.Timestamp("2015-01-01")
DATE_MAX = pd.Timestamp("2030-12-31")

# -----------------------------
# Helpers
# -----------------------------
def load_table(name: str) -> pd.DataFrame:
    return pd.read_sql(f"SELECT * FROM {name}", engine)

def rule_result(ok: bool, text: str):
    return {"success": bool(ok), "text": text}

def save_failing_rows(df: pd.DataFrame, table: str, rule_code: str):
    if df.empty:
        return None
    path = os.path.join(FAIL_DIR, f"{table}__{rule_code}.csv")
    df.to_csv(path, index=False)
    return path

# -----------------------------
# Règles par table
# -----------------------------
def check_dim_marque(df: pd.DataFrame):
    results = []

    # 1) unicité du code
    duplicates = df[df.duplicated(subset=["marque_code"], keep=False)]
    ok = duplicates.empty
    link = save_failing_rows(duplicates, "dim_marque", "dup_marque_code")
    msg = "Unicité de dim_marque.marque_code"
    if link: msg += f" — lignes en échec: {link}"
    results.append(rule_result(ok, msg))

    # 2) non nulls
    nulls = df[df["marque_code"].isna() | df["marque_nom"].isna()]
    ok = nulls.empty
    link = save_failing_rows(nulls, "dim_marque", "nulls")
    msg = "Valeurs non nulles (marque_code, marque_nom)"
    if link: msg += f" — lignes en échec: {link}"
    results.append(rule_result(ok, msg))

    return results

def check_fait_ventes(df: pd.DataFrame):
    results = []

    # 1) ca non nul & >= 0
    bad = df[df["ca"].isna() | (df["ca"] < 0)]
    ok = bad.empty
    link = save_failing_rows(bad, "fait_ventes", "ca_non_nul_positif")
    msg = "CA non nul et positif"
    if link: msg += f" — lignes en échec: {link}"
    results.append(rule_result(ok, msg))

    # 2) marge_pct entre 0 et 100
    bad = df[(df["marge_pct"] < 0) | (df["marge_pct"] > 100) | (df["marge_pct"].isna())]
    ok = bad.empty
    link = save_failing_rows(bad, "fait_ventes", "marge_0_100")
    msg = "Marge % dans [0,100]"
    if link: msg += f" — lignes en échec: {link}"
    results.append(rule_result(ok, msg))

    # 3) date_key dans la plage attendue
    dts = pd.to_datetime(df["date_key"])
    bad = df[(dts < DATE_MIN) | (dts > DATE_MAX)]
    ok = bad.empty
    link = save_failing_rows(bad, "fait_ventes", "date_plage")
    msg = f"Dates dans [{DATE_MIN.date()} ; {DATE_MAX.date()}]"
    if link: msg += f" — lignes en échec: {link}"
    results.append(rule_result(ok, msg))

    return results

def check_fait_trafic(df: pd.DataFrame):
    results = []

    # 1) visites >= 0
    bad = df[df["visites"] < 0]
    ok = bad.empty
    link = save_failing_rows(bad, "fait_trafic", "visites_pos")
    msg = "Visites >= 0"
    if link: msg += f" — lignes en échec: {link}"
    results.append(rule_result(ok, msg))

    # 2) taux_conversion dans [0,1]
    bad = df[(df["taux_conversion"] < 0) | (df["taux_conversion"] > 1) | (df["taux_conversion"].isna())]
    ok = bad.empty
    link = save_failing_rows(bad, "fait_trafic", "taux_0_1")
    msg = "Taux de conversion dans [0,1]"
    if link: msg += f" — lignes en échec: {link}"
    results.append(rule_result(ok, msg))

    # 3) dates cohérentes
    dts = pd.to_datetime(df["date_key"])
    bad = df[(dts < DATE_MIN) | (dts > DATE_MAX)]
    ok = bad.empty
    link = save_failing_rows(bad, "fait_trafic", "date_plage")
    msg = f"Dates dans [{DATE_MIN.date()} ; {DATE_MAX.date()}]"
    if link: msg += f" — lignes en échec: {link}"
    results.append(rule_result(ok, msg))

    return results

def check_fait_trends(df: pd.DataFrame):
    results = []

    # 1) indice_trends dans [0,100]
    bad = df[(df["indice_trends"] < 0) | (df["indice_trends"] > 100) | (df["indice_trends"].isna())]
    ok = bad.empty
    link = save_failing_rows(bad, "fait_trends", "trends_0_100")
    msg = "Indice Trends dans [0,100]"
    if link: msg += f" — lignes en échec: {link}"
    results.append(rule_result(ok, msg))

    # 2) dates cohérentes
    dts = pd.to_datetime(df["date_key"])
    bad = df[(dts < DATE_MIN) | (dts > DATE_MAX)]
    ok = bad.empty
    link = save_failing_rows(bad, "fait_trends", "date_plage")
    msg = f"Dates dans [{DATE_MIN.date()} ; {DATE_MAX.date()}]"
    if link: msg += f" — lignes en échec: {link}"
    results.append(rule_result(ok, msg))

    return results

# -----------------------------
# Génération du rapport HTML
# -----------------------------
def generate_html_report(results_by_table: dict):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(REPORT_DIR, f"quality_report_{ts}.html")

    # Petit style “sobre luxe”
    css = """
    <style>
      body { font-family: -apple-system, Arial, sans-serif; margin: 24px; color:#222; }
      h1 { color:#3b1d5a; }
      .card { border:1px solid #eee; border-radius:12px; padding:16px 20px; margin:18px 0; box-shadow:0 1px 6px rgba(0,0,0,0.05); }
      .ok { color: #1b8a5a; font-weight:600; }
      .ko { color: #b00020; font-weight:600; }
      ul { margin:8px 0 0 18px; }
      a { color:#3b1d5a; text-decoration:none; }
      a:hover { text-decoration:underline; }
      .legend { font-size: 12px; color:#666; }
    </style>
    """

    html = [f"<html><head><meta charset='utf-8'><title>Rapport Qualité Données</title>{css}</head><body>"]
    html.append("<h1>Rapport Qualité Données</h1>")
    html.append("<p class='legend'>Ce rapport vérifie des règles clés (unicité, bornes, dates, non-nuls) sur les tables du modèle en étoile.</p>")

    for table, rules in results_by_table.items():
        html.append(f"<div class='card'><h2>{table}</h2><ul>")
        for r in rules:
            badge = "<span class='ok'>✅</span>" if r["success"] else "<span class='ko'>❌</span>"
            html.append(f"<li>{badge} {r['text']}</li>")
        html.append("</ul></div>")

    html.append("</body></html>")

    with open(out, "w") as f:
        f.write("\n".join(html))

    print(f"\n📄 Rapport généré : {out}")

# -----------------------------
# Main
# -----------------------------
def main():
    results = {}

    # dim_marque
    df = load_table("dim_marque")
    results["dim_marque"] = check_dim_marque(df)

    # fait_ventes
    df = load_table("fait_ventes")
    results["fait_ventes"] = check_fait_ventes(df)

    # fait_trafic
    df = load_table("fait_trafic")
    results["fait_trafic"] = check_fait_trafic(df)

    # fait_trends
    df = load_table("fait_trends")
    results["fait_trends"] = check_fait_trends(df)

    generate_html_report(results)

if __name__ == "__main__":
    main()
