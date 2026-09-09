import os

from flask import Flask

from database import ItemCardapio, Mesa, Reserva, db, init_database
from routes import register_routes


backend = Flask(__name__)
backend.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///dom_do_sabor.db"
backend.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
backend.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")

init_database(backend)
register_routes(backend)


if __name__ == "__main__":
    backend.run(debug=True)
