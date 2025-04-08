# -*- coding: utf-8 -*-
"""
Created on Tue Apr  8 13:20:16 2025

@author: tevsl
"""

import os
from datetime import datetime
from dateutil import tz

def lambda_handler(event, context):
    name = os.getenv("HELLO_NAME", "World")
    now = datetime.now(tz=tz.tzlocal()).strftime("%Y-%m-%d %H:%M:%S %Z")
    return {
        "statusCode": 200,
        "body": f"Hello, {name}! The current time is {now}."
    }
