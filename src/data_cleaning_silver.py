# import os
# import re
# import glob
# import unicodedata
# import pandas as pd

# # 1. Configuration des dossiers
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# BRONZE_DIR = os.path.join(BASE_DIR, "bronze_data")
# SILVER_DIR = os.path.join(BASE_DIR, "silver_data")
# os.makedirs(SILVER_DIR, exist_ok=True)

# def remove_accents(input_str):
#     if not isinstance(input_str, str): return ""
#     return "".join([c for c in unicodedata.normalize('NFKD', str(input_str)) if not unicodedata.combining(c)])

# def format_currency(val):
#     """ Formate 7000000.0 en '7M' et 50000.0 en '50K' """
#     if pd.isna(val) or val == 0: return "0"
#     if val >= 1_000_000:
#         return f"{val / 1_000_000:.1f}M".replace('.0M', 'M')
#     elif val >= 1_000:
#         return f"{val / 1_000:.0f}K"
#     return str(int(val))

# # 2. Cleaning SoFIFA Data
# print("⏳ Cleaning SoFIFA Data...")
# sofifa_files = glob.glob(os.path.join(BRONZE_DIR, "sofifa_pro_players_bronze_*.csv"))

# if sofifa_files:
#     df_sofifa = pd.read_csv(sofifa_files[0])
#     df_sofifa = df_sofifa.loc[:, ~df_sofifa.columns.str.contains('^Unnamed')]

#     VALID_POSITIONS = {'GK', 'CB', 'LB', 'RB', 'LWB', 'RWB', 'CDM', 'CM', 'CAM', 'LM', 'RM', 'LW', 'RW', 'CF', 'ST'}

#     def split_name_positions(val):
#         if pd.isna(val): return "", ""
#         tokens = str(val).strip().split()
#         positions = []
#         while tokens and tokens[-1] in VALID_POSITIONS:
#             positions.insert(0, tokens.pop())
#         return " ".join(tokens), " ".join(positions)

#     df_sofifa[['Player_Name', 'Positions']] = df_sofifa['Name'].apply(lambda x: pd.Series(split_name_positions(x)))
#     df_sofifa['Primary_Position'] = df_sofifa['Positions'].apply(lambda x: x.split()[0] if x else "Unknown")
#     df_sofifa['Match_Name'] = df_sofifa['Player_Name'].apply(remove_accents)

#     # 🔹 Distinction entre Gardiens et Joueurs de champ
#     df_sofifa['Player_Type'] = df_sofifa['Primary_Position'].apply(lambda x: 'Goalkeeper' if x == 'GK' else 'Outfield')

#     def split_team_contract(val):
#         if pd.isna(val): return "Unknown", None
#         match = re.search(r'^(.*?)(?:\s+(\d{4}\s*~\s*\d{4}|\d{4}))?$', str(val).strip())
#         if match:
#             team = match.group(1).strip()
#             contract = match.group(2)
#             end_year = contract.split('~')[-1].strip() if contract and '~' in contract else contract
#             return team if team else "Unknown", end_year
#         return str(val).strip(), None

#     df_sofifa[['Club', 'Contract_End_Year']] = df_sofifa['Team & Contract'].apply(lambda x: pd.Series(split_team_contract(x)))
#     df_sofifa['Height_cm'] = df_sofifa['Height'].astype(str).str.extract(r'(\d+)cm').astype(float)
#     df_sofifa['Weight_kg'] = df_sofifa['Weight'].astype(str).str.extract(r'(\d+)kg').astype(float)

#     def parse_currency(val):
#         if pd.isna(val) or not isinstance(val, str): return 0.0
#         val = val.replace('€', '').strip()
#         if 'M' in val: return float(val.replace('M', '')) * 1_000_000
#         if 'K' in val: return float(val.replace('K', '')) * 1_000
#         try: return float(val)
#         except: return 0.0

#     df_sofifa['Value_EUR'] = df_sofifa['Value'].apply(parse_currency)
#     df_sofifa['Wage_EUR'] = df_sofifa['Wage'].apply(parse_currency)

#     # Nouveaux colonnes formatées (Ex: 7M, 150K)
#     df_sofifa['Value_Formatted'] = df_sofifa['Value_EUR'].apply(format_currency)
#     df_sofifa['Wage_Formatted'] = df_sofifa['Wage_EUR'].apply(format_currency)

#     df_sofifa['BMI'] = (df_sofifa['Weight_kg'] / ((df_sofifa['Height_cm'] / 100) ** 2)).round(2)
    
#     overall_col = next((col for col in ['Overall rating', 'Overall_rating', 'Overall'] if col in df_sofifa.columns), None)
#     if overall_col:
#         df_sofifa['Value_per_Overall'] = (df_sofifa['Value_EUR'] / df_sofifa[overall_col]).round(2)

