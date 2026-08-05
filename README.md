# ⚽ Smart Recruitment Warehouse

---

# 1. Nom du projet

**Nom du projet :** Smart Recruitment Warehouse

---

# 2. Présentation du projet

Ce projet est une analyse de données qui permet d'ingérer, nettoyer et modéliser les statistiques de joueurs de football professionnels issues des cinq grands championnats européens (Bundesliga, La Liga, Ligue 1, Premier League, Serie A), enrichies avec les attributs FIFA/Sofifa.

Il s'adresse principalement aux recruteurs sportifs, analystes de données et personnes souhaitant exploiter des statistiques de joueurs pour de l'analyse décisionnelle (BI).

Son objectif principal est de transformer des données brutes hétérogènes en un entrepôt de données structuré (schéma en étoile), prêt à être interrogé pour identifier et comparer des joueurs selon leurs performances et leurs caractéristiques FIFA.

---

# 3. Problématique

Le problème identifié est que les statistiques de joueurs et les attributs FIFA/Sofifa proviennent de sources séparées, dans des formats bruts non standardisés (CSV par championnat), rendant difficile toute analyse croisée fiable (noms différents selon les sources, doublons, formats de valeurs monétaires incohérents, etc.).

La solution proposée permet de centraliser ces données dans un pipeline ETL automatisé qui les nettoie, les standardise puis les organise en couches Bronze, Silver et Gold, afin d'obtenir un schéma en étoile exploitable directement pour des requêtes analytiques (ex : classement des meilleurs buteurs avec leur note FIFA et leur valeur marchande).

---

# 4. Fonctionnalités principales

- Extraire et fusionner les statistiques des cinq championnats (Bundesliga, La Liga, Ligue 1, Premier League, Serie A)
- Extraire les attributs de joueurs depuis le jeu de données Sofifa
- Nettoyer et standardiser les données (typage, dédoublonnage, suppression des espaces/guillemets superflus, parsing des valeurs monétaires)
- Charger les tables nettoyées dans le schéma Silver de PostgreSQL
- Construire un schéma en étoile (dimensions + table de faits) dans le schéma Gold
- Exécuter l'ensemble du pipeline ETL en une seule commande via `main.py`

---

# 5. Technologies utilisées

| Technologie | Utilisation dans le projet |
|-------------|----------------------------|
| Python | Développement de l'ensemble du pipeline ETL (extraction, transformation, chargement) |
| Pandas | Nettoyage, transformation et manipulation des données tabulaires |
| SQLAlchemy | Connexion et écriture des données dans PostgreSQL |
| PostgreSQL | Stockage des données dans les schémas Silver et Gold |
| Docker & Docker Compose | Conteneurisation et orchestration de la base de données PostgreSQL |

### Phrase type

> Nous avons utilisé **Pandas** pour nettoyer, dédupliquer et standardiser les données brutes issues des fichiers CSV avant leur chargement en base.

---

# 6. Installation et lancement

## 6.1 Prérequis

Pour utiliser ce projet, vous devez disposer de :

- Docker et Docker Compose
- Python 3.9 ou supérieur
- pip
- Git
- Un client PostgreSQL (optionnel, pour vérifier les données manuellement)

---

## 6.2 Cloner le dépôt

```bash
git clone https://github.com/<your-username>/football_pipeline.git
```

---

## 6.3 Ouvrir le dossier

```bash
cd football_pipeline
```

---

## 6.4 Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## 6.5 Variables d'environnement

Créer le fichier `.env`.

```env
DB_USER=admin
DB_PASSWORD=admin123
DB_HOST=localhost
DB_PORT=5432
DB_NAME=football_db
BRONZE_DIR=bronze_data
```

---

## 6.6 Lancer le projet

Démarrer PostgreSQL avec Docker :

```bash
docker compose up -d
```

Puis exécuter le pipeline complet :

```bash
python main.py
```

Cette commande unique exécute l'ensemble du processus ETL : extraction → nettoyage → chargement Silver → construction du schéma en étoile → chargement Gold.

---

## 6.7 Vérifier le projet

Après le lancement, se connecter à la base de données pour vérifier les résultats :

```bash
docker exec -it football_postgres psql -U admin -d football_db
```

Vérifier les schémas et les tables :

```sql
\dn
\dt silver.*
\dt gold.*
```

Exemple de requête — meilleurs buteurs avec équipe/championnat :

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

### Point de vigilance

- Tester toutes les commandes
- Vérifier les chemins
- Ne jamais publier :
  - mots de passe
  - clés API
  - tokens
  - identifiants

---

# 7. Architecture des données

## Architecture générale

```
Bronze (CSV bruts) → Silver (données nettoyées) → Gold (schéma en étoile)
```

- **Bronze** : fichiers CSV bruts, non modifiés
- **Silver** : tables nettoyées, standardisées et dédupliquées dans PostgreSQL
- **Gold** : schéma en étoile (table de faits + dimensions) prêt pour l'analyse BI

## Structure du projet

