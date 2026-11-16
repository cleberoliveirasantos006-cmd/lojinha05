from flask import Blueprint, request, jsonify
from flask_login import current_user
from app.extensions import db
from app.models import Store, Service, Product, Appointment, Order, User
from app.api._decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ================================================================
# LOJAS
# ================================================================
@admin_bp.get("/lojas")
@admin_required
def listar_lojas():
    q = Store.query
    if current_user.store_id:
        q = q.filter_by(id=current_user.store_id)
    return jsonify([{
        "id": s.id, "slug": s.slug, "nome": s.nome, "area": s.area,
        "cidade": s.cidade, "email_notificacao": s.email_notificacao,
        "ativo": s.ativo,
    } for s in q.all()])


@admin_bp.post("/lojas")
@admin_required
def criar_loja():
    if current_user.store_id:
        return jsonify(error="Admin de loja não pode criar outra loja"), 403
    d = request.get_json() or {}
    if not all(d.get(k) for k in ("slug", "nome", "email_notificacao")):
        return jsonify(error="slug, nome e email_notificacao obrigatórios"), 400
    if Store.query.filter_by(slug=d["slug"]).first():
        return jsonify(error="Slug já existe"), 409

    s = Store(
        slug=d["slug"], nome=d["nome"], area=d.get("area"),
        cidade=d.get("cidade"), bio=d.get("bio"), inicial=d.get("inicial"),
        cor=d.get("cor"), instagram=d.get("instagram"),
        whatsapp=d.get("whatsapp"), email_notificacao=d["email_notificacao"],
    )
    db.session.add(s)
    db.session.commit()
    return jsonify(id=s.id), 201


@admin_bp.put("/lojas/<int:store_id>")
@admin_required
def editar_loja(store_id):
    if current_user.store_id and current_user.store_id != store_id:
        return jsonify(error="Sem permissão"), 403
    s = Store.query.get_or_404(store_id)
    d = request.get_json() or {}
    for campo in ("nome", "area", "cidade", "bio", "inicial", "cor",
                  "instagram", "whatsapp", "email_notificacao", "ativo"):
        if campo in d:
            setattr(s, campo, d[campo])
    db.session.commit()
    return jsonify(ok=True)


@admin_bp.delete("/lojas/<int:store_id>")
@admin_required
def deletar_loja(store_id):
    if current_user.store_id:
        return jsonify(error="Admin de loja não pode deletar loja"), 403
    s = Store.query.get_or_404(store_id)
    db.session.delete(s)
    db.session.commit()
    return jsonify(ok=True)


# ================================================================
# SERVIÇOS
# ================================================================
@admin_bp.post("/lojas/<int:store_id>/servicos")
@admin_required
def criar_servico(store_id):
    if current_user.store_id and current_user.store_id != store_id:
        return jsonify(error="Sem permissão"), 403
    Store.query.get_or_404(store_id)
    d = request.get_json() or {}
    if not d.get("nome") or d.get("preco") is None:
        return jsonify(error="nome e preco obrigatórios"), 400
    sv = Service(store_id=store_id, nome=d["nome"],
                 preco=d["preco"], opcoes=d.get("opcoes") or [])
    db.session.add(sv)
    db.session.commit()
    return jsonify(id=sv.id), 201


@admin_bp.delete("/servicos/<int:service_id>")
@admin_required
def deletar_servico(service_id):
    sv = Service.query.get_or_404(service_id)
    if current_user.store_id and current_user.store_id != sv.store_id:
        return jsonify(error="Sem permissão"), 403
    db.session.delete(sv)
    db.session.commit()
    return jsonify(ok=True)


# ================================================================
# PRODUTOS
# ================================================================
@admin_bp.post("/lojas/<int:store_id>/produtos")
@admin_required
def criar_produto(store_id):
    if current_user.store_id and current_user.store_id != store_id:
        return jsonify(error="Sem permissão"), 403
    Store.query.get_or_404(store_id)
    d = request.get_json() or {}
    if not d.get("nome") or d.get("preco") is None:
        return jsonify(error="nome e preco obrigatórios"), 400
    p = Product(store_id=store_id, nome=d["nome"],
                descricao=d.get("descricao"), preco=d["preco"],
                emoji=d.get("emoji"))
    db.session.add(p)
    db.session.commit()
    return jsonify(id=p.id), 201


@admin_bp.delete("/produtos/<int:product_id>")
@admin_required
def deletar_produto(product_id):
    p = Product.query.get_or_404(product_id)
    if current_user.store_id and current_user.store_id != p.store_id:
        return jsonify(error="Sem permissão"), 403
    db.session.delete(p)
    db.session.commit()
    return jsonify(ok=True)


# ================================================================
# AGENDAMENTOS
# ================================================================
@admin_bp.get("/agendamentos")
@admin_required
def admin_agendamentos():
    q = Appointment.query
    if current_user.store_id:
        q = q.filter_by(store_id=current_user.store_id)
    out = []
    for a in q.order_by(Appointment.criado_em.desc()).all():
        store = Store.query.get(a.store_id)
        service = Service.query.get(a.service_id)
        out.append({
            "id": a.id, "store": store.nome if store else "-",
            "servico": service.nome if service else "-",
            "cliente": a.cliente_username, "data": a.data, "hora": a.hora,
            "tecnica": a.tecnica, "observacao": a.observacao,
            "status": a.status, "preco": float(a.preco or 0),
        })
    return jsonify(out)


