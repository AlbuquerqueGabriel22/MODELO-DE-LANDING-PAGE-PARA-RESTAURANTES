import os
from datetime import date, datetime
from functools import wraps

from flask import jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database import ItemCardapio, Mesa, Reserva, db


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


def pagina_principal():
    return render_template("paginaPrincipal.html")


def contato():
    return render_template("contato.html")


def pratos_receitas():
    return render_template("pratosReceitas.html")


def restaurante():
    return render_template("restaurante.html")


def reservas():
    reservation_date = get_reservation_date()
    mesas = Mesa.query.order_by(Mesa.numero).all()
    availability = {mesa.id: mesa_is_available(mesa.id, reservation_date) for mesa in mesas}
    return render_template(
        "reservas.html",
        mesas=mesas,
        reservation_date=reservation_date,
        availability=availability,
        hoje=date.today(),
    )


def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        configured_username = os.environ.get("ADMIN_USERNAME", "admin")
        configured_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        password_matches = (
            check_password_hash(configured_password, password)
            if configured_password.startswith(("scrypt:", "pbkdf2:"))
            else password == configured_password
        )
        if username == configured_username and password_matches:
            session["admin_authenticated"] = True
            next_url = request.args.get("next", "")
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("admin")
            return redirect(next_url)
        return render_template("admin_login.html", error="Usuário ou senha inválidos."), 401
    return render_template("admin_login.html")


def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@admin_required
def admin():
    mesas = Mesa.query.order_by(Mesa.numero).all()
    itens = ItemCardapio.query.order_by(ItemCardapio.ordem).all()
    reservas_ativas = Reserva.query.filter_by(status="ativa").order_by(Reserva.data_reserva, Reserva.horario).all()
    mesa_status = {
        mesa.id: Reserva.query.filter_by(mesa_id=mesa.id, status="ativa").first() is not None
        for mesa in mesas
    }
    return render_template(
        "admin.html",
        mesas=mesas,
        itens=itens,
        reservas=reservas_ativas,
        hoje=date.today(),
        mesa_status=mesa_status,
    )


@admin_required
def admin_mesas_disponiveis():
    reservation_date = get_reservation_date()
    mesas = Mesa.query.order_by(Mesa.numero).all()
    return jsonify({
        "success": True,
        "mesas": [
            {
                "id": mesa.id,
                "numero": mesa.numero,
                "disponivel": mesa_is_available(mesa.id, reservation_date),
                "tem_agendamento": Reserva.query.filter_by(mesa_id=mesa.id, status="ativa").first() is not None,
            }
            for mesa in mesas
        ],
    })


@admin_required
def admin_reservas_da_mesa(mesa_id):
    mesa = db.session.get(Mesa, mesa_id)
    if not mesa:
        return jsonify({"success": False, "message": "Mesa não encontrada."}), 404

    reservas_ativas = Reserva.query.filter_by(
        mesa_id=mesa.id, status="ativa"
    ).order_by(Reserva.data_reserva, Reserva.horario).all()
    return jsonify({
        "success": True,
        "mesa": mesa.numero,
        "reservas": [
            {
                "id": reserva.id,
                "nome": reserva.nome,
                "data": reserva.data_reserva.strftime("%d/%m/%Y") if reserva.data_reserva else "Data antiga",
                "horario": reserva.horario,
                "telefone": reserva.telefone,
                "email": reserva.email,
                "pessoas": reserva.pessoas,
            }
            for reserva in reservas_ativas
        ],
    })


@admin_required
def admin_toggle_mesa(mesa_id):
    mesa = db.session.get(Mesa, mesa_id)
    if not mesa:
        return jsonify({"success": False, "message": "Mesa não encontrada."}), 404
    mesa.disponivel = not mesa.disponivel
    db.session.commit()
    return jsonify({"success": True, "mesa": mesa.to_dict()})


@admin_required
def admin_salvar_cardapio():
    titulo = request.form.get("titulo", "").strip()
    descricao = request.form.get("descricao", "").strip()
    categoria = request.form.get("categoria", "pratos").strip()
    imagem = request.form.get("imagem", "").strip()
    ordem = request.form.get("ordem", "1")
    if not titulo or not descricao:
        return jsonify({"success": False, "message": "Título e descrição são obrigatórios."}), 400
    item = ItemCardapio(
        titulo=titulo,
        descricao=descricao,
        categoria=categoria,
        imagem=imagem or "images/default.jpg",
        ordem=int(ordem or 1),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"success": True, "item": {"id": item.id, "titulo": item.titulo, "categoria": item.categoria}})


@admin_required
def admin_excluir_cardapio(item_id):
    item = db.session.get(ItemCardapio, item_id)
    if not item:
        return jsonify({"success": False, "message": "Item não encontrado."}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"success": True})


