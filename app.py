"""Entry point: builds the Flask app and creates the database on first run."""
import os

from flask import Flask

from api import api
from db import DB_PATH, init_db

app = Flask(__name__)
app.register_blueprint(api)

__all__ = ["app", "init_db"]

if not os.path.exists(DB_PATH):
    init_db()
