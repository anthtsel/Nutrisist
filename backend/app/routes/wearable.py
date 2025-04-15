from flask import Blueprint, jsonify, request
from app.services.wearable_processor import process_wearable_data

bp = Blueprint('wearable', __name__)

@bp.route('/api/wearable/data', methods=['POST'])
def receive_wearable_data():
    data = request.json
    processed_data = process_wearable_data(data)
    return jsonify(processed_data) 