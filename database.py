from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text


db = SQLAlchemy()


class Mesa(db.Model):
    __tablename__ = "mesas"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    disponivel = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {"id": self.id, "numero": self.numero, "disponivel": self.disponivel}


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
    categoria = db.Column(db.String(50), nullable=False, default="pratos")
    imagem = db.Column(db.String(255), nullable=False, default="")
    ordem = db.Column(db.Integer, default=1)


def init_database(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        reserva_columns = {column["name"] for column in inspect(db.engine).get_columns("reservas")}
        with db.engine.begin() as connection:
            if "data_reserva" not in reserva_columns:
                connection.execute(text("ALTER TABLE reservas ADD COLUMN data_reserva DATE"))
            if "status" not in reserva_columns:
                connection.execute(text("ALTER TABLE reservas ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'ativa'"))

        if Mesa.query.count() == 0:
            db.session.add_all(Mesa(numero=numero, disponivel=True) for numero in range(1, 13))
            db.session.commit()

        if ItemCardapio.query.count() == 0:
            db.session.add_all([
                ItemCardapio(
                    titulo="Picanha na brasa",
                    descricao="Cortes nobres, sabor intenso e acabamento perfeito para uma mesa memorável.",
                    categoria="pratos",
                    imagem="images/rodiziocarne/18e85bdf44209e9320a14be8174761f1.jpg",
                    ordem=1,
                ),
                ItemCardapio(
                    titulo="Rodízio de massas",
                    descricao="Massa artesanal, pizzas quentes e opções que agradam a todos os paladares.",
                    categoria="rodizios",
                    imagem="images/rodiziomassaepizzas/00c8a9ed39118068621788d25481d98f.jpg",
                    ordem=2,
                ),
                ItemCardapio(
                    titulo="Vinho do Porto",
                    descricao="Elegância, aroma refinado e o acompanhamento ideal para a sua noite.",
                    categoria="bebidas",
                    imagem="images/bebidas/a027c436bbd2c68340f5e618fb933d9a.jpg",
                    ordem=3,
                ),
                ItemCardapio(
                    titulo="Crepe de morango",
                    descricao="Final doce com textura leve, cremosidade e sabor marcante da casa.",
                    categoria="sobremesas",
                    imagem="images/sobremesas/0ac8688175d417151fa8df60db39f194.jpg",
                    ordem=4,
                ),
            ])
            db.session.commit()
