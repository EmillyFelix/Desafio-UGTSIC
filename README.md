# Desafio-UGTSIC Formulário de Envio de Currículos
Sistema simples de cadastro e envio de currículos.

- Backend: Python (Flask + SQLite + envio opcional de e-mail via SMTP)  
- Frontend: HTML, CSS (tema corporativo azul) e JavaScript puro  
- Banco: SQLite (`curriculos.db`)  
- Uploads: arquivos salvos em `uploads/`

## 💻 Como rodar no Windows
1. **Entrar na pasta do projeto**
   cd ugtsic-curriculos

2. **Criar e ativar o ambiente virtual**
    python -m venv .venv

3. **Instalar dependências**
    pip install -r requirements.txt

4. **Criar o .env a partir do exemplo e configurar**
    copy .env.example .env

    Edite o arquivo .env e defina:

    ADMIN_TOKEN=coloque_um_token_forte
    SMTP_USER=seu_email@gmail.com
    SMTP_PASS=sua_senha_de_app_ou_do_seu_smtp

        Se não quiser enviar e-mail agora, deixe SMTP_USER e SMTP_PASS vazios. O sistema salva no banco e registra um aviso.

5. **Subir a aplicação**
     python app.py

6. **Acessar**

    Formulário público: http://localhost:5000/

    Painel admin (HTML): http://localhost:5000/admin

    API JSON (lista): http://localhost:5000/api/candidaturas?token=SEU_TOKEN

    Download de currículo (exemplo id=1): http://localhost:5000/api/download/1?token=SEU_TOKEN

## ⚙️ Painel Admin

O painel /admin consome as rotas /api/*, que exigem o token ADMIN_TOKEN do .env.

Rotas:
- GET /api/candidaturas?token=SEU_TOKEN → lista registros (JSON)
- GET /api/download/<id>?token=SEU_TOKEN → baixa o arquivo do currículo

### 🔐 Segurança

- Não versionar .env, uploads/ e curriculos.db.
- Use .env.example como molde e mantenha o .env só localmente.
- Se por engano já tiver adicionado algum desses ao git, remova do índice:

    git rm --cached .env
    git rm -r --cached uploads/
    git rm --cached curriculos.db

###📧 SMTP (Gmail)

SMTP_SERVER=smtp.gmail.com, SMTP_PORT=587 (STARTTLS).
SMTP_USER = seu Gmail completo (ex.: seudominio@gmail.com).
SMTP_PASS = Senha de App do Google (não é a senha normal).
Ative 2FA na conta Google → “Senhas de app” → gere a senha (16 caracteres) → use no .env.
