"""
Vercel serverless entry point.
Exposes the Flask `app` object at module level so @vercel/python can serve it.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

_flask = create_app()


class StripBackendMountPrefix:
    _PREFIX = "/_/backend"

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO") or ""
        if path.startswith(self._PREFIX):
            new_environ = {k: environ[k] for k in environ}
            new_environ["PATH_INFO"] = path[len(self._PREFIX) :] or "/"
            return self.wsgi_app(new_environ, start_response)
        return self.wsgi_app(environ, start_response)


app = StripBackendMountPrefix(_flask)
