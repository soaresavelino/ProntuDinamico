from config.database import get_database
import bcrypt

db = get_database()
usuarios_collection = db['usuarios']

class UsuarioModel:
    @staticmethod
    def cadastrar(nome, crm, email, senha_plana, especialidade=None):
        """Criptografa a senha e salva o médico no MongoDB"""
        # Verifica se o e-mail já existe
        if usuarios_collection.find_one({"email": email}):
            return False
        
        # Gera o hash da senha
        senha_hash = bcrypt.hashpw(senha_plana.encode('utf-8'), bcrypt.gensalt())
        
        medico = {
            "nome": nome,
            "crm": crm,
            "email": email,
            "senha": senha_hash,
            "especialidade": especialidade or "Geral"
        }
        usuarios_collection.insert_one(medico)
        return True

    @staticmethod
    def verificar_login(email, senha_plana):
        """Busca o usuário e valida a senha"""
        usuario = usuarios_collection.find_one({"email": email})
        if usuario:
            senha_hash = usuario['senha']
            # Caso 1: veio como bytes direto do MongoDB (fluxo normal)
            if isinstance(senha_hash, bytes):
                pass
            # Caso 2: veio como string "b'$2b$12$...'" (importado via JSON/seed)
            elif isinstance(senha_hash, str):
                if senha_hash.startswith("b'") and senha_hash.endswith("'"):
                    senha_hash = senha_hash[2:-1].encode('utf-8')
                else:
                    senha_hash = senha_hash.encode('utf-8')
            if bcrypt.checkpw(senha_plana.encode('utf-8'), senha_hash):
                return usuario
        return None