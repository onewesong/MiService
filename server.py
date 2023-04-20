#!/usr/bin/env python3
import os
import time
import json
from pathlib import Path
import logging
logging.basicConfig(level=logging.DEBUG)
from fastapi import FastAPI, Response, Header
from typing import Dict, List
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from aiohttp import ClientSession
from miservice import MiAccount, MiIOService, MiNAService
from utils import parse_cookie_string
from dotenv import load_dotenv
load_dotenv()

MI_USER = os.environ["MI_USER"]
MI_PASS = os.environ["MI_PASS"]
MI_DID = os.getenv("MI_DID")
MI_HARDWARE = os.getenv("MI_HARDWARE", "L05C")
MI_DEVICE_ID = os.getenv("MI_DEVICE_ID", "c172ddc1-34f6-497f-a091-b35b97f14805")

LATEST_ASK_API = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit={limit}"
COOKIE_TEMPLATE = "deviceId={device_id}; serviceToken={service_token}; userId={user_id}"

VERSION = "0.3.0"

session = ClientSession()
account = MiAccount(session, MI_USER, MI_PASS)
service = MiIOService(account)


def get_cookie():
    mi_token_home = Path.home() / ".mi.token"
    with open(mi_token_home) as f:
        user_data = json.loads(f.read())
    user_id = user_data.get("userId")
    service_token = user_data.get("micoapi")[1]
    cookie_string = COOKIE_TEMPLATE.format(device_id=MI_DEVICE_ID,
                                           service_token=service_token,
                                           user_id=user_id)
    return parse_cookie_string(cookie_string)


mina_cookies = get_cookie()

app = FastAPI()


@app.get("/")
async def root():
    return VERSION


@app.get("/list")
async def list():
    result = await service.device_list()
    return JSONResponse(result)


@app.get("/spec")
async def spec(model: str):
    result = await service.miot_spec(model)
    return Response(result)


class Action(BaseModel):
    did: str  # device id
    siid: int  # service id
    aiid: int  # action id
    In: List[str]


class ActionSay(BaseModel):
    did: str = MI_DID
    text: str


class ActionCommand(BaseModel):
    did: str = MI_DID
    text: str
    silent: bool = False


@app.post("/say")
async def say(action: ActionSay):
    logging.info(action.text)
    result = await service.miot_request('action', {
        'did': action.did,
        'siid': 5,
        'aiid': 3,
        'in': [
            action.text,
        ]
    })
    return result


@app.post("/command")
async def command(action: ActionCommand):
    logging.info(action.text)
    result = await service.miot_request(
        'action', {
            'did': action.did,
            'siid': 5,
            'aiid': 4,
            'in': [action.text, int(action.silent)]
        })
    return result


@app.get("/volume")
async def get_volume(did: str = MI_DID):
    result = await service.miot_request('prop/get', [{
        'did': did,
        'siid': 2,
        'piid': 1,
    }])
    return result


@app.put("/volume")
async def set_volume(value: int, did: str = MI_DID):
    result = await service.miot_request('prop/set', [{
        'did': did,
        'siid': 2,
        'piid': 1,
        'value': value,
    }])
    return result

import time

@app.get("/last_ask")
async def get_latest_ask_from_xiaoai(limit=1, before=60):
    now = int(time.time() * 1000)
    before = int(before) * 1000
    session.cookie_jar.update_cookies(mina_cookies)
    r = await session.get(
        LATEST_ASK_API.format(
            hardware=MI_HARDWARE,
            timestamp=now,
            limit=limit,
        ))
    resp = json.loads((await r.json())["data"])["records"]

    return [i["query"] for i in resp if now - i["time"] < before]
