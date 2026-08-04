import pandas as pd


def parse_money(x):
    if pd.isna(x):
        return None
    x = str(x).replace("€", "").replace("$", "").strip()
    mult = 1
    if x.endswith("M"):
        mult, x = 1_000_000, x[:-1]
    elif x.endswith("K"):
        mult, x = 1_000, x[:-1]
    try:
        return float(x) * mult
    except ValueError:
        return None


def clean_player_attributes(df):
    df = df.rename(columns={
        "Name": "player_name",
        "Age": "age",
        "Overall rating": "overall_rating",
        "Potential": "potential",
        "Team & Contract": "team_contract",
        "ID": "sofifa_id",
        "Height": "height",
        "Weight": "weight",
        "foot": "preferred_foot",
        "Value": "value_raw",
        "Wage": "wage_raw",
        "Acceleration": "acceleration",
        "Sprint speed": "sprint_speed",
        "Stamina": "stamina",
        "Strength": "strength",
        "Interceptions": "interceptions",
        "Vision": "vision",
        "Composure": "composure",
        "Standing tackle": "standing_tackle",
        "Sliding tackle": "sliding_tackle",
        "GK Diving": "gk_diving",
        "GK Handling": "gk_handling",
        "GK Positioning": "gk_positioning",
        "Weak foot": "weak_foot",
        "Skill moves": "skill_moves",
    })

    df["player_name"] = df["player_name"].astype(str).str.strip()

    df["value_eur"] = df["value_raw"].apply(parse_money)
    df["wage_eur"] = df["wage_raw"].apply(parse_money)
    df = df.drop(columns=["value_raw", "wage_raw"])

    df["height_cm"] = df["height"].astype(str).str.extract(r"(\d+)").astype(float)
    df["weight_kg"] = df["weight"].astype(str).str.extract(r"(\d+)").astype(float)

    numeric_cols = ["age", "overall_rating", "potential", "acceleration",
                     "sprint_speed", "stamina", "strength", "interceptions",
                     "vision", "composure", "standing_tackle", "sliding_tackle",
                     "gk_diving", "gk_handling", "gk_positioning",
                     "weak_foot", "skill_moves"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["player_name"])
    df["player_name_clean"] = df["player_name"].str.lower().str.strip()
    df = df.drop_duplicates(subset=["player_name", "sofifa_id"])

    print(f"Cleaned player attributes: {len(df)} rows")
    return df.reset_index(drop=True)