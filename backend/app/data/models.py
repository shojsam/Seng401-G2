from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func

from app.data.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    winner = Column(Enum("reformers", "exploiters"), nullable=False)
    player_count = Column(Integer, nullable=False)
    sustainable_enacted = Column(Integer, default=0)
    exploiter_enacted = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class MatchPlayer(Base):
    __tablename__ = "match_players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum("reformer", "exploiter"), nullable=False)


class EnactedPolicy(Base):
    __tablename__ = "enacted_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    round_number = Column(Integer, nullable=False)
    policy_name = Column(String(100), nullable=False)
    policy_type = Column(Enum("sustainable", "exploitative"), nullable=False)
