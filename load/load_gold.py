from sqlalchemy import text


def load_gold(engine, dim_league, dim_team, dim_player, fact_gold):
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS gold"))

    dim_league.to_sql("dim_league", engine, schema="gold",
                       if_exists="replace", index=False)
    dim_team.to_sql("dim_team", engine, schema="gold",
                     if_exists="replace", index=False)
    dim_player.to_sql("dim_player", engine, schema="gold",
                       if_exists="replace", index=False)
    fact_gold.to_sql("fact_player_performance", engine, schema="gold",
                      if_exists="replace", index=False)

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE gold.dim_league ADD PRIMARY KEY (league_key)"))
        conn.execute(text("ALTER TABLE gold.dim_team ADD PRIMARY KEY (team_key)"))
        conn.execute(text("ALTER TABLE gold.dim_player ADD PRIMARY KEY (player_key)"))
        conn.execute(text("ALTER TABLE gold.fact_player_performance ADD PRIMARY KEY (fact_key)"))

    print(f"Gold loaded: dim_league({len(dim_league)}), "
          f"dim_team({len(dim_team)}), dim_player({len(dim_player)}), "
          f"fact_player_performance({len(fact_gold)})")