@admin_bp.patch("/agendamentos/<int:ag_id>")
@admin_required
def mudar_status_agendamento(ag_id):
    a = Appointment.query.get_or_404(ag_id)
    if current_user.store_id and a.store_id != current_user.store_id:
        return jsonify(error="Sem permissão"), 403
    d = request.get_json() or {}
    a.status = d.get("status", a.status)
    db.session.commit()
    return jsonify(ok=True, status=a.status)


# ================================================================
# PEDIDOS
# ================================================================
@admin_bp.get("/pedidos")
@admin_required
def admin_pedidos():
    q = Order.query
    if current_user.store_id:
        q = q.filter_by(store_id=current_user.store_id)
    out = []
    for o in q.order_by(Order.criado_em.desc()).all():
        store = Store.query.get(o.store_id)
        out.append({
            "id": o.id, "store": store.nome if store else "-",
            "cliente": o.cliente_username, "total": float(o.total),
            "status": o.status, "criado_em": o.criado_em.isoformat(),
            "itens": [{"nome": i.nome, "qtd": i.quantidade,
                       "preco": float(i.preco_unitario or 0)} for i in o.itens],
        })
    return jsonify(out)


@admin_bp.patch("/pedidos/<int:order_id>")
@admin_required
def mudar_status_pedido(order_id):
    o = Order.query.get_or_404(order_id)
    if current_user.store_id and o.store_id != current_user.store_id:
        return jsonify(error="Sem permissão"), 403
    d = request.get_json() or {}
    o.status = d.get("status", o.status)
    db.session.commit()
    return jsonify(ok=True, status=o.status)


# ================================================================
# USUÁRIOS / ADMINS
# ================================================================
@admin_bp.get("/usuarios")
@admin_required
def listar_usuarios():
    role = request.args.get("role")
    q = User.query
    if role:
        q = q.filter_by(role=role)

    # Admin de loja só vê admins da própria loja
    if current_user.store_id:
        q = q.filter(
            (User.store_id == current_user.store_id) | (User.id == current_user.id)
        )

    return jsonify([{
        "id": u.id, "username": u.username, "email": u.email,
        "role": u.role, "store_id": u.store_id,
        "criado_em": u.created_at.isoformat() if u.created_at else None,
    } for u in q.order_by(User.id).all()])


@admin_bp.post("/usuarios")
@admin_required
def criar_admin():
    """
    Cria um novo admin.
    - Admin de loja (store_id != None): só cria admin para a própria loja.
    - Super-admin (store_id == None): cria admin de qualquer loja
      ou outro super-admin (deixando store_slug vazio).
    """
    d = request.get_json() or {}
    username = (d.get("username") or "").strip()
    password = d.get("password") or ""
    email = (d.get("email") or "").strip() or None
    store_slug = d.get("store_slug")

    if not username or len(password) < 6:
        return jsonify(error="username e password (mín. 6) obrigatórios"), 400

    if User.query.filter_by(username=username).first():
        return jsonify(error="Usuário já existe"), 409

    store_id = None
    if store_slug:
        store = Store.query.filter_by(slug=store_slug).first()
        if not store:
            return jsonify(error="Loja não encontrada"), 404
        store_id = store.id

    # Admin de loja só cria admin da própria loja
    if current_user.store_id is not None and store_id != current_user.store_id:
        return jsonify(error="Só é possível criar admin da própria loja"), 403

    novo = User(username=username, email=email, role="admin", store_id=store_id)
    novo.set_password(password)
    db.session.add(novo)
    db.session.commit()
    return jsonify(id=novo.id, username=novo.username, store_id=novo.store_id), 201


@admin_bp.patch("/usuarios/me/senha")
@admin_required
def trocar_minha_senha():
    """Cada admin troca APENAS a própria senha, informando a atual."""
    d = request.get_json() or {}
    senha_atual = d.get("senha_atual") or ""
    nova_senha = d.get("nova_senha") or ""

    if not current_user.check_password(senha_atual):
        return jsonify(error="Senha atual incorreta"), 400
    if len(nova_senha) < 6:
        return jsonify(error="Nova senha deve ter no mínimo 6 caracteres"), 400

    current_user.set_password(nova_senha)
    db.session.commit()
    return jsonify(ok=True)


@admin_bp.patch("/usuarios/<int:user_id>/senha")
@admin_required
def redefinir_senha_de_outro(user_id):
    """
    Super-admin pode redefinir a senha de qualquer admin
    (útil em caso de perda). Admin de loja NÃO pode.
    Cada admin troca a sua via /me/senha.
    """
    if not current_user.is_super_admin:
        return jsonify(error="Apenas super-admin pode redefinir senha de outro admin"), 403

    alvo = User.query.get_or_404(user_id)
    if alvo.role != "admin":
        return jsonify(error="Alvo não é admin"), 400

    d = request.get_json() or {}
    nova = d.get("nova_senha") or ""
    if len(nova) < 6:
        return jsonify(error="Nova senha deve ter no mínimo 6 caracteres"), 400

    alvo.set_password(nova)
    db.session.commit()
    return jsonify(ok=True)


@admin_bp.delete("/usuarios/<int:user_id>")
@admin_required
def deletar_admin(user_id):
    """Apenas super-admin deleta admins. Não pode deletar a si mesmo."""
    if not current_user.is_super_admin:
        return jsonify(error="Apenas super-admin pode deletar admins"), 403
    if user_id == current_user.id:
        return jsonify(error="Você não pode deletar a si mesmo"), 400

    alvo = User.query.get_or_404(user_id)
    if alvo.role != "admin":
        return jsonify(error="Alvo não é admin"), 400

    db.session.delete(alvo)
    db.session.commit()
    return jsonify(ok=True)