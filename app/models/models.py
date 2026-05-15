import enum
from datetime import datetime
from hashlib import sha256
from uuid import uuid4
from sqlalchemy import String, Date, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
import hmac
import os
from base64 import b64encode, b64decode
from string import hexdigits
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from flask import current_app

# Importa l'istanza db che hai creato in app/__init__.py
from app import db


class UserRoles(enum.Enum):
    ADMIN = "admin"
    SELLER = "seller"
    BIDDER = "bidder"


class AuctionStatus(enum.Enum):
    LOCKED = "locked"  # per validazione delle offerte, quando è LOCKED non si possono più fare offerte, e si aspetta che venga aggiornata a CLOSED o CANCELLED
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"  # asta cancellata, non più attiva, ma non conclusa (es: venditore ritira l'asta prima della scadenza, oppure asta chiusa senza vincitori, ecc)
    SCHEDULED = "scheduled"  # asta programmata, con startTime nel futuro, non ancora attiva


class BidStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class AssetType(enum.Enum):
    VILLA = "villa"
    FLAT = "flat"
    COTTAGE = "cottage"
    BUNGALOW = "bungalow"
    FURNITURE = "furniture"
    DETACHED_HOUSE = "detached_house"
    OTHER = "other"

    @classmethod
    def from_value(cls, value: str):
        """Create enum from string value"""
        for member in cls:
            print(f"Checking {member.value} against {value}")  # Debug print
            if member.value == value:
                print(f"Matched {member} for value '{value}'")  # Debug print
                return member
        raise ValueError(f"No AssetType with value '{value}'")


class AssetStatus(enum.Enum):
    ACTIVE = "active" # asset disponibile, non in asta
    LOCKED = "locked"  # asset bloccato, non più disponibile per essere messo all'asta, ma non ancora venduto (es: asset in asta, ma asta non ancora conclusa)
    SOLD = "sold"

class LogType(enum.Enum):
    ALERT = "ALERT"
    INFO = "INFO"


class User:
    """Classe che rappresenta un utente memorizzato nella blockchain."""

    def __init__(
        self,
        name: str,
        surname: str,
        email: str,
        birthday,
        cellularNumber: str,
        passwordHash: str,
        codiceFiscale: str = None,
        role: UserRoles = UserRoles.BIDDER,
        blockChainId: str = None,
        lastLoginAt=None,
        created_at=None,
    ):
        self.name = name
        self.surname = surname
        self.email = email
        self.birthday = birthday
        self.cellularNumber = cellularNumber
        self.passwordHash = passwordHash
        self.codiceFiscale = codiceFiscale
        self.role = role if isinstance(role, UserRoles) else UserRoles(role)
        self.created_at = created_at or datetime.now()
        self.lastLoginAt = lastLoginAt or datetime.now()
        self.blockChainId = blockChainId or self._generate_blockchain_id()

    def _generate_blockchain_id(self) -> str:
        unique_string = f"{self.email}-{uuid4()}"
        return hmac.new(
            os.getenv("HMAC_SECRET_KEY").encode(), unique_string.encode(), sha256
        ).hexdigest()

    @classmethod
    def from_json(cls, data: dict):
        birthday = data.get("birthday")
        created_at = data.get("created_at")
        last_login_at = data.get("lastLoginAt")

        if isinstance(birthday, str):
            try:
                birthday = datetime.fromisoformat(birthday).date()
            except ValueError:
                pass

        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                pass

        if isinstance(last_login_at, str):
            try:
                last_login_at = datetime.fromisoformat(last_login_at)
            except ValueError:
                pass

        return cls(
            name=data.get("name"),
            surname=data.get("surname"),
            email=data.get("email"),
            birthday=birthday,
            cellularNumber=data.get("cellularNumber"),
            passwordHash=data.get("passwordHash"),
            codiceFiscale=data.get("codiceFiscale"),
            role=UserRoles(data.get("role", UserRoles.BIDDER.value)),
            blockChainId=data.get("blockChainId"),
            lastLoginAt=last_login_at,
            created_at=created_at,
        )

    def to_json(self) -> dict:
        return {
            "blockChainId": self.blockChainId,
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "cellularNumber": self.cellularNumber,
            "codiceFiscale": self.codiceFiscale,
            "role": self.role.value,
            "passwordHash": self.passwordHash,
            "lastLoginAt": self.lastLoginAt.isoformat() if self.lastLoginAt else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Auction:
    """Classe che rappresenta un'asta memorizzata nella blockchain"""

    def __init__(
        self,
        asset_id: str,
        seller_id: str,
        start_time: datetime,
        end_time: datetime,
        starting_price: float,
        min_incr: float,
        status: AuctionStatus = AuctionStatus.ACTIVE,
    ):
        self.id = self._generate_id(
            asset_id, seller_id, start_time, end_time, starting_price, min_incr
        )
        self.asset_id = asset_id
        self.seller_id = seller_id
        self.start_time = start_time
        self.end_time = end_time
        self.starting_price = starting_price
        self.min_incr = min_incr
        self.high_bid_id = None
        self.high_bid_amount = None
        self.bid_count = 0
        self.status = status

    def _generate_id(
        self,
        asset_id: str,
        seller_id: str,
        start_time: datetime,
        end_time: datetime,
        starting_price: float,
        min_incr: float,
    ) -> str:
        combined_string = f"{asset_id}-{seller_id}-{start_time.isoformat()}-{end_time.isoformat()}-{starting_price}-{min_incr}-{uuid4()}"

        print(f"Generating auction ID with combined string: {combined_string}")  # Debug print
        return hmac.new(
            os.getenv("HMAC_SECRET_KEY").encode(), combined_string.encode(), sha256
        ).hexdigest()

    def get_id(self) -> str:
        return self.id

    def __repr__(self) -> str:
        return f"Auction(id={self.id}, asset_id={self.asset_id}, seller_id={self.seller_id}, status={self.status})"

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "seller_id": self.seller_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "starting_price": self.starting_price,
            "min_incr": self.min_incr,
            "high_bid_id": self.high_bid_id,
            "high_bid_amount": self.high_bid_amount,
            "bid_count": self.bid_count,
            "status": self.status,
        }


