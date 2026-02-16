from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(req: RegisterRequest):
    # TODO: hash password, insert into MySQL
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/login")
async def login(req: LoginRequest):
    # TODO: verify credentials, return JWT
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/me")
async def get_current_user():
    # TODO: decode JWT, return user info
    raise HTTPException(status_code=501, detail="Not implemented")
