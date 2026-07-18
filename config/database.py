from pymongo import MongoClient

def get_database():
    # String de conexão local do MongoDB (ajuste se usar Docker ou credenciais)
    CONNECTION_STRING = "mongodb://localhost:27017/"
    client = MongoClient(CONNECTION_STRING)
    
    # Retorna o banco de dados chamado 'prontu_db'
    return client['prontu_db']