class Bid:
    """Classe che rappresenta un'offerta (bid) memorizzata nella blockchain"""

    def __init__(
        self,
        auction_id: str,
        bidder_id: str,
        bid_amount: float,
        status: BidStatus = BidStatus.PENDING,
        reason: str = None,
    ):
        self.id = self._generate_id(auction_id, bidder_id, bid_amount, status, reason)
        self.auction_id = auction_id
        self.bidder_id = bidder_id
        self.bid_amount = bid_amount
        self.timestamp = datetime.now()
        self.status = status
        self.reason = reason

    def _generate_id(
        self,
        auction_id: str,
        bidder_id: str,
        bid_amount: float,
        status: BidStatus,
        reason: str = None,
    ) -> str:
        combined_string = f"{auction_id}-{bidder_id}-{bid_amount}-{status}-{reason if reason else 'None'}-{uuid4()}"
        print(f"Generating bid ID with combined string: {combined_string}")  # Debug print
        return hmac.new(
            os.getenv("HMAC_SECRET_KEY").encode(), combined_string.encode(), sha256
        ).hexdigest()

    def get_id(self) -> str:
        return self.id

    def __repr__(self) -> str:
        return f"Bid(id={self.id}, auction_id={self.auction_id}, bidder_id={self.bidder_id}, bid_amount={self.bid_amount})"

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "auction_id": self.auction_id,
            "bidder_id": self.bidder_id,
            "bid_amount": self.bid_amount,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "reason": self.reason,
        }


class Asset:
    """Classe che rappresenta un asset memorizzato nella blockchain"""

    def __init__(
        self,
        owner_id: str,
        title: str,
        description: str,
        asset_type: AssetType,
        size: float,
        price: float,
        location: str,
        picture=None,
    ):
        self.id = self._generate_id(owner_id, title, description, asset_type, size, price, location)
        self.owner_id = owner_id
        self.title = title
        self.description = description
        self.asset_type = asset_type.value
        self.size = size
        self.price = price
        self.location = location
        self.created_at = datetime.now()
        self.status = AssetStatus.ACTIVE
        self.current_auction_id = None
        self.picture = picture

    def _generate_id(
        self,
        owner_id: str,
        title: str,
        description: str,
        asset_type: AssetType,
        size: float,
        price: float,
        location: str,
    ) -> str:
        combined_string = f"{owner_id}-{title}-{description}-{asset_type.value}-{size}-{price}-{location}-{uuid4()}"
        print(f"Generating asset ID with combined string: {combined_string}")  # Debug print
        return hmac.new(
            os.getenv("HMAC_SECRET_KEY").encode(), combined_string.encode(), sha256
        ).hexdigest()

    def get_id(self) -> str:
        return self.id

    def __repr__(self) -> str:
        return f"Asset(id={self.id}, title={self.title}, owner_id={self.owner_id}, status={self.status.value})"

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "title": self.title,
            "description": self.description,
            "asset_type": self.asset_type,
            "size": self.size,
            "price": self.price,
            "location": self.location,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "current_auction_id": self.current_auction_id,
            "picture": self.picture.filename if self.picture else None,
        }

