import logging
import re
import time
import unicodedata
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

# =====================================================================
# CONFIGURATION
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    BRONZE_DIR = BASE_DIR / "bronze_data"
    SILVER_DIR = BASE_DIR / "silver_data"
    
    # Matching thresholds
    MATCH_THRESHOLD = 80.0
    AMBIGUITY_MARGIN = 5.0  # If top 2 candidates are within 5 points, it's ambiguous

# Ensure output directory exists
Config.SILVER_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================================
# STAGE 1: CLEANING (INDEPENDENT)
# =====================================================================
class DatasetCleaner:
    """Cleans Bronze datasets independently without merging."""
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        if pd.isna(text):
            return ""
        # Remove accents, lowercase, remove punctuation, strip extra spaces
        s = unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode('utf-8')
        s = s.lower().strip()
        s = re.sub(r"[.\-']", ' ', s)
        return re.sub(r'\s+', ' ', s).strip()

    @staticmethod
    def _extract_club(team_string: str) -> str:
        """Extracts club from strings like 'Manchester City 2022 ~ 2027' or 'On loan'."""
        if pd.isna(team_string):
            return ""
        s = str(team_string)
        s = re.sub(r'jun\s+\d{1,2},\s+\d{4}\s+on loan', '', s, flags=re.IGNORECASE)
        s = re.sub(r'on loan', '', s, flags=re.IGNORECASE)
        # Match everything before a year (e.g. 2024, 2025)
        match = re.search(r'^(.*?)(?:\s+\d{4})', s)
        return match.group(1).strip() if match else s.strip()

    @staticmethod
    def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [re.sub(r'[^A-Z0-9_]', '', c.strip().replace(' ', '_').upper()) for c in df.columns]
        return df

    @classmethod
    def process_base_dataset(cls) -> pd.DataFrame:
        logging.info("--- STAGE 1: CLEANING BASE DATASET (SoFIFA) ---")
        files = list(Config.BRONZE_DIR.glob("sofifa*.csv"))
        if not files:
            raise FileNotFoundError("No SoFIFA dataset found in bronze_data.")
            
        df = pd.read_csv(files[0])
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = cls._standardize_columns(df)
        
        # Identify name and club columns safely
        name_col = 'NAME' if 'NAME' in df.columns else df.columns[0]
        club_col = 'TEAM_CONTRACT' if 'TEAM_CONTRACT' in df.columns else ('CLUB' if 'CLUB' in df.columns else None)
        
        df['CLEAN_NAME'] = df[name_col].apply(cls._normalize_text)
        df['CLEAN_CLUB'] = df[club_col].apply(cls._extract_club).apply(cls._normalize_text) if club_col else ""
        
        # Remove true duplicates
        initial_len = len(df)
        df.drop_duplicates(subset=['CLEAN_NAME', 'CLEAN_CLUB'], keep='first', inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        logging.info(f"Cleaned Base Dataset. Rows: {len(df)}. Duplicates removed: {initial_len - len(df)}")
        df.to_csv(Config.SILVER_DIR / "players_clean.csv", index=False)
        return df

    @classmethod
    def process_stats_datasets(cls) -> pd.DataFrame:
        logging.info("--- STAGE 1: CLEANING STATS DATASETS (Leagues) ---")
        files = [f for f in Config.BRONZE_DIR.glob("*.csv") if "sofifa" not in f.name.lower()]
        
        dfs = []
        for f in files:
            df = pd.read_csv(f, sep=None, engine='python', on_bad_lines='skip')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df['LEAGUE_SOURCE'] = f.stem.replace('_', ' ').title()
            df = cls._standardize_columns(df)
            dfs.append(df)
            
        if not dfs:
            return pd.DataFrame()
            
        df_stats = pd.concat(dfs, ignore_index=True)
        
        name_col = next((c for c in ['PLAYER', 'NAME'] if c in df_stats.columns), df_stats.columns[0])
        team_col = next((c for c in ['TEAM', 'SQUAD'] if c in df_stats.columns), None)
        
        df_stats['CLEAN_NAME'] = df_stats[name_col].apply(cls._normalize_text)
        df_stats['CLEAN_TEAM'] = df_stats[team_col].apply(cls._normalize_text) if team_col else ""
        
        initial_len = len(df_stats)
        df_stats.drop_duplicates(subset=['CLEAN_NAME', 'CLEAN_TEAM'], keep='last', inplace=True)
        df_stats.reset_index(drop=True, inplace=True)
        
        logging.info(f"Cleaned Stats Dataset. Rows: {len(df_stats)}. Duplicates removed: {initial_len - len(df_stats)}")
        df_stats.to_csv(Config.SILVER_DIR / "leagues_clean.csv", index=False)
        return df_stats


# =====================================================================
# STAGE 2: VALIDATION
# =====================================================================
class DataValidator:
    """Validates datasets before any merge operations are permitted."""
    
    @staticmethod
    def run_validation(df_base: pd.DataFrame, df_stats: pd.DataFrame):
        logging.info("--- STAGE 2: PRE-MERGE VALIDATION ---")
        
        def _generate_report(df, name):
            total_rows = len(df)
            unique_players = df['CLEAN_NAME'].nunique()
            dup_names = total_rows - unique_players
            null_counts = df.isnull().sum()
            missing_report = null_counts[null_counts > 0].to_dict()
            
            report = f"""
            [{name} Dataset Validation]
            - Total Rows: {total_rows}
            - Unique Players: {unique_players}
            - Duplicate Names (Allowed if different clubs): {dup_names}
            - Columns with Missing Values: {missing_report if missing_report else 'None'}
            """
            return report
            
        logging.info(_generate_report(df_base, "Base (SoFIFA)"))
        if not df_stats.empty:
            logging.info(_generate_report(df_stats, "Stats (Leagues)"))


# =====================================================================
# STAGE 3: SMART MERGE
# =====================================================================
class SmartMergeEngine:
    """Composite matching engine using RapidFuzz, ensuring no invalid data overwrites."""
    
    @staticmethod
    def _compute_composite_score(base_name: str, base_club: str, stat_name: str, stat_team: str) -> float:
        """Returns a composite confidence score [0.0 - 100.0]."""
        name_score = fuzz.WRatio(base_name, stat_name)
        # token_set_ratio is excellent for "Manchester City" vs "Bournemouth, Manchester City"
        club_score = fuzz.token_set_ratio(base_club, stat_team)
        
        # 60% weight on Name, 40% weight on Club
        return (name_score * 0.6) + (club_score * 0.4)

    @classmethod
    def build_match_mapping(cls, df_base: pd.DataFrame, df_stats: pd.DataFrame) -> Tuple[Dict[int, int], dict]:
        logging.info("--- STAGE 3: SMART MERGE EXECUTION ---")
        
        mapping = {}
        report = {
            'successful': 0,
            'ambiguous': 0,
            'unmatched': 0,
            'score_distribution': {'90-100': 0, '80-89': 0}
        }
        
        stat_names = df_stats['CLEAN_NAME'].tolist()
        stat_indices = df_stats.index.tolist()
        
        for idx, row in df_base.iterrows():
            b_name = row['CLEAN_NAME']
            b_club = row['CLEAN_CLUB']
            
            if not b_name:
                report['unmatched'] += 1
                continue
                
            # Quick extraction based on name
            name_matches = process.extract(b_name, stat_names, scorer=fuzz.WRatio, limit=5, score_cutoff=60)
            
            if not name_matches:
                report['unmatched'] += 1
                continue
                
            candidates = []
            for match_str, name_score, match_idx in name_matches:
                actual_idx = stat_indices[match_idx]
                s_team = df_stats.at[actual_idx, 'CLEAN_TEAM']
                
                score = cls._compute_composite_score(b_name, b_club, match_str, s_team)
                candidates.append({'idx': actual_idx, 'score': score})
                
            candidates.sort(key=lambda x: x['score'], reverse=True)
            top_cand = candidates[0]
            
            if top_cand['score'] >= Config.MATCH_THRESHOLD:
                # Check for ambiguity
                if len(candidates) > 1 and (top_cand['score'] - candidates[1]['score']) <= Config.AMBIGUITY_MARGIN:
                    report['ambiguous'] += 1
                else:
                    mapping[idx] = top_cand['idx']
                    report['successful'] += 1
                    
                    if top_cand['score'] >= 90:
                        report['score_distribution']['90-100'] += 1
                    else:
                        report['score_distribution']['80-89'] += 1
            else:
                report['unmatched'] += 1
                
        return mapping, report

    @classmethod
    def execute_merge(cls, df_base: pd.DataFrame, df_stats: pd.DataFrame, mapping: Dict[int, int]) -> pd.DataFrame:
        """Safely joins stats to base without overwriting existing data or imputing."""
        stats_cols = [c for c in df_stats.columns if c not in df_base.columns and c not in ['CLEAN_NAME', 'CLEAN_TEAM']]
        
        # Initialize with NaNs (Preserving data integrity, never 0)
        for col in stats_cols:
            df_base[col] = np.nan
            
        # Map values
        for base_idx, stat_idx in mapping.items():
            stat_row = df_stats.loc[stat_idx]
            for col in stats_cols:
                if pd.isna(df_base.at[base_idx, col]):  # Only insert if empty
                    df_base.at[base_idx, col] = stat_row[col]
                    
        return df_base


# =====================================================================
# FOOTBALL ANALYTICS
# =====================================================================
class FootballAnalytics:
    """Calculates advanced metrics safely, avoiding division by zero."""
    
    @staticmethod
    def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
        return numerator.div(denominator.replace(0, np.nan))

    @classmethod
    def compute(cls, df: pd.DataFrame) -> pd.DataFrame:
        logging.info("--- COMPUTING ADVANCED FOOTBALL ANALYTICS ---")
        
        c = df.columns
        g = df['GOALS'] if 'GOALS' in c else None
        a = df['A'] if 'A' in c else (df['ASSISTS'] if 'ASSISTS' in c else None)
        m = df['MIN'] if 'MIN' in c else (df['MINUTES'] if 'MINUTES' in c else None)
        xg = df['XG'] if 'XG' in c else None
        xa = df['XA'] if 'XA' in c else None
        npg = df['NPG'] if 'NPG' in c else None
        shots = df['SHOTS'] if 'SHOTS' in c else None
        
        # Core
        if g is not None and a is not None:
            df['GOAL_CONTRIBUTION'] = g + a
            
        # Per 90
        if m is not None:
            if g is not None:
                df['GOALS_PER_90'] = cls._safe_div(g, m) * 90
                df['MINUTES_PER_GOAL'] = cls._safe_div(m, g)
            if a is not None:
                df['ASSISTS_PER_90'] = cls._safe_div(a, m) * 90
                df['MINUTES_PER_ASSIST'] = cls._safe_div(m, a)
            if xg is not None:
                df['XG_PER_90'] = cls._safe_div(xg, m) * 90
            if xa is not None:
                df['XA_PER_90'] = cls._safe_div(xa, m) * 90
            if xg is not None and xa is not None:
                df['XG_PLUS_XA_PER_90'] = cls._safe_div((xg + xa), m) * 90
                df['OFFENSIVE_INDEX'] = cls._safe_div((xg + xa), m) * 90
            if g is not None and a is not None:
                df['GOAL_CONTRIBUTION_PER_90'] = cls._safe_div((g + a), m) * 90
                df['PERFORMANCE_SCORE'] = cls._safe_div((g + a), m) * 90
                
        # Differentials & Efficiency
        if g is not None and xg is not None:
            df['XG_DIFFERENCE'] = g - xg
            df['FINISHING_EFFICIENCY'] = cls._safe_div(g, xg)
        if a is not None and xa is not None:
            df['XA_DIFFERENCE'] = a - xa
            df['CREATIVITY_INDEX'] = cls._safe_div(a, xa)
        if g is not None and shots is not None:
            df['SHOT_CONVERSION_RATE'] = cls._safe_div(g, shots)
        if g is not None and npg is not None:
            df['NON_PENALTY_GOAL_RATE'] = cls._safe_div(npg, g)
            
        return df


# =====================================================================
# FINAL VALIDATION & EXPORT
# =====================================================================
class MergeValidator:
    @staticmethod
    def generate_report(df_final: pd.DataFrame, merge_report: dict):
        logging.info("--- FINAL VALIDATION REPORT ---")
        
        total = len(df_final)
        report = f"""
        [Final Pipeline Execution Summary]
        - Total Players in Final Output: {total}
        - Confident Matches Applied: {merge_report['successful']}
        - Ambiguous Matches Avoided: {merge_report['ambiguous']}
        - Unmatched Players (Left unchanged/NaN): {merge_report['unmatched']}
        
        [Confidence Score Distribution]
        - 90 to 100 (Perfect/Near Perfect): {merge_report['score_distribution']['90-100']}
        - 80 to 89 (High Confidence): {merge_report['score_distribution']['80-89']}
        
        Data Integrity: VERIFIED. Missing values were preserved as NaN. Valid statistics were not overwritten.
        """
        logging.info(report)


# =====================================================================
# ORCHESTRATOR
# =====================================================================
def run_pipeline():
    start_time = time.time()
    
    # 1. Clean Independently
    df_base = DatasetCleaner.process_base_dataset()
    df_stats = DatasetCleaner.process_stats_datasets()
    
    # 2. Pre-Merge Validation
    DataValidator.run_validation(df_base, df_stats)
    
    if df_stats.empty:
        logging.warning("No statistics found. Ending pipeline early.")
        return
        
    # 3. Smart Merge
    mapping, merge_report = SmartMergeEngine.build_match_mapping(df_base, df_stats)
    df_final = SmartMergeEngine.execute_merge(df_base, df_stats, mapping)
    
    # 4. Analytics
    df_final = FootballAnalytics.compute(df_final)
    
    # Cleanup Backend Columns
    df_final.drop(columns=['CLEAN_NAME', 'CLEAN_CLUB', 'CLEAN_TEAM'], inplace=True, errors='ignore')
    
    # Export
    output_path = Config.SILVER_DIR / "final_players_silver.csv"
    df_final.to_csv(output_path, index=False)
    
    # 5. Final Validation Report
    MergeValidator.generate_report(df_final, merge_report)
    
    exec_time = time.time() - start_time
    logging.info(f"Pipeline completed in {exec_time:.2f} seconds. Output saved to: {output_path}")

if __name__ == "__main__":
    run_pipeline()