from pymongo import MongoClient
import os

def get_database():
    # Usa a variável de ambiente MONGO_URI se existir (Docker),
    # caso contrário usa o MongoDB local
    CONNECTION_STRING = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    client = MongoClient(CONNECTION_STRING)
    return client['prontu_db']