class Messages(enum.Enum):
    ACCESSO_NEGATO = "Accesso negato"
    ACCESSO_RIUSCITO = "Accesso riuscito"
    PREFIX_ACCESSO_NON_AUTORIZZATO = "Accesso non autorizzato -> "
    ECCESSO_RICHIESTE_LOGIN = "Eccesso di richieste di login" # DA IMPLEMENTARE CON SISTEMA DI RATE LIMITING (FORSE)
    NUOVO_UTENTE_REGISTRATO = "Nuovo utente registrato"
    REGISTRAZIONE_ASTA_BL = "Asta registrata su Blockchain"
    REGISTRAZIONE_ASSET_BL = "Asset registrato su Blockchain"
    OFFERTA_REGISTRATA_BL = "Offerta registrata su Blockchain"
    PREFIX_GET_ADMIN_ROUTE = "Accesso a route admin -> "

class Log:
    """Classe che definisce un Log presente nella Blockchain con cifratura AES-GCM"""

    @staticmethod
    def _get_aes_key() -> bytes:
        """Restituisce una chiave AES valida a partire dalla configurazione."""
        raw_key = current_app.config.get("AES_SECRET_KEY")

        if not raw_key:
            raise ValueError("AES_SECRET_KEY non configurata")

        if isinstance(raw_key, bytes):
            key_bytes = raw_key
        else:
            raw_key = str(raw_key).strip()
            if len(raw_key) % 2 == 0 and all(char in hexdigits for char in raw_key):
                key_bytes = bytes.fromhex(raw_key)
            else:
                key_bytes = raw_key.encode()

        if len(key_bytes) in (16, 24, 32):
            return key_bytes

        return sha256(key_bytes).digest()
    
    @staticmethod
    def _encrypt_field(data: str) -> str:
        """Cifra un campo usando AES-GCM con nonce casuale e ritorna base64"""
        key = Log._get_aes_key()
        nonce = get_random_bytes(16)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())
        # Concatena nonce + ciphertext + tag e converti a base64
        encrypted_data = nonce + ciphertext + tag
        return b64encode(encrypted_data).decode('utf-8')
    
    @staticmethod
    def decrypt_field(encrypted_data_b64: str) -> str:
        """Decifra un campo da base64 usando AES-GCM"""
        encrypted_data = b64decode(encrypted_data_b64.encode('utf-8'))
        key = Log._get_aes_key()
        # Estrai nonce (primi 16 bytes), ciphertext (tutto tranne ultimi 16), tag (ultimi 16)
        nonce = encrypted_data[:16]
        ciphertext = encrypted_data[16:-16]
        tag = encrypted_data[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode()
    
    def __init__(
        self,
        from_ip: str,
        level: LogType,
        method: str,
        description: Messages | str,
        user_agent: str,
    ):
        self.id = self._generate_id(description, from_ip, level, user_agent, method)
        self.description = description.value if isinstance(description, Messages) else description
        self.method = method
        self.created_at = datetime.now()
        self.level = level.value
        self.from_ip = self._encrypt_field(from_ip)
        self.user_agent = self._encrypt_field(user_agent)

    def _generate_id(
        self,
        description: str,
        from_ip: str,
        level: LogType,
        user_agent: str,
        method: str,
    ) -> str:
        combined_string = f"{description}-{level.value}-{from_ip}-{user_agent}-{method}-{uuid4()}"
        return hmac.new(
            os.getenv("HMAC_SECRET_KEY").encode(), combined_string.encode(), sha256
        ).hexdigest()
    
    def get_id(self) -> str:
        return self.id

    def to_json(self) -> dict:
        #from_ip_decrypted = self._decrypt_field(self.from_ip)
        #user_agent_decrypted = self._decrypt_field(self.user_agent)
        return {
            "id": self.id,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "level": self.level,
            "from_ip": self.from_ip,
            "user_agent": self.user_agent,
            "method": self.method,
        }