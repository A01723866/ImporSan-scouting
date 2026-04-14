"""
Analysis routes blueprint.

Endpoints:
    GET  /api/health
    POST /api/analysis/upload
"""

import os
from flask import Blueprint, request, current_app, jsonify

from app.config import ProspectConfig
from app.services.helium10_xlsx_parser import (
    parse_helium10_xlsx,
    deduplicate_by_asin,
    Helium10XlsxParseError,
)
from app.services.market_analysis_engine import run_market_analysis

prospect_analysis_bp = Blueprint("prospect_analysis", __name__)


@prospect_analysis_bp.get("/health")
def health_check():
    """GET /api/health — liveness check."""
    return jsonify({"status": "ok", "service": "imporsan-prospect"})


@prospect_analysis_bp.post("/analysis/upload")
def upload_and_analyze():
    """
    POST /api/analysis/upload

    Accepts multipart/form-data:
        file     (required) — Helium 10 Xray .xlsx
        top_n    (optional) — integer, default 10
        usd_rate (optional) — float, default from config

    Returns:
        200  { "success": true,  "data": { ...analysis... } }
        400  { "success": false, "error": "..." }
        422  { "success": false, "error": "..." }
    """
    cfg = ProspectConfig()

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded. Send a .xlsx file in the 'file' field."}), 400

    uploaded_file = request.files["file"]
    if not uploaded_file.filename:
        return jsonify({"success": False, "error": "Empty filename."}), 400

    ext = os.path.splitext(uploaded_file.filename)[1].lower()
    if ext not in cfg.ALLOWED_EXTENSIONS:
        return jsonify({"success": False, "error": f"Invalid file type '{ext}'. Only .xlsx files are accepted."}), 400

    try:
        top_n = max(1, min(int(request.form.get("top_n", 10)), 50))
    except (ValueError, TypeError):
        top_n = 10

    try:
        usd_rate = max(1.0, float(request.form.get("usd_rate", cfg.USD_RATE)))
    except (ValueError, TypeError):
        usd_rate = cfg.USD_RATE

    try:
        file_bytes = uploaded_file.read()
        raw_records = parse_helium10_xlsx(file_bytes)
    except Helium10XlsxParseError as exc:
        current_app.logger.warning("Parse error for '%s': %s", uploaded_file.filename, exc)
        return jsonify({"success": False, "error": str(exc)}), 422
    except Exception:
        current_app.logger.exception("Unexpected parse error for '%s'", uploaded_file.filename)
        return jsonify({"success": False, "error": "Unexpected error while reading the file."}), 500

    if not raw_records:
        return jsonify({"success": False, "error": "The file appears to be empty."}), 422

    unique_records = deduplicate_by_asin(raw_records)

    try:
        result = run_market_analysis(
            raw_records=raw_records,
            unique_records=unique_records,
            usd_rate=usd_rate,
            top_n=top_n,
        )
    except Exception:
        current_app.logger.exception("Analysis error for '%s'", uploaded_file.filename)
        return jsonify({"success": False, "error": "Error during market analysis."}), 500

    current_app.logger.info(
        "Analyzed '%s' — %d rows, %d unique ASINs, MEFS %.1f",
        uploaded_file.filename, len(raw_records), len(unique_records), result["mefs"]["score"],
    )

    return jsonify({"success": True, "data": result})
