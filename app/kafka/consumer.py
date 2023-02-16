from confluent_kafka import Consumer
from internal import enums
import traceback
import settings
import asyncio
import threading
import logging

logger = logging.getLogger("uvicorn.error")


async def consume(callback: callable):
    c = Consumer({
        'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'websocket',
        'auto.offset.reset': 'earliest'
    })
    c.subscribe([enums.KafkaQueue.account.value, enums.KafkaQueue.public.value])
    logger.warning("consumer connected!")

    while True:
        msg = c.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            logger.warning("Consumer error: {}".format(msg.error()))
            continue
        topic = msg.topic()
        subscription_key = msg.key()
        if subscription_key:
            subscription_key = subscription_key.decode('utf-8')
        msg = msg.value().decode('utf-8')
        logger.warning(f"subscription_key: {topic} {subscription_key}, {msg} {type(msg)}\n\n")
        await callback(subscription_key, msg, topic == "ACCOUNT")
    c.close()

async def consumer(callback: callable):
    try:
        await consume(callback=callback)
    except Exception as e:
        logger.error(e)
        logger.warning(traceback.format_exc())
        await consumer(callback)
        
def start_consumer(callback):
    def between_callback(args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(consumer(args))
        loop.close()

    _thread = threading.Thread(
        target=between_callback, 
        args=(callback,),
        daemon=True
        )
    _thread.start() 