import os
import re
import glob
import logging
import unicodedata
import pandas as pd
from pathlib import Path

# 1. Configuration du Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

BASE_DIR = Path(__file__).resolve().parent.parent
BRONZE_DIR = BASE_DIR / "bronze_data"
SILVER_DIR = BASE_DIR / "silver_data"
SILVER_DIR.mkdir(parents=True, exist_ok=True)

def remove_accents(input_str: str) -> str:
    """Nettoyage des accents et caractères spéciaux."""
    if not isinstance(input_str, str) or pd.isna(input_str):
        return ""
    s = "".join([c for c in unicodedata.normalize('NFKD', str(input_str)) if not unicodedata.combining(c)])
    s = s.lower().strip()
    s = re.sub(r"[.\-']", ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def create_join_key(name: str) -> str:
    """
    💡 CRÉATION D'UNE CLÉ UNIVERSELLE :
    Prend la 1ère lettre du prénom + le nom de famille (ex: 'e_haaland', 'm_salah')
    Résout le problème E. Haaland vs Erling Haaland !
    """
    cleaned = remove_accents(name)
    if not cleaned:
        return ""
    words = cleaned.split()
    if len(words) == 1:
        return words[0]
    return f"{words[0][0]}_{words[-1]}"

def format_currency(val) -> str:
    """Formate 7000000.0 en '7M' et 50000.0 en '50K'"""
    if pd.isna(val) or val == 0: return "0"
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M".replace('.0M', 'M')
    elif val >= 1_000:
        return f"{val / 1_000:.0f}K"
    return str(int(val))

def process_silver_layer():
    # ==========================================
    # ETAPE 1 : CLEANING SOFIFA DATA
    # ==========================================
    logging.info("Démarrage du nettoyage des données SoFIFA...")
    sofifa_files = glob.glob(str(BRONZE_DIR / "sofifa_pro_players_bronze_*.csv"))
    
    df_sofifa = None
    if sofifa_files:
        try:
            df_sofifa = pd.read_csv(sofifa_files[0])
            df_sofifa = df_sofifa.loc[:, ~df_sofifa.columns.str.contains('^Unnamed')]

            VALID_POSITIONS = {'GK', 'CB', 'LB', 'RB', 'LWB', 'RWB', 'CDM', 'CM', 'CAM', 'LM', 'RM', 'LW', 'RW', 'CF', 'ST'}

            def split_name_positions(val):
                if pd.isna(val): return "", ""
                tokens = str(val).strip().split()
                positions = []
                while tokens and tokens[-1] in VALID_POSITIONS:
                    positions.insert(0, tokens.pop())
                return " ".join(tokens), " ".join(positions)

            df_sofifa[['Player_Name', 'Positions']] = df_sofifa['Name'].apply(lambda x: pd.Series(split_name_positions(x)))
            df_sofifa['Primary_Position'] = df_sofifa['Positions'].apply(lambda x: x.split()[0] if x else "Unknown")
            
            # 💡 Création de la clé de jointure intelligente
            df_sofifa['Join_Key'] = df_sofifa['Player_Name'].apply(create_join_key)
            df_sofifa['Player_Type'] = df_sofifa['Primary_Position'].apply(lambda x: 'Goalkeeper' if x == 'GK' else 'Outfield')

            def split_team_contract(val):
                if pd.isna(val): return "Unknown", None
                match = re.search(r'^(.*?)(?:\s+(\d{4}\s*~\s*\d{4}|\d{4}))?$', str(val).strip())
                if match:
                    team = match.group(1).strip()
                    contract = match.group(2)
                    end_year = contract.split('~')[-1].strip() if contract and '~' in contract else contract
                    return team if team else "Unknown", end_year
                return str(val).strip(), None

            df_sofifa[['Club', 'Contract_End_Year']] = df_sofifa['Team & Contract'].apply(lambda x: pd.Series(split_team_contract(x)))
            df_sofifa['Height_cm'] = df_sofifa['Height'].astype(str).str.extract(r'(\d+)cm').astype(float)
            df_sofifa['Weight_kg'] = df_sofifa['Weight'].astype(str).str.extract(r'(\d+)kg').astype(float)

            def parse_currency(val):
                if pd.isna(val) or not isinstance(val, str): return 0.0
                val = val.replace('€', '').strip()
                if 'M' in val: return float(val.replace('M', '')) * 1_000_000
                if 'K' in val: return float(val.replace('K', '')) * 1_000
                try: return float(val)
                except: return 0.0

            df_sofifa['Value_EUR'] = df_sofifa['Value'].apply(parse_currency)
            df_sofifa['Wage_EUR'] = df_sofifa['Wage'].apply(parse_currency)
            df_sofifa['Value_Formatted'] = df_sofifa['Value_EUR'].apply(format_currency)
            df_sofifa['Wage_Formatted'] = df_sofifa['Wage_EUR'].apply(format_currency)
            df_sofifa['BMI'] = (df_sofifa['Weight_kg'] / ((df_sofifa['Height_cm'] / 100) ** 2)).round(2)

            overall_col = next((col for col in ['Overall rating', 'Overall_rating', 'Overall'] if col in df_sofifa.columns), None)
            if overall_col:
                df_sofifa['Value_per_Overall'] = (df_sofifa['Value_EUR'] / df_sofifa[overall_col]).round(2)

            cols_to_drop = ['Name', 'Team & Contract', 'Height', 'Weight', 'Value', 'Wage', 'Attacking work rate', 'Defensive work rate']
            df_sofifa = df_sofifa.drop(columns=[c for c in cols_to_drop if c in df_sofifa.columns])
            df_sofifa = df_sofifa.drop_duplicates(subset='Join_Key', keep='first')
            logging.info(f"SoFIFA Data nettoyée : {len(df_sofifa)} lignes.")
            
        except Exception as e:
            logging.error(f"Erreur lors du traitement de SoFIFA : {e}")
    else:
        logging.warning("Aucun fichier SoFIFA trouvé dans bronze_data/")

    # ==========================================
    # ETAPE 2 : CLEANING LEAGUES DATA
    # ==========================================
    logging.info("Démarrage du nettoyage des données des Ligues...")
    league_files = ['premier_league.csv', 'la_liga.csv', 'bundesliga.csv', 'serie_a.csv', 'Ligue_1.csv']
    dfs = []

    for f in league_files:
        path = BRONZE_DIR / f
        if path.exists():
            try:
                df = pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip')
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                df['League'] = f.replace('.csv', '').replace('_', ' ').title()

                player_col = next((c for c in ['player', 'Player', 'name', 'Name'] if c in df.columns), None)
                if player_col:
                    # 💡 Création de la même clé sur le fichier ligue
                    df['Join_Key'] = df[player_col].apply(create_join_key)
                    df = df.drop(columns=[player_col])

                dfs.append(df)
            except Exception as e:
                logging.error(f"Erreur sur le fichier {f} : {e}")
        else:
            logging.warning(f"Fichier introuvable : {f}")

    df_leagues = None
    if dfs:
        df_leagues = pd.concat(dfs, ignore_index=True)
        df_leagues = df_leagues.drop_duplicates(subset='Join_Key', keep='first')
        logging.info(f"Leagues Data nettoyée : {len(df_leagues)} lignes.")
    else:
        logging.warning("Aucun fichier de ligue trouvé.")

    # ==========================================
    # ETAPE 3 : MERGE & FINAL FORMATTING
    # ==========================================
    if df_sofifa is not None and df_leagues is not None:
        logging.info("Fusion des datasets sur Join_Key...")

        # 💡 Fusion basée sur notre clé intelligente
        df_final = pd.merge(df_sofifa, df_leagues, on="Join_Key", how="left")
        
        if 'team' in df_final.columns:
            df_final = df_final.drop(columns=['team'])

        # Gestion des Nulls
        df_final['League'] = df_final['League'].fillna('Other Leagues')
        df_final['Club'] = df_final['Club'].fillna('Free Agent')
        df_final['Contract_End_Year'] = df_final['Contract_End_Year'].fillna('Unknown')

        stats_cols = ['apps', 'min', 'goals', 'a', 'NPG']
        for col in stats_cols:
            if col in df_final.columns:
                df_final[col] = df_final[col].fillna(0)

        if all(c in df_final.columns for c in ['goals', 'a', 'min']):
            df_final['Performance_Score'] = ((df_final['goals'] + df_final['a']) / (df_final['min'] + 1) * 90).round(2)

        priority_cols = [
            'ID', 'Player_Name', 'Age', 'Primary_Position', 'Player_Type', 'Positions', 'Club', 'League', 'Contract_End_Year',
            'Height_cm', 'Weight_kg', 'BMI', 'Value_EUR', 'Value_Formatted', 'Wage_EUR', 'Wage_Formatted',
            'Value_per_Overall', 'apps', 'min', 'goals', 'a', 'NPG', 'Performance_Score'
        ]

        existing_priority = [c for c in priority_cols if c in df_final.columns]
        remaining_cols = [c for c in df_final.columns if c not in existing_priority and c not in ['Match_Name', 'Join_Key']]

        df_final = df_final[existing_priority + remaining_cols]
        df_final = df_final.dropna(how='all', axis=1)

        # Formatage des colonnes pour SNOWFLAKE
        df_final.columns = [
            re.sub(r'[^A-Z0-9_]', '', col.strip().replace(' ', '_').replace('\ufeff', '').upper())
            for col in df_final.columns
        ]

        final_out = SILVER_DIR / "final_players_silver.csv"
        df_final.to_csv(final_out, index=False)
        
        logging.info(f"✅ DATASET SILVER CREÉ AVEC SUCCÈS : {final_out}")
        logging.info(f"📊 Total des lignes : {len(df_final)}")
        logging.info(f"📊 Exemple Joueur 1 : {df_final['PLAYER_NAME'].iloc[0]} | League: {df_final['LEAGUE'].iloc[0]} | Goals: {df_final['GOALS'].iloc[0]}")
    else:
        logging.error("❌ Impossible de créer le dataset final : Données manquantes.")

if __name__ == "__main__":
    process_silver_layer()