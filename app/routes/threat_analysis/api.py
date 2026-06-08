from flask import Blueprint, current_app, request
from flask_jwt_extended import get_current_user, jwt_required

from app.models.models import LogType, Messages
from app.services.jsend import jsend_response
from app.services.log_services import LogService
from app.services.threat_services import ThreatService

api_ta = Blueprint("api_ta", __name__)

# METTERE I LOG DI OLLAMA COME CLASSE "AI-LOGS" SU BL

def _ensure_admin():
    user = get_current_user()
    if not user or user.get("role") != "admin":
        LogService.record_log(
            message=Messages.PREFIX_ACCESSO_NON_AUTORIZZATO.value + "/analyze-logs",
            level=LogType.ALERT,
            from_ip=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            method=request.method,
        )
        return None, jsend_response("fail", data={"error": "Accesso riservato agli amministratori"}, code=403)
    return user, None


def _safe_numkeys(result):
    if isinstance(result, dict):
        return result.get("answer", {}).get("numkeys", 0)
    return 0

@api_ta.route("/analyze-logs", methods=["POST"])
@jwt_required()
def analyzed_logs():
    user, error = _ensure_admin()
    if error:
        return error

    list_result = LogService.list_logs(limit=20)
    if not list_result.get("success"):
        current_app.logger.error("Threat Analyst API: failed to retrieve logs for analysis - " + list_result.get("error", "unknown error"))
        LogService.record_log(
            message=Messages.PREFIX_GET_ADMIN_ROUTE.value + "/analyze-logs - failed to fetch logs",
            level=LogType.ALERT,
            from_ip=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            method="POST",
        )
        return jsend_response("fail", data={"error": "Impossibile recuperare i log per l'analisi"}, code=500)

    payload = request.get_json(silent=True) or {}
    logs = payload.get("logs")
    if not isinstance(logs, list) or not logs:
        logs = list_result.get("logs", [])

    # Avvia l'analisi tramite ThreatService
   
    ai_result = ThreatService.analyze_logs(logs)

    if isinstance(ai_result, dict) and ai_result.get("error"):
        current_app.logger.error("Threat Analyst API: Ollama analysis failed - " + ai_result.get("detail", "unknown error"))
        LogService.record_log(
            message=Messages.PREFIX_GET_ADMIN_ROUTE.value + "/analyze-logs - failed: " + ai_result.get("detail", str(ai_result)),
            level=LogType.ALERT,
            from_ip=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            method="POST",
        )
        return jsend_response("fail", data=ai_result, code=502)

    # Mappa il livello di severità restituito dall'AI al LogType (uso ALERT per severità elevata)
    severity = None
    if isinstance(ai_result, dict):
        severity = ai_result.get("severity")

    sev_val = str(severity).upper() if severity else ""
    if sev_val in ("ALERT", "CRITICAL", "HIGH"):
        level = LogType.ALERT
    else:
        level = LogType.INFO

    return jsend_response("success", data={"analysis": ai_result})