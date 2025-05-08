import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RedisConstants:
    REDIS_HOST = os.environ.get("VALKEY_PROD_SVC_SERVICE_HOST", "test_redis")
    REDIS_PASSWORD = os.environ.get("VALKEY_PASSWORD", "test_redis_password")
    MURKO_REDIS_DB = 7
