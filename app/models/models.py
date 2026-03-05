import enum
from datetime import datetime
from hashlib import sha256
from uuid import uuid4
from sqlalchemy import String, Date, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

# Importa l'istanza db che hai creato in app/__init__.py
from app import db


class UserRoles(enum.Enum):
    ADMIN = "admin"
    SELLER = "seller"
    BIDDER = "bidder"

class AuctionStatus(enum.Enum):
    LOCKED = "locked" #per validazione delle offerte, quando è LOCKED non si possono più fare offerte, e si aspetta che venga aggiornata a CLOSED o CANCELLED
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled" #asta cancellata, non più attiva, ma non conclusa (es: venditore ritira l'asta prima della scadenza, oppure asta chiusa senza vincitori, ecc)

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
    ACTIVE = "active"
    SOLD = "sold"


class User(db.Model):

    # In questa classe sto definendo lo schem per la tabella User. Sto usando un ORM (SQL Alchemy), invece
    # di usare SQL puro (è piu semplice e pulito :) ).

    # Nota: usando bcrypt, lui concatena il salt direttamente all'hash della password, non è quindi
    # necessario definire una colonna apposita per il salt.
    # Il formato bcrypt è $<id>$<cost>$<salt><digest> dove
    # $<id>$: l'algoritmo
    # $<cost>$: il costo per la creazione dell'hash
    # La lunghezza totale è di 60 byte

    # Da questa definizione, usando flask migrate, viene creata in automatico la tabella user in postgres.

    # Per aggiungere utenti all'intenro del db:
    # user = User(...)
    # db.session.add(user)
    # db.session.commit()
    # Questo farà il comando SQL: INSERTO INTO user (...) VALUES (...)

    # blockChainId è un identificativo univoco che viene generato al momento della registrazione dell'utente, e viene usato per identificare l'utente all'interno della blockchain.
    # Viene generato come hash dei dati dell'utente (es: email) + un valore random (es: uuid4), in modo da garantire l'unicità e la sicurezza dell'identificativo.

    __tablename__ = "user"

    # id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codiceFiscale: Mapped[str] = mapped_column(String(16), unique=True, nullable=True)
    blockChainId: Mapped[str] = mapped_column(
        String(64), primary_key=True, unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    surname: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    birthday: Mapped[Date] = mapped_column(Date, nullable=False)
    cellularNumber: Mapped[str] = mapped_column(String(16), nullable=False)
    role: Mapped[UserRoles] = mapped_column(
        Enum(UserRoles), default=UserRoles.BIDDER, nullable=False
    )
    passwordHash: Mapped[str] = mapped_column(String(60), nullable=False)
    lastLoginAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Genera un blockChainId unico per l'utente, usando email + uuid4
        unique_string = f"{self.email}-{uuid4()}" # cambia con HMAC!!!
        self.blockChainId = sha256(unique_string.encode()).hexdigest()


class Auction:
    """Classe che rappresenta un'asta memorizzata nella blockchain"""
    """
    value = {
        "assetId": assetId,
        "sellerId": sellerId,
        "startTime": data.get("startTime"),
        "endTime": data.get("endTime"),
        "startingPrice": data.get("startingPrice"),
        "minIncr": data.get("minIncr"),
        "highBidId": highBidId,
        "highBidAmount": highBidAmount,
        "bidCount": bidCount,
        "status": status,
    }
    """
    def __init__(
        self,
        asset_id: str,
        seller_id: str,
        start_time: datetime,
        end_time: datetime,
        starting_price: float,
        min_incr: float

    ):
        self.id = self._generate_id(asset_id, seller_id, start_time, end_time, starting_price, min_incr)
        self.asset_id = asset_id
        self.seller_id = seller_id
        self.start_time = start_time
        self.end_time = end_time
        self.starting_price = starting_price
        self.min_incr = min_incr
        self.high_bid_id = None
        self.high_bid_amount = None
        self.bid_count = 0
        self.status = AuctionStatus.ACTIVE

    def _generate_id(
        self,
        asset_id: str,
        seller_id: str,
        start_time: datetime,
        end_time: datetime,
        starting_price: float,
        min_incr: float,
    ) -> str:
        combined_string = f"{asset_id}-{seller_id}-{start_time.isoformat()}-{end_time.isoformat()}-{starting_price}-{min_incr}-{uuid4()}" #HMAC!!!
        print(f"Generating auction ID with combined string: {combined_string}")  # Debug print
        return sha256(combined_string.encode()).hexdigest()

    def get_id(self) -> str:
        return self.id
    
    def __repr__(self) -> str:
        return f"Auction(id={self.id}, asset_id={self.asset_id}, seller_id={self.seller_id}, status={self.status.value})"

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
            "status": self.status.value,
        }
class Bid:
    """Classe che rappresenta un'offerta (bid) memorizzata nella blockchain"""

    """
    value = {
        "auctionId": auctionId,
        "bidderId": bidderId,
        "amount": amount,
        "timestamp": timestamp,
        "status": status,
        "reason": reason
    }
    """
    def __init__(
        self,
        auction_id: str,
        bidder_id: str,
        bid_amount: float,
        status: str = "pending",
        reason: str = None
    ):
        self.id = self._generate_id(auction_id, bidder_id, bid_amount,status,reason)
        self.auction_id = auction_id
        self.bidder_id = bidder_id
        self.bid_amount = bid_amount
        self.timestamp = datetime.now()
        self.status = status  # pending, accepted, rejected
        self.reason = reason  # reason for rejection, if applicable

    def _generate_id(
        self,
        auction_id: str,
        bidder_id: str,
        bid_amount: float,
        status: str,
        reason: str = None
    ) -> str:
        combined_string = f"{auction_id}-{bidder_id}-{bid_amount}-{status}-{reason if reason else 'None'}-{uuid4()}" # HMAC!!!
        print(f"Generating bid ID with combined string: {combined_string}")  # Debug print
        return sha256(combined_string.encode()).hexdigest()

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
        picture=None
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
        combined_string = f"{owner_id}-{title}-{description}-{asset_type.value}-{size}-{price}-{location}-{uuid4()}" # HMAC!!!
        print(f"Generating asset ID with combined string: {combined_string}")  # Debug print
        return sha256(combined_string.encode()).hexdigest()

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
