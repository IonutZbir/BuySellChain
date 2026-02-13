import enum
from datetime import datetime
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
    
    __tablename__ = "user"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    surname: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    birthday: Mapped[Date] = mapped_column(Date, nullable=False)
    cellularNumber: Mapped[str] = mapped_column(String(16), nullable=False)
    role: Mapped[UserRoles] = mapped_column(Enum(UserRoles), default=UserRoles.BIDDER, nullable=False)
    passwordHash: Mapped[str] = mapped_column(String(60), nullable=False)
    lastLoginAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


# class Auction:
# class Bid:
class Asset:
    def __init__(self, parametri):
        pass
    # gestione percoso immagine
    # def get_url_immagine():
    