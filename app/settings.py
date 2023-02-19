import os
from decimal import Decimal


SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8003))
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "SECRET_TOKEN")

_KAFKA_SERVERS = [
    {
        "host": os.getenv('KAFKA_HOST1', '0.0.0.0'),
        "port": os.getenv('KAFKA_HOST1PORT', '9092'),
    },
    {
        "host": os.getenv('KAFKA_HOST2', ''),
        "port": os.getenv('KAFKA_HOST2PORT', '9092'),
    },
    {
        "host": os.getenv('KAFKA_HOST3', ''),
        "port": os.getenv('KAFKA_HOST3PORT', '9092'),
    },
]
KAFKA_BOOTSTRAP_SERVERS = ','.join([
    f"{bootstrap_server['host']}:{bootstrap_server['port']}" for bootstrap_server in _KAFKA_SERVERS if bootstrap_server['host']]
)
