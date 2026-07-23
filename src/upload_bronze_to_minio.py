import os
import glob
import logging
import boto3
from botocore.client import Config

# 1. Configuration du système de journalisation (Logging) pour suivre l'exécution dans le terminal
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 2. Paramètres de connexion au serveur MinIO local
MINIO_URL = "http://localhost:9000"       # Adresse de l'API S3 de MinIO
ACCESS_KEY = "minioadmin"                # Identifiant par défaut
SECRET_KEY = "minioadminpassword"        # Mot de passe par défaut
BUCKET_NAME = "bronze-layer"             # Nom du bucket cible dans notre Data Lake

def get_s3_client():
    """
    Crée et retourne un client S3 configuré pour communiquer avec notre instance MinIO.
    Utilise la bibliothèque standard AWS boto3 compatible avec MinIO.
    """
    return boto3.client(
        's3',
        endpoint_url=MINIO_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

def upload_bronze_to_minio():
    """
    Vérifie l'existence du bucket 'bronze-layer' (le crée si nécessaire)
    et téléverse tous les fichiers CSV bruts depuis le dossier local 'bronze_data/'.
    """
    # Initialisation du client S3
    s3 = get_s3_client()
    
    # ÉTAPE 1 : Gestion de la création du Bucket
    # On récupère la liste de tous les buckets existants sur MinIO
    response = s3.list_buckets()
    existing_buckets = [b['Name'] for b in response.get('Buckets', [])]
    
    # Si le bucket 'bronze-layer' n'existe pas encore, on le crée
    if BUCKET_NAME not in existing_buckets:
        s3.create_bucket(Bucket=BUCKET_NAME)
        logging.info(f"🪣 Bucket '{BUCKET_NAME}' créé avec succès.")
    else:
        logging.info(f"🪣 Le bucket '{BUCKET_NAME}' existe déjà.")

    # ÉTAPE 2 : Ingestion et organisation des fichiers locaux
    bronze_dir = "bronze_data"
    
    # Recherche de tous les fichiers CSV présents dans le dossier bronze_data/
    files = glob.glob(os.path.join(bronze_dir, "*.csv"))
    
    if not files:
        logging.error("❌ Aucun fichier CSV trouvé dans le dossier 'bronze_data/'.")
        return

    # Boucle de téléversement fichier par fichier
    for csv_file in files:
        file_name = os.path.basename(csv_file)
        
        # Structuration de l'arborescence à l'intérieur du Bucket S3 (Prefixes/Dossiers virtuels)
        if "sofifa" in file_name.lower():
            s3_key = f"sofifa/{file_name}"        # Fichiers SoFIFA dans le sous-dossier 'sofifa/'
        else:
            s3_key = f"understat/{file_name}"     # Fichiers des championnats dans 'understat/'
            
        # Téléversement effectif du fichier local vers MinIO S3
        s3.upload_file(csv_file, BUCKET_NAME, s3_key)
        logging.info(f"📤 Téléversé : {file_name} -> MinIO ({BUCKET_NAME}/{s3_key})")

if __name__ == "__main__":
    # Point d'entrée principal du script
    upload_bronze_to_minio()