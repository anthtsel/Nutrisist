from flask import Blueprint, jsonify
from flask_login import login_required, current_user

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile')
@login_required
def get_profile():
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name
    }) 