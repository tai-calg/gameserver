
from enum import Enum
from enum import IntEnum


from fastapi import Depends, FastAPI, HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import BIGINT

from . import model
from .model import RoomInfo, SafeUser, RoomUser, LiveDifficulty, JoinRoomResult,\
    WaitRoomStatus, ResultUser


app = FastAPI()

# Sample APIs



@app.get("/")
async def root():
    return {"message": "Hello World"}


# User APIs


### Request and Response Models ###


class UserCreateRequest(BaseModel):
    user_name: str
    leader_card_id: int


class UserCreateResponse(BaseModel):  # ここでjson型にしている（BaseModelによって）
    user_token: str
    
    
class RoomCreateRequest(BaseModel):
    live_id: int
    select_difficulty: LiveDifficulty 
    # json とmustで同じ名前にする必要あり
    
    
class RoomCreateResponse(BaseModel):  # ここでjson型にしている.ここでの変数名がjsonのキーになる
    room_id: int
    

class RoomListRequest(BaseModel):
    live_id: int


class RoomListResponse(BaseModel):
    room_info_list: list[RoomInfo]


class JoinRoomRequest(BaseModel):
    room_id: int
    select_difficulty: LiveDifficulty


class JoinRoomResponse(BaseModel):
    join_room_result: JoinRoomResult
    

class WaitRoomRequest(BaseModel):
    room_id: int


class WaitRoomResponse(BaseModel):
    status: WaitRoomStatus
    room_user_list: list[RoomUser]


class GameStartRequest(BaseModel):
    room_id: int


class GameStartResponse(BaseModel):
    None


class GameEndRequest(BaseModel):
    room_id: int
    judge_count_list: list[int]
    score: int


class GameEndResponse(BaseModel):
    None


class GameResultRequest(BaseModel):
    room_id: int


class GameResultResponse(BaseModel):
    result_user_list: list[ResultUser]


class GameLeaveRequest(BaseModel):
    room_id: int


class GameLeaveResponse(BaseModel):
    None


### end of Request and Response Models ###



@app.post("/user/create", response_model=UserCreateResponse)
def user_create(req: UserCreateRequest):
    """新規ユーザー作成"""
    token = model.create_user(req.user_name, req.leader_card_id)
    return UserCreateResponse(user_token=token)


bearer = HTTPBearer()


def get_auth_token(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    assert cred is not None
    if not cred.credentials:
        raise HTTPException(status_code=401, detail="invalid credential")
    return cred.credentials


@app.get("/user/me", response_model=SafeUser)
def user_me(token: str = Depends(get_auth_token)):
    user = model.get_user_by_token(token)
    if user is None:
        raise HTTPException(status_code=404)
    # print(f"user_me({token=}, {user=})")
    return user


class Empty(BaseModel):
    pass


@app.post("/user/update", response_model=Empty)
def update(req: UserCreateRequest, token: str = Depends(get_auth_token)):
    """Update user attributes"""
    # print(req)
    model.update_user(token, req.user_name, req.leader_card_id)
    return {}


# room/create
@app.post("/room/create", response_model=RoomCreateResponse)
def room_create(req: RoomCreateRequest, token: str = Depends(get_auth_token)):
    model.create_room(req.live_id, req.select_difficulty, token)
    room_id = model.get_last_insert_id()
    print("ルームIDは", room_id)
   
    return RoomCreateResponse(room_id=room_id)


@app.post("/room/list", response_model=RoomListResponse)
def get_room_list(req: RoomListRequest):
    _room_info_list: list[RoomInfo] = model.get_room_list(req.live_id)
    return RoomListResponse(room_info_list=_room_info_list)


@app.post("/room/join", response_model=JoinRoomResponse)
def join_room(req: JoinRoomRequest, token: str = Depends(get_auth_token)):
    join_room_result: JoinRoomResult = model.join_room(req.room_id, int(req.select_difficulty), False, token) 
    # :Result[Ok(), Err(JoinRoomError)]
    return JoinRoomResponse(join_room_result=join_room_result)


@app.post("/room/wait", response_model=WaitRoomResponse)
def wait_in_room(req: WaitRoomRequest):  # DOING
    """ルーム待機中（ポーリング）。APIの結果でゲーム開始がわかる。 クライアントはn秒間隔で投げる想定。"""
    status: WaitRoomStatus = model.pooling_wait(req.room_id)
    room_user_list: list[RoomUser] = model.get_room_user_list(req.room_id)
    return WaitRoomResponse(status=status, room_user_list=room_user_list)
