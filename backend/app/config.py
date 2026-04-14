import os
from dotenv import load_dotenv

load_dotenv()


class ProspectConfig:
    FLASK_ENV: str = os.environ.get("FLASK_ENV", "development")
    PORT: int = int(os.environ.get("PORT", 5001))
    # En producción (Vercel) frontend y backend están en el mismo dominio;
    # setear CORS_ORIGIN=* en las env vars de Vercel, o dejar el default para dev.
    CORS_ORIGIN: str = os.environ.get("CORS_ORIGIN", "http://localhost:5173")
    USD_RATE: float = float(os.environ.get("USD_RATE", 17))
    MAX_UPLOAD_BYTES: int = 20 * 1024 * 1024
    ALLOWED_EXTENSIONS: set[str] = {".xlsx", ".xls"}
