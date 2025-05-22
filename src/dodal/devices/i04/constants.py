import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RedisConstants:
    REDIS_HOST = os.environ.get(
        "VALKEY_PROD_SVC_SERVICE_HOST", "i04-valkey-murko.diamond.ac.uk"
    )
    REDIS_PASSWORD = os.environ.get("VALKEY_PASSWORD", "8zIu7TlnrA3449r4MShIS9Mb")
    MURKO_REDIS_DB = 7
