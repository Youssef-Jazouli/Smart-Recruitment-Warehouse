import os
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

def get_snowflake_connection():
    """
    Crée et retourne une connexion sécurisée à Snowflake.
    """
    return snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA')
    )

def load_data_to_snowflake(file_path: str, table_name: str):
    """
    Lit un fichier CSV et charge ses données directement dans Snowflake.
    """
    print(f"Lecture du fichier : {file_path}...")
    df = pd.read_csv(file_path)
    
    # Convertir tous les noms de colonnes en MAJUSCULES (recommandé par Snowflake)
    df.columns = [col.upper() for col in df.columns]
    
    # Ouvrir la connexion avec Snowflake
    conn = get_snowflake_connection()
    
    try:
        print(f"Chargement de {len(df)} lignes vers la table Snowflake : {table_name.upper()}...")
        
        # Envoi automatique des données pandas vers Snowflake
        success, nchunks, nrows, _ = write_pandas(
            conn=conn,
            df=df,
            table_name=table_name.upper(),
            auto_create_table=True,  # Crée la table automatiquement si elle n'existe pas
            overwrite=True          # Remplace les anciennes données par les nouvelles
        )
        
        # Vérification du succès de l'opération
        if success:
            print(f" Succès ! {nrows} lignes insérées dans {table_name.upper()}.")
        else:
            print(f" Échec du chargement des données dans {table_name.upper()}.")
            
    except Exception as e:
        print(f"Erreur lors du chargement vers Snowflake : {e}")
        
    finally:
        # Toujours fermer la connexion à la fin
        conn.close()

if __name__ == "__main__":
    # Fichier source préparé dans la couche Silver
    silver_file = "silver_data/final_players_silver.csv"
    
    # Lancement du chargement vers la table GOLD dans Snowflake
    load_data_to_snowflake(silver_file, "PLAYERS_GOLD")