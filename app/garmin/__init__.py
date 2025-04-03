from flask import Blueprint

bp = Blueprint('garmin', __name__)

from app.garmin import routes 