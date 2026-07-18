from config.database import get_database
from bson.objectid import ObjectId

db = get_database()
# Coleção polimórfica única para os atendimentos
atendimentos_collection = db['atendimentos']

class ProntuarioModel:
    @staticmethod
    def inserir(dados_atendimento):
        """Insere um documento de prontuário com estrutura flexível no BD"""
        result = atendimentos_collection.insert_one(dados_atendimento)
        return result.inserted_id

    @staticmethod
    def buscar_por_paciente(cpf_paciente):
        """Busca o histórico e ordena por data decrescente (MQL pura)"""
        query = {"paciente_cpf": cpf_paciente}
        # Ordena por 'data_consulta' de forma decrescente (-1)
        fech_cursor = atendimentos_collection.find(query).sort("data_consulta", -1)
        return list(fech_cursor)

    @staticmethod
    def listar_todos():
        """Retorna todas as consultas registradas no sistema"""
        return list(atendimentos_collection.find().sort("data_consulta", -1))

    @staticmethod
    def listar_especialidades():
        """Busca todas as especialidades e seus campos dinâmicos do banco"""
        db = get_database()
        # Busca da nova coleção que criamos no Compass
        return list(db['especialidades'].find({}, {"_id": 0}))