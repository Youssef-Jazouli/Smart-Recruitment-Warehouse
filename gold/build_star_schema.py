# def build_star_schema(league_stats, player_attributes):
#     # ---- Dimensions ----
#     dim_league = (
#         league_stats[["league"]].drop_duplicates().reset_index(drop=True)
#     )
#     dim_league.insert(0, "league_key", dim_league.index + 1)

#     dim_team = (
#         league_stats[["team_name", "team_name_clean"]]
#         .drop_duplicates().reset_index(drop=True)
#     )
#     dim_team.insert(0, "team_key", dim_team.index + 1)

#     dim_player = (
#         league_stats[["player_name", "player_name_clean"]]
#         .drop_duplicates().reset_index(drop=True)
#     )
#     dim_player.insert(0, "player_key", dim_player.index + 1)

#     # ---- Fact table ----
#     fact = league_stats.merge(
#         dim_league, on="league", how="left"
#     ).merge(
#         dim_team, on=["team_name", "team_name_clean"], how="left"
#     ).merge(
#         dim_player, on=["player_name", "player_name_clean"], how="left"
#     )

#     attrs = player_attributes[[
#         "player_name_clean", "overall_rating", "potential",
#         "preferred_foot", "value_eur", "wage_eur", "age"
#     ]].drop_duplicates(subset=["player_name_clean"])

#     fact = fact.merge(attrs, on="player_name_clean", how="left")

#     fact_gold = fact[[
#         "player_key", "team_key", "league_key",
#         "shirt_number", "appearances", "minutes_played",
#         "goals", "non_penalty_goals", "assists",
#         "overall_rating", "potential", "preferred_foot",
#         "value_eur", "wage_eur", "age",
#     ]].reset_index(drop=True)
#     fact_gold.insert(0, "fact_key", fact_gold.index + 1)

#     dim_league = dim_league.rename(columns={"league": "league_name"})
#     dim_team = dim_team.drop(columns=["team_name_clean"])
#     dim_player = dim_player.drop(columns=["player_name_clean"])

#     return dim_league, dim_team, dim_player, fact_gold

import pandas as pd

def build_star_schema(league_stats, player_attributes):
    # ---- Dimensions ----
    dim_league = (
        league_stats[["league"]].drop_duplicates().reset_index(drop=True)
    )
    dim_league.insert(0, "league_key", dim_league.index + 1)

    dim_team = (
        league_stats[["team_name", "team_name_clean"]]
        .drop_duplicates().reset_index(drop=True)
    )
    dim_team.insert(0, "team_key", dim_team.index + 1)

    dim_player = (
        league_stats[["player_name", "player_name_clean"]]
        .drop_duplicates().reset_index(drop=True)
    )
    dim_player.insert(0, "player_key", dim_player.index + 1)

    # ---- Fact table ----
    fact = league_stats.merge(
        dim_league, on="league", how="left"
    ).merge(
        dim_team, on=["team_name", "team_name_clean"], how="left"
    ).merge(
        dim_player, on=["player_name", "player_name_clean"], how="left"
    )

    # ---- Normalization & Cleaning for Matching ----
    # توحيد صيغة الأسماء بمسح المسافات وتحويل الحروف لـ lower باش ينجح الـ Merge 100%
    player_attributes["player_name_clean"] = (
        player_attributes["player_name_clean"].astype(str).str.lower().str.strip()
    )
    fact["player_name_clean"] = (
        fact["player_name_clean"].astype(str).str.lower().str.strip()
    )

    attrs = player_attributes[[
        "player_name_clean", "overall_rating", "potential",
        "preferred_foot", "value_eur", "wage_eur", "age"
    ]].drop_duplicates(subset=["player_name_clean"])

    # الربط مع جدول الخصائص
    fact = fact.merge(attrs, on="player_name_clean", how="left")

    # التعامل مع القيم الفارغة لتفادي ظهور Blank في Power BI
    fact["overall_rating"] = fact["overall_rating"].fillna(0)
    fact["potential"] = fact["potential"].fillna(0)
    fact["value_eur"] = fact["value_eur"].fillna(0)
    fact["wage_eur"] = fact["wage_eur"].fillna(0)
    fact["age"] = fact["age"].fillna(0)
    fact["preferred_foot"] = fact["preferred_foot"].fillna("Unknown")

    fact_gold = fact[[
        "player_key", "team_key", "league_key",
        "shirt_number", "appearances", "minutes_played",
        "goals", "non_penalty_goals", "assists",
        "overall_rating", "potential", "preferred_foot",
        "value_eur", "wage_eur", "age",
    ]].reset_index(drop=True)
    
    fact_gold.insert(0, "fact_key", fact_gold.index + 1)

    dim_league = dim_league.rename(columns={"league": "league_name"})
    dim_team = dim_team.drop(columns=["team_name_clean"])
    dim_player = dim_player.drop(columns=["player_name_clean"])

    return dim_league, dim_team, dim_player, fact_gold