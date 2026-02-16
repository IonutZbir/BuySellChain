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
            if member.value == value:
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
        unique_string = f"{self.email}-{uuid4()}"
        self.blockChainId = sha256(unique_string.encode()).hexdigest()


# class Auction:
# class Bid:
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
    ):
        self.id = self._generate_id(owner_id, title, description, asset_type, size, price, location)
        self.owner_id = owner_id
        self.title = title
        self.description = description
        self.asset_type = asset_type
        self.size = size
        self.price = price
        self.location = location
        self.created_at = datetime.now()
        self.status = AssetStatus.ACTIVE
        self.current_auction_id = None

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
        return sha256(combined_string.encode()).hexdigest()

    def get_id(self) -> str:
        return self.id;

    def __repr__(self) -> str:
        return f"Asset(id={self.id}, title={self.title}, owner_id={self.owner_id}, status={self.status.value})"

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "title": self.title,
            "description": self.description,
            "asset_type": self.asset_type.value,
            "size": self.size,
            "price": self.price,
            "location": self.location,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "current_auction_id": self.current_auction_id,
        }
