#!/usr/bin/env python3
from aiohttp import ClientSession
import asyncio
import logging
import json
import os
import sys
import time
from pathlib import Path
from pprint import pprint

from miservice import MiAccount, MiNAService, MiIOService, miio_command, miio_command_help


async def main(args):
    async with ClientSession() as session:
        env = os.environ
        account = MiAccount(session, env.get('MI_USER'), env.get('MI_PASS'), os.path.join(str(Path.home()), '.mi.token'))

        service = MiNAService(account)
        result = await service.device_list()
        if args.verbose:
            level = logging.WARNING
        if args.name:
            target = None
            for i in result:
                if i["name"] == args.name:
                    target = i
                    break
            if not target:
                print("No such device: " + args.name)
                sys.exit(1)

            hardware = target["hardware"]
            deviceID = target["deviceID"]
            timestamp = int(time.time() * 1000)
            limit = 2

            result = await service.conversation(hardware, deviceID, timestamp, limit)
            pprint(result)

import argparse

def get_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("name", help='specify soundbox by name')
    parser.add_argument("-v", "--verbose", action="store")
    # parser.add_argument("-a", "--action", choices=['conversation'])
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    asyncio.run(main(get_args()))
