from flask import Blueprint, jsonify
from flask_login import login_required

wearable_bp = Blueprint('wearable', __name__)

@wearable_bp.route('/')
@login_required
def get_wearable_data():
    return jsonify({"message": "Wearable data feature coming soon"}) 