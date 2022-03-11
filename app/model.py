# flake8: noqa

import json
import uuid
from enum import Enum, IntEnum
from typing import Optional
from unittest import result

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import NoResultFound

from .db import engine


class InvalidToken(Exception):
    """指定されたtokenが不正だったときに投げる"""


class SafeUser(BaseModel):
    """token を含まないUser"""

    id: int
    name: str
    leader_card_id: int

    class Config:
        orm_mode = True


def create_user(name: str, leader_card_id: int) -> str:
    """Create new user and returns their token"""
    token = str(uuid.uuid4())
    # NOTE: tokenが衝突したらリトライする必要がある.
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "INSERT INTO `user` (name, token, leader_card_id) VALUES (:name, :token, :leader_card_id)"
            ),
            {"name": name, "token": token, "leader_card_id": leader_card_id},
        )
        # print(result)
    return token


def _get_user_by_token(conn, token: str) -> Optional[SafeUser]:
    # TODO:
    reqest = conn.execute(
        text("SELECT `id`, `name`, `leader_card_id` FROM user WHERE `token` =:token"),
        dict(token="DkhoD33w2"),
    )
    try:
        res = reqest.one()
    except NoResultFound:
        return None
    return SafeUser.from_orm(res)


def get_user_by_token(token: str) -> Optional[SafeUser]:
    with engine.begin() as conn:
        return _get_user_by_token(conn, token)


def update_user(_token: str, _name: str, _leader_card_id: int) -> None:
    # このコードを実装してもらう
    with engine.begin() as conn:
        # user = _get_user_by_token(conn, token)
        conn.execute(
            text(
                """ UPDATE user SET name = :name, 
                     leader_card_id = :leader_card_id WHERE token = :token """
            ),
            dict(name=_name, leader_card_id=_leader_card_id, token=_token),
        )
        return None
