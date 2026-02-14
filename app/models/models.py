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
    
    #id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    blockChainId: Mapped[str] = mapped_column(String(64),primary_key=True, unique=True, nullable=False) 
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    surname: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    birthday: Mapped[Date] = mapped_column(Date, nullable=False)
    cellularNumber: Mapped[str] = mapped_column(String(16), nullable=False)
    role: Mapped[UserRoles] = mapped_column(Enum(UserRoles), default=UserRoles.BIDDER, nullable=False)
    passwordHash: Mapped[str] = mapped_column(String(60), nullable=False)
    lastLoginAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Genera un blockChainId unico per l'utente, usando email + uuid4
        unique_string = f"{self.email}-{uuid4()}" 
        self.blockChainId = sha256(unique_string.encode()).hexdigest()[:64]  # Prendi i primi 64 caratteri dell'hash

# class Auction:
# class Bid:
class Asset:
    def __init__(self, parametri):
        pass
    # gestione percoso immagine
    # def get_url_immagine():