```
football_pipeline/
│
├── docker-compose.yml
├── requirements.txt
├── .env
├── main.py                     # orchestre l'ensemble du pipeline
│
├── bronze_data/                # CSV bruts
│   ├── bundesliga.csv
│   ├── la_liga.csv
│   ├── Ligue_1.csv
│   ├── premier_league.csv
│   ├── serie_a.csv
│   └── sofifa_pro_players_bronze_20260723_143815.csv
│
├── config/
│   └── db_config.py            # connexion DB et configuration env
│
├── extract/
│   ├── extract_leagues.py      # lit et fusionne les 5 CSV de championnats
│   └── extract_sofifa.py       # lit le CSV Sofifa
│
├── transform/
│   ├── clean_league_stats.py   # nettoyage/renommage des stats de championnats
│   └── clean_player_attrs.py   # nettoyage/renommage des attributs Sofifa
│
├── load/
│   ├── load_silver.py          # écrit les tables nettoyées dans le schéma silver
│   └── load_gold.py            # écrit le schéma en étoile dans le schéma gold
│
└── gold/
    └── build_star_schema.py    # construit dim_league, dim_team, dim_player, table de faits
```

## Schéma en étoile (couche Gold)

| Table | Type | Description |
|-------|------|-------------|
| dim_league | Dimension | Noms des championnats |
| dim_team | Dimension | Noms des équipes |
| dim_player | Dimension | Noms des joueurs |
| fact_player_performance | Fait | Statistiques + attributs FIFA par joueur et par championnat |

---

# 8. Contribution personnelle

Ma contribution principale a porté sur la conception et le développement de l'ensemble du pipeline ETL, depuis l'extraction des données brutes jusqu'à la construction du schéma en étoile.

J'ai également travaillé sur la logique de nettoyage et de standardisation des données (typage, dédoublonnage, suppression des espaces/guillemets, parsing des valeurs monétaires) dans la couche `transform/`.

J'ai été responsable de la configuration de l'environnement Docker/PostgreSQL, ainsi que de la construction du schéma en étoile (dimensions et table de faits) dans la couche Gold.

---

# 9. Difficultés rencontrées

## Difficulté 1 : Correspondance des noms de joueurs entre sources

### Problème rencontré

Les noms de joueurs présents dans les fichiers de statistiques de championnats ne correspondaient pas toujours exactement aux noms utilisés dans le jeu de données Sofifa, notamment à cause des accents et des surnoms.

### Recherches / Tests

J'ai testé plusieurs approches de nettoyage de chaînes de caractères (normalisation des accents, suppression des espaces superflus, mise en minuscule) pour maximiser le taux de correspondance entre les deux sources.

### Solution

J'ai mis en place une étape de nettoyage systématique des noms avant la jointure, réduisant significativement le nombre de mismatches, bien que certains cas restent non résolus.

### Ce que j'ai appris

Cette difficulté m'a permis d'apprendre l'importance de la standardisation des clés de jointure lors de la fusion de sources de données hétérogènes, et les limites du matching par nom exact.

---

## Difficulté 2 : Formats monétaires incohérents

### Problème rencontré

Les valeurs marchandes des joueurs (`value_eur`) étaient stockées sous des formats variés selon les fichiers sources (avec symboles monétaires, unités abrégées comme "M" ou "K", séparateurs différents).

### Recherches / Tests

J'ai analysé les différents formats présents dans les fichiers CSV afin de définir une fonction de parsing générique capable de les interpréter correctement.

### Solution

J'ai développé une fonction de parsing dédiée dans la couche `transform/`, capable de convertir tous ces formats en une valeur numérique standardisée en euros.

### Ce que j'ai appris

Cette difficulté m'a permis d'apprendre à anticiper la variabilité des formats de données réelles et à écrire des fonctions de transformation robustes et réutilisables.

---

# 10. Améliorations possibles

Dans une prochaine version, je pourrais :

- améliorer l'algorithme de correspondance des noms de joueurs (fuzzy matching) ;
- ajouter des tests automatisés sur les étapes de transformation ;
- ajouter un scheduler pour automatiser l'exécution périodique du pipeline ;
- déployer le pipeline sur un environnement cloud avec orchestration (Airflow, par exemple).

### Conclusion

Ces améliorations permettraient de rendre le pipeline plus fiable, plus automatisé et plus facilement exploitable en production pour des besoins de recrutement sportif à grande échelle.

---

# 📊 Sources de données

- Statistiques de joueurs par championnat : Bundesliga, La Liga, Ligue 1, Premier League, Serie A
- Attributs de joueurs : jeu de données Sofifa pro players

# 🔍 Notes

- L'enrichissement des joueurs (attributs FIFA) est réalisé via une correspondance sur le nom nettoyé du joueur ; certains mismatches peuvent survenir à cause des accents ou des surnoms.
- L'ensemble du nettoyage des données (typage, dédoublonnage, suppression des espaces/guillemets, parsing monétaire) est géré dans la couche `transform/`.

# 📄 Licence

MIT
