import json
import logging
import os
import time
from datetime import datetime
from typing import Any
import hashlib

import requests
import websockets
from pydantic import BaseModel


def generate_md5_hash(data):
    json_data = json.dumps(data, sort_keys=True)
    return hashlib.md5(json_data.encode("utf-8")).hexdigest()


class Push(BaseModel):
    type: str
    source_user_iden: str
    source_device_iden: str
    client_version: int
    icon: str
    title: str
    body: str
    application_name: str
    package_name: str
    notification_id: str
    notification_tag: str

    def generate_payload(self) -> dict[str, Any]:
        result = {
            "input": {
                "notification_id": self.notification_id,
                "notification_tag": self.notification_tag,
                "package_name": self.package_name,
                "source_user_iden": self.source_user_iden,
                "title": self.title,
                "message": self.body,
                "app_name": self.application_name,
            },
            "config": {},
            "kwargs": {},
        }
        id = generate_md5_hash(result)
        result["input"]["id"] = id
        result["input"]["timestamp"] = time.time()
        return result


logging.basicConfig(
    format="%(asctime)s %(message)s",
    level=logging.CRITICAL,
)


def dismiss_notification(id: str):
    KEY = os.getenv("PUSHBULLET_API_KEY")
    response = requests.delete(
        f"https://api.pushbullet.com/v2/pushes/{id}",
        headers={
            "Access-Token": KEY,
        },
    )
    print("response status:", response.status_code)


def list_pushes():
    KEY = os.getenv("PUSHBULLET_API_KEY")
    response = requests.get(
        "https://api.pushbullet.com/v2/pushes",
        headers={
            "Access-Token": KEY,
        },
    )
    print("response status:", response.status_code)
    print("response json:", response.json())


def dismiss_push(push: Push):
    KEY = os.getenv("PUSHBULLET_API_KEY")

    headers = {
        "Access-Token": KEY,
        "Content-Type": "application/json",
    }

    json_data = {
        "push": {
            "notification_id": push.notification_id,
            "notification_tag": push.notification_tag,
            "package_name": push.package_name,
            "source_user_iden": push.source_user_iden,
            "type": "dismissal",
        },
        "type": "push",
    }

    response = requests.post(
        "https://api.pushbullet.com/v2/ephemerals", headers=headers, json=json_data
    )

    print("notification dismiss response status code", response.status_code)


def classify(push: Push):

    print(push.generate_payload())
    output = push.generate_payload()
    response = requests.post(
        "http://localhost:8000/classify/invoke",
        # "https://mind-sift-app-262464751960.us-central1.run.app/classify/invoke",
        json=output,
    )
    print("classify response", response.status_code)


async def process(msg):
    event = json.loads(msg)
    if event.get("type") == "push":
        p_json_data = event.get("push", {})
        try:
            push = Push(**p_json_data)
        except ValueError as e:
            print(e.errors())
            print()
            print(p_json_data)
            return
        print()
        print(push.model_dump())
        print()
        # dismiss_push(push)
        classify(push)


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
