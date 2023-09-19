from flask import Flask, render_template, request, redirect, url_for, send_file, session
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename 
from flask_login import LoginManager, login_user, login_required, UserMixin, logout_user, current_user
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'key'

# Configurar a conexão com o banco de dados
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'jm_veiculos'
# Configurar a pasta onde as imagens serão salvas
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Inicializar o sistema de login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_index"

# Inicializar a extensão MySQL
mysql = MySQL(app)

# Classe de usuário para representar um usuário autenticado
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    # Consultar o banco de dados para carregar o usuário com base no user_id
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM funcionarios WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()
    
    if user_data:
        return User(user_data[0])  # Crie um objeto User com o ID do usuário
    else:
        return None  # Retorne None se o usuário não for encontrado

# Rota para a página inicial de clientes
@app.route("/sobre")
def sobre_index():
   
     
    return render_template("sobre.html")
    
# Rota para a página inicial de clientes
@app.route("/")
def cliente_index():
    if current_user.is_authenticated:
        # Se o usuário estiver autenticado, redirecione-o para outra página (funcionário)
        return redirect(url_for('funcionario_index'))
    
    # Consulta os veículos cadastrados no banco de dados
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM veiculos")
    veiculos = cur.fetchall()
    cur.close()
    
    return render_template("cliente.html", veiculos=veiculos)

# Rota para o processo de login
@app.route('/login_entrar', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Conectar ao banco de dados
        cur = mysql.connection.cursor()

        # Verificar as informações de login na tabela funcionarios
        cur.execute("SELECT * FROM funcionarios WHERE username = %s AND password = %s", (username, password))
        funcionario = cur.fetchone()
        cur.close()

        if funcionario is not None:
            funcionario_id = funcionario[0]
            user = User(funcionario_id)  # Crie um objeto User com o ID do funcionário
            login_user(user)  # Faça o login do usuário
            
            return redirect(url_for('funcionario_index'))  # Redireciona para a página protegida do funcionário
            
        else:
            # Se as informações estiverem incorretas, exiba uma mensagem de erro
            return render_template('login.html', error='Usuário ou senha incorretos')

    return render_template('login.html')

# Rota para a página de login
@app.route("/login_html")
def login_index():
    return render_template("login.html")

# Rota para realizar logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('cliente_index'))

# Rota para a página inicial de funcionários
@app.route("/funcionario")
@login_required
def funcionario_index():
    # Consulta os veículos cadastrados no banco de dados
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM veiculos")
    veiculos = cur.fetchall()
    cur.close()
    return render_template("funcionario.html", veiculos=veiculos)

# Rota para exibir o formulário de adicionar veículo
@app.route("/adicionar")
@login_required
def exibir_adicionar():
    return render_template("adicionar.html")

# Rota para adicionar um veículo
@app.route("/adicionar_veiculo", methods=["POST"])
@login_required 
def adicionar_veiculo():
    if request.method == "POST":
        # Recebe os dados do formulário
        tipo = request.form["tipo"]
        cor = request.form["cor"]
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        ano = request.form["ano"]
        estado = request.form["estado"]
        km_rodados = request.form["km_rodados"]
        leilao = request.form.get("leilao", False)
        formas_pagamento = request.form.getlist("formas_pagamento")

        # Processar a imagem enviada
        foto = request.files["foto"]
        if foto and allowed_file(foto.filename):
            # Garanta que o nome do arquivo é seguro usando secure_filename
            filename = secure_filename(foto.filename)
            # Salve a imagem na pasta de uploads
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Insira os dados no banco de dados, incluindo o caminho da imagem
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO veiculos (tipo, cor, marca, modelo, ano_fabricacao, estado, km_rodados, leilao, formas_pagamento, foto) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (tipo, cor, marca, modelo, ano, estado, km_rodados, leilao, ', '.join(formas_pagamento), filename))
            mysql.connection.commit()
            cur.close()

    return redirect(url_for("funcionario_index"))

# Função para verificar a extensão do arquivo permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Rota para excluir um veículo
@app.route("/excluir_veiculo/<int:veiculo_id>")
@login_required 
def excluir_veiculo(veiculo_id):
    # Exclui o veículo do banco de dados
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM veiculos WHERE id = %s", (veiculo_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for("funcionario_index"))

# Rota para editar um veículo
@app.route("/editar_veiculo/<int:veiculo_id>")
@login_required 
def editar_veiculo(veiculo_id):
    # Consulta as informações do veículo com base no ID
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM veiculos WHERE id = %s", (veiculo_id,))
    veiculo = cur.fetchone()
    cur.close()
    return render_template("editar_veiculo.html", veiculo=veiculo)

