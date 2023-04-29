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
from dotenv import load_dotenv
load_dotenv()

MI_USER = os.environ["MI_USER"]
MI_PASS = os.environ["MI_PASS"]
MI_DID = os.getenv("MI_DID")
MI_HARDWARE = os.getenv("MI_HARDWARE", "L05C")
MI_DEVICE_ID = os.getenv("MI_DEVICE_ID", "c172ddc1-34f6-497f-a091-b35b97f14805")
MI_TOKEN_HOME = os.path.join(str(Path.home()), '.mi.token')

VERSION = "0.3.0"

session = ClientSession()
account = MiAccount(session, MI_USER, MI_PASS, MI_TOKEN_HOME)
miio_service = MiIOService(account)
mina_service = MiNAService(account)


async def get_device_by_name(name):
    result = await mina_service.device_list()
    for i in result:
        if i['name'] == name:
            return i["hardware"], i["deviceID"]

app = FastAPI()


@app.get("/")
async def root():
    return VERSION


@app.get("/list")
async def list():
    result = await miio_service.device_list()
    return JSONResponse(result)


@app.get("/spec")
async def spec(model: str):
    result = await miio_service.miot_spec(model)
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
    result = await miio_service.miot_request('action', {
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
    result = await miio_service.miot_request(
        'action', {
            'did': action.did,
            'siid': 5,
            'aiid': 4,
            'in': [action.text, int(action.silent)]
        })
    return result


@app.get("/volume")
async def get_volume(did: str = MI_DID):
    result = await miio_service.miot_request('prop/get', [{
        'did': did,
        'siid': 2,
        'piid': 1,
    }])
    return result


@app.put("/volume")
async def set_volume(value: int, did: str = MI_DID):
    result = await miio_service.miot_request('prop/set', [{
        'did': did,
        'siid': 2,
        'piid': 1,
        'value': value,
    }])
    return result


@app.get("/conversation")
async def get_conversation(name):
    hardware, deviceID = await get_device_by_name(name)
    result = await mina_service.conversation(hardware,
                                                deviceID,
                                                int(time.time() * 1000),
                                                limit=2)
    return result


@app.get("/last_ask")
async def get_latest_ask_from_xiaoai(limit=1, before=60):
    now = int(time.time() * 1000)
    before = int(before) * 1000

    data = await mina_service.conversation(MI_HARDWARE, MI_DEVICE_ID, now, limit=limit)
    resp = data["records"]

    return [i["query"] for i in resp if now - i["time"] < before]
