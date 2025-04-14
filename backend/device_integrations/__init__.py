from flask import Blueprint

device_integrations = Blueprint('device_integrations', __name__)

from . import routes 