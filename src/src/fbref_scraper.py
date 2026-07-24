import os
import time
import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Configuration du Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Les URLs des 5 Grands Championnats sur FBref (Saison courante/récente)
FBREF_LEAGUES = {
    'premier_league': 'https://fbref.com/en/squads/9/stats/Big-Five-European-Leagues-Stats',
    'la_liga': 'https://fbref.com/en/squads/12/stats/Big-Five-European-Leagues-Stats',
    'serie_a': 'https://fbref.com/en/squads/11/stats/Big-Five-European-Leagues-Stats',
    'bundesliga': 'https://fbref.com/en/squads/20/stats/Big-Five-European-Leagues-Stats',
    'ligue_1': 'https://fbref.com/en/squads/13/stats/Big-Five-European-Leagues-Stats'
}

# URL Globale Big 5 Players (FBref)
BIG_5_PLAYERS_URL = "https://fbref.com/en/comps/Big5/stats/players/Big-5-European-Leagues-Stats"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def scrape_fbref_advanced_stats():
    """ Scrape les statistiques avancées (xG, xA, Key Passes, SCA) depuis FBref """
    logging.info("🚀 Lancement du Scraper FBref (Advanced Metrics: xG, xA, PrgP)...")
    
    output_dir = "bronze_data"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        response = requests.get(BIG_5_PLAYERS_URL, headers=HEADERS)
        if response.status_status_code if hasattr(response, 'status_status_code') else response.status_code != 200:
            logging.error(f"❌ Erreur d'accès à FBref (Code: {response.status_code})")
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Trouver la table des joueurs
        table = soup.find('table', {'id': 'stats_standard'})
        if not table:
            # Recherche alternative si la table est encapsulée dans des commentaires HTML
            comments = soup.find_all(string=lambda text: isinstance(text, str) and 'id="stats_standard"' in text)
            if comments:
                comment_soup = BeautifulSoup(comments[0], 'html.parser')
                table = comment_soup.find('table', {'id': 'stats_standard'})

        if table:
            df = pd.read_html(str(table))[0]
            
            # Nettoyage des MultiIndex de colonnes si présents
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() if not col[0].startswith('Unnamed') else col[1] for col in df.columns]
                
            output_file = os.path.join(output_dir, "fbref_big5_advanced_stats.csv")
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            logging.info(f"✅ Scraping FBref Réussi ! Fichier sauvegardé : {output_file} ({len(df)} lignes)")
        else:
            logging.warning("⚠️ Table FBref non trouvée. Vérification des protections Anti-Bot...")

    except Exception as e:
        logging.error(f"❌ Erreur lors du scraping FBref : {str(e)}")

if __name__ == "__main__":
    scrape_fbref_advanced_stats()