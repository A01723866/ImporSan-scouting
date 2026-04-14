import os
from dotenv import load_dotenv

load_dotenv()


class ProspectConfig:
    FLASK_ENV: str = os.environ.get("FLASK_ENV", "development")
    PORT: int = int(os.environ.get("PORT", 5001))
    CORS_ORIGIN: str = os.environ.get("CORS_ORIGIN", "http://localhost:5173")
    USD_RATE: float = float(os.environ.get("USD_RATE", 17))
    MAX_UPLOAD_BYTES: int = 20 * 1024 * 1024
    ALLOWED_EXTENSIONS: set[str] = {".xlsx", ".xls"}
