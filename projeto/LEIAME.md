# Configuração do PostgreSQL, variáveis de ambiente e primeiro admin

## 1. Conectar o PostgreSQL ao Web Service

No painel do Render, abra o seu banco PostgreSQL e vá em **Connect**. Copie a **Internal Database URL** (começa com `postgresql://`). Ela é a única que deve ser usada pelo Web Service, pois a conexão acontece pela rede interna do Render.

No Web Service, vá em **Environment** e crie (ou edite) a variável:

| Key | Value |
|---|---|
| `DATABASE_URL` | Internal Database URL do PostgreSQL |

Cole a URL inteira, sem espaços antes ou depois. O `config.py` do projeto já converte automaticamente o prefixo `postgres://` para `postgresql+psycopg2://`, então não é necessário alterar nada na URL.

## 2. Variáveis de ambiente obrigatórias

No Web Service, em **Environment**, além da `DATABASE_URL`, adicione:

| Key | Value |
|---|---|
| `SECRET_KEY` | Uma chave longa e aleatória (o Render pode gerar automaticamente) |
| `ADMIN_BOOTSTRAP_TOKEN` | `token-secreto-para-primeiro-admin` (ou outro valor à sua escolha) |
| `SUPORTE_URL` | `mailto:seuemail@exemplo.com?subject=Suporte%20-%20Amora%20Beauty&body=Descreva%20o%20problema%3A%0A%0A` |

A `SECRET_KEY` é usada para assinar a sessão dos usuários. A `ADMIN_BOOTSTRAP_TOKEN` protege o endpoint que cria o primeiro admin. A `SUPORTE_URL` é o link do rodapé "Reportar bug / Falar com suporte".

Depois de salvar as variáveis, o Render faz o redeploy automaticamente. Aguarde o status ficar **Live**.

## 3. Criar o primeiro admin (bootstrap)

Com o serviço Live, rode o comando abaixo no Termux (ou em qualquer terminal com `curl`):

```bash
curl -X POST https://lojinha05.onrender.com/api/auth/bootstrap-admin \
  -H "Content-Type: application/json" \
  -H "X-Bootstrap-Token: token-secreto-para-primeiro-admin" \
  -d '{"username":"admin","password":"SUA-SENHA-FORTE","email":"seu-email@exemplo.com"}'
