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

_flask = create_app()


class StripBackendMountPrefix:
    """
    Vercel experimentalServices monta el backend en /_/backend.
    Si PATH_INFO llega con ese prefijo, lo quitamos para que coincidan las rutas /api/... de Flask.
    """

    _PREFIX = "/_/backend"

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO") or ""
        if path.startswith(self._PREFIX):
            # Copia explícita: dict(environ) puede fallar en algunos runtimes WSGI
            new_environ = {k: environ[k] for k in environ}
            new_environ["PATH_INFO"] = path[len(self._PREFIX) :] or "/"
            return self.wsgi_app(new_environ, start_response)
        return self.wsgi_app(environ, start_response)


app = StripBackendMountPrefix(_flask)
