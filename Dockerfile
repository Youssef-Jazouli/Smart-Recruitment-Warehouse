FROM python:3.10-slim

# Installation de Chrome et des dépendances nécessaires pour Selenium sous Linux
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libappindicator1 \
    libasound2 \
    fonts-liberation \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Installer Chrome
RUN curl -LO https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "src/sofifa_bronze_scraper.py"]