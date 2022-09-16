from enum import Enum


class KafkaQueue(Enum):
    match_engine = "MATCH_ENGINE"
    account = "ACCOUNT"
    public = "PUBLIC"
    