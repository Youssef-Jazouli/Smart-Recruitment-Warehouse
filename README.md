# ⚽ Smart Recruitment Warehouse

A data engineering pipeline that ingests football player statistics and FIFA/Sofifa attributes, cleans them, and builds a **Bronze → Silver → Gold** layered architecture using **Pandas** and **PostgreSQL**, orchestrated with **Docker**.

## 📌 Overview

This project merges player performance data from Europe's top 5 leagues (Bundesliga, La Liga, Ligue 1, Premier League, Serie A) with Sofifa player attribute data, cleans and standardizes it, then models it into a **Star Schema** for analytics.

## 🏗️ Architecture

```
Bronze (raw CSVs) → Silver (cleaned data) → Gold (star schema)
```

- **Bronze**: Raw, untouched CSV files
- **Silver**: Cleaned, standardized, deduplicated tables in PostgreSQL
- **Gold**: Star schema (fact + dimension tables) ready for BI/analytics

## 📁 Project Structure

```
football_pipeline/
│
├── docker-compose.yml
├── requirements.txt
├── .env
├── main.py                     # orchestrates the whole pipeline
│
├── bronze_data/                # raw CSVs
│   ├── bundesliga.csv
│   ├── la_liga.csv
│   ├── Ligue_1.csv
│   ├── premier_league.csv
│   ├── serie_a.csv
│   └── sofifa_pro_players_bronze_20260723_143815.csv
│
├── config/
│   └── db_config.py            # DB connection & env config
│
├── extract/
│   ├── extract_leagues.py      # reads & merges the 5 league CSVs
│   └── extract_sofifa.py       # reads the sofifa CSV
│
├── transform/
│   ├── clean_league_stats.py   # cleaning/renaming league stats
│   └── clean_player_attrs.py   # cleaning/renaming sofifa attributes
│
├── load/
│   ├── load_silver.py          # writes cleaned tables to silver schema
│   └── load_gold.py            # writes star schema to gold schema
│
└── gold/
    └── build_star_schema.py    # builds dim_league, dim_team, dim_player, fact table
```

## ⭐ Star Schema (Gold Layer)

| Table | Type | Description |
|---|---|---|
| `dim_league` | Dimension | League names |
| `dim_team` | Dimension | Team names |
| `dim_player` | Dimension | Player names |
| `fact_player_performance` | Fact | Stats + FIFA attributes per player per league |

## 🛠️ Tech Stack

- **Python** (Pandas, SQLAlchemy)
- **PostgreSQL** (Docker container)
- **Docker Compose**

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.9+

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/football_pipeline.git
cd football_pipeline
```

### 2. Start PostgreSQL
```bash
docker compose up -d
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file:
```
DB_USER=admin
DB_PASSWORD=admin123
DB_HOST=localhost
DB_PORT=5432
DB_NAME=football_db
BRONZE_DIR=bronze_data
```

### 5. Run the pipeline
```bash
python main.py
```

This single command runs the full ETL: extraction → cleaning → silver load → gold star schema build → gold load.

## ✅ Verifying the Data

Connect to the database:
```bash
docker exec -it football_postgres psql -U admin -d football_db
```

Check schemas and tables:
```sql
\dn
\dt silver.*
\dt gold.*
```

Sample query — top scorers with team/league names:
```sql
SELECT 
    p.player_name,
    t.team_name,
    l.league_name,
    f.goals,
    f.assists,
    f.overall_rating,
    f.value_eur
FROM gold.fact_player_performance f
JOIN gold.dim_player p ON f.player_key = p.player_key
JOIN gold.dim_team t ON f.team_key = t.team_key
JOIN gold.dim_league l ON f.league_key = l.league_key
ORDER BY f.goals DESC
LIMIT 15;
```

## 📊 Data Sources

- League player statistics: Bundesliga, La Liga, Ligue 1, Premier League, Serie A
- Player attributes: Sofifa pro players dataset

## 🔍 Notes

- Player enrichment (FIFA attributes) is matched via cleaned player name; some mismatches may occur due to accents/nicknames.
- All data cleaning (type casting, deduplication, whitespace/quote stripping, money parsing) is handled in the `transform/` layer.

## 📄 License

MIT