# Rota para atualizar um veículo
@app.route("/atualizar_veiculo/<int:veiculo_id>", methods=["POST"])
@login_required 
def atualizar_veiculo(veiculo_id):
    if request.method == "POST":
        # Recebe os dados do formulário
        tipo = request.form["tipo"]
        cor = request.form["cor"]
        marca = request.form["marca"]
        modelo = request.form["modelo"]
        ano = request.form["ano"]
        estado = request.form["estado"]
        km_rodados = request.form["km_rodados"]
        leilao = 1 if request.form.get("leilao") == "on" else 0  # Converte para 1 ou 0
        formas_pagamento = request.form.getlist("formas_pagamento")

        # Verifica se um arquivo de imagem foi enviado
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto.filename != '':
                # Salva a imagem no diretório de uploads
                foto.save(os.path.join(app.config['UPLOAD_FOLDER'], foto.filename))

                # Atualiza o nome da imagem no banco de dados
                cur = mysql.connection.cursor()
                cur.execute("UPDATE veiculos SET tipo=%s, cor=%s, marca=%s, modelo=%s, ano_fabricacao=%s, estado=%s, km_rodados=%s, leilao=%s, formas_pagamento=%s, foto=%s WHERE id=%s",
                            (tipo, cor, marca, modelo, ano, estado, km_rodados, leilao, ', '.join(formas_pagamento), foto.filename, veiculo_id))
                mysql.connection.commit()
                cur.close()
            else:
                # Se não houver nova imagem, atualize apenas os outros campos
                cur = mysql.connection.cursor()
                cur.execute("UPDATE veiculos SET tipo=%s, cor=%s, marca=%s, modelo=%s, ano_fabricacao=%s, estado=%s, km_rodados=%s, leilao=%s, formas_pagamento=%s WHERE id=%s",
                            (tipo, cor, marca, modelo, ano, estado, km_rodados, leilao, ', '.join(formas_pagamento), veiculo_id))
                mysql.connection.commit()
                cur.close()

    return redirect(url_for("funcionario_index"))

# Rota para servir arquivos enviados (fotos)
@app.route('/uploads/<filename>')
def get_uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

# Rota para aplicar filtro de pesquisa para clientes
@app.route("/filtro_cliente", methods=["GET", "POST"])
def filtro_cliente():
    if request.method == "POST":
        categoria = request.form.get("categoria")
        modelo = request.form.get("modelo")

        # Monta a consulta SQL baseada na categoria e no modelo
        consulta_sql = "SELECT * FROM veiculos WHERE 1"

        if categoria != "todos":
            consulta_sql += f" AND tipo = '{categoria}'"
        
        if modelo:
            consulta_sql += f" AND modelo LIKE '%{modelo}%'"

        # Consulta os veículos com base nos critérios selecionados
        cur = mysql.connection.cursor()
        cur.execute(consulta_sql)
        veiculos = cur.fetchall()
        cur.close()

        # Passa os valores da categoria e do modelo para o contexto do template
        return render_template("cliente.html", veiculos=veiculos, categoria=categoria, modelo=modelo)


    # Se for uma solicitação GET, carregue todos os veículos
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM veiculos")
    veiculos = cur.fetchall()
    cur.close()

    return render_template("cliente.html", veiculos=veiculos)

# Rota para aplicar filtro de pesquisa para funcionários
@app.route("/filtro_funcionario", methods=["GET", "POST"])
def filtro_funcionario():
    if request.method == "POST":
        categoria = request.form.get("categoria", "todos")
        modelo = request.form.get("modelo", "")
        id_veiculo = request.form.get("id_veiculo")

        # Monta a consulta SQL baseada na categoria e no modelo
        consulta_sql = "SELECT * FROM veiculos WHERE 1"

        if categoria != "todos":
            consulta_sql += f" AND tipo = '{categoria}'"
        
        if modelo:
            consulta_sql += f" AND modelo LIKE '%{modelo}%'"

        if id_veiculo:
            consulta_sql += f" AND id = {id_veiculo}"     

        # Consulta os veículos com base nos critérios selecionados
        cur = mysql.connection.cursor()
        cur.execute(consulta_sql)
        veiculos = cur.fetchall()
        cur.close()

        return render_template("funcionario.html", veiculos=veiculos, categoria=categoria, modelo=modelo)

    # Se for uma solicitação GET, carregue todos os veículos
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM veiculos")
    veiculos = cur.fetchall()
    cur.close()

    return render_template("funcionario.html", veiculos=veiculos)

if __name__ == "__main__":
    app.run(debug=True)
