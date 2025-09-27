# 💎 Luxury BI Portfolio

📊 Dashboard interactif de Business Intelligence appliqué au **secteur du luxe**.  
Projet réalisé dans le cadre de mon portfolio BI / Data pour décrocher une alternance en tant que **Business Intelligence Analyst / Consultant BI**.

👉 **[Démo en ligne (Streamlit Cloud)](https://lux-bi-portfolio-987atk4ppmvzxqjhrrntpk.streamlit.app/)**  
👉 **[Code source (GitHub)](https://github.com/dontuseitiguess/lux-bi-portfolio)**

---

## 🚀 Fonctionnalités principales

- **KPI Direction** : CA, unités, marge, YoY, YTD  
- **E-commerce** : part online/offline, séries mensuelles cumulées  
- **Marques** : benchmark, classement Top 20, comparateur dynamique  
- **Pays** : classement marchés, focus pays, YoY  
- **Tendances** : prévisions jusqu’à 2030 (Prophet ou fallback moyenne mobile)  
- **Exports** : téléchargement CSV direct (classements, prévisions)  
- **Insight box** : résumé automatique (année record, marque #1, pays #1)  

---

## 🏗️ Architecture

```bash
lux-bi-portfolio/
├── bi/streamlit_app/      # Dashboard Streamlit multipages
│   ├── Home.py
│   ├── pages/
│   │   ├── 01_Direction.py
│   │   ├── 02_Ecommerce.py
│   │   ├── 03_Marques.py
│   │   ├── 04_Pays.py
│   │   └── 05_Tendances.py
│   └── _shared.py         # Fonctions partagées (filtres, load_data, utils)
├── data/                  # Données raw + processed (CSV fallback)
├── etl/                   # Scripts ETL + qualité (Great Expectations)
├── sql/                   # Modèle en étoile + vues matérialisées
├── docs/                  # Screenshots + documentation (KPI_BOOK.md, REPORT.md)
└── requirements.txt       # Dépendances (pandas, streamlit, plotly, prophet…)
