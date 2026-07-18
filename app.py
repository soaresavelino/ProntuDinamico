from flask import Flask, redirect, url_for, session, request
from controllers.prontuario_controller import prontuario_blueprint
from controllers.auth_controller import auth_blueprint
# PASSO 1: Importar o novo controlador de prescrição
from controllers.prescricao_controller import prescricao_blueprint
import os

app = Flask(__name__)
app.secret_key = "chave_secreta_super_segura_para_o_tp"

# Configuração da pasta de upload de imagens
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# FILTRO CUSTOMIZADO: Resolve o problema de comparação entre ObjectId e String no Jinja2
@app.template_filter('eh_o_mesmo_medico')
def eh_o_mesmo_medico(medico_id, usuario_id):
    if not medico_id or not usuario_id:
        return False
    
    # Função interna para limpar "ObjectId", parênteses, aspas e espaços de ambos os lados
    def limpar_id(id_bruto):
        id_str = str(id_bruto).replace("ObjectId", "").replace("(", "").replace(")", "").replace("'", "").replace('"', "")
        return id_str.strip()
        
    return limpar_id(medico_id) == limpar_id(usuario_id)


# Registra os controladores do MVC
app.register_blueprint(prontuario_blueprint)
app.register_blueprint(auth_blueprint)
# PASSO 2: Registrar o Blueprint da prescrição no Flask
app.register_blueprint(prescricao_blueprint)


# Rota raiz do sistema direciona para a listagem principal
@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    # ALTERADO: Agora aponta para a listagem (index do blueprint)
    return redirect(url_for('prontuario.index'))

# Interceptador corrigido
@app.before_request
def antes_da_requisicao():
    # Adicionado variações comuns de nome de rota para evitar o loop/404
    # PASSO 3: Adicionar as rotas de prescrição na proteção se necessário (já estão protegidas pelo session abaixo)
    rotas_livres = ['auth.login', 'auth.cadastro', 'login', 'cadastro', 'static']
    
    # Se não houver endpoint (página não encontrada), deixa o Flask lançar o 404 real ou o login
    if not request.endpoint:
        return

    if 'usuario_id' not in session and request.endpoint not in rotas_livres:
        # Verifica se a rota requisitada não faz parte dos arquivos estáticos do Bootstrap/Imagens
        if 'static' not in request.endpoint:
            return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0")