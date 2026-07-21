import os
import time
import random
import logging
from datetime import datetime
from io import StringIO
import pandas as pd
import undetected_chromedriver as uc  # 🚀 La meilleure library pour contourner Cloudflare

# Configuration du Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_complete_sofifa_dataset():
    logging.info("🚀 Lancement du Scraper avec Undetected-Chromedriver (Bypass Anti-Bot)...")
    
    output_dir = "bronze_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 🕒 Création d'un nouveau fichier avec Timestamp pour ne pas écraser l'ancien
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"sofifa_full_players_bronze_{timestamp}.csv")

    # Configuration de undetected_chromedriver
    options = uc.ChromeOptions()
    # On laisse le navigateur visible. S'il y a un CAPTCHA extrême, tu peux le cliquer à la main.
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Initialisation du driver "indétectable"
    driver = uc.Chrome(options=options, version_main=150)
    driver.implicitly_wait(10)

    base_url = "https://sofifa.com/players?type=all&lg%5B%5D=13&lg%5B%5D=31&lg%5B%5D=53&lg%5B%5D=19&lg%5B%5D=16"
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
                    
                    # Simulation d'un comportement humain (Scroll)
                    driver.execute_script("window.scrollTo(0, 500);")
                    time.sleep(random.uniform(4.0, 7.5))
                    
                    html_content = StringIO(driver.page_source)
                    tables = pd.read_html(html_content)
                    
                    if len(tables) > 0 and len(tables[0]) > 0:
                        df_page = tables[0]
                        logging.info(f"✅ Succès ! {len(df_page)} joueurs extraits.")
                        all_dfs.append(df_page)
                        table_extracted = True
                        break
                    else:
                        logging.warning("⚠️ Aucun tableau détecté. Blocage Cloudflare possible. Validation manuelle requise ?")
                        # Pause plus longue pour te laisser le temps de cliquer sur "Je suis un humain" si besoin
                        time.sleep(12) 
                except Exception as e:
                    logging.warning(f"⚠️ Erreur sur l'offset {offset} (Tentative {attempt}): {str(e)}")
                    time.sleep(5)
            
            if not table_extracted:
                logging.error(f"❌ Échec définitif pour l'offset {offset}. On passe au suivant.")
                
            # Sauvegarde intermédiaire tous les 5 pages (Safety Net)
            if all_dfs and (page + 1) % 5 == 0:
                temp_df = pd.concat(all_dfs, ignore_index=True)
                temp_df.to_csv(output_file, index=False, encoding='utf-8-sig')
                logging.info(f"💾 Sauvegarde intermédiaire effectuée : {len(temp_df)} joueurs.")

        # Sauvegarde finale
        if all_dfs:
            df_master = pd.concat(all_dfs, ignore_index=True)
            df_master.to_csv(output_file, index=False, encoding='utf-8-sig')
            logging.info(f"🎉 PIPELINE TERMINÉ ! NOUVEAU FICHIER CRÉÉ : {output_file} ({len(df_master)} joueurs)")
        else:
            logging.error("❌ Aucune donnée n'a été extraite.")

    except Exception as global_err:
        logging.error(f"❌ Erreur globale du pipeline : {str(global_err)}")
    finally:
        driver.quit()
        logging.info("🔒 Navigateur fermé proprement.")

if __name__ == "__main__":
    scrape_complete_sofifa_dataset()