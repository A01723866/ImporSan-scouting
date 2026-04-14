"""
Flask entrypoint at repo root — Vercel scans the monorepo root for wsgi.py / app.py.
Adds backend/ to PYTHONPATH so `app` package resolves to backend/app/.
"""

import os
import sys

_root = os.path.dirname(os.path.abspath(__file__))
_backend = os.path.join(_root, "backend")
sys.path.insert(0, _backend)

from app import create_app

app = create_app()
