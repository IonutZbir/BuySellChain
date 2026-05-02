import enum
from datetime import datetime
from hashlib import sha256
from uuid import uuid4
from sqlalchemy import String, Date, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
import hmac
import os

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
    WARNING = "WARNING"
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

class Log:
    """Classe che definisce un Log presente nella Blockchain"""

    def __init__(
        self,
        from_ip: str,
        level: LogType,
        description: str,
        user_agent: str,
    ):
        self.id = self._generate_id(description, from_ip, level, user_agent)
        self.description = description
        self.created_at = datetime.now()
        self.level = level if isinstance(level, LogType) else LogType.OK
        self.from_ip = from_ip
        self.user_agent = user_agent

    def _generate_id(
        self,
        description: str,
        from_ip: str,
        level: LogType,
        user_agent: str,
    ) -> str:
        combined_string = f"{description}-{level.value}-{from_ip}-{user_agent}-{uuid4()}"
        return hmac.new(
            os.getenv("HMAC_SECRET_KEY").encode(), combined_string.encode(), sha256
        ).hexdigest()

    def get_id(self) -> str:
        return self.id

    def __repr__(self) -> str:
        return f"Log(id={self.id}, description={self.description}, from_ip={self.from_ip}, level={self.level.value})"

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "level": self.level.value,
            "from_ip": self.from_ip,
            "user_agent": self.user_agent,
        }