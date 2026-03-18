from fastapi import APIRouter

from ..data.models import get_recent_results

router = APIRouter()


@router.get("/")
async def get_results():
    results = get_recent_results()
    return {
        "results": [
            {
                "id": r.get("id"),
                "winner": r.get("winner"),
                "played_at": str(r.get("played_at")),
            }
            for r in results
        ]
    }
