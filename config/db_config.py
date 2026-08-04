import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
BRONZE_DIR = os.getenv("BRONZE_DIR", "bronze_data")

LEAGUE_FILES = {
    "Bundesliga": "bundesliga.csv",
    "La Liga": "la_liga.csv",
    "Ligue 1": "Ligue_1.csv",
    "Premier League": "premier_league.csv",
    "Serie A": "serie_a.csv",
}

SOFIFA_FILE = "sofifa_pro_players_bronze_20260723_143815.csv"


def get_engine():
    return create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )