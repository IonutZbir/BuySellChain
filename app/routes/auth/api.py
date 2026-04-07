import re
from datetime import timedelta, datetime
from sqlalchemy import select

from flask import Blueprint, jsonify, request, current_app, session
from flask_jwt_extended import get_jwt_identity, jwt_required, create_access_token

from app.models.models import User, UserRoles
from app import bcrypt, db

from email_validator import validate_email, EmailNotValidError

from app.services.email_service import EmailService

api_auth = Blueprint("api", __name__)


def is_valid_phone(phone):
    # Rimuove eventuali spazi, trattini o parentesi che l'utente potrebbe inserire
    clean_phone = re.sub(r"[\s\-\(\)]", "", phone)
    # Verifica che ci siano solo numeri e che la lunghezza sia tra 9 e 15
    return clean_phone.isdigit() and 9 <= len(clean_phone) <= 15


@api_auth.route("/signin", methods=["POST"])
def signin():
    name = request.json.get("name", None)
    surname = request.json.get("surname", None)
    email = request.json.get("email", None)
    birthday = request.json.get("birthday", None)
    cellularNumber = request.json.get("cellularNumber", None)
    password = request.json.get("password", None)
    is_vendor = request.json.get("isVendor", False)
    tax_code = request.json.get("taxCode", None)

    # Validazione input

    # 1. Controllo campi vuoti
    if not all([name, surname, email, password]):
        return (
            jsonify({"status": "fail", "data": {"message": "Tutti i campi sono obbligatori"}}),
            400,
        )

    # 2. Validazione Formato Email
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return jsonify({"status": "fail", "data": {"message": "Formato email non valido"}}), 400

    # 3. Controllo Unicità Email
    existing_user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing_user:
        return (
            jsonify({"status": "fail", "data": {"message": "Questa email è già registrata"}}),
            409,
        )

    # 5. Gestione Data di nascita
    try:
        birthday = datetime.strptime(birthday, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return jsonify({"status": "fail", "data": {"message": "Data di nascita non valida"}}), 400

    # 6. Controllo numero di telefono - più avanti magari faremo qualcosa più complesso
    if cellularNumber and not is_valid_phone(cellularNumber):
        return (
            jsonify({"status": "fail", "data": {"message": "Numero di telefono non valido"}}),
            400,
        )

    # .7 Controllo codice fiscale se è venditore
    if is_vendor:
        # check che nel db non esista già un venditore con lo stesso codice fiscale
        existing_tax_code = db.session.execute(
            select(User).where(User.codiceFiscale == tax_code)
        ).scalar_one_or_none()
        if existing_tax_code:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "data": {
                            "message": "Esiste già un venditore registrato con questo codice fiscale"
                        },
                    }
                ),
                409,
            )

        if not tax_code:
            return (
                jsonify(
                    {
                        "status": "fail",
                        "data": {"message": "Il codice fiscale è obbligatorio per i venditori"},
                    }
                ),
                400,
            )
        cf_regex = r"^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$"
        if not re.match(cf_regex, tax_code, re.IGNORECASE):
            return (
                jsonify({"status": "fail", "data": {"message": "Codice fiscale non valido"}}),
                400,
            )

    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    if is_vendor:
        user = User(
            name=name,
            surname=surname,
            email=email,
            birthday=birthday,
            cellularNumber=cellularNumber,
            passwordHash=password_hash,
            codiceFiscale=tax_code,
            role=UserRoles.SELLER,
        )
        EmailService.send_email_to_admin()
        current_app.logger.warning(
            f"New vendor registered: {email=}, {user.blockChainId=}, {user.role=}"
        )
    else:
        user = User(
            name=name,
            surname=surname,
            email=email,
            birthday=birthday,
            cellularNumber=cellularNumber,
            passwordHash=password_hash,
        )

    db.session.add(user)
    db.session.commit()

    session["user_id"] = user.blockChainId
    session["role"] = user.role.value

    if is_vendor:
        additional_info = {
            "name": name,
            "surname": surname,
            "email": email,
            "role": user.role.value,
            "taxCode": tax_code,
        }
        session["taxCode"] = tax_code
        user_data = {
            "id": user.blockChainId,
            "role": user.role.value,
            "email": user.email,
            "taxCode": tax_code,
        }
    else:
        additional_info = {
            "name": name,
            "surname": surname,
            "email": email,
            "role": user.role.value,
        }
        user_data = {
            "id": user.blockChainId,
            "role": user.role.value,
            "email": user.email,
            "taxCode": None,
        }

    current_app.logger.info(f"USER CREATED: {email=}, {user.blockChainId=}, {user.role=}")
    access_token = create_access_token(identity=user_data, additional_claims=additional_info)

    return jsonify({"status": "success", "data": {"authorization": access_token}}), 200


@api_auth.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "").strip()
    password = request.json.get("password", None)
    remember = request.json.get("remember", None)

    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        return jsonify({"status": "fail", "data": {"message": "Credenziali errate!"}}), 401

    current_app.logger.debug(f"{email=}, {password=}")
    current_app.logger.info(f"LOGIN")

    query = select(User).where(User.email == email)
    user = db.session.execute(query).scalar_one_or_none()

    # Anche se l'utente non è presente nel database, non ritorno direttamente la risposta HTTP,
    # prima calcolo un hash dummy, contro attacchi basati sul tempo, in quanto bcrypt è una funzione lenta.

    if not user:
        dummy_hash = bcrypt.generate_password_hash(password)
        bcrypt.check_password_hash(dummy_hash, password)
        return jsonify({"status": "fail", "data": {"message": "Credenziali errate!"}}), 401

    if not bcrypt.check_password_hash(user.passwordHash, password):
        return jsonify({"status": "fail", "data": {"message": "Credenziali errate!"}}), 401

    session.clear()

    if remember:
        # l'utente ha selezionata "Remember me", viene creato un token con durata maggiore
        expires = timedelta(days=30)
        current_app.permanent_session_lifetime = timedelta(days=30)
    else:
        expires = timedelta(hours=2)

    session["user_id"] = user.blockChainId
    session["role"] = user.role.value

    additional_info = {
        "name": user.name,
        "surname": user.surname,
        "email": user.email,
        "role": user.role.value,
        "taxCode": user.codiceFiscale if user.role == UserRoles.SELLER else None,
    }
    user_data = {
        "id": user.blockChainId,
        "role": user.role.value,
        "email": user.email,
        "taxCode": user.codiceFiscale if user.role == UserRoles.SELLER else None,
    }

    if user.role == UserRoles.SELLER:
        session["taxCode"] = user.codiceFiscale

    access_token = create_access_token(
        identity=user_data, additional_claims=additional_info, expires_delta=expires
    )

    current_app.logger.info(
        f"USER LOGGED IN: {email=}, {user.blockChainId=}, {user.role=}, expires in {expires}"
    )

    return jsonify({"status": "success", "data": {"authorization": access_token}}), 200


@api_auth.route("/logout", methods=["POST", "GET"])
@jwt_required()
def logout():
    session.clear()

    return jsonify({"status": "success", "data": {"message": "Log out correttamente!"}}), 200
