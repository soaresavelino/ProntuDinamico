from config.database import get_database
import bcrypt

db = get_database()
usuarios_collection = db['usuarios']

class UsuarioModel:
    @staticmethod
    def cadastrar(nome, crm, email, senha_plana):
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
            "senha": senha_hash
        }
        usuarios_collection.insert_one(medico)
        return True

    @staticmethod
    def verificar_login(email, senha_plana):
        """Busca o usuário e valida a senha"""
        usuario = usuarios_collection.find_one({"email": email})
        if usuario and bcrypt.checkpw(senha_plana.encode('utf-8'), usuario['senha']):
            return usuario
        return None