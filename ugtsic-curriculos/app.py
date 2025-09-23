import os
import sqlite3
import smtplib
import mimetypes
from email.message import EmailMessage
from datetime import datetime
from flask import Flask, request, send_from_directory, jsonify, send_file, abort
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

# ===== Config =====
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB
DB_PATH = os.getenv("DB_PATH", "curriculos.db")

MAIL_TO = os.getenv("MAIL_TO", "ugtsicdev@gmail.com")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")            # usar em produção
SMTP_PASS = os.getenv("SMTP_PASS")            # senha de app (Gmail) ou SMTP
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")        # token simples para /api/*

app = Flask(__name__, static_folder="static")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===== DB =====
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS candidaturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL,
                telefone TEXT NOT NULL,
                cargo TEXT NOT NULL,
                escolaridade TEXT NOT NULL,
                observacoes TEXT,
                arquivo_nome TEXT NOT NULL,
                arquivo_caminho TEXT NOT NULL,
                ip TEXT NOT NULL,
                enviado_em TEXT NOT NULL
            )
            """
        )
        conn.commit()

# ===== Helpers =====
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def client_ip(req: request) -> str:
    forwarded = req.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    return forwarded or req.remote_addr or "0.0.0.0"

def send_email_with_attachment(data: dict, filepath: str):
    """Envia e-mail com anexo """
    if not (SMTP_USER and SMTP_PASS):
        app.logger.warning("SMTP_USER/SMTP_PASS não definidos – e-mail não enviado (modo dev)")
        return

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    msg["Subject"] = f"Nova candidatura: {data['nome']} - {data['cargo']}"

    body = (
        f"Nome: {data['nome']}\n"
        f"E-mail: {data['email']}\n"
        f"Telefone: {data['telefone']}\n"
        f"Cargo Desejado: {data['cargo']}\n"
        f"Escolaridade: {data['escolaridade']}\n"
        f"Observações: {data.get('observacoes') or '-'}\n"
        f"IP: {data['ip']}\n"
        f"Enviado em: {data['enviado_em']}\n"
    )
    msg.set_content(body)

    ctype, _ = mimetypes.guess_type(filepath)
    if ctype is None:
        ctype = "application/octet-stream"
    maintype, subtype = ctype.split("/", 1)
    with open(filepath, "rb") as f:
        msg.add_attachment(
            f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(filepath)
        )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)

# ===== Rotas públicas =====
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/submit", methods=["POST"])
def submit():
    required = ["nome", "email", "telefone", "cargo", "escolaridade"]
    for field in required:
        if not request.form.get(field):
            return jsonify({"ok": False, "error": f"Campo obrigatório: {field}"}), 400

    file = request.files.get("arquivo")
    if not file or file.filename == "":
        return jsonify({"ok": False, "error": "Arquivo do currículo é obrigatório"}), 400
    if not allowed_file(file.filename):
        return jsonify({"ok": False, "error": "Extensão inválida. Use .pdf, .doc ou .docx"}), 400

    filename = secure_filename(file.filename)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    stored_name = f"{ts}_{filename}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
    file.save(filepath)

    dados = {
        "nome": request.form.get("nome").strip(),
        "email": request.form.get("email").strip(),
        "telefone": request.form.get("telefone").strip(),
        "cargo": request.form.get("cargo").strip(),
        "escolaridade": request.form.get("escolaridade").strip(),
        "observacoes": request.form.get("observacoes", "").strip(),
        "arquivo_nome": filename,
        "arquivo_caminho": filepath,
        "ip": client_ip(request),
        "enviado_em": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO candidaturas
            (nome, email, telefone, cargo, escolaridade, observacoes,
             arquivo_nome, arquivo_caminho, ip, enviado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dados["nome"], dados["email"], dados["telefone"], dados["cargo"],
                dados["escolaridade"], dados["observacoes"], dados["arquivo_nome"],
                dados["arquivo_caminho"], dados["ip"], dados["enviado_em"]
            ),
        )
        conn.commit()

    try:
        send_email_with_attachment(dados, filepath)
    except Exception as e:
        app.logger.exception("Falha ao enviar e-mail: %s", e)
        return jsonify({"ok": True, "email_enviado": False, "mensagem": "Dados salvos. Falha ao enviar e-mail."})

    return jsonify({"ok": True, "email_enviado": True, "mensagem": "Candidatura enviada com sucesso!"})

# ===== Rotas Admin  =====
@app.route("/api/candidaturas")
def api_candidaturas():
    # proteção simples por token
    token = request.args.get("token")
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        return abort(401)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nome, email, telefone, cargo, escolaridade,
                   observacoes, arquivo_nome, arquivo_caminho, ip, enviado_em
            FROM candidaturas
            ORDER BY id DESC
        """)
        rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"ok": True, "rows": rows})

@app.route("/api/download/<int:candidatura_id>")
def api_download(candidatura_id):
    token = request.args.get("token")
    if not ADMIN_TOKEN or token != ADMIN_TOKEN:
        return abort(401)

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT arquivo_nome, arquivo_caminho
            FROM candidaturas
            WHERE id = ?
        """, (candidatura_id,))
        row = cur.fetchone()

    if not row:
        return abort(404)

    arquivo_nome, arquivo_caminho = row
    if not os.path.isfile(arquivo_caminho):
        return abort(404)

    return send_file(arquivo_caminho, as_attachment=True, download_name=arquivo_nome)

@app.route("/admin")
def admin_page():
    # Se não existir o arquivo admin.html, retorna 404
    path = os.path.join(app.static_folder, "admin.html")
    if not os.path.isfile(path):
        return "Painel indisponível: crie static/admin.html.", 404
    return send_from_directory(app.static_folder, "admin.html")

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
