"""
Script de seed: importa os dados da pasta /data para o MongoDB.
Roda uma unica vez quando o container sobe.
"""
import json
import os
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson import ObjectId

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

COLECOES = ["especialidades", "atendimentos", "prescricoes", "usuarios"]

# Campos que devem ser convertidos de string para ObjectId
CAMPOS_OBJECTID = ["_id", "medico_id", "atendimento_id"]

def aguardar_mongo(client, tentativas=10):
    for i in range(tentativas):
        try:
            client.admin.command("ping")
            print("MongoDB pronto!")
            return True
        except ConnectionFailure:
            print(f"Aguardando MongoDB... ({i+1}/{tentativas})")
            time.sleep(3)
    return False

def converter_objectids(doc):
    """Converte campos de ID conhecidos de string para ObjectId."""
    for campo in CAMPOS_OBJECTID:
        if campo in doc and isinstance(doc[campo], str):
            try:
                doc[campo] = ObjectId(doc[campo])
            except Exception:
                pass
    return doc

def main():
    client = MongoClient(MONGO_URI)

    if not aguardar_mongo(client):
        print("Nao foi possivel conectar ao MongoDB. Abortando seed.")
        return

    db = client["prontu_db"]

    for colecao in COLECOES:
        caminho = os.path.join(DATA_DIR, f"{colecao}.json")
        if not os.path.exists(caminho):
            print(f"Arquivo nao encontrado: {caminho}")
            continue

        # Só importa se a coleção estiver vazia
        if db[colecao].count_documents({}) > 0:
            print(f"{colecao}: ja possui dados, pulando.")
            continue

        with open(caminho, "r", encoding="utf-8") as f:
            documentos = json.load(f)

        # Converte strings de ID para ObjectId antes de inserir
        documentos = [converter_objectids(doc) for doc in documentos]

        if documentos:
            db[colecao].insert_many(documentos)
            print(f"{colecao}: {len(documentos)} documentos importados.")
        else:
            print(f"{colecao}: arquivo vazio.")

    print("Seed concluido!")

if __name__ == "__main__":
    main()