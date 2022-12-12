#!/usr/bin/env python3
import os
# import logging
# logging.basicConfig(level=logging.DEBUG)
from fastapi import FastAPI, Response, Header
from typing import Dict, List
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from aiohttp import ClientSession
from miservice import MiAccount, MiIOService
from dotenv import load_dotenv
load_dotenv()

MI_USER = os.environ["MI_USER"]
MI_PASS = os.environ["MI_PASS"]
MI_DID = os.getenv("MI_DID")

VERSION = "0.1.0"

session = ClientSession()
account = MiAccount(session, MI_USER, MI_PASS)
service = MiIOService(account)

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
    echo: bool = True

@app.post("/say")
async def say(action: ActionSay):
    result = await service.miot_request(
        'action', {
            'did': action.did,
            'siid': 5,
            'aiid': 3,
            'in': [action.text, ]
        })
    return result

@app.post("/command")
async def command(action: ActionCommand):
    result = await service.miot_request(
        'action', {
            'did': action.did,
            'siid': 5,
            'aiid': 4,
            'in': [action.text, int(action.echo)]
        })
    return result
