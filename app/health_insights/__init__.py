from flask import Blueprint

bp = Blueprint('health_insights', __name__)

from app.health_insights import routes 