#     cols_to_drop = ['Name', 'Team & Contract', 'Height', 'Weight', 'Value', 'Wage', 'Attacking work rate', 'Defensive work rate']
#     df_sofifa = df_sofifa.drop(columns=[c for c in cols_to_drop if c in df_sofifa.columns])
# else:
#     df_sofifa = None

# # 3. Cleaning Understat Leagues
# print("⏳ Cleaning Leagues Data...")
# league_files = ['premier_league.csv', 'la_liga.csv', 'bundesliga.csv', 'serie_a.csv', 'Ligue_1.csv']
# dfs = []

# for f in league_files:
#     path = os.path.join(BRONZE_DIR, f)
#     if os.path.exists(path):
#         try:
#             df = pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip')
#             df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
#             df['League'] = f.replace('.csv', '').replace('_', ' ').title()
            
#             player_col = next((c for c in ['player', 'Player', 'name', 'Name'] if c in df.columns), None)
#             if player_col:
#                 df['Match_Name'] = df[player_col].apply(remove_accents)
#                 df = df.drop(columns=[player_col])
                
#             dfs.append(df)
#         except Exception as e:
#             print(f"  ⚠️ Erreur sur {f} : {e}")

# if dfs:
#     df_leagues = pd.concat(dfs, ignore_index=True)
# else:
#     df_leagues = None

# # 4. Merge Final & Structured Reordering
# if df_sofifa is not None and df_leagues is not None:
#     print("⏳ Merging Datasets & Reordering Columns...")
#     df_final = pd.merge(df_sofifa, df_leagues, on="Match_Name", how="inner")
    
#     if 'team' in df_final.columns: df_final = df_final.drop(columns=['team'])
    
#     # KPIs
#     if 'goals' in df_final.columns and 'a' in df_final.columns and 'min' in df_final.columns:
#         df_final['Performance_Score'] = ((df_final['goals'] + df_final['a']) / (df_final['min'] + 1) * 90).round(2)

#     # Definition de l'ordre parfait des colonnes
#     # Definition de l'ordre parfait des colonnes (avec Age)
#     priority_cols = [
#         'ID', 'Player_Name', 'Age', 'Primary_Position', 'Player_Type', 'Positions', 'Club', 'League', 'Contract_End_Year',
#         'Height_cm', 'Weight_kg', 'BMI', 'Value_EUR', 'Value_Formatted', 'Wage_EUR', 'Wage_Formatted',
#         'Value_per_Overall', 'apps', 'min', 'goals', 'a', 'NPG', 'Performance_Score'
#     ]
    
#     # Garder les colonnes de priorité au début, suivies du reste des statistiques
#     existing_priority = [c for c in priority_cols if c in df_final.columns]
#     remaining_cols = [c for c in df_final.columns if c not in existing_priority and c != 'Match_Name']
    
#     df_final = df_final[existing_priority + remaining_cols]
#     df_final = df_final.dropna(how='all', axis=1)

#     # Save
#     final_out = os.path.join(SILVER_DIR, "final_players_silver.csv")
#     df_final.to_csv(final_out, index=False)
#     print(f"\n🚀 FINAL CLEANED SILVER DATASET CREATED : {final_out}")
#     print(f"📊 Premier joueur : {df_final['Player_Name'].iloc[0]} ({df_final['Club'].iloc[0]}) | Value: {df_final['Value_Formatted'].iloc[0]}")






#################################################################################################################################################

####################################################################""
import os
import re
import glob
import unicodedata
import pandas as pd

# 1. Configuration des dossiers
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRONZE_DIR = os.path.join(BASE_DIR, "bronze_data")
SILVER_DIR = os.path.join(BASE_DIR, "silver_data")
os.makedirs(SILVER_DIR, exist_ok=True)

def remove_accents(input_str):
    """Nettoyage robuste : accents, casse, espaces multiples, ponctuation légère."""
    if not isinstance(input_str, str) or pd.isna(input_str):
        return ""
    s = "".join([c for c in unicodedata.normalize('NFKD', str(input_str)) if not unicodedata.combining(c)])
    s = s.lower().strip()
    s = re.sub(r'[.\-\']', ' ', s)      # points, tirets, apostrophes -> espace
    s = re.sub(r'\s+', ' ', s)          # espaces multiples -> un seul
    return s.strip()

def format_currency(val):
    """ Formate 7000000.0 en '7M' et 50000.0 en '50K' """
    if pd.isna(val) or val == 0: return "0"
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M".replace('.0M', 'M')
    elif val >= 1_000:
        return f"{val / 1_000:.0f}K"
    return str(int(val))

# 2. Cleaning SoFIFA Data
print("⏳ Cleaning SoFIFA Data...")
sofifa_files = glob.glob(os.path.join(BRONZE_DIR, "sofifa_pro_players_bronze_*.csv"))

