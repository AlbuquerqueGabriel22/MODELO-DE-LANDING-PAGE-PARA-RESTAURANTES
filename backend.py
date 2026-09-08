from datetime import datetime

from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

backend = Flask(__name__)
backend.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dom_do_sabor.db"
backend.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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
    horario = db.Column(db.String(50), nullable=False)
    pessoas = db.Column(db.Integer, nullable=False)
    telefone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(150), nullable=False)
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
    mesas = Mesa.query.order_by(Mesa.numero).all()
    return render_template('reservas.html', mesas=mesas)


@backend.route('/admin', methods=['GET'])
def admin():
    mesas = Mesa.query.order_by(Mesa.numero).all()
    itens = ItemCardapio.query.order_by(ItemCardapio.ordem).all()
    return render_template('admin.html', mesas=mesas, itens=itens)


@backend.route('/admin/mesa/<int:mesa_id>/toggle', methods=['POST'])
def admin_toggle_mesa(mesa_id):
    mesa = db.session.get(Mesa, mesa_id)
    if not mesa:
        return jsonify({"success": False, "message": "Mesa não encontrada."}), 404

    mesa.disponivel = not mesa.disponivel
    db.session.commit()
    return jsonify({"success": True, "mesa": mesa.to_dict()})


@backend.route('/admin/cardapio', methods=['POST'])
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
def admin_excluir_cardapio(item_id):
    item = db.session.get(ItemCardapio, item_id)
    if not item:
        return jsonify({"success": False, "message": "Item não encontrado."}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"success": True})


@backend.route('/reservas/<int:mesa_id>/toggle', methods=['POST'])
def alternar_reserva(mesa_id):
    mesa = db.session.get(Mesa, mesa_id)
    if not mesa:
        return jsonify({"success": False, "message": "Mesa não encontrada."}), 404

    mesa.disponivel = not mesa.disponivel
    db.session.commit()

    if mesa.disponivel:
        mensagem = f"Mesa {mesa.numero} liberada com sucesso."
    else:
        mensagem = f"Mesa {mesa.numero} reservada com sucesso."

    return jsonify({"success": True, "mesa": mesa.to_dict(), "message": mensagem})


@backend.route('/reservas/<int:mesa_id>/confirmar', methods=['POST'])
def confirmar_reserva(mesa_id):
    mesa = db.session.get(Mesa, mesa_id)
    if not mesa:
        return jsonify({"success": False, "message": "Mesa não encontrada."}), 404

    if not mesa.disponivel:
        return jsonify({"success": False, "message": "Essa mesa já está reservada."}), 400

    tipo = request.form.get('tipo', '').strip().lower()
    nome = request.form.get('nome', '').strip()
    horario = request.form.get('horario', '').strip()
    pessoas = request.form.get('quantas_pessoas', '').strip()
    telefone = request.form.get('telefone', '').strip()
    email = request.form.get('email', '').strip()

    if tipo not in {"rodizio", "alacarte"}:
        return jsonify({"success": False, "message": "Selecione um tipo de experiência válido."}), 400

    if not all([nome, horario, pessoas, telefone, email]):
        return jsonify({"success": False, "message": "Preencha todos os campos do formulário."}), 400

    try:
        qtd_pessoas = int(pessoas)
    except ValueError:
        return jsonify({"success": False, "message": "Quantidade de pessoas inválida."}), 400

    mesa.disponivel = False
    reserva = Reserva(
        mesa_id=mesa.id,
        tipo=tipo,
        nome=nome,
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


@backend.route('/pagamento')
def pagamento():
    reserva_id = request.args.get('reserva_id', type=int)
    reserva = db.session.get(Reserva, reserva_id) if reserva_id else None

    if not reserva:
        return redirect(url_for('reservas'))

    return render_template('pagamento.html', reserva=reserva)


if __name__ == '__main__':
    backend.run(debug=True)