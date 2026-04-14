"""
Vercel serverless entry point.
Exposes the Flask `app` object at module level so @vercel/python can serve it.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

app = create_app()
