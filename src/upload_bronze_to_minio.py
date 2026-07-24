import os
import glob
import logging
import boto3
from botocore.client import Config
from dotenv import load_dotenv

# 1. Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# 2. Configuration du système de journalisation (Logging)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 3. Récupération des paramètres de connexion depuis .env
MINIO_URL = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadminpassword")
BUCKET_NAME = "bronze-layer"

def get_s3_client():
    """
    Crée et retourne un client S3 configuré pour communiquer avec notre instance MinIO.
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
    s3 = get_s3_client()
    
    # ÉTAPE 1 : Gestion du Bucket
    try:
        response = s3.list_buckets()
        existing_buckets = [b['Name'] for b in response.get('Buckets', [])]
        
        if BUCKET_NAME not in existing_buckets:
            s3.create_bucket(Bucket=BUCKET_NAME)
            logging.info(f"🪣 Bucket '{BUCKET_NAME}' créé avec succès.")
        else:
            logging.info(f"🪣 Le bucket '{BUCKET_NAME}' existe déjà.")
    except Exception as e:
        logging.error(f"❌ Impossible de se connecter à MinIO : {str(e)}")
        return

    # ÉTAPE 2 : Téléversement des fichiers CSV
    bronze_dir = "bronze_data"
    files = glob.glob(os.path.join(bronze_dir, "*.csv"))
    
    if not files:
        logging.error("❌ Aucun fichier CSV trouvé dans le dossier 'bronze_data/'.")
        return

    for csv_file in files:
        file_name = os.path.basename(csv_file)
        
        # Organisation dans le Data Lake (Virtual Prefixes)
        if "sofifa" in file_name.lower():
            s3_key = f"sofifa/{file_name}"
        else:
            s3_key = f"understat/{file_name}"
            
        s3.upload_file(csv_file, BUCKET_NAME, s3_key)
        logging.info(f"📤 Téléversé : {file_name} -> MinIO ({BUCKET_NAME}/{s3_key})")

if __name__ == "__main__":
    upload_bronze_to_minio()