if sofifa_files:
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
    df_sofifa['Match_Name'] = df_sofifa['Player_Name'].apply(remove_accents)

    # Distinction entre Gardiens et Joueurs de champ
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

    # Sécurité : éviter les doublons de Match_Name qui gonfleraient le merge
    dupes = df_sofifa['Match_Name'].duplicated().sum()
    if dupes:
        print(f"  ⚠️ {dupes} doublons de Match_Name détectés dans SoFIFA (gardés tels quels, vérifie si voulu)")
else:
    df_sofifa = None
    print("  ⚠️ Aucun fichier SoFIFA trouvé dans bronze_data/")

# 3. Cleaning Understat Leagues
print("⏳ Cleaning Leagues Data...")
league_files = ['premier_league.csv', 'la_liga.csv', 'bundesliga.csv', 'serie_a.csv', 'Ligue_1.csv']
dfs = []

for f in league_files:
    path = os.path.join(BRONZE_DIR, f)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df['League'] = f.replace('.csv', '').replace('_', ' ').title()

            player_col = next((c for c in ['player', 'Player', 'name', 'Name'] if c in df.columns), None)
            if player_col:
                df['Match_Name'] = df[player_col].apply(remove_accents)
                df = df.drop(columns=[player_col])

            dfs.append(df)
        except Exception as e:
            print(f"  ⚠️ Erreur sur {f} : {e}")
    else:
        print(f"  ⚠️ Fichier introuvable : {f}")

if dfs:
    df_leagues = pd.concat(dfs, ignore_index=True)
    # Si un joueur apparaît dans plusieurs ligues (transfert en cours saison), garder la première occurrence
    league_dupes = df_leagues['Match_Name'].duplicated().sum()
    if league_dupes:
        print(f"  ⚠️ {league_dupes} doublons de Match_Name dans les ligues (transferts probables), on garde la 1ère occurrence")
        df_leagues = df_leagues.drop_duplicates(subset='Match_Name', keep='first')
else:
    df_leagues = None
    print("  ⚠️ Aucun fichier de ligue trouvé dans bronze_data/")

# 4. Merge Final & Structured Reordering
if df_sofifa is not None and df_leagues is not None:
    print("⏳ Merging Datasets & Reordering Columns...")

    # Diagnostic AVANT le merge, pour comprendre le taux de correspondance
    sofifa_names = set(df_sofifa['Match_Name'])
    league_names = set(df_leagues['Match_Name'])
    overlap = sofifa_names & league_names
    print(f"  📊 SoFIFA players: {len(df_sofifa)}")
    print(f"  📊 League records: {len(df_leagues)}")
    print(f"  📊 Match_Name overlap: {len(overlap)} ({len(overlap)/max(len(sofifa_names),1)*100:.1f}% des joueurs SoFIFA)")

    # LEFT JOIN au lieu de INNER : on garde TOUS les joueurs SoFIFA,
    # même ceux sans stats de ligue (ils auront des NaN sur les colonnes de ligue)
    df_final = pd.merge(df_sofifa, df_leagues, on="Match_Name", how="left")

    if 'team' in df_final.columns:
        df_final = df_final.drop(columns=['team'])

    # KPIs (uniquement calculable pour les joueurs ayant des stats de ligue)
    if 'goals' in df_final.columns and 'a' in df_final.columns and 'min' in df_final.columns:
        df_final['Performance_Score'] = ((df_final['goals'] + df_final['a']) / (df_final['min'] + 1) * 90).round(2)

    # Definition de l'ordre parfait des colonnes (avec Age)
    priority_cols = [
        'ID', 'Player_Name', 'Age', 'Primary_Position', 'Player_Type', 'Positions', 'Club', 'League', 'Contract_End_Year',
        'Height_cm', 'Weight_kg', 'BMI', 'Value_EUR', 'Value_Formatted', 'Wage_EUR', 'Wage_Formatted',
        'Value_per_Overall', 'apps', 'min', 'goals', 'a', 'NPG', 'Performance_Score'
    ]

    existing_priority = [c for c in priority_cols if c in df_final.columns]
    remaining_cols = [c for c in df_final.columns if c not in existing_priority and c != 'Match_Name']

    df_final = df_final[existing_priority + remaining_cols]
    df_final = df_final.dropna(how='all', axis=1)

    # Save
    final_out = os.path.join(SILVER_DIR, "final_players_silver.csv")
    df_final.to_csv(final_out, index=False)
    print(f"\n🚀 FINAL CLEANED SILVER DATASET CREATED : {final_out}")
    print(f"📊 Total rows in final dataset: {len(df_final)}")
    print(f"📊 Premier joueur : {df_final['Player_Name'].iloc[0]} ({df_final['Club'].iloc[0]}) | Value: {df_final['Value_Formatted'].iloc[0]}")
else:
    print("❌ Impossible de créer le dataset final : SoFIFA ou Leagues data manquant.")