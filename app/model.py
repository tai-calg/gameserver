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
        
class LiveDifficulty(IntEnum):
    normal = 1
    hard = 2
class RoomInfo(BaseModel):
    room_id: int
    live_id: int
    joined_user_count: int
    max_user_count: int

class RoomUser(BaseModel):
    user_id: int
    name:str 
    leader_card_id: int
    select_difficulty:LiveDifficulty
    is_me: bool
    is_host:bool
    


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
        dict(token=token),
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

def create_room(liveid: int, select_difi: LiveDifficulty):
    """Create new room and returns its id"""
    token = str(uuid.uuid4()) # 同じ設定値のルームが建てるようになるためにトークンを作る
    with engine.begin() as conn:
        result = conn.execute(
            text("INSERT INTO `room` (select_difficulty , live_id, token) VALUES (:select_difficulty, :live_id, :token)"),
            dict(live_id=liveid, select_difficulty=int(select_difi), token=token),
        )
        #room_id = result.lastrowid
        #print(room_id)
        return

def get_last_insert_id()-> int:
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT LAST_INSERT_ID()"),
        )
        return result.scalar()