import traceback
import sys
import os

try:
    port = int(os.environ.get("PORT", "8080"))
except ValueError:
    port = -1

if not 1 <= port <= 65535:
    print("Please make sure the PORT environment variable is an integer between 1 and 65535")
    sys.exit(1)

try:
    api_id = int(os.environ["API_ID"])
    api_hash = os.environ["API_HASH"]
except (KeyError, ValueError):
    traceback.print_exc()
    print("\n\nPlease set the API_ID and API_HASH environment variables correctly")
    print("You can get your own API keys at https://my.telegram.org/apps")
    sys.exit(1)

try:
    index_settings = {
        "index_all": False,
        "index_private": True,
        "index_group": True,
        "index_channel": True,
        "exclude_chats": [],
        "include_chats": [int(os.environ["INDEXING_CHAT"])],
        "otg": {
            "enable": True,
            "include_private": True,
            "include_group": True,
            "include_channel": True
        }
    }
    otg_settings = index_settings["otg"]
    enable_otg = otg_settings["enable"]
except Exception:
    traceback.print_exc()
    print("\n\nPlease set the INDEXING_CHAT environment variable correctly")
    sys.exit(1)

try:
    session_string = os.environ["SESSION_STRING"]
except (KeyError, ValueError):
    traceback.print_exc()
    print("\n\nPlease set the SESSION_STRING environment variable correctly")
    sys.exit(1)

host = os.environ.get("HOST", "0.0.0.0")
debug = bool(os.environ.get("DEBUG"))

chat_ids = []
alias_ids = []

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# URL pública de esta web
INDEXWEBOFICA_URL = os.environ.get("INDEXWEBOFICA_URL", "")

# Secreto de sesión web
WEB_SESSION_SECRET = os.environ.get("WEB_SESSION_SECRET", "CHANGE_THIS_SECRET_PLEASE")

# Tiempo de validez de tokens de login web
WEB_LOGIN_TOKEN_TTL_MINUTES = int(os.environ.get("WEB_LOGIN_TOKEN_TTL_MINUTES", "10"))

# Planes web
WEB_PLANS = {
    "1d": {
        "label": "1 día",
        "days": 1,
        "coins": 150,
        "device_limit": 3,
    },
    "7d": {
        "label": "7 días",
        "days": 7,
        "coins": 450,
        "device_limit": 3,
    },
    "30d": {
        "label": "30 días",
        "days": 30,
        "coins": 1200,
        "device_limit": 3,
    },
}

# Clave interna para servicios autorizados como botneflixtelegram
INTERNAL_SERVICE_KEY = os.environ.get("INTERNAL_SERVICE_KEY", "")
