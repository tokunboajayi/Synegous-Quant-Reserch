import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory: nmie/nmie/config.py -> nmie/nmie -> nmie (project root)
# So we want parent.parent
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Data Providers
PRIMARY_PROVIDER = os.getenv("NMIE_PROVIDER", "polygon")  # polygon or iex

# API Keys
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
IEX_API_KEY = os.getenv("IEX_API_KEY", "")

# Ingestion Settings
START_DATE = "2024-06-01"
END_DATE = "2025-12-31"  # Recent data
TIMEFRAME = "1m"         # 1-minute bars

# System Settings
RANDOM_SEED = 42
DEBUG_MODE = os.getenv("NMIE_DEBUG", "False").lower() == "true"