def confirmar_reserva(mesa_id):
    mesa = db.session.get(Mesa, mesa_id)
    if not mesa:
        return jsonify({"success": False, "message": "Mesa não encontrada."}), 404

    tipo = request.form.get("tipo", "").strip().lower()
    nome = request.form.get("nome", "").strip()
    data_reserva = request.form.get("data_reserva", "").strip()
    horario = request.form.get("horario", "").strip()
    pessoas = request.form.get("quantas_pessoas", "").strip()
    telefone = request.form.get("telefone", "").strip()
    email = request.form.get("email", "").strip()
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
        "redirect": url_for("pagamento", reserva_id=reserva.id),
    })


@admin_required
def admin_adicionar_reserva():
    form = request.form
    try:
        data_reserva = datetime.strptime(form.get("data_reserva", ""), "%Y-%m-%d").date()
        pessoas = int(form.get("quantas_pessoas", ""))
        mesa_id = int(form.get("mesa_id", ""))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Preencha data, mesa e quantidade corretamente."}), 400

    required = [form.get(field, "").strip() for field in ("nome", "horario", "telefone", "email")]
    mesa = db.session.get(Mesa, mesa_id)
    if not mesa or not all(required) or pessoas < 1:
        return jsonify({"success": False, "message": "Preencha todos os campos da reserva."}), 400
    if data_reserva < date.today():
        return jsonify({"success": False, "message": "Escolha uma data futura."}), 400
    if not mesa_is_available(mesa.id, data_reserva):
        return jsonify({"success": False, "message": "Essa mesa já está reservada para essa data."}), 400

    reserva = Reserva(
        mesa_id=mesa.id,
        tipo=form.get("tipo", "rodizio"),
        nome=form.get("nome").strip(),
        data_reserva=data_reserva,
        horario=form.get("horario").strip(),
        pessoas=pessoas,
        telefone=form.get("telefone").strip(),
        email=form.get("email").strip(),
        status="ativa",
    )
    db.session.add(reserva)
    db.session.commit()
    return jsonify({"success": True, "message": "Reserva adicionada com sucesso."})


@admin_required
def admin_cancelar_reserva(reserva_id):
    reserva = db.session.get(Reserva, reserva_id)
    if not reserva:
        return jsonify({"success": False, "message": "Reserva não encontrada."}), 404
    reserva.status = "cancelada"
    db.session.commit()
    return jsonify({"success": True, "message": "Reserva cancelada."})


def pagamento():
    reserva_id = request.args.get("reserva_id", type=int)
    reserva = db.session.get(Reserva, reserva_id) if reserva_id else None
    if not reserva:
        return redirect(url_for("reservas"))
    return render_template("pagamento.html", reserva=reserva)


def register_routes(app):
    routes = [
        ("paginaPrincipal", "/", pagina_principal, ["GET"]),
        ("contato", "/contato", contato, ["GET"]),
        ("pratosReceitas", "/receitas", pratos_receitas, ["GET"]),
        ("restaurante", "/restaurante", restaurante, ["GET"]),
        ("reservas", "/reservas", reservas, ["GET"]),
        ("admin_login", "/admin/login", admin_login, ["GET", "POST"]),
        ("admin_logout", "/admin/logout", admin_logout, ["GET"]),
        ("admin", "/admin", admin, ["GET"]),
        ("admin_mesas_disponiveis", "/admin/mesas-disponiveis", admin_mesas_disponiveis, ["GET"]),
        ("admin_reservas_da_mesa", "/admin/mesa/<int:mesa_id>/reservas", admin_reservas_da_mesa, ["GET"]),
        ("admin_toggle_mesa", "/admin/mesa/<int:mesa_id>/toggle", admin_toggle_mesa, ["POST"]),
        ("admin_salvar_cardapio", "/admin/cardapio", admin_salvar_cardapio, ["POST"]),
        ("admin_excluir_cardapio", "/admin/cardapio/<int:item_id>/delete", admin_excluir_cardapio, ["POST"]),
        ("confirmar_reserva", "/reservas/<int:mesa_id>/confirmar", confirmar_reserva, ["POST"]),
        ("admin_adicionar_reserva", "/admin/reservas", admin_adicionar_reserva, ["POST"]),
        ("admin_cancelar_reserva", "/admin/reservas/<int:reserva_id>/cancelar", admin_cancelar_reserva, ["POST"]),
        ("pagamento", "/pagamento", pagamento, ["GET"]),
    ]
    for endpoint, rule, view, methods in routes:
        app.add_url_rule(rule, endpoint=endpoint, view_func=view, methods=methods)
