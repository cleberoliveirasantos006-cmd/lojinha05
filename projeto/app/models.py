from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120))
    role = db.Column(db.String(20), default="customer")  # customer | admin
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    store = db.relationship("Store", foreign_keys=[store_id], backref="admins")

    def set_password(self, pwd):
        self.password_hash = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password_hash, pwd)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_super_admin(self):
        return self.role == "admin" and self.store_id is None


class Store(db.Model):
    __tablename__ = "stores"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(120), nullable=False)
    area = db.Column(db.String(120))
    cidade = db.Column(db.String(120))
    bio = db.Column(db.Text)
    inicial = db.Column(db.String(4))
    cor = db.Column(db.String(20))
    instagram = db.Column(db.String(120))
    whatsapp = db.Column(db.String(30))
    email_notificacao = db.Column(db.String(120), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    imagem_url = db.Column(db.String(500), nullable=True)

    servicos = db.relationship("Service", backref="store", cascade="all, delete-orphan")
    produtos = db.relationship("Product", backref="store", cascade="all, delete-orphan")


class Service(db.Model):
    __tablename__ = "services"
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    opcoes = db.Column(db.JSON, default=list)


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    emoji = db.Column(db.String(10))
    imagem_url = db.Column(db.String(500), nullable=True)


class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    cliente_username = db.Column(db.String(80), nullable=False)
    cliente_email = db.Column(db.String(120))
    tecnica = db.Column(db.String(120))
    data = db.Column(db.String(10), nullable=False)
    hora = db.Column(db.String(5), nullable=False)
    observacao = db.Column(db.Text)
    preco = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(40), default="Aguardando confirmação")
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    store = db.relationship("Store")
    service = db.relationship("Service")


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("stores.id"), nullable=False)
    cliente_username = db.Column(db.String(80), nullable=False)
    cliente_email = db.Column(db.String(120))
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(40), default="Aguardando confirmação")
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    store = db.relationship("Store")
    itens = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    nome = db.Column(db.String(120))
    quantidade = db.Column(db.Integer, default=1)
    preco_unitario = db.Column(db.Numeric(10, 2))
