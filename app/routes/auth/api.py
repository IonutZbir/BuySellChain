from flask import Blueprint, jsonify

api_auth = Blueprint('api', __name__)

@api_auth.route('/login', methods=['POST'])
def status():
    return jsonify({
        "status": "online",
        "message": "Backend Flask API pronto!",
        "version": "1.0.0"
    }), 200