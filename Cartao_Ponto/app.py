from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, session, redirect, render_template
from datetime import datetime


app = Flask(__name__)

# Caminho completo para o arquivo do banco de dados SQLite
app.secret_key = 'abc123'
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///C:/Users/User/OneDrive/Área de Trabalho/Cartao_Ponto/cartaoponto.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Modelos
class Funcionario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    whatsapp = db.Column(db.String(20))
    senha = db.Column(db.String(100), nullable=False)
    registros = db.relationship('RegistroPonto', backref='funcionario', lazy=True)

class Administrador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    whatsapp = db.Column(db.String(20))
    senha = db.Column(db.String(100), nullable=False)

class RegistroPonto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    entrada = db.Column(db.String(5))
    saida_almoco = db.Column(db.String(5))
    retorno_almoco = db.Column(db.String(5))
    saida = db.Column(db.String(5))
    horas_normais = db.Column(db.Float)
    horas_extras = db.Column(db.Float)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)


# Página de login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form['cpf']
        senha = request.form['senha']
        tipo = request.form['tipo']
        if tipo == 'funcionario':
            user = Funcionario.query.filter_by(cpf=cpf, senha=senha).first()
            if user:
                session['user_id'] = user.id
                session['tipo'] = 'funcionario'
                return redirect('/funcionario')
            else:
                return render_template('login.html', erro='CPF ou senha inválidos para funcionário.')
        else:
            admin = Administrador.query.filter_by(cpf=cpf, senha=senha).first()
            if admin:
                session['user_id'] = admin.id
                session['tipo'] = 'admin'
                return redirect('/admin')
            else:
                return render_template('login.html', erro='CPF ou senha inválidos para administrador.')
    return render_template('login.html')


# Página do funcionário
@app.route('/funcionario')
def funcionario_dashboard():
    if session.get('tipo') != 'funcionario':
        return redirect('/')
    user = Funcionario.query.get(session['user_id'])
    registros = RegistroPonto.query.filter_by(funcionario_id=user.id).all()
    return render_template('dashboard_funcionario.html', user=user, registros=registros)

# Registro de ponto
@app.route('/registrar', methods=['GET', 'POST'])
def registrar_ponto():
    if session.get('tipo') != 'funcionario':
        return redirect('/')
    
    if request.method == 'POST':
        entrada = request.form['entrada']
        saida_almoco = request.form['saida_almoco']
        retorno_almoco = request.form['retorno_almoco']
        saida = request.form['saida']
        data_str = request.form['data']
        funcionario_id = session['user_id']

        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()

        # Cálculo de horas (exemplo)
        horas_normais = 8.0
        horas_extras = 0.0

        novo = RegistroPonto(
            funcionario_id=funcionario_id,
            data=data_obj,
            entrada=entrada,
            saida_almoco=saida_almoco,
            retorno_almoco=retorno_almoco,
            saida=saida,
            horas_normais=horas_normais,
            horas_extras=horas_extras,
            data_registro=datetime.now()
        )
        db.session.add(novo)
        db.session.commit()
        return redirect('/funcionario')
    
    return render_template('registro_ponto.html')

# Página do administrador
@app.route('/admin')
def admin_dashboard():
    if session.get('tipo') != 'admin':
        return redirect('/')
    funcionarios = Funcionario.query.all()
    return render_template('dashboard_admin.html', funcionarios=funcionarios)
@app.route('/admin/funcionario/<int:id>')
def visualizar_registros_funcionario(id):
    if session.get('tipo') != 'admin':
        return redirect('/')
    
    funcionario = Funcionario.query.get_or_404(id)
    registros = RegistroPonto.query.filter_by(funcionario_id=funcionario.id).all()
    return render_template('registros_funcionario.html', funcionario=funcionario, registros=registros)
    
# Página para cadastrar novo funcionário 
@app.route('/cadastrar_funcionario', methods=['GET', 'POST'])
def cadastrar_funcionario():
    if session.get('tipo') != 'admin':
        return redirect('/')
    
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        whatsapp = request.form['whatsapp']
        senha = request.form['senha']

        novo_func = Funcionario(
            nome=nome,
            cpf=cpf,
            whatsapp=whatsapp,
            senha=senha
        )
        db.session.add(novo_func)
        db.session.commit()
        return redirect('/admin')
    
    return render_template('cadastrar_funcionario.html')

@app.route('/admin/registros')
def listar_todos_registros():
    if session.get('tipo') != 'admin':
        return redirect('/')
    
    registros = db.session.query(RegistroPonto, Funcionario).join(Funcionario).order_by(RegistroPonto.data.desc()).all()
    return render_template('todos_registros.html', registros=registros)

@app.route('/admin/registros_por_funcionario')
def registros_por_funcionario():
    if session.get('tipo') != 'admin':
        return redirect('/')
    
    funcionarios = Funcionario.query.order_by(Funcionario.nome).all()
    return render_template('registros_por_funcionario.html', funcionarios=funcionarios)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # criar as tabelas
        
        # Verifica se já existe algum admin cadastrado
        admin_existe = Administrador.query.first()
        
        if not admin_existe:
            admin_padrao = Administrador(
                nome='Administrador Padrão',
                cpf='00000000000',
                whatsapp='00000000000',
                senha='abc123'
            )
            db.session.add(admin_padrao)
            db.session.commit()
            print("Administrador padrão criado: cpf='00000000000', senha='abc123'")
        else:
            print("Administrador já existe no banco.")
    
    app.run(debug=True)






