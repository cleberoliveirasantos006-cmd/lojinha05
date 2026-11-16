from flask import Blueprint, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Appointment, Order, Store, Service

cli_bp = Blueprint("cliente", __name__, url_prefix="/api/me")


@cli_bp.get("/agendamentos")
@login_required
def meus_agendamentos():
    ags = (Appointment.query
           .filter_by(cliente_username=current_user.username)
           .order_by(Appointment.criado_em.desc()).all())
    out = []
    for a in ags:
        store = Store.query.get(a.store_id)
        service = Service.query.get(a.service_id)
        out.append({
            "id": a.id, "store": store.nome if store else "-",
            "servico": service.nome if service else "-",
            "tecnica": a.tecnica, "data": a.data, "hora": a.hora,
            "preco": float(a.preco or 0), "status": a.status,
            "criado_em": a.criado_em.isoformat(),
        })
    return jsonify(out)


@cli_bp.get("/pedidos")
@login_required
def meus_pedidos():
    pedidos = (Order.query
               .filter_by(cliente_username=current_user.username)
               .order_by(Order.criado_em.desc()).all())
    out = []
    for o in pedidos:
        store = Store.query.get(o.store_id)
        out.append({
            "id": o.id, "store": store.nome if store else "-",
            "total": float(o.total), "status": o.status,
            "criado_em": o.criado_em.isoformat(),
            "itens": [{"nome": i.nome, "qtd": i.quantidade,
                       "preco": float(i.preco_unitario or 0)} for i in o.itens],
        })
    return jsonify(out)


@cli_bp.patch("/agendamentos/<int:ag_id>/cancelar")
@login_required
def cancelar_meu_agendamento(ag_id):
    a = Appointment.query.filter_by(id=ag_id, cliente_username=current_user.username).first()
    if not a:
        abort(404)
    if a.status != "Aguardando confirmação":
        return jsonify(error="Só é possível cancelar antes da confirmação"), 400
    a.status = "Cancelado"
    db.session.commit()
    return jsonify(ok=True)


@cli_bp.patch("/pedidos/<int:order_id>/cancelar")
@login_required
def cancelar_meu_pedido(order_id):
    o = Order.query.filter_by(id=order_id, cliente_username=current_user.username).first()
    if not o:
        abort(404)
    if o.status != "Aguardando confirmação":
        return jsonify(error="Só é possível cancelar antes da confirmação"), 400
    o.status = "Cancelado"
    db.session.commit()
    return jsonify(ok=True)