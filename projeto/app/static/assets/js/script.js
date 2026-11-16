const moeda = v => Number(v).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

async function api(url, opts = {}) {
  const r = await fetch(url, { credentials: "include", ...opts });
  if (!r.ok && r.status !== 204) throw new Error((await r.json()).error || r.statusText);
  return r.status === 204 ? null : r.json();
}

async function usuarioLogado() {
  try { return await api("/api/auth/me"); } catch { return { authenticated: false }; }
}

async function sair() {
  await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
  localStorage.removeItem("logado");
  location.href = "/index.html";
}

// =====================================================
// HOME (index.html)
// =====================================================
async function renderizarInicio() {
  const alvo = document.getElementById("listaProfissionais");
  if (!alvo) return;
  const profs = await api("/api/profissionais");
  alvo.innerHTML = profs.map(p => `
    <article class="seller-card">
      <div class="seller-cover ${p.cor || 'rose'}">
        <span class="cover-flower">✿</span>
        <div class="avatar">${p.inicial || p.nome[0]}</div>
      </div>
      <div class="seller-card-body">
        <span class="eyebrow">${p.area || ''}</span>
        <h3>${p.nome}</h3>
        <p>📍 ${p.cidade || ''}</p>
        <p class="seller-description">${p.bio || ''}</p>
        <a class="btn btn-primary btn-full" href="/vendedor.html?vendedor=${p.slug}">
          Conhecer profissional →
        </a>
      </div>
    </article>`).join("");
}

// =====================================================
// VENDEDOR (vendedor.html)
// =====================================================
let vendedorAtual = null;
let carrinho = [];

async function renderizarVendedor() {
  const slug = new URLSearchParams(location.search).get("vendedor");
  const perfilEl = document.getElementById("perfilVendedor");
  if (!perfilEl || !slug) return;

  vendedorAtual = await api(`/api/profissionais/${slug}`);
  document.title = vendedorAtual.nome + " | Amora Beauty";

  perfilEl.innerHTML = `
    <section class="seller-hero">
      <div class="seller-cover large ${vendedorAtual.cor || 'rose'}">
        <span class="cover-flower">✿</span>
        <div class="avatar">${vendedorAtual.inicial || vendedorAtual.nome[0]}</div>
      </div>
      <div class="seller-hero-text">
        <span class="eyebrow">${vendedorAtual.area || ''}</span>
        <h1>${vendedorAtual.nome}</h1>
        <p>📍 ${vendedorAtual.cidade || ''}</p>
        <p>${vendedorAtual.bio || ''}</p>
        <span class="social-label">${vendedorAtual.instagram || ''}</span>
      </div>
    </section>`;

  document.getElementById("listaServicos").innerHTML =
    vendedorAtual.servicos.map(s => `
      <article class="service-card">
        <div><h3>${s.nome}</h3><p>Atendimento personalizado</p></div>
        <strong>${moeda(s.preco)}</strong>
      </article>`).join("");

  const select = document.getElementById("servico");
  select.innerHTML = '<option value="">Selecione um serviço</option>' +
    vendedorAtual.servicos.map(s =>
      `<option value="${s.id}">${s.nome} — ${moeda(s.preco)}</option>`).join("");

  select.addEventListener("change", atualizarOpcoes);
  atualizarOpcoes();

  document.getElementById("dataAgenda").min = new Date().toISOString().split("T")[0];
  document.getElementById("formAgendamento").addEventListener("submit", solicitarAgendamento);

  document.getElementById("listaProdutos").innerHTML = vendedorAtual.produtos.map(p => `
    <article class="product-card">
      <div class="product-art">${p.emoji || "🎀"}</div>
      <div class="product-card-body">
        <h3>${p.nome}</h3>
        <p>${p.descricao || ""}</p>
        <strong>${moeda(p.preco)}</strong>
        <button class="btn btn-outline btn-full" onclick="adicionarProduto(${p.id})">
          Adicionar à sacolinha
        </button>
      </div>
    </article>`).join("");

  document.getElementById("finalizarCompra").addEventListener("click", finalizarCompra);
}

