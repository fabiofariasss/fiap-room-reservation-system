import os
import json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'super_secret_key_fiap'  # Necessário para flash messages e session

# Caminhos dos arquivos de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
RESERVAS_FILE = os.path.join(DATA_DIR, "reservas.json")

# Garante que a pasta data exista
os.makedirs(DATA_DIR, exist_ok=True)

# Inicializa arquivos se não existirem
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump([], f)
if not os.path.exists(RESERVAS_FILE):
    with open(RESERVAS_FILE, 'w') as f:
        json.dump([], f)

# =========================
# FUNÇÕES AUXILIARES
# =========================
def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return []

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash("Por favor, faça login para acessar essa página.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# =========================
# ROTAS DE AUTENTICAÇÃO
# =========================
@app.route('/cadastro', methods=['GET', 'POST'])
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
            return redirect(url_for('login'))
            
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_email' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        users = load_json(USERS_FILE)
        user = next((u for u in users if u['email'] == email and u['senha'] == senha), None)
        
        if user:
            session['user_email'] = user['email']
            session['user_nome'] = user['nome']
            return redirect(url_for('dashboard'))
        else:
            flash("E-mail ou senha incorretos.", "error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# =========================
# ROTAS DO SISTEMA
# =========================
from datetime import datetime

# ... (Funções auxiliares load_json/save_json e login_required permanecem as mesmas)

@app.route('/dashboard')
@login_required
def dashboard():
    reservas = load_json(RESERVAS_FILE)
    email_usuario = session.get('user_email')
    agora_dt = datetime.now()
    hoje = agora_dt.strftime("%Y-%m-%d")
    agora_hora = agora_dt.strftime("%H:%M")
    
    todas_salas = ["Sala 1", "Sala 2", "Sala 3"]
    
    # 1. Estatísticas Básicas
    total_reservas = len(reservas)
    salas_ocupadas_agora = [r['sala'] for r in reservas if r.get('dia') == hoje and r.get('inicio', '') <= agora_hora < r.get('fim', '')]
    salas_disponiveis_count = len(todas_salas) - len(set(salas_ocupadas_agora))
    
    # 2. Ocupação Hoje (Cálculo de % baseado em horas reservadas / 24h)
    ocupacao = {}
    for sala in todas_salas:
        horas_reservadas = 0
        for r in reservas:
            if r.get('dia') == hoje and r['sala'] == sala:
                h1 = datetime.strptime(r['inicio'], "%H:%M")
                h2 = datetime.strptime(r['fim'], "%H:%M")
                horas_reservadas += (h2 - h1).seconds / 3600
        # Porcentagem simples (limitada a 100%)
        ocupacao[sala] = min(100, int((horas_reservadas / 12) * 100)) # Baseado em 12h úteis
    
    # 3. Próxima Reserva e Atividades
    minhas_reservas = [r for r in reservas if r.get('email') == email_usuario and (r.get('dia') > hoje or (r.get('dia') == hoje and r.get('fim', '') > agora_hora))]
    minhas_reservas.sort(key=lambda x: (x['dia'], x['inicio']))
    
    minhas_atividades = [r for r in reservas if r.get('email') == email_usuario]
    minhas_atividades.sort(key=lambda x: (x['dia'], x['inicio']), reverse=True)
    
    return render_template('dashboard.html', 
                           nome=session.get('user_nome'), 
                           total_reservas=total_reservas,
                           salas_disponiveis=salas_disponiveis_count,
                           proxima_reserva=minhas_reservas[0] if minhas_reservas else None,
                           atividades=minhas_atividades[:5],
                           ocupacao=ocupacao,
                           salas_ocupadas_agora=salas_ocupadas_agora)

@app.route('/relatorios')
@login_required
def relatorios():
    reservas = load_json(RESERVAS_FILE)
    return render_template('relatorios.html', total=len(reservas))

@app.route('/configuracoes')
@login_required
def configuracoes():
    return render_template('configuracoes.html')

@app.route('/reservar', methods=['GET', 'POST'])
@login_required
def reservar():
    salas = ["Sala 1", "Sala 2", "Sala 3"]
    if request.method == 'POST':
        sala = request.form.get('sala')
        dia = request.form.get('dia')
        inicio = request.form.get('inicio')
        fim = request.form.get('fim')
        
        if not dia or not inicio or not fim or inicio >= fim:
            flash("❌ Dados inválidos! Verifique horários e data.", "error")
            return render_template('reservar.html', salas=salas)

        reservas = load_json(RESERVAS_FILE)
        
        # Conflito: Mesma sala, Mesmo dia, Horários sobrepostos
        conflito = any(
            r['sala'] == sala and r.get('dia') == dia and (inicio < r['fim'] and fim > r['inicio'])
            for r in reservas
        )
        
        if conflito:
            flash("❌ Conflito! Esta sala já está ocupada neste horário no dia selecionado.", "error")
        else:
            reservas.append({
                "nome": session.get('user_nome'),
                "email": session.get('user_email'),
                "sala": sala,
                "dia": dia,
                "inicio": inicio,
                "fim": fim
            })
            save_json(RESERVAS_FILE, reservas)
            flash("✅ Reserva realizada com sucesso!", "success")
            return redirect(url_for('reservas_view'))
            
    return render_template('reservar.html', salas=salas)

@app.route('/reservas')
@login_required
def reservas_view():
    reservas = load_json(RESERVAS_FILE)
    # Ordenar por dia, sala e horário
    reservas.sort(key=lambda x: (x.get('dia', ''), x['sala'], x['inicio']))
    return render_template('reservas.html', reservas=reservas, user_email=session.get('user_email'))

@app.route('/cancelar', methods=['POST'])
@login_required
def cancelar():
    sala = request.form.get('sala')
    dia = request.form.get('dia')
    inicio = request.form.get('inicio')
    fim = request.form.get('fim')
    email = session.get('user_email')
    
    reservas = load_json(RESERVAS_FILE)
    nova_lista = [
        r for r in reservas if not (
            r['sala'] == sala and 
            r.get('dia') == dia and 
            r['inicio'] == inicio and 
            r['fim'] == fim and 
            r['email'] == email
        )
    ]
    
    if len(nova_lista) < len(reservas):
        save_json(RESERVAS_FILE, nova_lista)
        flash("✅ Reserva cancelada!", "success")
    else:
        flash("❌ Erro ao cancelar reserva.", "error")
        
    return redirect(url_for('reservas_view'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
