from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.data.database import Base


class GameResult(Base):
    __tablename__ = "game_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    winner = Column(String(20), nullable=False)
    played_at = Column(DateTime, server_default=func.now())
