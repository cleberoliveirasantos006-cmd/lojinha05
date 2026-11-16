from flask import Blueprint, jsonify, abort
from app.models import Store

prof_bp = Blueprint("prof", __name__, url_prefix="/api")


def _store_to_dict(s, incluir_itens=True):
    data = {
        "id": s.id, "slug": s.slug, "nome": s.nome, "area": s.area,
        "cidade": s.cidade, "bio": s.bio, "inicial": s.inicial, "cor": s.cor,
        "instagram": s.instagram, "whatsapp": s.whatsapp,
    }
    if incluir_itens:
        data["servicos"] = [
            {"id": sv.id, "nome": sv.nome, "preco": float(sv.preco), "opcoes": sv.opcoes or []}
            for sv in s.servicos
        ]
        data["produtos"] = [
            {"id": p.id, "nome": p.nome, "descricao": p.descricao,
             "preco": float(p.preco), "emoji": p.emoji}
            for p in s.produtos
        ]
    return data


@prof_bp.get("/profissionais")
def listar_profissionais():
    stores = Store.query.filter_by(ativo=True).all()
    return jsonify([_store_to_dict(s, incluir_itens=False) for s in stores])


@prof_bp.get("/profissionais/<slug>")
def detalhe_profissional(slug):
    s = Store.query.filter_by(slug=slug, ativo=True).first()
    if not s:
        abort(404)
    return jsonify(_store_to_dict(s))