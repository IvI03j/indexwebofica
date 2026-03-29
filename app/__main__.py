import os

# Cargar .env si existe (para desarrollo local y Replit)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Si no está dotenv, cargar .env manualmente
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, val = line.partition('=')
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and not key.startswith('THESE_VALUES'):
                        os.environ.setdefault(key, val)

try:
    import telethon
except:
    os.system("pip3 install -U -r requirements.txt")

import logging

from .main import Indexer
from .config import debug

logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
logging.getLogger("telethon").setLevel(logging.INFO if debug else logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.INFO if debug else logging.ERROR)

Indexer().run()