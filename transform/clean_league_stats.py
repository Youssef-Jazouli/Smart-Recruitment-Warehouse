import pandas as pd


def clean_league_stats(df):
    df = df.rename(columns={
        "number": "shirt_number",
        "player": "player_name",
        "team": "team_name",
        "apps": "appearances",
        "min": "minutes_played",
        "goals": "goals",
        "NPG": "non_penalty_goals",
        "a": "assists",
    })

    for col in ["player_name", "team_name", "league"]:
        df[col] = df[col].astype(str).str.strip().str.strip('"')

    numeric_cols = ["shirt_number", "appearances", "minutes_played",
                     "goals", "non_penalty_goals", "assists"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["player_name"])
    df[numeric_cols] = df[numeric_cols].fillna(0).astype(int)

    df["player_name_clean"] = df["player_name"].str.lower().str.strip()
    df["team_name_clean"] = df["team_name"].str.lower().str.strip()

    df = df.drop_duplicates(subset=["player_name", "team_name", "league"])

    print(f"Cleaned league stats: {len(df)} rows")
    return df.reset_index(drop=True)