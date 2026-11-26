import hashlib
import hmac
import time

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from src.config import settings
from src.enums import Role

router = APIRouter(prefix="/auth")
bearer = HTTPBearer(auto_error=False)
USERS = {
    "editor": ("黄曼", Role.EDITOR),
    "reviewer": ("童雨", Role.REVIEWER),
    "reader": ("陈嘉", Role.READER),
}


class Login(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)


def identity(username):
    name, role = USERS[username]
    return {"username": username, "name": name, "role": role}


@router.post("/login")
def login(form: Login):
    if form.username not in USERS or not hmac.compare_digest(
        hashlib.sha256(form.password.encode()).digest(),
        hashlib.sha256(settings.demo_password.encode()).digest(),
    ):
        raise HTTPException(401, "账号或密码不正确")
    payload = identity(form.username)
    token = jwt.encode(
        {"sub": form.username, "exp": int(time.time()) + 8 * 3600},
        settings.token_key,
        algorithm="HS256",
    )
    return {"token": token, "user": payload}


def current(token: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        if token is None:
            raise ValueError("missing token")
        username = jwt.decode(token.credentials, settings.token_key, algorithms=["HS256"])["sub"]
        return identity(username)
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(401, "请重新登录")


def allow(*roles):
    def permitted(user=Depends(current)):
        if user["role"] not in roles:
            raise HTTPException(403, "当前角色无权执行此操作")
        return user

    return permitted


@router.get("/me")
def me(user=Depends(current)):
    return user
