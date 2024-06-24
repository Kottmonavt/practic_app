import os
import json
from dotenv import load_dotenv
from supabase import create_client
from fastapi import FastAPI, HTTPException
from gotrue.errors import AuthApiError
from pydantic import BaseModel
import random

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
SECRET_KEY = os.environ.get("SECRET_KEY")

supabase = create_client(url, key)

def json_reader(file_path):
    with open(file_path, encoding="utf-8") as f:
        json_res = json.load(f)
    
    return json_res

json_signup = json_reader('./json_schemes/example_signup.json')
json_signin = json_reader('./json_schemes/example_login.json')
json_user = json_reader("./json_schemes/example_user.json")
json_session = json_reader("./json_schemes/example_session.json")

json_warning = json_reader("./json_schemes/example_warning.json")
json_user_info = json_reader("./json_schemes/example_userInfo.json")
json_get_zone = json_reader("./json_schemes/example_get_zone.json")
json_get_track_id = json_reader("./json_schemes/example_getTrackId.json")
json_get_track_info = json_reader("./json_schemes/example_get_track_info.json")

class ErrorMessage(BaseModel):
    detail: str


responses_sign_up = {
        400: {"model": ErrorMessage, "description": "Ошибка при попытке регистрации"},
        200: json_signup
    }

responses_sign_in = {
        400: {"model": ErrorMessage, "description": "Ошибка при попытке входа"},
        200: json_signin
    }

app = FastAPI()

class User(BaseModel):
    login: str
    password: str 


class warningZone(BaseModel):
    xCoord: float
    yCoord: float
    typeZone: str
    distance: float
    #secret_key: str


class userPosition(BaseModel):
    xCoord: float
    yCoord: float
    #secret_key: str


class trackInfo(BaseModel):
    user_id: str
    currentSpeed: float
    xCoord: float
    yCoord: float
    track_id: int
    #secret_key: str



# Регистрация пользователя
@app.post("/users/sign-up", responses=responses_sign_up)
async def create_user(user: User):
    
    credentials = {
    "email": user.login,
    "password": user.password
    }
    
    # TODO добавить обработку различных исключение при регистрации
    try:
        session = supabase.auth.sign_up(credentials)
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=AuthApiError.to_dict(e)['message'])
    
    return session


@app.post("/users/sign-out", responses={400: {"model": ErrorMessage, "description": "Нет авторизованных пользователей"}})
async def log_out():
    res = supabase.auth.sign_out()
    user = supabase.auth.get_user()

    if user:
        return "success"
    else:
        raise HTTPException(status_code=400, detail="Отсутствует пользователь")


# Получение информации о текущей сесссии
@app.get("/users/session", responses={400: {"model": ErrorMessage, "description": "Текущая сессия отсуствует"},
                                                                   200: json_session})
async def get_session():
    res = supabase.auth.get_session()
    if res:
        return res
    else:
        raise HTTPException(status_code=400, detail="Сессия не начата")

    

# Получение информации о текущем пользователе 
@app.get("/users/user", responses={400: {"model": ErrorMessage, "description": "Нет авторизованных пользователей"},
                                                             200: json_user})
async def get_user():
    res = supabase.auth.get_user()
    
    if res:
        return res
    else:
        raise HTTPException(status_code=400, detail="Отсутствует пользователь")


# Вход пользователя
@app.post("/users/sign-in", responses=responses_sign_in)
async def log_in(user: User):

    credentials = {
    "email": user.login,
    "password": user.password
    }

    # TODO добавить обработку различных исключение при входе пользователя
    try:
        session = supabase.auth.sign_in_with_password(credentials)
    except AuthApiError as e:
        raise HTTPException(status_code=400, detail=AuthApiError.to_dict(e)["message"])


    return session



# Добавление записи об опасной зоне
@app.post("/warningZone/add", responses={200: json_warning})
async def add_warning_zone(warningZone: warningZone):
    x_p = warningZone.xCoord + warningZone.distance
    x_m = warningZone.xCoord - warningZone.distance
    y_p = warningZone.yCoord + warningZone.distance
    y_m = warningZone.yCoord - warningZone.distance
    data_coord = supabase.table('warningZone').insert({"typeZone": warningZone.typeZone, "distance": warningZone.distance,"x_p": x_p, "x_m": x_m, "y_p": y_p, "y_m": y_m}).execute()
    assert len(data_coord.data) > 0

    return json.loads(data_coord.model_dump_json())


# Получение информации о подходящих зонах
@app.post("/warningZone/get", responses={400: {"model": ErrorMessage, "description": "Нет подходящих зон"},
                                         200: json_get_zone})
async def get_warning_zone(userPosition: userPosition):
    data = supabase.table('warningZone').select("*", count='exact').filter('x_p', 'gte', userPosition.xCoord).filter('x_m', 'lte', userPosition.xCoord).filter('y_p', 'gte', userPosition.yCoord).filter('y_m', 'lte', userPosition.yCoord).execute()
    if data.count > 0:
        return json.loads(data.model_dump_json())
    else:
        raise HTTPException(status_code=400, detail="Координаты зон не найдены")
    

# Получение track_id
@app.post("/getTrackId", responses={200: json_get_track_id})
async def get_track_id(user_id: str):
    track_id = hash(user_id) + hash(random.randint(0, 1000))
    data = supabase.table("trackId").select("*").eq("track_id", track_id).execute()
    if data.count != 0:
        while data.count != 0:
            track_id = hash(user_id) + hash(random.randint(0, 1000))
            data = supabase.table("trackId").select("*").eq("track_id", track_id).execute()
    data_track = supabase.table("trackId").insert({'user_id': user_id, 'track_id': track_id}).execute()
    assert len(data_track.data) > 0

    return json.loads(data_track.model_dump_json())
    
    

# Добавление записи о треке
@app.post("/trackInfo/add", responses={200: json_user_info})
async def add_track_info(trackInfo: trackInfo):
    #assert trackInfo.secret_key == SECRET_KEY, "Wrong secret key"
    data = supabase.table("trackInfo").insert({"user_id": trackInfo.user_id, "currentSpeed": trackInfo.currentSpeed, "xCoord": trackInfo.xCoord, "yCoord": trackInfo.yCoord, "track_id": trackInfo.track_id}).execute()
    assert len(data.data) > 0

    return json.loads(data.model_dump_json())


# Получение статистики по треку
@app.post("/getTrackInfo", responses={200: json_get_track_info})
async def get_track_info(user_id: str, track_id: int):
    allowedSpeed = 60
    data_ = supabase.table("trackId").select('*').filter('user_id', 'eq', user_id).filter('track_id', 'eq', track_id).execute()
    if data_.count < 0:
        raise HTTPException(status_code=400, detail="Данного трека не существует")
    else:   
        data = supabase.table("trackInfo").select('*').filter('user_id', 'eq', user_id).filter('track_id', 'eq', track_id).filter('currentSpeed', 'gt', allowedSpeed).execute()
        if data.count > 0:
            return json.loads(data.model_dump_json())
        else:
            raise HTTPException(status_code=400, detail="На данном треке не было превышений скорости")
    
