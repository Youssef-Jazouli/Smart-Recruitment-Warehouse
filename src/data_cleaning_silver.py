import os
import io
import logging
import unicodedata
import pandas as pd
import boto3
from botocore.client import Config

# Configuration Log
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MINIO_URL = "http://localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadminpassword"
BRONZE_BUCKET = "bronze-layer"
SILVER_BUCKET = "silver-layer"

def get_s3_client():
    return boto3.client(
        's3', endpoint_url=MINIO_URL,
        aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version='s3v4'), region_name='us-east-1'
    )

def remove_accents(input_str):
    if not isinstance(input_str, str):
        return input_str
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def parse_currency(val):
    if pd.isna(val) or not isinstance(val, str):
        return 0.0
    val = val.replace('€', '').strip()
    if 'M' in val:
        return float(val.replace('M', '')) * 1_000_000
    elif 'K' in val:
        return float(val.replace('K', '')) * 1_000
    try:
        return float(val)
    except ValueError:
        return 0.0

def clean_and_merge_sofifa_datasets(df_base, df_advanced):
    """ Fusionne et nettoie les deux fichiers SoFIFA (Base + Advanced Metrics) """
    logging.info("🧹 Fusion et nettoyage des fichiers SoFIFA...")

    # Normalisation des noms pour le Matching
    df_base['Clean_Name'] = df_base['Name'].str.replace(r'([A-Z]{2}(?:\s+[A-Z]{2})*)$', '', regex=True).str.strip()
    df_base['Match_Name'] = df_base['Clean_Name'].apply(remove_accents)

    df_advanced['Clean_Name'] = df_advanced['Name'].str.replace(r'([A-Z]{2}(?:\s+[A-Z]{2})*)$', '', regex=True).str.strip()
    df_advanced['Match_Name'] = df_advanced['Clean_Name'].apply(remove_accents)

    # MERGE des deux datasets sur le nom nettoyé
    df_merged = pd.merge(df_base, df_advanced, on='Match_Name', how='inner', suffixes=('', '_adv'))

    # Nettoyage Taille / Poids
    if 'Height' in df_merged.columns:
        df_merged['Height_cm'] = df_merged['Height'].astype(str).str.extract(r'(\d+)cm').astype(float)
    if 'Weight' in df_merged.columns:
        df_merged['Weight_kg'] = df_merged['Weight'].astype(str).str.extract(r'(\d+)kg').astype(float)

    # Parsing Finances
    if 'Value' in df_merged.columns:
        df_merged['Value_EUR'] = df_merged['Value'].apply(parse_currency)
    if 'Wage' in df_merged.columns:
        df_merged['Wage_EUR'] = df_merged['Wage'].apply(parse_currency)

    # Calculations des KPIs (Feature Engineering)
    if 'Height_cm' in df_merged.columns and 'Weight_kg' in df_merged.columns:
        df_merged['BMI'] = (df_merged['Weight_kg'] / ((df_merged['Height_cm'] / 100) ** 2)).round(2)

    logging.info(f"✅ Fusion réussie ! Dataset final SoFIFA : {len(df_merged)} joueurs.")
    return df_merged

# (باقي كود Upload لـ MinIO كيبقاء كيمشي عادي للـ silver-layer)