import os
import pandas as pd
from config.db_config import BRONZE_DIR, LEAGUE_FILES


def extract_league_file(path, league_name):
    df = pd.read_csv(
        path,
        sep=";",
        quotechar='"',
        encoding="utf-8-sig",   # handles the BOM before "number"
        engine="python",
    )
    df.columns = [c.strip().strip('"') for c in df.columns]
    df["league"] = league_name
    return df


def extract_all_leagues():
    league_dfs = []
    for league_name, filename in LEAGUE_FILES.items():
        path = os.path.join(BRONZE_DIR, filename)
        league_dfs.append(extract_league_file(path, league_name))

    leagues_merged = pd.concat(league_dfs, ignore_index=True)
    print(f"Extracted leagues: {len(leagues_merged)} rows")
    return leagues_merged