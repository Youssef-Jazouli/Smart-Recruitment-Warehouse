import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 1. Charger les variables d'environnement depuis le fichier .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH)

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "smart_recruitment_db")

# 2. Chemin du fichier Silver
SILVER_FILE = os.path.join(BASE_DIR, "silver_data", "final_players_silver.csv")

if not os.path.exists(SILVER_FILE):
    print(f"❌ Erreur : Le fichier {SILVER_FILE} n'existe pas. Exécute d'abord data_cleaning_silver.py !")
    exit()

print(f"📊 Chargement du dataset Silver : {SILVER_FILE}...")
df_silver = pd.read_csv(SILVER_FILE)

# 3. Vérifier & Créer la BDD si elle n'existe pas
ADMIN_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/postgres"

try:
    admin_engine = create_engine(ADMIN_DATABASE_URL, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'"))
        db_exists = result.scalar()
        
        if not db_exists:
            print(f"⚙️ La base de données '{DB_NAME}' n'existe pas. Création en cours...")
            conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
            print(f"✅ Base de données '{DB_NAME}' créée avec succès !")
        else:
            print(f"✅ La base de données '{DB_NAME}' existe déjà.")
except Exception as e:
    print(f"⚠️ Remarque lors de la vérification de la BDD : {e}")

# 4. Connexion à la base de données cible (smart_recruitment_db)
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print(f"✅ Connexion réussie à PostgreSQL ({DB_NAME}) !")
except Exception as e:
    print(f"❌ Erreur de connexion à PostgreSQL : {e}")
    exit()

# 5. Construction du Star Schema (Couche Gold)
print("\n⏳ Construction du Star Schema (Couche Gold)...")

# --- A. DIMENSION TABLE: Dim_Team ---
team_cols = ['Club', 'League', 'Contract_End_Year']
existing_team_cols = [c for c in team_cols if c in df_silver.columns]

df_teams = df_silver[existing_team_cols].drop_duplicates().reset_index(drop=True)
df_teams['team_id'] = df_teams.index + 1

df_teams = df_teams[['team_id'] + existing_team_cols]
df_teams.to_sql('dim_team', engine, if_exists='replace', index=False)
print("  ⭐ Table Dimension 'dim_team' créée avec succès !")

# --- B. DIMENSION TABLE: Dim_Player ---
player_cols = [
    'ID', 'Player_Name', 'Age', 'Primary_Position', 'Player_Type', 'Positions', 
    'Height_cm', 'Weight_kg', 'BMI', 'Preferred_foot'
]
existing_player_cols = [c for c in player_cols if c in df_silver.columns]

df_players = df_silver[existing_player_cols].drop_duplicates().reset_index(drop=True)
df_players.to_sql('dim_player', engine, if_exists='replace', index=False)
print("  ⭐ Table Dimension 'dim_player' créée avec succès !")

# --- C. FACT TABLE: Fact_Performances ---
df_fact = pd.merge(df_silver, df_teams, on=existing_team_cols, how='left')

cols_to_exclude = ['Player_Name', 'Positions', 'Club', 'League', 'Contract_End_Year', 'Preferred_foot']
fact_cols = [c for c in df_fact.columns if c not in cols_to_exclude]

df_fact_final = df_fact[fact_cols]
df_fact_final.to_sql('fact_performances', engine, if_exists='replace', index=False)
print("  ⭐ Table de Faits 'fact_performances' créée avec succès !")

print("\n🏆 GOLD LAYER COMPLETÉ AVEC SUCCÈS DANS POSTGRESQL !")