function atualizarOpcoes() {
  const idSel = document.getElementById("servico").value;
  const area = document.getElementById("opcoesTecnica");
  if (!idSel) { area.innerHTML = ""; return; }
  const s = vendedorAtual.servicos.find(x => String(x.id) === idSel);
  const opcoes = s?.opcoes || [];
  area.innerHTML = opcoes.length
    ? `<label for="tecnica">Escolha o estilo / técnica</label>
       <select id="tecnica" required>
         <option value="">Selecione uma opção</option>
         ${opcoes.map(o => `<option>${o}</option>`).join("")}
       </select>`
    : "";
}

async function solicitarAgendamento(e) {
  e.preventDefault();
  const u = await usuarioLogado();
  if (!u.authenticated) { location.href = "/login.html"; return; }

  const serviceId = document.getElementById("servico").value;
  const tecnica = document.getElementById("tecnica")?.value || "";
  const data = document.getElementById("dataAgenda").value;
  const hora = document.getElementById("horaAgenda").value;
  const observacao = document.getElementById("observacao").value;

  try {
    const r = await api("/api/agendamentos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        store_slug: vendedorAtual.slug,
        service_id: Number(serviceId),
        tecnica, data, hora, observacao,
      }),
    });
    alert("Solicitação enviada! A profissional precisa confirmar o horário.");
    e.target.reset();
    document.getElementById("opcoesTecnica").innerHTML = "";
  } catch (err) {
    alert(err.message || "Erro ao agendar");
  }
}

function adicionarProduto(productId) {
  const p = vendedorAtual.produtos.find(x => x.id === productId);
  if (!p) return;
  const ex = carrinho.find(x => x.product_id === productId);
  if (ex) ex.quantidade += 1;
  else carrinho.push({ product_id: productId, nome: p.nome, preco: p.preco, quantidade: 1 });
  atualizarCarrinho();
}

function atualizarCarrinho() {
  const lista = document.getElementById("itensCarrinho");
  if (!lista) return;
  lista.innerHTML = carrinho.length
    ? carrinho.map((p, i) => `
        <li>${p.nome} × ${p.quantidade} — ${moeda(p.preco * p.quantidade)}
          <button class="remove-item" onclick="removerProduto(${i})">×</button></li>`).join("")
    : '<li class="empty-cart">Sua sacolinha está vazia.</li>';
  document.getElementById("totalCarrinho").textContent =
    moeda(carrinho.reduce((s, p) => s + p.preco * p.quantidade, 0));
}

function removerProduto(i) { carrinho.splice(i, 1); atualizarCarrinho(); }

async function finalizarCompra() {
  const u = await usuarioLogado();
  if (!u.authenticated) { location.href = "/login.html"; return; }
  if (!carrinho.length) { alert("Sua sacolinha está vazia."); return; }

  try {
    const r = await api("/api/pedidos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        store_slug: vendedorAtual.slug,
        itens: carrinho.map(c => ({ product_id: c.product_id, quantidade: c.quantidade })),
      }),
    });
    alert(`Pedido registrado! Total: ${moeda(r.total)}. Combine pagamento e entrega diretamente.`);
    carrinho = [];
    atualizarCarrinho();
  } catch (err) {
    alert(err.message || "Erro ao finalizar");
  }
}

// =====================================================
// TOPO / BOOT
// =====================================================
document.addEventListener("DOMContentLoaded", async () => {
  const u = await usuarioLogado();
  const nome = document.getElementById("usuarioNome");
  if (nome && u.authenticated) nome.textContent = "Olá, " + u.username;

  const entrar = document.getElementById("entrarBtn");
  const cadastro = document.getElementById("cadastroBtn");
  const perfil = document.getElementById("perfilBtn");
  const sairBtn = document.getElementById("sairBtn");
  if (u.authenticated) {
    if (entrar) entrar.hidden = true;
    if (cadastro) cadastro.hidden = true;
    if (perfil) {
      perfil.hidden = false;
      perfil.textContent = u.role === "admin" ? "Painel" : "Meu perfil";
      perfil.href = u.role === "admin" ? "/admin.html" : "/perfil.html";
    }
    if (sairBtn) sairBtn.hidden = false;
  }

  renderizarInicio();
  renderizarVendedor();
});