import os
import time
import random
import logging
from datetime import datetime
from io import StringIO
import pandas as pd
import undetected_chromedriver as uc

# Configuration du Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_complete_sofifa_dataset():
    logging.info("🚀 Lancement du Scraper SoFIFA (Version ULTIME: Physique + Tactique + GK)...")
    
    output_dir = "bronze_data"
    os.makedirs(output_dir, exist_ok=True)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"sofifa_pro_players_bronze_{timestamp}.csv")

    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Initialisation du driver (Assure-toi que version_main correspond à ton Chrome, ici 150)
    driver = uc.Chrome(options=options, version_main=150)
    driver.implicitly_wait(10)

    # 🌟 LE SECRET : Une URL personnalisée qui force SoFIFA à afficher TOUTES les colonnes dans la grille principale !
    # Colonnes incluses : Age, Overall, Potential, Value, Wage, Height, Weight, Preferred Foot, 
    # Pace, Acceleration, Sprint Speed, Stamina, Strength, Interceptions, Tackles, GK stats, Vision, Composure...
    base_url = (
        "https://sofifa.com/players?type=all"
        "&lg%5B%5D=13&lg%5B%5D=31&lg%5B%5D=53&lg%5B%5D=19&lg%5B%5D=16" # 5 Grands Championnats
        "&showCol%5B%5D=ae&showCol%5B%5D=oa&showCol%5B%5D=pt&showCol%5B%5D=vl&showCol%5B%5D=wg" # Base
        "&showCol%5B%5D=hi&showCol%5B%5D=wi&showCol%5B%5D=pf&showCol%5B%5D=aw&showCol%5B%5D=dw" # Physique & Work Rate
        "&showCol%5B%5D=pi&showCol%5B%5D=ac&showCol%5B%5D=sp&showCol%5B%5D=st&showCol%5B%5D=sr" # Vitesse & Endurance
        "&showCol%5B%5D=in&showCol%5B%5D=sa&showCol%5B%5D=sl" # Défense (Interceptions, Tackles)
        "&showCol%5B%5D=vi&showCol%5B%5D=cm&showCol%5B%5D=wk&showCol%5B%5D=sk" # Mental & Technique
        "&showCol%5B%5D=gd&showCol%5B%5D=gh&showCol%5B%5D=gp" # Goalkeeper
    )
    
    all_dfs = []
    max_pages = 50 
    
    try:
        for page in range(0, max_pages):
            offset = page * 60
            url = f"{base_url}&offset={offset}"
            
            table_extracted = False
            retries = 3 
            
            for attempt in range(1, retries + 1):
                logging.info(f"🌐 Ingestion Page {page + 1}/{max_pages} (Offset: {offset}) - Tentative {attempt}/{retries}...")
                
                try:
                    driver.get(url)
                    
                    # Simuler un humain qui lit la page pour tromper Cloudflare
                    driver.execute_script("window.scrollTo(0, 500);")
                    time.sleep(random.uniform(4.0, 7.5))
                    
                    html_content = StringIO(driver.page_source)
                    tables = pd.read_html(html_content)
                    
                    if len(tables) > 0 and len(tables[0]) > 0:
                        df_page = tables[0]
                        logging.info(f"✅ Succès ! {len(df_page)} joueurs extraits avec toutes les métriques PRO.")
                        all_dfs.append(df_page)
                        table_extracted = True
                        break
                    else:
                        logging.warning("⚠️ Blocage Cloudflare possible. Validation manuelle requise (12 sec)...")
                        time.sleep(12) 
                except Exception as e:
                    logging.warning(f"⚠️ Erreur offset {offset} : {str(e)}")
                    time.sleep(5)
            
            if not table_extracted:
                logging.error(f"❌ Échec pour l'offset {offset}. Passage au suivant.")
                
            # Sauvegarde de sécurité chaque 5 pages
            if all_dfs and (page + 1) % 5 == 0:
                temp_df = pd.concat(all_dfs, ignore_index=True)
                temp_df.to_csv(output_file, index=False, encoding='utf-8-sig')
                logging.info(f"💾 Sauvegarde intermédiaire : {len(temp_df)} joueurs.")

        # Sauvegarde FINALE
        if all_dfs:
            df_master = pd.concat(all_dfs, ignore_index=True)
            df_master.to_csv(output_file, index=False, encoding='utf-8-sig')
            logging.info(f"🎉 PIPELINE TERMINÉ ! DATASET PRO CRÉÉ : {output_file} ({len(df_master)} joueurs, {len(df_master.columns)} colonnes)")
        else:
            logging.error("❌ Aucune donnée n'a été extraite.")

    except Exception as global_err:
        logging.error(f"❌ Erreur globale du pipeline : {str(global_err)}")
    finally:
        driver.quit()
        logging.info("🔒 Navigateur fermé proprement.")

if __name__ == "__main__":
    scrape_complete_sofifa_dataset()