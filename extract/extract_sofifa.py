import os
import pandas as pd
from config.db_config import BRONZE_DIR, SOFIFA_FILE


def extract_sofifa():
    path = os.path.join(BRONZE_DIR, SOFIFA_FILE)
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"Unnamed: 0": "row_id_drop"})

    drop_cols = [c for c in ["row_id_drop", "Attacking work rate",
                              "Defensive work rate", "Unnamed: 28"] if c in df.columns]
    df = df.drop(columns=drop_cols)

    print(f"Extracted sofifa: {len(df)} rows")
    return df