import os
import re
import unicodedata
import pandas as pd

# 1. Chargement du fichier CSV
file_path = "bronze_data/sofifa_pro_players_bronze_20260723_143815.csv"
df = pd.read_csv(file_path)

def clean_sofifa_dataframe(df_raw):
    df_clean = df_raw.copy()

    # Liste des positions officielles FIFA pour un Matching exact
    VALID_POSITIONS = {'GK', 'CB', 'LB', 'RB', 'LWB', 'RWB', 'CDM', 'CM', 'CAM', 'LM', 'RM', 'LW', 'RW', 'CF', 'ST'}

    # A. Séparer le Nom et les Positions de façon stricte
    def split_name_positions(val):
        if pd.isna(val): return "", ""
        tokens = str(val).strip().split()
        
        # Récupérer les positions à la fin du texte
        positions = []
        while tokens and tokens[-1] in VALID_POSITIONS:
            positions.insert(0, tokens.pop())
            
        name = " ".join(tokens)
        pos_str = " ".join(positions)
        return name, pos_str

    df_clean[['Player_Name', 'Positions']] = df_clean['Name'].apply(lambda x: pd.Series(split_name_positions(x)))
    df_clean['Primary_Position'] = df_clean['Positions'].apply(lambda x: x.split()[0] if x else "Unknown")

    # Nom normalisé pour le Matching
    def remove_accents(input_str):
        if not isinstance(input_str, str): return ""
        return "".join([c for c in unicodedata.normalize('NFKD', input_str) if not unicodedata.combining(c)])

    df_clean['Match_Name'] = df_clean['Player_Name'].apply(remove_accents)

    # B. Séparer le Club et la fin du Contrat
    def split_team_contract(val):
        if pd.isna(val): return "Unknown", None
        match = re.search(r'^(.*?)(?:\s+(\d{4}\s*~\s*\d{4}|\d{4}))?$', str(val).strip())
        if match:
            team = match.group(1).strip()
            contract = match.group(2)
            end_year = contract.split('~')[-1].strip() if contract and '~' in contract else contract
            return team if team else "Unknown", end_year
        return str(val).strip(), None

    df_clean[['Club', 'Contract_End_Year']] = df_clean['Team & Contract'].apply(lambda x: pd.Series(split_team_contract(x)))

    # C. Nettoyage Taille (cm) et Poids (kg)
    df_clean['Height_cm'] = df_clean['Height'].astype(str).str.extract(r'(\d+)cm').astype(float)
    df_clean['Weight_kg'] = df_clean['Weight'].astype(str).str.extract(r'(\d+)kg').astype(float)

    # D. Parsing Finances (€)
    def parse_currency(val):
        if pd.isna(val) or not isinstance(val, str): return 0.0
        val = val.replace('€', '').strip()
        if 'M' in val: return float(val.replace('M', '')) * 1_000_000
        if 'K' in val: return float(val.replace('K', '')) * 1_000
        try: return float(val)
        except: return 0.0

    df_clean['Value_EUR'] = df_clean['Value'].apply(parse_currency)
    df_clean['Wage_EUR'] = df_clean['Wage'].apply(parse_currency)

    # E. Detection dynamique de la colonne Overall
    overall_col = next((col for col in ['Overall rating', 'Overall_rating', 'Overall'] if col in df_clean.columns), None)

    # F. Feature Engineering (KPIs)
    if 'Weight_kg' in df_clean.columns and 'Height_cm' in df_clean.columns:
        df_clean['BMI'] = (df_clean['Weight_kg'] / ((df_clean['Height_cm'] / 100) ** 2)).round(2)

    if overall_col and 'Value_EUR' in df_clean.columns:
        df_clean['Value_per_Overall'] = (df_clean['Value_EUR'] / df_clean[overall_col]).round(2)

    # Suppression des colonnes brutes inutiles
    cols_to_drop = ['Name', 'Team & Contract', 'Height', 'Weight', 'Value', 'Wage']
    df_clean = df_clean.drop(columns=[c for c in cols_to_drop if c in df_clean.columns])

    return df_clean

if __name__ == "__main__":
    df_cleaned = clean_sofifa_dataframe(df)
    
    # Création du dossier silver_data s'il n'existe pas
    os.makedirs("silver_data", exist_ok=True)
    
    # Sauvegarde des données nettoyées au format CSV
    output_path = "silver_data/sofifa_cleaned_silver.csv"
    df_cleaned.to_csv(output_path, index=False)
    
    print("\n✅ Data Cleaning Silver Terminé et enregistré !")
    print(f"📁 Fichier sauvegardé : {output_path}")
    print("\n--- Aperçu des données propres ---")
    print(df_cleaned[['Player_Name', 'Primary_Position', 'Club', 'Height_cm', 'Weight_kg', 'Value_EUR', 'BMI']].head())