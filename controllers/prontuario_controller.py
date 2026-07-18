from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from models.prontuario_model import ProntuarioModel
from datetime import datetime
import os
from werkzeug.utils import secure_filename

prontuario_blueprint = Blueprint('prontuario', __name__)

# Extensões de imagem permitidas para os prontuários
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def arquivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 1. ROTA PRINCIPAL: Tela de Listagem com Busca por Nome/CPF e Filtro por Especialidade
@prontuario_blueprint.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    
    from config.database import get_database
    db = get_database()
    
    # Captura os filtros que vieram da tela (index.html)
    termo_busca = request.args.get('cpf_busca', '').strip()
    especialidade_busca = request.args.get('especialidade_busca', '').strip()
    
    # Limpa a máscara do CPF caso o médico tenha digitado formatado na busca
    cpf_limpo = termo_busca.replace('.', '').replace('-', '')
    
    # Monta o dicionário de filtros para o MongoDB dinamicamente
    query_mongo = {}
    
    # Se digitou algo na busca por texto (CPF ou Nome)
    if termo_busca:
        query_mongo["$or"] = [
            {"paciente_cpf": cpf_limpo},
            {"paciente_nome": {"$regex": termo_busca, "$options": "i"}}
        ]
        
    # Se escolheu uma especialidade específica no select
    if especialidade_busca:
        query_mongo["especialidade"] = especialidade_busca
        
    # Busca no banco aplicando todos os filtros combinados
    todos_atendimentos_cursor = db['atendimentos'].find(query_mongo)
    
    # 🌟 CORREÇÃO/ADICIONAL: Percorre os atendimentos e injeta a prescrição vinculada (se houver)
    todos_atendimentos = []
    for atendimento in todos_atendimentos_cursor:
        prescricao = db['prescricoes'].find_one({"atendimento_id": atendimento["_id"]})
        atendimento["prescricao"] = prescricao  # Coloca a receita dentro do objeto do atendimento
        todos_atendimentos.append(atendimento)
    
    # Busca a lista de todas as especialidades para renderizar no select de busca da tela
    todas_especialidades = list(db['especialidades'].find())
    
    return render_template(
        'index.html', 
        historico=todos_atendimentos, 
        cpf_busca=termo_busca,
        especialidade_busca=especialidade_busca,
        lista_especialidades=todas_especialidades
    )


# 2. ROTA DE CADASTRO: Criação de novos prontuários
@prontuario_blueprint.route('/novo', methods=['GET', 'POST'])
def novo_prontuario():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        paciente_cpf = request.form.get("paciente_cpf").strip()
        paciente_nome = request.form.get("paciente_nome").strip()

        # REMOVE A MÁSCARA: Garante que pontos e traços não entrem no MongoDB
        paciente_cpf_limpo = paciente_cpf.replace('.', '').replace('-', '')

        # TRAVA DE SEGURANÇA: Busca se já existe alguma consulta com o CPF limpo
        from config.database import get_database
        db = get_database()
        existente = db['atendimentos'].find_one({"paciente_cpf": paciente_cpf_limpo})

        # Se o CPF já existe, o nome digitado deve ser exatamente igual ao do histórico
        if existente and existente['paciente_nome'].lower() != paciente_nome.lower():
            flash(f"Erro: O CPF {paciente_cpf} já está registrado para o paciente '{existente['paciente_nome']}'.", "danger")
            lista_especialidades = ProntuarioModel.listar_especialidades()
            return render_template('novo_prontuario.html', especialidades=lista_especialidades)

        # Se passou na validação, segue o fluxo normal de salvamento
        imagem_url = None
        if 'foto_exame' in request.files:
            file = request.files['foto_exame']
            if file and arquivo_permitido(file.filename):
                filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                imagem_url = f"/static/uploads/{filename}"

        # O dicionário agora armazena também idade, gênero e contato de forma fixa na raiz do documento
        atendimento = {
            "paciente_nome": paciente_nome,
            "paciente_cpf": paciente_cpf_limpo,
            "paciente_idade": request.form.get("paciente_idade", "").strip(),
            "paciente_genero": request.form.get("paciente_genero", "").strip(),
            "paciente_contato": request.form.get("paciente_contato", "").strip(),
            "medico_id": session['usuario_id'],
            "medico_nome": session['usuario_nome'],
            "especialidade": request.form.get("especialidade"),
            "data_consulta": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "imagem_url": imagem_url,
            "anamnese_dinamica": {}
        }
        
        # 'paciente_contato' adicionado na lista para não entrar no loop dinâmico
        campos_fixos = ['paciente_nome', 'paciente_cpf', 'paciente_idade', 'paciente_genero', 'paciente_contato', 'especialidade', 'foto_exame']
        for chave, valor in request.form.items():
            if chave not in campos_fixos and valor:
                atendimento["anamnese_dinamica"][chave] = valor

        ProntuarioModel.inserir(atendimento)
        
        # Redireciona com sucesso para a listagem principal
        return redirect(url_for('prontuario.index'))
        
    lista_especialidades = ProntuarioModel.listar_especialidades()
    return render_template('novo_prontuario.html', especialidades=lista_especialidades)