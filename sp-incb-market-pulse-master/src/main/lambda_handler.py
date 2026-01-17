#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" WSGI Requirements for Flask API """
import importlib
import json
import logging
import os
import traceback
import shutil
import sys
import zipfile


def zip_req():
    """ Zipping requirements for heavy Python packages """
    pkgdir = '/tmp/flask-py-req'

    # We want our path to look like [working_dir, requirements, ...]
    sys.path.insert(1, pkgdir)

    if not os.path.exists(pkgdir):
        tempdir = '/tmp/_temp-flask-py-req'
        if os.path.exists(tempdir):
            shutil.rmtree(tempdir)

        lambda_task_root = os.environ.get('LAMBDA_TASK_ROOT', os.getcwd())
        zip_requirements = os.path.join(lambda_task_root, '.requirements.zip')

        zipfile.ZipFile(zip_requirements, 'r').extractall(tempdir)
        os.rename(tempdir, pkgdir)  # Atomic


def import_app():
    """ Load the application WSGI handler
    """
    local_wsgi_app = os.environ.get('PYTHON_HANDLER', "handler.app")
    app_module = local_wsgi_app.rsplit(".")[0]
    app_function = local_wsgi_app.rsplit(".")[1]

    try:
        wsgi_module = importlib.import_module(app_module)
        return getattr(wsgi_module, app_function)
    except AttributeError:
        traceback.print_exc()
        raise Exception("Unable to import {}".format(app_module)) from AttributeError


def extractEventSource(event):
    if "Records" in event:
        records = event.get("Records", [])  # Kinesis, sqs
        item = records[0]
    else:
        records = event.get("records", [])  # Firehose
        item = records[0]
    if item.get("eventSource", "") != "":
        eventSource = item.get("eventSource", "")
    elif item.get("EventSource", "") != "":
        eventSource = item.get("EventSource", "")
    elif item.get("source", "") != "":
        eventSource = item.get("source", "")
    elif event.get("records", "") != "" and "deliveryStreamArn" in event:  # Firehose
        eventSource = "aws:firehose"
    else:
        raise ValueError("Unsupported Event")
    return eventSource


event_handler_dict = {
    "aws:s3": "s3_event_handler",
    "aws:sqs": "sqs_event_handler",
    "aws.events": "cw_event_handler",
    "aws:sns": "sns_event_handler",
    "aws:kinesis": "kinesis_event_handler",
    "aws:firehose": "firehose_event_handler"
}
headers = {
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
    'Access-Control-Allow-Origin': '*'
}


def handler(event, context):
    """ Lambda event handler, invokes the WSGI wrapper and handles command invocation
    """
    try:
        if event.get("httpMethod", "") == "":
            eventSource = extractEventSource(event)
            event_handler = event_handler_dict.get(eventSource, "")
            if event_handler == "":
                raise ValueError("Unsupported Event Type")
            else:
                event_handler_module = importlib.import_module(event_handler)
                return event_handler_module.handle(event)
        else:
            if(os.environ.get('LAMBDA_TYPE',"") == ""):
                zip_req()
            from handler import app
            from mangum import Mangum
            asgi_handler = Mangum(app)
            response = asgi_handler(event, context)
            return response
    except ValueError as err:
        logging.info(event)
        logging.error("%s : %s", type(err), err)
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'statusMessage': str(err)})
        }
