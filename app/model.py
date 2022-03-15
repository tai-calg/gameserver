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


class JoinRoomResult(IntEnum):
    Ok = 1,
    RoomFull = 2,
    Disbanded = 3,
    OtherError = 4


class WaitRoomStatus(IntEnum):
    Waiting = 1,
    LiveStart = 2,
    Dissolution = 3

class RoomInfo(BaseModel):
    room_id: int
    live_id: int
    joined_user_count: int
    max_user_count: int
    class Config:
        orm_mode = True

class RoomUser(BaseModel):
    user_id: int
    user_name:str 
    leader_card_id: int
    select_difficulty:LiveDifficulty
    is_me: bool
    is_host:bool


class ResultUser(BaseModel):
    user_id: int
    judge_count_list: list[int]
    score: int


MAX_USER_COUNT = 4

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

def get_room_id(room_token:str) -> int:
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT room_id FROM room WHERE token = :room_token"),
            dict(room_token=room_token),
        )
        return result.scalar()
    

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

def create_room(liveid: int, select_difi: LiveDifficulty)-> str:
    """Create new room and returns its id"""
    room_token = str(uuid.uuid4()) # 同じ設定値のルームが建てるようになるためにトークンを作る
    with engine.begin() as conn:
        result = conn.execute(
            text("""INSERT INTO `room` (select_difficulty , live_id, token, joined_user_count, max_user_count) 
                 VALUES (:select_difficulty, :live_id, :token, :joined_user_count, :max_user_count)"""),
            dict(live_id=liveid, select_difficulty=int(select_difi), token=room_token, \
                 joined_user_count=1, max_user_count=MAX_USER_COUNT),
        )

        return room_token

def get_last_insert_id()-> int:
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT LAST_INSERT_ID()"),
        )
        return result.scalar()


def get_room_list(live_id: int)-> list[RoomInfo]:
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT room_id, live_id, joined_user_count, max_user_count FROM room WHERE live_id = :live_id "),
            dict(live_id=live_id),
        )
        return [RoomInfo.from_orm(res) for res in result]


def join_room(room_id: int, select_difi:int , token: str)-> JoinRoomResult:
    with engine.begin() as conn:
        result = conn.execute(
            text(""" SELECT joined_user_count FROM room WHERE room_id = :room_id """),
            dict(room_id=room_id),
        )
        if result.one()[0] < 4 :
            # joinする
            conn.execute(
                text(""" UPDATE room SET joined_user_count = joined_user_count + 1 WHERE room_id = :room_id"""),  # ayashii
                dict(room_id=room_id),
            )
            
            create_user_info(user_info, room_id)
            return JoinRoomResult.Ok
        else:
            return JoinRoomResult.RoomFull  #TODO: disbanded , other errorのコーディングを後でやる
            

def create_user_info(userinfo: RoomUser, room_id: int)-> None:
    with engine.begin() as conn:
        result = conn.execute(
            text("""INSERT INTO `user_info` (user_id, room_id, leader_card_id , select_difficulty, is_me, is_host) 
                 VALUES (:user_id, :room_id, :leader_card_id, :select_difficulty, :is_me, :is_host)"""),
            dict(user_id=userinfo.user_id, room_id=room_id,leader_card_id = userinfo.leader_card_id , \
                select_difficulty=userinfo.select_difficulty, \
                 is_me=userinfo.is_me, is_host=userinfo.is_host),
        )
        return



def register_roomuser_ref(room_id: int , token: str):
    with engine.begin() as conn:
        conn.execute(
            text("""UPDATE room_user_token SET token1 = :token WHERE room_id = :room_id"""),
            # token1だけでなく、順に走査してnullになってる箇所に挿入したい. mysqlの命令調べなくては
            # room_user_token TABLE はトークンを参照してその部屋にいる人の user TABLEのデータを取得するためのテーブル
            dict(token=token, room_id=room_id),
        )
        return


def get_room_users(room_id: int)-> list[RoomUser]:
    # room_user_tokenに登録されてるtokenを全部取得して、user　TABLEのgetしてくる。そしてRoomUser型にしてリストで返す
    with engine.begin() as conn:  
        # result = conn.execute(
        #     text("""SELECT user_id, room_id, leader_card_id, select_difficulty, is_me, is_host FROM user_info"""),
        # )
        return [RoomUser.from_orm(res) for res in result]

    

def pooling_wait(room_id: int)-> WaitRoomStatus:  #DOING
    """ホストが開始ボタンを押せばゲーム開始でEnumステータスが変更される。その変更をホスト以外がこの関数で受け取る。"""

    with engine.begin() as conn:
        result = conn.execute(
            text("""SELECT joined_user_count FROM room WHERE room_id = :room_id"""),
            dict(room_id=room_id),
        )
        if result.one()[0] == 4:
            return WaitRoomStatus.LiveStart
        else:
            return WaitRoomStatus.Waiting