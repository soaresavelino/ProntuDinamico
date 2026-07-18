from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.usuario_model import UsuarioModel
from models.prontuario_model import ProntuarioModel

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        usuario = UsuarioModel.verificar_login(email, senha)
        if usuario:
            session['usuario_id'] = str(usuario['_id'])
            session['usuario_nome'] = usuario['nome']
            # 🌟 ADICIONADO: Grava a especialidade na sessão
            session['usuario_especialidade'] = usuario.get('especialidade', 'Geral')
            return redirect(url_for('prontuario.index'))
        
        flash('E-mail ou senha incorretos!', 'danger')
    return render_template('login.html')

@auth_blueprint.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        crm = request.form.get('crm')
        email = request.form.get('email')
        senha = request.form.get('senha')
        especialidade = request.form.get('especialidade')
        
        if UsuarioModel.cadastrar(nome, crm, email, senha, especialidade):
            flash('Cadastro realizado com sucesso! Faça o login.', 'success')
            return redirect(url_for('auth.login'))
        
        flash('Este e-mail já está cadastrado.', 'danger')
    
    especialidades = ProntuarioModel.listar_especialidades()
    return render_template('cadastro.html', especialidades=especialidades)

@auth_blueprint.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))