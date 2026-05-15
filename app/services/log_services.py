from datetime import datetime
import enum

from app.models.models import Log, LogType, Messages
from app.services.guile_services import GuileService


class LogService:
    LOGS_CLASS = "Logs"

    @staticmethod
    def _normalize_keys(result):
        answer = result.get("answer", {}) if isinstance(result, dict) else {}
        keys = answer.get("keys", []) if isinstance(answer, dict) else []
        normalized = []

        for key in keys:
            if isinstance(key, (list, tuple)) and key:
                normalized.append(str(key[0]))
            else:
                normalized.append(str(key))

        return normalized

    @staticmethod
    def _extract_value(result):
        if not isinstance(result, dict):
            return None

        answer = result.get("answer", {})
        if not isinstance(answer, dict):
            return None

        value = answer.get("value")
        if isinstance(value, dict):
            return value
        return None


    @staticmethod
    def record_log(message: str | Messages, level: LogType, from_ip: str,user_agent: str,method: str):
        log = Log(from_ip=from_ip, level=level, description=message, user_agent=user_agent, method=method)
        result = GuileService.AddKV(Class=LogService.LOGS_CLASS, key=log.get_id(), value=log.to_json())
        return result

    @staticmethod
    def list_logs(limit: int = 120):
        result = GuileService.GetKeys(Class=LogService.LOGS_CLASS)
        if "error" in result:
            return {"success": False, "error": result.get("error")}

        logs = []
        for key in LogService._normalize_keys(result):
            log_result = GuileService.GetKV(Class=LogService.LOGS_CLASS, key=key)
            if "error" in log_result:
                continue

            value = LogService._extract_value(log_result)
            if not value:
                continue

            logs.append(value)

        def _sort_key(entry):
            created_at = entry.get("created_at")
            if not created_at:
                return datetime.min
            try:
                return datetime.fromisoformat(created_at)
            except ValueError:
                return datetime.min

        logs.sort(key=_sort_key, reverse=True)

        formatted_logs = []
        for index, log in enumerate(logs[:limit], 1):
            formatted_logs.append(
                {
                    "id": log.get("id", index),
                    "message": log.get("description", ""),
                    "level": log.get("level", "ok"),
                    "from_ip": Log.decrypt_field(log.get("from_ip", "system")),
                    "created_at": log.get("created_at"),
                    "user_agent": Log.decrypt_field(log.get("user_agent", "unknown")),
                    "method": log.get("method", "-"),
                }
            )

        return {"success": True, "logs": formatted_logs}