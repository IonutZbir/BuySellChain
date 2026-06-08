from datetime import timedelta

from flask import Blueprint, jsonify, request, current_app, session
from flask_jwt_extended import create_access_token, get_current_user, jwt_required

from app.services.user_services import UserService
from app.services.log_services import LogService
from app.models.models import Messages, LogType

api_auth = Blueprint("api", __name__)


def _apply_auth_session(user):
    session.clear()
    session["user_id"] = user.blockChainId
    session["role"] = user.role.value

    if user.role.value == "seller":
        session["taxCode"] = user.codiceFiscale
    else:
        session.pop("taxCode", None)


def _auth_response(result, expires_delta=None):
    user = result["user"]
    _apply_auth_session(user)

    token_kwargs = {
        "identity": result["identity"],
        "additional_claims": result["claims"],
    }
    if expires_delta is not None:
        token_kwargs["expires_delta"] = expires_delta

    access_token = create_access_token(**token_kwargs)
    return jsonify({"status": "success", "data": {"authorization": access_token}}), 200

@api_auth.route("/user", methods=["GET"])
def list_all_users():
    result = UserService.list_users()

    if not result.get("success"):
        return jsonify({"status": "fail", "data": {"message": result.get("message", "Errore nel recupero utenti")}}), 500

    users = []
    for user in result.get("users", []):
        users.append(
            {
                "id": user.blockChainId,
                "name": user.name,
                "surname": user.surname,
                "email": user.email,
                "role": user.role.value,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login_at": user.lastLoginAt.isoformat() if user.lastLoginAt else None,
            }
        )

    return jsonify({"status": "success", "data": {"users": users}}), 200


"""
Endpoint per la registrazione e il login degli utenti. Utilizza JWT per l'autenticazione e gestisce le sessioni utente.
"""

@api_auth.route("/signin", methods=["POST"])
def signin():
    
    payload = request.get_json(silent=True) or {}
    result = UserService.register_user(payload)

    if not result.get("success"):
        return jsonify({"status": "fail", "data": {"message": result.get("message")}}), result.get("status_code", 400)
    if result.get("user").role.value == "seller":
        LogService.record_log(message=Messages.NUOVO_SELLER_REGISTRATO.value.format(user_id=result.get("user").blockChainId), level=LogType.INFO, from_ip=request.remote_addr, user_agent=request.headers.get("User-Agent"), method="POST")
    else:
        LogService.record_log(message=Messages.NUOVO_BUYER_REGISTRATO.value.format(user_id=result.get("user").blockChainId), level=LogType.INFO, from_ip=request.remote_addr, user_agent=request.headers.get("User-Agent"), method="POST")

    return _auth_response(result)


@api_auth.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    remember = bool(payload.get("remember", False))
    result = UserService.login_user(payload)

    if not result.get("success"):
        return jsonify({"status": "fail", "data": {"message": result.get("message")}}), result.get("status_code", 401)

    expires = timedelta(days=30) if remember else timedelta(hours=2)
    if remember:
        current_app.permanent_session_lifetime = timedelta(days=30)

    LogService.record_log(message=Messages.ACCESSO_RIUSCITO.value.format(user_id=result.get("user").blockChainId, role=result.get("user").role.value), level=LogType.INFO, from_ip=request.remote_addr, user_agent=request.headers.get("User-Agent"), method="POST")

    return _auth_response(result, expires_delta=expires)



@api_auth.route("/logout", methods=["POST", "GET"])
@jwt_required()
def logout():
    session.clear()

    return jsonify({"status": "success", "data": {"message": "Log out correttamente!"}}), 200


@api_auth.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    current_user = get_current_user() or {}
    user_id = current_user.get("id")

    if not user_id:
        return jsonify({"status": "fail", "data": {"message": "Utente non autenticato"}}), 401

    result = UserService.get_profile(user_id)
    if not result.get("success"):
        return jsonify({"status": "fail", "data": {"message": "Utente non trovato"}}), 404

    user = result.get("user")

    return jsonify(
        {
            "status": "success",
            "data": {
                "id": user.blockChainId,
                "name": user.name,
                "surname": user.surname,
                "email": user.email,
                "birthday": user.birthday.isoformat() if user.birthday else None,
                "cellularNumber": user.cellularNumber,
                "role": user.role.value,
                "taxCode": user.codiceFiscale,
            },
        }
    ), 200