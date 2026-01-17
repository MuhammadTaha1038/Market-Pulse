import importlib
import os
import json


def handle(event):
    print("event in kinesis: ", event)
    records = event.get("Records", [])
    return "success from kinesis endpoint"
