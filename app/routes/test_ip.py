import re
from datetime import timedelta, datetime
from sqlalchemy import select

from flask import Blueprint, jsonify, request, current_app, session
from flask_jwt_extended import jwt_required, create_access_token, get_current_user
from app.services.log_services import LogService
api_test_ip = Blueprint("test_ip", __name__)

@api_test_ip.route("/whoami",methods = ["GET"])
def whoami():
    log_message = f"IP {request.remote_addr} accessed /whoami endpoint"
    LogService.record_log(message=log_message, levelno=20, from_ip=request.remote_addr, user_agent=request.headers.get("User-Agent"))
    return jsonify({"status": "success", "data": {"whoami": request.remote_addr}}), 200
