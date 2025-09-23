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
);