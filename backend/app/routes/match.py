from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/history")
async def get_match_history():
    # TODO: return current user's past matches from MySQL
    raise HTTPException(status_code=501, detail="Not implemented")
