import importlib
import os
import json


def handle(event):
    print("event in sqs: ", event)
    records = event.get("Records", [])
    return "success from sqs endpoint"
