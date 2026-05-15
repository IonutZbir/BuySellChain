import re
from datetime import datetime

from email_validator import EmailNotValidError, validate_email
from flask import current_app

from app import bcrypt
from app.models.models import UserRoles, User
from app.services.email_service import EmailService
from app.services.guile_services import GuileService

class UserService:
    USERS_CLASS = "Users"

    @staticmethod
    def _normalize_email(email: str) -> str:
        return str(email or "").strip().lower()

    @staticmethod
    def _normalize_string(value) -> str:
        return str(value or "").strip()

    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        clean_phone = re.sub(r"[\s\-\(\)]", "", phone)
        return clean_phone.isdigit() and 9 <= len(clean_phone) <= 15

    @staticmethod
    def _parse_birthday(birthday):
        try:
            return datetime.strptime(str(birthday), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _extract_keys(result):
        answer = result.get("answer", {}) if isinstance(result, dict) else {}
        keys = answer.get("keys", []) if isinstance(answer, dict) else []
        normalized_keys = []

        for key in keys:
            if isinstance(key, (list, tuple)) and key:
                normalized_keys.append(str(key[0]))
            else:
                normalized_keys.append(str(key))

        return normalized_keys

    @staticmethod
    def _extract_user_value(result):
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
    def _get_user_record_by_id(user_id: str):
        result = GuileService.GetKV(Class=UserService.USERS_CLASS, key=str(user_id))
        if "error" in result:
            return {"success": False, "error": result.get("error")}

        user_value = UserService._extract_user_value(result)
        if not user_value:
            return {"success": False, "error": "Utente non trovato"}

        return {"success": True, "user": User.from_json(user_value)}

    @staticmethod
    def list_users():
        result = GuileService.GetKeys(Class=UserService.USERS_CLASS)
        if "error" in result:
            return {"success": False, "error": result.get("error")}

        users = []
        for user_id in UserService._extract_keys(result):
            user_result = UserService._get_user_record_by_id(user_id)
            if user_result.get("success"):
                users.append(user_result.get("user"))

        return {"success": True, "users": users}

    @staticmethod
    def get_user_by_email(email: str):
        normalized_email = UserService._normalize_email(email)
        users_result = UserService.list_users()
        if not users_result.get("success"):
            return users_result

        for user in users_result.get("users", []):
            if UserService._normalize_email(user.email) == normalized_email:
                return {"success": True, "user": user}

        return {"success": False, "error": "Utente non trovato"}

    @staticmethod
    def _build_auth_payload(user: User) -> dict:
        payload = {
            "id": user.blockChainId,
            "role": user.role.value,
            "email": user.email,
            "taxCode": user.codiceFiscale if user.role == UserRoles.SELLER else None,
        }
        claims = {
            "name": user.name,
            "surname": user.surname,
            "email": user.email,
            "role": user.role.value,
            "taxCode": user.codiceFiscale if user.role == UserRoles.SELLER else None,
        }
        return {"identity": payload, "claims": claims}

    @staticmethod
    def register_user(payload: dict):
        name = UserService._normalize_string(payload.get("name"))
        surname = UserService._normalize_string(payload.get("surname"))
        email = UserService._normalize_email(payload.get("email"))
        birthday_raw = payload.get("birthday")
        cellular_number = UserService._normalize_string(payload.get("cellularNumber"))
        password = str(payload.get("password") or "")
        is_vendor = bool(payload.get("isVendor", False))
        tax_code = UserService._normalize_string(payload.get("taxCode")).upper()

        if not all([name, surname, email, password]):
            return {
                "success": False,
                "status_code": 400,
                "message": "Tutti i campi sono obbligatori",
            }

        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            return {
                "success": False,
                "status_code": 400,
                "message": "Formato email non valido",
            }

        birthday = UserService._parse_birthday(birthday_raw)
        if not birthday:
            return {
                "success": False,
                "status_code": 400,
                "message": "Data di nascita non valida",
            }

        if cellular_number and not UserService._is_valid_phone(cellular_number):
            return {
                "success": False,
                "status_code": 400,
                "message": "Numero di telefono non valido",
            }

        existing_user = UserService.get_user_by_email(email)
        if existing_user.get("success"):
            return {
                "success": False,
                "status_code": 409,
                "message": "Questa email è già registrata",
            }

        user_role = UserRoles.SELLER if is_vendor else UserRoles.BIDDER

        if is_vendor:
            if not tax_code:
                return {
                    "success": False,
                    "status_code": 400,
                    "message": "Il codice fiscale è obbligatorio per i venditori",
                }

            cf_regex = r"^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$"
            if not re.match(cf_regex, tax_code, re.IGNORECASE):
                return {
                    "success": False,
                    "status_code": 400,
                    "message": "Codice fiscale non valido",
                }

            users_result = UserService.list_users()
            if users_result.get("success"):
                for user in users_result.get("users", []):
                    if user.role == UserRoles.SELLER and UserService._normalize_string(user.codiceFiscale).upper() == tax_code:
                        return {
                            "success": False,
                            "status_code": 409,
                            "message": "Esiste già un venditore registrato con questo codice fiscale",
                        }

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(
            name=name,
            surname=surname,
            email=email,
            birthday=birthday,
            cellularNumber=cellular_number,
            passwordHash=password_hash,
            codiceFiscale=tax_code if is_vendor else None,
            role=user_role,
        )

        result = GuileService.AddKV(
            Class=UserService.USERS_CLASS,
            key=user.blockChainId,
            value=user.to_json(),
        )

        if "error" in result:
            current_app.logger.error(f"Errore salvataggio utente su blockchain: {result.get('error')}")
            return {
                "success": False,
                "status_code": 500,
                "message": "Errore interno durante la registrazione",
            }

        if is_vendor:
            EmailService.send_email_to_admin()

        current_app.logger.info(f"USER CREATED ON CHAIN: {email=}, {user.blockChainId=}, {user.role=}")
        auth_payload = UserService._build_auth_payload(user)
        return {
            "success": True,
            "user": user,
            "identity": auth_payload["identity"],
            "claims": auth_payload["claims"],
        }

    @staticmethod
    def login_user(payload: dict):
        email = UserService._normalize_email(payload.get("email"))
        password = str(payload.get("password") or "")

        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            return {
                "success": False,
                "status_code": 401,
                "message": "Credenziali errate!",
            }

        user_result = UserService.get_user_by_email(email)
        if not user_result.get("success"):
            dummy_hash = bcrypt.generate_password_hash(password)
            bcrypt.check_password_hash(dummy_hash, password)
            return {
                "success": False,
                "status_code": 401,
                "message": "Credenziali errate!",
            }

        user = user_result.get("user")
        if not bcrypt.check_password_hash(user.passwordHash, password):
            return {
                "success": False,
                "status_code": 401,
                "message": "Credenziali errate!",
            }

        user.lastLoginAt = datetime.now()
        GuileService.AddKV(
            Class=UserService.USERS_CLASS,
            key=user.blockChainId,
            value=user.to_json(),
        )

        #current_app.logger.info(f"USER LOGGED IN FROM CHAIN: {email=}, {user.blockChainId=}, {user.role=}")  #log in locale
        #LogService.record_log(message=f"User {email} logged in", levelno=20, from_ip=request.remote_addr, user_agent=request.headers.get("User-Agent"))

        auth_payload = UserService._build_auth_payload(user)
        return {
            "success": True,
            "user": user,
            "identity": auth_payload["identity"],
            "claims": auth_payload["claims"],
        }

    @staticmethod
    def get_profile(user_id: str):
        return UserService._get_user_record_by_id(user_id)

    @staticmethod
    def update_profile(user_id: str, payload: dict):
        record = UserService._get_user_record_by_id(user_id)
        if not record.get("success"):
            return record

        user = record.get("user")
        update_data = {
            k: v
            for k, v in (payload or {}).items()
            if k in {"name", "surname", "email", "birthday", "cellularNumber", "taxCode"}
        }

        if "name" in update_data:
            name = UserService._normalize_string(update_data.get("name"))
            if not name:
                return {"success": False, "status_code": 400, "message": "Il nome non puo essere vuoto"}
            user.name = name

        if "surname" in update_data:
            surname = UserService._normalize_string(update_data.get("surname"))
            if not surname:
                return {"success": False, "status_code": 400, "message": "Il cognome non puo essere vuoto"}
            user.surname = surname

        if "email" in update_data:
            email = UserService._normalize_email(update_data.get("email"))
            try:
                validate_email(email, check_deliverability=False)
            except EmailNotValidError:
                return {"success": False, "status_code": 400, "message": "Formato email non valido"}

            existing_email = UserService.get_user_by_email(email)
            if existing_email.get("success") and existing_email.get("user").blockChainId != user_id:
                return {"success": False, "status_code": 409, "message": "Questa email e gia registrata"}

            user.email = email

        if "birthday" in update_data:
            birthday = UserService._parse_birthday(update_data.get("birthday"))
            if not birthday:
                return {"success": False, "status_code": 400, "message": "Data di nascita non valida"}
            user.birthday = birthday

        if "cellularNumber" in update_data:
            cellular_number = UserService._normalize_string(update_data.get("cellularNumber"))
            if cellular_number and not UserService._is_valid_phone(cellular_number):
                return {"success": False, "status_code": 400, "message": "Numero di telefono non valido"}
            user.cellularNumber = cellular_number

        if "taxCode" in update_data and user.role == UserRoles.SELLER:
            tax_code = UserService._normalize_string(update_data.get("taxCode")).upper()
            if tax_code:
                cf_regex = r"^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$"
                if not re.match(cf_regex, tax_code, re.IGNORECASE):
                    return {"success": False, "status_code": 400, "message": "Codice fiscale non valido"}

                users_result = UserService.list_users()
                if users_result.get("success"):
                    for other_user in users_result.get("users", []):
                        if (
                            other_user.blockChainId != user_id
                            and other_user.role == UserRoles.SELLER
                            and UserService._normalize_string(other_user.codiceFiscale).upper() == tax_code
                        ):
                            return {"success": False, "status_code": 409, "message": "Codice fiscale gia in uso"}

            user.codiceFiscale = tax_code or None

        result = GuileService.AddKV(
            Class=UserService.USERS_CLASS,
            key=user.blockChainId,
            value=user.to_json(),
        )

        if "error" in result:
            current_app.logger.error(f"Errore aggiornamento profilo su blockchain: {result.get('error')}")
            return {"success": False, "status_code": 500, "message": "Errore interno durante l'aggiornamento"}

        return {"success": True, "user": user}