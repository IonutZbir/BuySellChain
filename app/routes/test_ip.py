import re
from datetime import timedelta, datetime
from sqlalchemy import select

from flask import Blueprint, jsonify, request, current_app, session
from flask_jwt_extended import jwt_required, create_access_token, get_current_user
api_test_ip = Blueprint("test_ip", __name__)

@api_test_ip.route("/whoami",methods = ["GET"])
def whoami():
    return jsonify({"status": "success", "data": {"whoami": request.remote_addr}}), 200
