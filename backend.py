import os
from datetime import date, datetime
from functools import wraps

from flask import Flask, jsonify, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.security import check_password_hash, generate_password_hash

backend = Flask(__name__)
backend.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dom_do_sabor.db"
backend.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
backend.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")

db = SQLAlchemy(backend)


class Mesa(db.Model):
    __tablename__ = "mesas"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    disponivel = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "numero": self.numero,
            "disponivel": self.disponivel,
        }


class Reserva(db.Model):
    __tablename__ = "reservas"

    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey("mesas.id"), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    data_reserva = db.Column(db.Date, nullable=True)
    horario = db.Column(db.String(50), nullable=False)
    pessoas = db.Column(db.Integer, nullable=False)
    telefone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="ativa")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    mesa = db.relationship("Mesa", backref=db.backref("reservas", lazy=True))


class ItemCardapio(db.Model):
    __tablename__ = "itens_cardapio"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), nullable=False, default='pratos')
    imagem = db.Column(db.String(255), nullable=False, default='')
    ordem = db.Column(db.Integer, default=1)


with backend.app_context():
    db.create_all()
    reserva_columns = {column["name"] for column in inspect(db.engine).get_columns("reservas")}
    with db.engine.begin() as connection:
        if "data_reserva" not in reserva_columns:
            connection.execute(text("ALTER TABLE reservas ADD COLUMN data_reserva DATE"))
        if "status" not in reserva_columns:
            connection.execute(text("ALTER TABLE reservas ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'ativa'"))
    if Mesa.query.count() == 0:
        mesas_iniciais = [Mesa(numero=i, disponivel=True) for i in range(1, 13)]
        db.session.add_all(mesas_iniciais)
        db.session.commit()

    if ItemCardapio.query.count() == 0:
        itens_iniciais = [
            ItemCardapio(
                titulo='Picanha na brasa',
                descricao='Cortes nobres, sabor intenso e acabamento perfeito para uma mesa memorável.',
                categoria='pratos',
                imagem='images/rodiziocarne/18e85bdf44209e9320a14be8174761f1.jpg',
                ordem=1,
            ),
            ItemCardapio(
                titulo='Rodízio de massas',
                descricao='Massa artesanal, pizzas quentes e opções que agradam a todos os paladares.',
                categoria='rodizios',
                imagem='images/rodiziomassaepizzas/00c8a9ed39118068621788d25481d98f.jpg',
                ordem=2,
            ),
            ItemCardapio(
                titulo='Vinho do Porto',
                descricao='Elegância, aroma refinado e o acompanhamento ideal para a sua noite.',
                categoria='bebidas',
                imagem='images/bebidas/a027c436bbd2c68340f5e618fb933d9a.jpg',
                ordem=3,
            ),
            ItemCardapio(
                titulo='Crepe de morango',
                descricao='Final doce com textura leve, cremosidade e sabor marcante da casa.',
                categoria='sobremesas',
                imagem='images/sobremesas/0ac8688175d417151fa8df60db39f194.jpg',
                ordem=4,
            ),
        ]
        db.session.add_all(itens_iniciais)
        db.session.commit()


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_authenticated"):
            if request.path.startswith("/admin/") and request.method != "GET":
                return jsonify({"success": False, "message": "Faça login para continuar."}), 401
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


def get_reservation_date():
    requested_date = request.args.get("data", "").strip()
    try:
        return datetime.strptime(requested_date, "%Y-%m-%d").date() if requested_date else date.today()
    except ValueError:
        return date.today()


def mesa_is_available(mesa_id, reservation_date):
    return not Reserva.query.filter_by(
        mesa_id=mesa_id, data_reserva=reservation_date, status="ativa"
    ).first()


@backend.route('/')
def paginaPrincipal():
    return render_template('paginaPrincipal.html')


@backend.route('/contato')
def contato():
    return render_template('contato.html')


@backend.route('/receitas')
def pratosReceitas():
    return render_template('pratosReceitas.html')


@backend.route('/restaurante')
def restaurante():
    return render_template('restaurante.html')


@backend.route('/reservas', methods=['GET'])
def reservas():
    reservation_date = get_reservation_date()
    mesas = Mesa.query.order_by(Mesa.numero).all()
    availability = {mesa.id: mesa_is_available(mesa.id, reservation_date) for mesa in mesas}
    return render_template('reservas.html', mesas=mesas, reservation_date=reservation_date, availability=availability, hoje=date.today())


