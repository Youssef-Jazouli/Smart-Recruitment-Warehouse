from config.db_config import get_engine
from extract.extract_leagues import extract_all_leagues
from extract.extract_sofifa import extract_sofifa
from transform.clean_league_stats import clean_league_stats
from transform.clean_player_attrs import clean_player_attributes
from load.load_silver import load_silver
from load.load_gold import load_gold
from gold.build_star_schema import build_star_schema


def run_pipeline():
    engine = get_engine()

    print("STEP 1: Extracting bronze data...")
    leagues_raw = extract_all_leagues()
    sofifa_raw = extract_sofifa()

    print("STEP 2: Cleaning -> silver...")
    league_stats = clean_league_stats(leagues_raw)
    player_attributes = clean_player_attributes(sofifa_raw)

    print("STEP 3: Loading silver schema...")
    load_silver(engine, league_stats, player_attributes)

    print("STEP 4: Building gold star schema...")
    dim_league, dim_team, dim_player, fact_gold = build_star_schema(
        league_stats, player_attributes
    )

    print("STEP 5: Loading gold schema...")
    load_gold(engine, dim_league, dim_team, dim_player, fact_gold)

    print("Pipeline finished successfully.")


if __name__ == "__main__":
    run_pipeline()