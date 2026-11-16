from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Store, Service, Appointment

ag_bp = Blueprint("agend", __name__, url_prefix="/api/agendamentos")


@ag_bp.post("")
@login_required
def criar_agendamento():
    data = request.get_json() or {}
    store = Store.query.filter_by(slug=data.get("store_slug"), ativo=True).first()
    if not store:
        return jsonify(error="Loja não encontrada"), 404

    service = Service.query.filter_by(id=data.get("service_id"), store_id=store.id).first()
    if not service:
        return jsonify(error="Serviço não encontrado"), 404

    if not data.get("data") or not data.get("hora"):
        return jsonify(error="Data e hora são obrigatórias"), 400

    conflito = Appointment.query.filter_by(
        store_id=store.id, data=data["data"], hora=data["hora"]
    ).filter(Appointment.status != "Cancelado").first()
    if conflito:
        return jsonify(error="Horário já solicitado"), 409

    ag = Appointment(
        store_id=store.id, service_id=service.id,
        cliente_username=current_user.username,
        cliente_email=current_user.email,
        tecnica=data.get("tecnica"),
        data=data["data"], hora=data["hora"],
        observacao=data.get("observacao"),
        preco=service.preco,
    )
    db.session.add(ag)
    db.session.commit()

    return jsonify(id=ag.id, status=ag.status), 201