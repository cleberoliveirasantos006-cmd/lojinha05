from flask import Blueprint, jsonify, abort, request
from flask_login import login_required, current_user
from app.extensions import db, limiter
from app.models import Appointment, Order, Store, Service, Pergunta

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
            "motivo_negacao": a.motivo_negacao,
            "mensagem_lojista": a.mensagem_lojista,
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
            "motivo_negacao": o.motivo_negacao,
            "mensagem_lojista": o.mensagem_lojista,
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


# ---------- PERGUNTAS DO CLIENTE ----------
@cli_bp.get("/perguntas")
@login_required
def minhas_perguntas():
    qs = (Pergunta.query
          .filter_by(cliente_username=current_user.username)
          .order_by(Pergunta.criado_em.desc()).all())
    out = []
    for q in qs:
        store = Store.query.get(q.store_id)
        out.append({
            "id": q.id, "store": store.nome if store else "-",
            "pergunta": q.pergunta, "resposta": q.resposta,
            "respondido_em": q.respondido_em.isoformat() if q.respondido_em else None,
            "criado_em": q.criado_em.isoformat(),
        })
    return jsonify(out)


@cli_bp.post("/perguntas")
@login_required
@limiter.limit("10 per hour")
def enviar_pergunta():
    d = request.get_json() or {}
    store_slug = d.get("store_slug")
    texto = (d.get("pergunta") or "").strip()
    if not store_slug or not texto:
        return jsonify(error="Loja e pergunta obrigatórias"), 400

    store = Store.query.filter_by(slug=store_slug, ativo=True).first()
    if not store:
        return jsonify(error="Loja não encontrada"), 404

    p = Pergunta(cliente_username=current_user.username, store_id=store.id, pergunta=texto)
    db.session.add(p)
    db.session.commit()
    return jsonify(id=p.id), 201
