from __future__ import absolute_import, unicode_literals
from connections import ConnectionManager as manager
import asyncio
from celery import shared_task
from internal import enums
import json


@shared_task
def publish_event(event):
    topic = event['topic']
    subscription_key = event['key']
    msg = event['event']
    account_update = topic in enums.Topics.account.value
    return asyncio.run(manager.publish(subscription_key, json.dumps({"topic": topic, "event": msg}), account_update))
