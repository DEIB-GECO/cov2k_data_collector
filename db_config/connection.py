from typing import Optional
from logger import logger
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
import pymongo

USE_DB = 'COV2K'
LOCAL_DB_CONNECTION_STRING = "mongodb://localhost:27017"
GECO_DB_CONNECTION_STRING = "mongodb://localhost:23456/gcm_gisaid"
MONGO_DB_CONNECTION_URI = LOCAL_DB_CONNECTION_STRING if USE_DB == 'COV2K' else GECO_DB_CONNECTION_STRING
DB_NAME = 'cov2k_v21_11_30' if USE_DB == 'COV2K' else 'gcm_gisaid'

_client: Optional[MongoClient] = None


def close_conn():
    global _client
    if _client:
        _client.close()
        logger.info(f'Connection with mongoDB {MONGO_DB_CONNECTION_URI} CLOSED')
        _client = None
    else:
        logger.warning("Request to close connection that was never opened.")


def open_conn() -> Database:
    global _client
    if not _client:
        _client = MongoClient(MONGO_DB_CONNECTION_URI)
        logger.info(f"Connection with mongoDB {MONGO_DB_CONNECTION_URI} ESTABLISHED")
    return _client[DB_NAME]


if __name__ == "__main__":
    pass
    # dbname = get_database()

    # get_variants().insert({
    #     "pangolin-id": "B.1.1.7"
    # })
    # for item in get_variants().find():
    #     print(item)
