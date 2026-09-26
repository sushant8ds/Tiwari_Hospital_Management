"""
Jinja2 template configuration for FastAPI HTML responses
"""

from fastapi.templating import Jinja2Templates
import os

templates_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "templates"))
templates = Jinja2Templates(directory=templates_dir)