@backend.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        configured_username = os.environ.get("ADMIN_USERNAME", "admin")
        configured_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        password_matches = check_password_hash(configured_password, password) if configured_password.startswith("scrypt:") or configured_password.startswith("pbkdf2:") else password == configured_password
        if username == configured_username and password_matches:
            session["admin_authenticated"] = True
            next_url = request.args.get("next", "")
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("admin")
            return redirect(next_url)
        return render_template("admin_login.html", error="Usuário ou senha inválidos."), 401
    return render_template("admin_login.html")


@backend.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@backend.route('/admin', methods=['GET'])
@admin_required
def admin():
    mesas = Mesa.query.order_by(Mesa.numero).all()
    itens = ItemCardapio.query.order_by(ItemCardapio.ordem).all()
    reservas_ativas = Reserva.query.filter_by(status="ativa").order_by(Reserva.data_reserva, Reserva.horario).all()
    mesa_status = {mesa.id: not mesa_is_available(mesa.id, date.today()) for mesa in mesas}
    return render_template('admin.html', mesas=mesas, itens=itens, reservas=reservas_ativas, hoje=date.today(), mesa_status=mesa_status)


@backend.route('/admin/mesas-disponiveis', methods=['GET'])
@admin_required
def admin_mesas_disponiveis():
    reservation_date = get_reservation_date()
    mesas = Mesa.query.order_by(Mesa.numero).all()
    return jsonify({
        "success": True,
        "mesas": [
            {"id": mesa.id, "numero": mesa.numero, "disponivel": mesa_is_available(mesa.id, reservation_date)}
            for mesa in mesas
        ],
    })


@backend.route('/admin/mesa/<int:mesa_id>/reservas', methods=['GET'])
@admin_required
def admin_reservas_da_mesa(mesa_id):
    mesa = db.session.get(Mesa, mesa_id)
    if not mesa:
        return jsonify({"success": False, "message": "Mesa não encontrada."}), 404

    reservation_date = get_reservation_date()
    reservas = Reserva.query.filter_by(
        mesa_id=mesa.id, data_reserva=reservation_date, status="ativa"
    ).order_by(Reserva.horario).all()
    return jsonify({
        "success": True,
        "mesa": mesa.numero,
        "data": reservation_date.strftime("%d/%m/%Y"),
        "reservas": [
            {
                "id": reserva.id,
                "nome": reserva.nome,
                "horario": reserva.horario,
                "telefone": reserva.telefone,
                "email": reserva.email,
                "pessoas": reserva.pessoas,
            }
            for reserva in reservas
        ],
    })


@backend.route('/admin/mesa/<int:mesa_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_mesa(mesa_id):
    mesa = db.session.get(Mesa, mesa_id)
    if not mesa:
        return jsonify({"success": False, "message": "Mesa não encontrada."}), 404

    mesa.disponivel = not mesa.disponivel
    db.session.commit()
    return jsonify({"success": True, "mesa": mesa.to_dict()})


@backend.route('/admin/cardapio', methods=['POST'])
@admin_required
def admin_salvar_cardapio():
    titulo = request.form.get('titulo', '').strip()
    descricao = request.form.get('descricao', '').strip()
    categoria = request.form.get('categoria', 'pratos').strip()
    imagem = request.form.get('imagem', '').strip()
    ordem = request.form.get('ordem', '1')

    if not titulo or not descricao:
        return jsonify({"success": False, "message": "Título e descrição são obrigatórios."}), 400

    item = ItemCardapio(
        titulo=titulo,
        descricao=descricao,
        categoria=categoria,
        imagem=imagem or 'images/default.jpg',
        ordem=int(ordem or 1),
    )
    db.session.add(item)
    db.session.commit()

    return jsonify({"success": True, "item": {"id": item.id, "titulo": item.titulo, "categoria": item.categoria}})


@backend.route('/admin/cardapio/<int:item_id>/delete', methods=['POST'])
@admin_required
def admin_excluir_cardapio(item_id):
    item = db.session.get(ItemCardapio, item_id)
    if not item:
        return jsonify({"success": False, "message": "Item não encontrado."}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"success": True})


