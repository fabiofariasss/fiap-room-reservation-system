from flask import render_template, request, redirect, url_for, session, flash
from functools import wraps
from . import auth_bp
from models.utils import USERS_FILE, load_json, save_json

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash("Por favor, faça login para acessar essa página.", "error")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        users = load_json(USERS_FILE)
        
        if any(u['email'] == email for u in users):
            flash("E-mail já cadastrado!", "error")
        else:
            users.append({'nome': nome, 'email': email, 'senha': senha})
            save_json(USERS_FILE, users)
            flash("Cadastro realizado com sucesso! Faça login.", "success")
            return redirect(url_for('auth.login'))
            
    return render_template('cadastro.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if 'user_email' in session:
        return redirect(url_for('views.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        users = load_json(USERS_FILE)
        user = next((u for u in users if u['email'] == email and u['senha'] == senha), None)
        
        if user:
            session['user_email'] = user['email']
            session['user_nome'] = user['nome']
            return redirect(url_for('views.dashboard'))
        else:
            flash("E-mail ou senha incorretos.", "error")
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
