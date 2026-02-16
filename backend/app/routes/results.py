from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.data.database import get_db
from app.data.models import GameResult

router = APIRouter()


@router.get("/")
async def get_results(db: Session = Depends(get_db)):
    results = db.query(GameResult).order_by(GameResult.played_at.desc()).all()
    return {
        "results": [
            {"id": r.id, "winner": r.winner, "played_at": str(r.played_at)}
            for r in results
        ]
    }
