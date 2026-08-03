import os
import time
import random
import logging
from datetime import datetime
from io import StringIO
import pandas as pd
import undetected_chromedriver as uc

# 1. Configuration du Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_advanced_metrics():
    """
    Scrape les métriques avancées (Physique, Technique, GK, Mental) 
    pour enrichir le dataset principal (Bronze Layer).
    """
    logging.info("🚀 Lancement du Scraper SoFIFA (Métriques Avancées & Physiques)...")
    
    # Création du dossier de destination s'il n'existe pas
    output_dir = "bronze_data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Horodatage pour la traçabilité du fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"sofifa_advanced_metrics_{timestamp}.csv")

    # Options du navigateur
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = uc.Chrome(options=options, version_main=150)
    driver.implicitly_wait(10)

    # 🔗 L'URL sur-mesure contenant EXACTEMENT tes demandes :
    # showCol[]=pi : Player ID (Crucial pour le Merge futur !!!)
    # showCol[]=hi&showCol[]=wi : Taille (Height) et Poids (Weight)
    # showCol[]=pf : Pied Fort (Preferred Foot)
    # showCol[]=pa&showCol[]=ac&showCol[]=sp : Pace, Acceleration, Sprint
    # showCol[]=mda&showCol[]=sa&showCol[]=sl&showCol[]=in : Défense (Awareness, Tackles, Interceptions)
    # showCol[]=gp&showCol[]=gd&showCol[]=gh : Gardien (Positioning, Diving, Handling)
    # showCol[]=st&showCol[]=sr : Stamina (Endurance) et Strength (Force)
    # showCol[]=wk&showCol[]=sk : Weak Foot et Skill Moves
    # showCol[]=cm&showCol[]=vi : Composure (Calme) et Vision
    # showCol[]=aw&showCol[]=dw : Work Rates (Attaquant / Défenseur)
    base_url = (
        "https://sofifa.com/players?type=all"
        "&lg%5B%5D=13&lg%5B%5D=31&lg%5B%5D=53&lg%5B%5D=19&lg%5B%5D=16"
        "&showCol%5B%5D=pi&showCol%5B%5D=na" 
        "&showCol%5B%5D=hi&showCol%5B%5D=wi&showCol%5B%5D=pf"
        "&showCol%5B%5D=pa&showCol%5B%5D=ac&showCol%5B%5D=sp"
        "&showCol%5B%5D=mda&showCol%5B%5D=sa&showCol%5B%5D=sl&showCol%5B%5D=in"
        "&showCol%5B%5D=gp&showCol%5B%5D=gd&showCol%5B%5D=gh"
        "&showCol%5B%5D=st&showCol%5B%5D=sr"
        "&showCol%5B%5D=wk&showCol%5B%5D=sk"
        "&showCol%5B%5D=cm&showCol%5B%5D=vi"
        "&showCol%5B%5D=aw&showCol%5B%5D=dw"
    )
    
    all_dfs = []
    max_pages = 50 # Environ 3000 joueurs des 5 grands championnats

    try:
        for page in range(0, max_pages):
            offset = page * 60
            url = f"{base_url}&offset={offset}"
            
            table_extracted = False
            retries = 3
            
            for attempt in range(1, retries + 1):
                logging.info(f"📄 Page {page + 1}/{max_pages} - Extraction des stats avancées (Tentative {attempt})...")
                
                try:
                    driver.get(url)
                    driver.execute_script("window.scrollTo(0, 500);")
                    time.sleep(random.uniform(3.5, 6.0)) # Attente aléatoire pour éviter le blocage
                    
                    html_content = StringIO(driver.page_source)
                    tables = pd.read_html(html_content)
                    
                    if len(tables) > 0 and len(tables[0]) > 0:
                        df_page = tables[0]
                        logging.info(f"✅ {len(df_page)} joueurs extraits.")
                        all_dfs.append(df_page)
                        table_extracted = True
                        break
                    else:
                        logging.warning("⚠️ Table non trouvée, protection anti-bot probable. Pause de 10s...")
                        time.sleep(10)
                        
                except Exception as e:
                    logging.warning(f"⚠️ Erreur sur la page {page + 1} : {str(e)}")
                    time.sleep(4)
            
            if not table_extracted:
                logging.error(f"❌ Impossible d'extraire la page {page + 1}.")

            # Sauvegarde partielle chaque 5 pages pour sécuriser la donnée
            if all_dfs and (page + 1) % 5 == 0:
                temp_df = pd.concat(all_dfs, ignore_index=True)
                temp_df.to_csv(output_file, index=False, encoding='utf-8-sig')

        # Sauvegarde finale du fichier CSV complet
        if all_dfs:
            df_master = pd.concat(all_dfs, ignore_index=True)
            df_master.to_csv(output_file, index=False, encoding='utf-8-sig')
            logging.info(f"🎉 DATASET MÉTRIQUES AVANCÉES CRÉÉ : {output_file}")
        else:
            logging.error("❌ Aucune donnée extraite.")

    except Exception as global_err:
        logging.error(f"❌ Erreur critique : {str(global_err)}")
    finally:
        driver.quit()
        logging.info("🔒 Navigateur fermé avec succès.")

if __name__ == "__main__":
    scrape_advanced_metrics()