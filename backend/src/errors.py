from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder


def missing(label, code):
    return HTTPException(404, f"未找到{label} {code}")


def conflict(code, reason, **context):
    return HTTPException(409, jsonable_encoder({"code": code, "message": reason, **context}))
