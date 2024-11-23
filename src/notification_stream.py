import asyncio
import json
import logging
import os

import requests
import websockets

logging.basicConfig(
    format="%(asctime)s %(message)s",
    level=logging.CRITICAL,
)


def dismiss_notification(id: str):
    KEY = os.getenv("PUSHBULLET_API_KEY")
    response = requests.delete(
        f'https://api.pushbullet.com/v2/pushes/{id}',
        headers={
            'Access-Token': KEY,
        },
    )
    print("response status:", response.status_code)


def list_pushes():
    KEY = os.getenv("PUSHBULLET_API_KEY")
    response = requests.get(
        'https://api.pushbullet.com/v2/pushes',
        headers={
            'Access-Token': KEY,
        },
    )
    print("response status:", response.status_code)
    print("response json:", response.json())


async def process(msg):
    event = json.loads(msg)
    if event.get("type", "nop") != "nop":
        p = event.get("push", {})
        title = p.get("title")
        body = p.get("body")
        app_name = p.get("application_name")
        print()
        print(event)
        print()
        print(10 * "-")
        print("app_name", app_name)
        print("title", title)
        print("body", body)
        print(10 * "-")


async def stream():
    KEY = os.getenv("PUSHBULLET_API_KEY")
    async for websocket in websockets.connect(
        f"wss://stream.pushbullet.com/websocket/{KEY}",
        logger=logging.getLogger("websockets"),
    ):
        try:
            async for message in websocket:
                await process(message)
        except websockets.ConnectionClosed:
            continue
