from flask import Flask
from flask_cors import CORS

from app.config import ProspectConfig
from app.utils.app_logger import setup_app_logger


def create_app(config: ProspectConfig = None) -> Flask:
    app = Flask(__name__)

    cfg = config or ProspectConfig()
    app.config.from_object(cfg)
    app.config["MAX_CONTENT_LENGTH"] = cfg.MAX_UPLOAD_BYTES
    app.json.ensure_ascii = False

    cors_origins = ["*"] if cfg.CORS_ORIGIN == "*" else [cfg.CORS_ORIGIN]
    CORS(app, origins=cors_origins)
    setup_app_logger(app)

    from app.api.prospect_analysis_routes import prospect_analysis_bp
    app.register_blueprint(prospect_analysis_bp, url_prefix="/api")

    app.logger.info("Imporsan Prospect started — CORS origin: %s", cfg.CORS_ORIGIN)
    return app