@backend.route('/reservas/<int:mesa_id>/confirmar', methods=['POST'])
def confirmar_reserva(mesa_id):
    mesa = db.session.get(Mesa, mesa_id)
    if not mesa:
        return jsonify({"success": False, "message": "Mesa não encontrada."}), 404

    tipo = request.form.get('tipo', '').strip().lower()
    nome = request.form.get('nome', '').strip()
    data_reserva = request.form.get('data_reserva', '').strip()
    horario = request.form.get('horario', '').strip()
    pessoas = request.form.get('quantas_pessoas', '').strip()
    telefone = request.form.get('telefone', '').strip()
    email = request.form.get('email', '').strip()

    if tipo not in {"rodizio", "alacarte"}:
        return jsonify({"success": False, "message": "Selecione um tipo de experiência válido."}), 400

    if not all([nome, data_reserva, horario, pessoas, telefone, email]):
        return jsonify({"success": False, "message": "Preencha todos os campos do formulário."}), 400

    try:
        qtd_pessoas = int(pessoas)
        data_formatada = datetime.strptime(data_reserva, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "message": "Data ou quantidade de pessoas inválida."}), 400

    if data_formatada < date.today():
        return jsonify({"success": False, "message": "Escolha uma data futura."}), 400
    if not mesa_is_available(mesa.id, data_formatada):
        return jsonify({"success": False, "message": "Essa mesa já está reservada para essa data."}), 400

    reserva = Reserva(
        mesa_id=mesa.id,
        tipo=tipo,
        nome=nome,
        data_reserva=data_formatada,
        horario=horario,
        pessoas=qtd_pessoas,
        telefone=telefone,
        email=email,
    )
    db.session.add(reserva)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Reserva confirmada com sucesso.",
        "mesa": mesa.to_dict(),
        "reserva_id": reserva.id,
        "redirect": url_for('pagamento', reserva_id=reserva.id),
    })


@backend.route('/admin/reservas', methods=['POST'])
@admin_required
def admin_adicionar_reserva():
    form = request.form
    try:
        data_reserva = datetime.strptime(form.get('data_reserva', ''), "%Y-%m-%d").date()
        pessoas = int(form.get('quantas_pessoas', ''))
        mesa_id = int(form.get('mesa_id', ''))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Preencha data, mesa e quantidade corretamente."}), 400

    required = [form.get(field, '').strip() for field in ('nome', 'horario', 'telefone', 'email')]
    mesa = db.session.get(Mesa, mesa_id)
    if not mesa or not all(required) or pessoas < 1:
        return jsonify({"success": False, "message": "Preencha todos os campos da reserva."}), 400
    if data_reserva < date.today():
        return jsonify({"success": False, "message": "Escolha uma data futura."}), 400
    if not mesa_is_available(mesa.id, data_reserva):
        return jsonify({"success": False, "message": "Essa mesa já está reservada para essa data."}), 400

    reserva = Reserva(
        mesa_id=mesa.id, tipo=form.get('tipo', 'rodizio'), nome=form.get('nome').strip(),
        data_reserva=data_reserva, horario=form.get('horario').strip(), pessoas=pessoas,
        telefone=form.get('telefone').strip(), email=form.get('email').strip(), status='ativa'
    )
    db.session.add(reserva)
    db.session.commit()
    return jsonify({"success": True, "message": "Reserva adicionada com sucesso."})


@backend.route('/admin/reservas/<int:reserva_id>/cancelar', methods=['POST'])
@admin_required
def admin_cancelar_reserva(reserva_id):
    reserva = db.session.get(Reserva, reserva_id)
    if not reserva:
        return jsonify({"success": False, "message": "Reserva não encontrada."}), 404
    reserva.status = "cancelada"
    db.session.commit()
    return jsonify({"success": True, "message": "Reserva cancelada."})


@backend.route('/pagamento')
def pagamento():
    reserva_id = request.args.get('reserva_id', type=int)
    reserva = db.session.get(Reserva, reserva_id) if reserva_id else None

    if not reserva:
        return redirect(url_for('reservas'))

    return render_template('pagamento.html', reserva=reserva)


if __name__ == '__main__':
    backend.run(debug=True)