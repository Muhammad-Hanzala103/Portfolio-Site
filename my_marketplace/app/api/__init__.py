from flask import Blueprint, jsonify

api_bp = Blueprint('api_v1', __name__)

@api_bp.get('/ping')
def ping():
    return jsonify(msg='api ok', version='v1')