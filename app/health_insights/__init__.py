from flask import Blueprint

health_insights = Blueprint('health_insights', __name__)

from . import routes 