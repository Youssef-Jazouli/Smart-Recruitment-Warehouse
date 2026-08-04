from sqlalchemy import text


def load_silver(engine, league_stats, player_attributes):
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver"))

    league_stats.to_sql("league_stats", engine, schema="silver",
                         if_exists="replace", index=False)
    player_attributes.to_sql("player_attributes", engine, schema="silver",
                              if_exists="replace", index=False)

    print(f"Silver loaded: league_stats({len(league_stats)}), "
          f"player_attributes({len(player_attributes)})")