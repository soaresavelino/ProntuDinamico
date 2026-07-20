from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, flash
from models.prontuario_model import ProntuarioModel
from datetime import datetime
import os
import base64

prontuario_blueprint = Blueprint('prontuario', __name__)

# Extensões de imagem permitidas para os prontuários
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def arquivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def converter_para_base64(file):
    """Lê um arquivo de imagem e retorna uma data URI base64 para armazenar no MongoDB."""
    extensao = file.filename.rsplit('.', 1)[1].lower()
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
    }
    mime = mime_types.get(extensao, 'image/jpeg')
    dados = file.read()
    b64 = base64.b64encode(dados).decode('utf-8')
    return f"data:{mime};base64,{b64}"


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
    
    # Percorre os atendimentos e injeta a prescrição vinculada (se houver)
    # Busca por ObjectId E por string para compatibilidade com dados importados
    todos_atendimentos = []
    for atendimento in todos_atendimentos_cursor:
        atendimento_id = atendimento["_id"]
        prescricao = db['prescricoes'].find_one({
            "$or": [
                {"atendimento_id": atendimento_id},
                {"atendimento_id": str(atendimento_id)}
            ]
        })
        atendimento["prescricao"] = prescricao
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
        # Upload de arquivo tem prioridade sobre URL externa
        imagem_url = None
        if 'foto_exame' in request.files:
            file = request.files['foto_exame']
            if file and file.filename and arquivo_permitido(file.filename):
                imagem_url = converter_para_base64(file)

        if not imagem_url:
            url_externa = request.form.get('imagem_url_externa', '').strip()
            if url_externa:
                imagem_url = url_externa

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


# 3. ROTA DE EDIÇÃO: Editar prontuário existente
@prontuario_blueprint.route('/editar/<atendimento_id>', methods=['GET', 'POST'])
def editar_prontuario(atendimento_id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    atendimento = ProntuarioModel.buscar_por_id(atendimento_id)

    if not atendimento:
        flash("Prontuário não encontrado.", "danger")
        return redirect(url_for('prontuario.index'))

    # Apenas o médico dono pode editar
    if str(atendimento['medico_id']).strip() != str(session['usuario_id']).strip():
        flash("Acesso negado: você não pode editar este prontuário.", "danger")
        return redirect(url_for('prontuario.index'))

    if request.method == 'POST':
        imagem_url = atendimento.get('imagem_url')
        if 'foto_exame' in request.files:
            file = request.files['foto_exame']
            if file and file.filename and arquivo_permitido(file.filename):
                imagem_url = converter_para_base64(file)

        if not imagem_url or imagem_url == atendimento.get('imagem_url'):
            url_externa = request.form.get('imagem_url_externa', '').strip()
            if url_externa:
                imagem_url = url_externa

        dados_atualizados = {
            "paciente_nome": request.form.get("paciente_nome", "").strip(),
            "paciente_idade": request.form.get("paciente_idade", "").strip(),
            "paciente_genero": request.form.get("paciente_genero", "").strip(),
            "paciente_contato": request.form.get("paciente_contato", "").strip(),
            "imagem_url": imagem_url,
            "anamnese_dinamica": {}
        }

        campos_fixos = ['paciente_nome', 'paciente_cpf', 'paciente_idade', 'paciente_genero', 'paciente_contato', 'especialidade', 'foto_exame']
        for chave, valor in request.form.items():
            if chave not in campos_fixos and valor:
                dados_atualizados["anamnese_dinamica"][chave] = valor

        ProntuarioModel.atualizar(atendimento_id, dados_atualizados)
        flash("Prontuário atualizado com sucesso!", "success")
        return redirect(url_for('prontuario.index'))

    lista_especialidades = ProntuarioModel.listar_especialidades()
    return render_template('editar_prontuario.html', atendimento=atendimento, especialidades=lista_especialidades)


# 4. ROTA DE EXCLUSÃO: Excluir prontuário e sua prescrição vinculada
@prontuario_blueprint.route('/excluir/<atendimento_id>', methods=['POST'])
def excluir_prontuario(atendimento_id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    atendimento = ProntuarioModel.buscar_por_id(atendimento_id)

    if not atendimento:
        flash("Prontuário não encontrado.", "danger")
        return redirect(url_for('prontuario.index'))

    # Apenas o médico dono pode excluir
    if str(atendimento['medico_id']).strip() != str(session['usuario_id']).strip():
        flash("Acesso negado: você não pode excluir este prontuário.", "danger")
        return redirect(url_for('prontuario.index'))

    from config.database import get_database
    from bson.objectid import ObjectId
    db = get_database()

    # Remove a prescrição vinculada (se houver)
    db['prescricoes'].delete_one({
        "$or": [
            {"atendimento_id": atendimento["_id"]},
            {"atendimento_id": str(atendimento["_id"])}
        ]
    })

    # Remove o prontuário
    ProntuarioModel.excluir(atendimento_id)

    flash("Prontuário excluído com sucesso.", "success")
    return redirect(url_for('prontuario.index'))
