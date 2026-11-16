from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Store, Product, Order, OrderItem

ord_bp = Blueprint("ord", __name__, url_prefix="/api/pedidos")


@ord_bp.post("")
@login_required
def criar_pedido():
    data = request.get_json() or {}
    store = Store.query.filter_by(slug=data.get("store_slug"), ativo=True).first()
    if not store:
        return jsonify(error="Loja não encontrada"), 404

    itens_req = data.get("itens") or []
    if not itens_req:
        return jsonify(error="Pedido vazio"), 400

    order = Order(
        store_id=store.id,
        cliente_username=current_user.username,
        cliente_email=current_user.email,
        total=0,
    )
    db.session.add(order)
    db.session.flush()

    total = 0.0
    for it in itens_req:
        prod = Product.query.filter_by(id=it.get("product_id"), store_id=store.id).first()
        if not prod:
            db.session.rollback()
            return jsonify(error=f"Produto {it.get('product_id')} não encontrado"), 400
        qtd = int(it.get("quantidade") or 1)
        total += float(prod.preco) * qtd
        db.session.add(OrderItem(
            order_id=order.id, product_id=prod.id, nome=prod.nome,
            quantidade=qtd, preco_unitario=prod.preco,
        ))

    order.total = total
    db.session.commit()

    return jsonify(id=order.id, total=float(order.total)), 201