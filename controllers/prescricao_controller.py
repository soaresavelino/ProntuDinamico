from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from bson.objectid import ObjectId
from datetime import datetime
from config.database import get_database

prescricao_blueprint = Blueprint('prescricao', __name__, url_prefix='/atendimento')


def ids_iguais(id_a, id_b):
    """Compara dois IDs independente de serem ObjectId, string ou string com prefixo b'...'"""
    def limpar(id_bruto):
        s = str(id_bruto)
        # Remove prefixo ObjectId('...') se existir
        s = s.replace("ObjectId('", "").replace("')", "")
        # Remove prefixo b'...' se existir
        if s.startswith("b'") and s.endswith("'"):
            s = s[2:-1]
        return s.strip()
    return limpar(id_a) == limpar(id_b)


@prescricao_blueprint.route('/<atendimento_id>/prescricao', methods=['GET'])
def nova_prescricao(atendimento_id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_database()
    atendimento = db['atendimentos'].find_one({"_id": ObjectId(atendimento_id)})

    if not atendimento:
        flash("Atendimento clínico não encontrado.", "danger")
        return redirect(url_for('prontuario.index'))

    #  TRAVA DE IDENTIDADE
    if not ids_iguais(atendimento['medico_id'], session['usuario_id']):
        flash(f"Acesso negado: Este atendimento é de responsabilidade do(a) Dr(a). {atendimento['medico_nome']}.", "danger")
        return redirect(url_for('prontuario.index'))

    return render_template('nova_prescricao.html', atendimento=atendimento)


@prescricao_blueprint.route('/<atendimento_id>/prescricao', methods=['POST'])
def salvar_prescricao(atendimento_id):
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))

    db = get_database()
    atendimento = db['atendimentos'].find_one({"_id": ObjectId(atendimento_id)})

    if not atendimento:
        flash("Atendimento clínico não encontrado.", "danger")
        return redirect(url_for('prontuario.index'))

    #  TRAVA DE IDENTIDADE no POST
    if not ids_iguais(atendimento['medico_id'], session['usuario_id']):
        flash("Operação não autorizada.", "danger")
        return redirect(url_for('prontuario.index'))

    nomes_medicamentos = request.form.getlist('nome_medicamento[]')
    posologias = request.form.getlist('posologia[]')

    lista_medicamentos = []
    for i in range(len(nomes_medicamentos)):
        if nomes_medicamentos[i].strip():
            lista_medicamentos.append({
                "nome": nomes_medicamentos[i].strip(),
                "posologia": posologias[i].strip()
            })

    if not lista_medicamentos:
        flash("Por favor, adicione ao menos um medicamento válido à receita.", "warning")
        return redirect(url_for('prescricao.nova_prescricao', atendimento_id=atendimento_id))

    nova_receita = {
        "atendimento_id": ObjectId(atendimento_id),
        "data_emissao": datetime.now().strftime("%d/%m/%Y"),
        "medicamentos": lista_medicamentos
    }

    db['prescricoes'].insert_one(nova_receita)

    flash("Prescrição médica cadastrada com sucesso!", "success")
    return redirect(url_for('prontuario.index'))
