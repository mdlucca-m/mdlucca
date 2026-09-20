#!/usr/bin/env python3
"""ELASE — servidor do sistema de treinamento.

    python3 elase.py            # abre em http://localhost:8000
    python3 elase.py --porta 80 --host 0.0.0.0

Só biblioteca padrão: nada de instalar. O banco é um arquivo SQLite ao lado
(`elase.db`), criado na primeira execução.

Sobre a tranca: as abas de comando (Elenco, Prescrição, Sistema, SQL) pedem o
PIN do preparador. É uma tranca de porta de sala, não de cofre — serve para o
atleta não abrir a prescrição sem querer, e está escrito na tela que é isso.
Rodando na internet aberta, ponha atrás de HTTPS e troque o PIN.
"""

import argparse
import json
import os
import re
import sqlite3
import traceback
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import banco
import analise
import sistema

AQUI = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(AQUI, "web")


class ErroPedido(Exception):
    """Erro que o cliente causou e deve ver explicado — não um 500 mudo."""

    def __init__(self, msg, codigo=400):
        super().__init__(msg)
        self.codigo = codigo


# ── Regras de negócio, longe do HTTP ─────────────────────────────────────────
def _exige(d, *campos):
    faltam = [c for c in campos if d.get(c) in (None, "")]
    if faltam:
        raise ErroPedido("Faltou preencher: " + ", ".join(faltam))


def estado(con):
    cfg = banco.config(con)
    hoje = date.today().isoformat()
    bl = banco.blocos(con)
    sem = banco.semana_de(hoje, cfg["macro_inicio"])
    n = len(bl)
    return {
        "config": cfg,
        "blocos": bl,
        "hoje": hoje,
        "semana": sem,
        "ciclo": sistema.ciclo_de(sem, n) if n and sem > 0 else 0,
        "posicao": sistema.posicao_no_ciclo(sem, n) if n and sem > 0 else 0,
        "bloco_atual": bl[sistema.posicao_no_ciclo(sem, n) - 1] if n and sem > 0 else None,
        "posicoes": banco.POSICOES,
        "tipos": banco.TIPOS,
        "brums_itens": banco.BRUMS_ITENS,
        "atletas": banco.dics(con.execute(
            "SELECT id,nome,apelido,posicao,camisa,estatura,massa,status"
            " FROM atletas ORDER BY nome").fetchall()),
    }


def criar_atleta(con, d):
    _exige(d, "nome")
    cfg = banco.config(con)
    nome = d["nome"].strip()
    apelido = (d.get("apelido") or "").strip() or nome.split()[0]
    status = "Ativo" if cfg["cadastro_liberado"] else "Pendente"
    campos = ["nome", "apelido", "nasc", "posicao", "camisa", "telefone",
              "estatura", "massa", "alcance_pe", "alcance_ataque",
              "alcance_bloqueio", "anos_pratica", "dominancia", "perna_impulsao",
              "escolaridade", "emergencia", "lesoes", "obs"]
    valores = {c: d.get(c) for c in campos}
    valores["nome"] = nome
    valores["apelido"] = apelido
    # posição fora da lista viraria erro de CHECK lá embaixo, com mensagem de
    # SQLite. Melhor recusar aqui, com o nome do campo em português.
    if valores["posicao"] and valores["posicao"] not in banco.POSICOES:
        raise ErroPedido(f"Posição desconhecida: {valores['posicao']}")
    cols = ", ".join(campos + ["status"])
    marc = ", ".join("?" * (len(campos) + 1))
    cur = con.execute(f"INSERT INTO atletas ({cols}) VALUES ({marc})",
                      [valores[c] for c in campos] + [status])
    return {"id": cur.lastrowid, "status": status,
            "liberado": bool(cfg["cadastro_liberado"])}


def salvar_prescricao(con, d):
    _exige(d, "data", "tipo")
    exs = d.get("exercicios") or []
    if not exs:
        raise ErroPedido("Uma sessão sem exercício não é uma sessão.")
    cur = con.execute(
        "INSERT INTO prescricoes (data,hora,tipo,objetivo,bloco,notas,atleta_id,dur_prev)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (d["data"], d.get("hora") or "09:00", d["tipo"], d.get("objetivo") or "",
         d.get("bloco") or "", d.get("notas") or "", d.get("atleta_id"),
         d.get("dur_prev")))
    pid = cur.lastrowid
    _gravar_exercicios(con, pid, exs)
    return {"id": pid}


def _gravar_exercicios(con, pid, exs):
    con.executemany(
        "INSERT INTO presc_exercicios"
        " (prescricao_id,ordem,nome,grupo,series,reps,pausa,pct_rm,ref1rm,tempo,rir,vel,obs)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(pid, i, e["nome"], e["grupo"], int(e["series"]), str(e["reps"]),
          int(e.get("pausa") or 90), e.get("pct_rm"), e.get("ref1rm"),
          e.get("tempo"), e.get("rir"), e.get("vel"), e.get("obs") or "")
         for i, e in enumerate(exs)])


def prescricoes(con, de=None, ate=None, atleta_id=None):
    sql = "SELECT * FROM prescricoes WHERE 1=1"
    p = []
    if de:
        sql += " AND data >= ?"
        p.append(de)
    if ate:
        sql += " AND data <= ?"
        p.append(ate)
    if atleta_id:
        sql += " AND (atleta_id IS NULL OR atleta_id = ?)"
        p.append(atleta_id)
    sql += " ORDER BY data, hora"
    fora = banco.dics(con.execute(sql, p).fetchall())
    for pr in fora:
        # a dica e o vídeo vêm da biblioteca, por NOME: assim, corrigir a dica de
        # um exercício conserta todas as sessões já prescritas de uma vez
        pr["exercicios"] = banco.dics(con.execute(
            "SELECT pe.*, ex.dica, ex.video_url"
            " FROM presc_exercicios pe"
            " LEFT JOIN exercicios ex ON ex.nome = pe.nome"
            " WHERE pe.prescricao_id=? ORDER BY pe.ordem", (pr["id"],)).fetchall())
        for e in pr["exercicios"]:
            e["busca"] = banco.busca_video(e["nome"])
        pr["plano"] = banco.plano_sessao(pr["exercicios"], pr["tipo"], pr["dur_prev"])
    return fora


def previa_sistema(con, de_semana, ate_semana):
    cfg = banco.config(con)
    bl = banco.blocos(con)
    ocupadas = [r["data"] for r in con.execute(
        "SELECT data FROM prescricoes WHERE atleta_id IS NULL").fetchall()]
    sess, pulados = sistema.gerar(bl, cfg["macro_inicio"], de_semana, ate_semana, ocupadas)
    return {"sessoes": sess, "pulados": pulados,
            "resumo": sistema.resumo(sess, bl, cfg["macro_inicio"])}


def gerar_sistema(con, de_semana, ate_semana):
    p = previa_sistema(con, de_semana, ate_semana)
    for s in p["sessoes"]:
        salvar_prescricao(con, s)
    return {"criadas": len(p["sessoes"]), "pulados": len(p["pulados"]),
            "resumo": p["resumo"]}


def abrir_sessao(con, atleta_id, prescricao_id, wellness=None, brums=None):
    hoje = date.today().isoformat()
    ja = con.execute(
        "SELECT * FROM sessoes WHERE atleta_id=? AND prescricao_id=?",
        (atleta_id, prescricao_id)).fetchone()
    if ja:
        if ja["check_out"]:
            raise ErroPedido("Esta sessão já foi encerrada.")
        sid = ja["id"]
    else:
        pr = con.execute("SELECT tipo FROM prescricoes WHERE id=?",
                         (prescricao_id,)).fetchone()
        cur = con.execute(
            "INSERT INTO sessoes (atleta_id,prescricao_id,data,tipo,check_in)"
            " VALUES (?,?,?,?,?)",
            (atleta_id, prescricao_id, hoje, pr["tipo"] if pr else "",
             datetime.now().isoformat(timespec="seconds")))
        sid = cur.lastrowid
    if wellness:
        salvar_wellness(con, atleta_id, hoje, wellness)
    if brums:
        salvar_brums(con, atleta_id, hoje, brums, "pre")
    return {"sessao_id": sid}


def salvar_serie(con, sessao_id, exercicio, numero, d):
    con.execute(
        "INSERT INTO series (sessao_id,exercicio,numero,carga,reps,rir,vel,feita)"
        " VALUES (?,?,?,?,?,?,?,?)"
        " ON CONFLICT(sessao_id,exercicio,numero) DO UPDATE SET"
        " carga=excluded.carga, reps=excluded.reps, rir=excluded.rir,"
        " vel=excluded.vel, feita=excluded.feita",
        (sessao_id, exercicio, numero, d.get("carga"), d.get("reps"),
         d.get("rir"), d.get("vel"), 1 if d.get("feita") else 0))
    return {"ok": True}


def fechar_sessao(con, sessao_id, pse, brums=None):
    s = con.execute("SELECT * FROM sessoes WHERE id=?", (sessao_id,)).fetchone()
    if not s:
        raise ErroPedido("Sessão não encontrada.", 404)
    if s["check_out"]:
        raise ErroPedido("Esta sessão já foi encerrada.")
    agora = datetime.now()
    entrada = datetime.fromisoformat(s["check_in"]) if s["check_in"] else agora
    dur = max(1, int((agora - entrada).total_seconds() // 60))
    # Tonelagem conta SÓ série marcada como feita: série digitada e não
    # concluída é intenção, não trabalho.
    ton = con.execute(
        "SELECT COALESCE(SUM(carga*reps),0) AS t FROM series"
        " WHERE sessao_id=? AND feita=1", (sessao_id,)).fetchone()["t"]
    contatos = con.execute(
        "SELECT COALESCE(SUM(s.reps),0) AS c FROM series s"
        " JOIN sessoes ss ON ss.id = s.sessao_id"
        " JOIN presc_exercicios pe ON pe.prescricao_id = ss.prescricao_id"
        "   AND pe.ordem = s.exercicio"
        " WHERE s.sessao_id=? AND s.feita=1 AND pe.grupo='Pliometria'",
        (sessao_id,)).fetchone()["c"]
    con.execute(
        "UPDATE sessoes SET check_out=?, dur_min=?, pse=?, carga_ua=?,"
        " tonelagem=?, contatos=? WHERE id=?",
        (agora.isoformat(timespec="seconds"), dur, pse, dur * float(pse),
         ton, contatos, sessao_id))
    if brums:
        salvar_brums(con, s["atleta_id"], s["data"], brums, "pos")
    return {"dur_min": dur, "carga_ua": dur * float(pse),
            "tonelagem": ton, "contatos": contatos}


def salvar_wellness(con, atleta_id, data, d):
    con.execute(
        "INSERT INTO wellness (atleta_id,data,sono_qual,sono_horas,estresse,dor,kss)"
        " VALUES (?,?,?,?,?,?,?)"
        " ON CONFLICT(atleta_id,data) DO UPDATE SET"
        " sono_qual=excluded.sono_qual, sono_horas=excluded.sono_horas,"
        " estresse=excluded.estresse, dor=excluded.dor, kss=excluded.kss",
        (atleta_id, data, d.get("sono_qual"), d.get("sono_horas"),
         d.get("estresse"), d.get("dor"), d.get("kss")))
    return {"ok": True}


def salvar_brums(con, atleta_id, data, respostas, momento="pre"):
    """`respostas` é {item: 0..4}. Item desconhecido é recusado — errar o nome
    do item e gravar numa subescala errada seria pior do que falhar."""
    linhas = []
    for item, valor in respostas.items():
        sub = banco.ITEM_SUB.get(item)
        if sub is None:
            raise ErroPedido(f"Item da BRUMS desconhecido: {item}")
        linhas.append((atleta_id, data, momento, item, sub, int(valor)))
    con.executemany(
        "INSERT INTO brums (atleta_id,data,momento,item,subescala,valor)"
        " VALUES (?,?,?,?,?,?)"
        " ON CONFLICT(atleta_id,data,momento,item) DO UPDATE SET"
        " valor=excluded.valor", linhas)
    return {"gravados": len(linhas)}


def analise_atleta(con, atleta_id):
    a = con.execute("SELECT * FROM atletas WHERE id=?", (atleta_id,)).fetchone()
    if not a:
        raise ErroPedido("Atleta não encontrado.", 404)
    pr = analise.prontidao(con, atleta_id)
    return {
        "atleta": banco.dic(a),
        "carga": pr["carga"],
        "zona": pr["zona"],
        "prontidao": pr["valor"],
        "componentes": pr["componentes"],
        "bandeiras": pr["bandeiras"],
        "nivel": pr["nivel"],
        "nivel_texto": analise.NIVEIS[pr["nivel"]],
        "z": analise.z_hoje(con, atleta_id),
        "sessoes": banco.dics(con.execute(
            "SELECT data, tipo, dur_min, pse, carga_ua, tonelagem, contatos"
            " FROM sessoes WHERE atleta_id=? AND check_out IS NOT NULL"
            " ORDER BY data", (atleta_id,)).fetchall()),
    }


# ── Console SQL, só leitura ──────────────────────────────────────────────────
PROIBIDO = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|pragma|vacuum)\b",
    re.I)


def consultar(caminho, sql):
    """Roda uma consulta de LEITURA. Duas travas, porque uma só não basta:
    a palavra proibida é recusada antes, e a conexão é aberta em modo somente
    leitura — se a primeira falhar, o banco recusa a escrita de qualquer jeito."""
    if PROIBIDO.search(sql):
        raise ErroPedido("Aqui só roda consulta de leitura (SELECT).")
    if not sql.strip().lower().startswith(("select", "with")):
        raise ErroPedido("A consulta precisa começar com SELECT ou WITH.")
    uri = "file:" + os.path.abspath(caminho) + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    try:
        cur = con.execute(sql)
        linhas = cur.fetchmany(1000)
        return {"colunas": [c[0] for c in cur.description] if cur.description else [],
                "linhas": [list(r) for r in linhas], "n": len(linhas)}
    except sqlite3.Error as e:
        raise ErroPedido(f"SQL: {e}")
    finally:
        con.close()


# ── HTTP ─────────────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    server_version = "ELASE"

    def log_message(self, formato, *args):
        pass  # o terminal fica para as mensagens do app, não para o log de acesso

    # -- utilidades --
    def _json(self, dados, codigo=200):
        corpo = json.dumps(dados, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _corpo(self):
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except json.JSONDecodeError:
            raise ErroPedido("Corpo do pedido não é JSON válido.")

    def _treinador(self, con):
        pin = self.headers.get("X-Pin") or ""
        if pin != banco.config(con)["pin_treinador"]:
            raise ErroPedido("Esta área é do preparador físico. PIN incorreto.", 403)

    def _estatico(self, caminho):
        rel = caminho.lstrip("/") or "index.html"
        destino = os.path.normpath(os.path.join(WEB, rel))
        if not destino.startswith(WEB) or not os.path.isfile(destino):
            self.send_error(404)
            return
        tipo = {".html": "text/html; charset=utf-8",
                ".js": "text/javascript; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".json": "application/json"}.get(os.path.splitext(destino)[1],
                                                 "application/octet-stream")
        dados = open(destino, "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    # -- rotas --
    def do_GET(self):
        u = urlparse(self.path)
        if not u.path.startswith("/api/"):
            return self._estatico(u.path)
        self._rodar(lambda con: self._get(con, u.path, parse_qs(u.query)))

    def do_POST(self):
        u = urlparse(self.path)
        self._rodar(lambda con: self._post(con, u.path, self._corpo()))

    def do_DELETE(self):
        u = urlparse(self.path)
        self._rodar(lambda con: self._delete(con, u.path))

    def _rodar(self, fn):
        try:
            # O resultado é calculado DENTRO do `with`, mas a resposta sai
            # DEPOIS que ele fecha — ou seja, depois do commit. Responder de
            # dentro do bloco mandava 200 antes de gravar: quem gravasse e
            # relesse em seguida podia não ver o próprio registro, e uma falha
            # de escrita chegaria ao cliente como sucesso.
            with banco.conectar(self.server.caminho_db) as con:
                resultado = fn(con)
            self._json(resultado)
        except ErroPedido as e:
            self._json({"erro": str(e)}, e.codigo)
        except sqlite3.IntegrityError as e:
            self._json({"erro": f"O banco recusou: {e}"}, 400)
        except Exception:
            traceback.print_exc()
            self._json({"erro": "Erro interno. O terminal do servidor tem o detalhe."}, 500)

    def _get(self, con, caminho, q):
        um = lambda k, p=None: (q.get(k) or [p])[0]
        if caminho == "/api/estado":
            return estado(con)
        if caminho == "/api/prescricoes":
            return prescricoes(con, um("de"), um("ate"),
                               int(um("atleta")) if um("atleta") else None)
        if caminho == "/api/analise":
            return analise_atleta(con, int(um("atleta")))
        if caminho == "/api/exercicios":
            exs = banco.dics(con.execute(
                "SELECT * FROM exercicios ORDER BY grupo, nome").fetchall())
            for e in exs:
                e["busca"] = banco.busca_video(e["nome"])
            return exs
        if caminho == "/api/sessoes":
            return banco.dics(con.execute(
                "SELECT s.*, a.apelido FROM sessoes s JOIN atletas a ON a.id=s.atleta_id"
                " ORDER BY s.data DESC, s.id DESC LIMIT 200").fetchall())
        if caminho == "/api/minha-sessao":
            aid, pid = int(um("atleta")), int(um("prescricao"))
            s = con.execute("SELECT * FROM sessoes WHERE atleta_id=? AND prescricao_id=?",
                            (aid, pid)).fetchone()
            if not s:
                return {"sessao": None, "series": []}
            return {"sessao": banco.dic(s),
                    "series": banco.dics(con.execute(
                        "SELECT * FROM series WHERE sessao_id=? ORDER BY exercicio, numero",
                        (s["id"],)).fetchall())}
        raise ErroPedido("Rota desconhecida: " + caminho, 404)

    def _post(self, con, caminho, d):
        if caminho == "/api/cadastro":
            return criar_atleta(con, d)
        if caminho == "/api/wellness":
            return salvar_wellness(con, int(d["atleta_id"]),
                                   d.get("data") or date.today().isoformat(), d)
        if caminho == "/api/brums":
            return salvar_brums(con, int(d["atleta_id"]),
                                d.get("data") or date.today().isoformat(),
                                d["respostas"], d.get("momento") or "pre")
        if caminho == "/api/sessao/abrir":
            return abrir_sessao(con, int(d["atleta_id"]), int(d["prescricao_id"]),
                                d.get("wellness"), d.get("brums"))
        if caminho == "/api/sessao/serie":
            return salvar_serie(con, int(d["sessao_id"]), int(d["exercicio"]),
                                int(d["numero"]), d)
        if caminho == "/api/sessao/fechar":
            _exige(d, "sessao_id", "pse")
            return fechar_sessao(con, int(d["sessao_id"]), float(d["pse"]), d.get("brums"))

        # daqui para baixo, só o preparador
        self._treinador(con)
        if caminho == "/api/prescricoes":
            return salvar_prescricao(con, d)
        if caminho == "/api/sistema/previa":
            return previa_sistema(con, int(d["de"]), int(d["ate"]))
        if caminho == "/api/sistema/gerar":
            return gerar_sistema(con, int(d["de"]), int(d["ate"]))
        if caminho == "/api/config":
            campos = [c for c in ("equipe", "categoria", "temporada", "macro_inicio",
                                  "cadastro_liberado", "pin_treinador") if c in d]
            if campos:
                con.execute("UPDATE config SET " + ", ".join(f"{c}=?" for c in campos)
                            + " WHERE id=1", [d[c] for c in campos])
            return banco.config(con)
        if caminho == "/api/atleta/status":
            con.execute("UPDATE atletas SET status=? WHERE id=?",
                        (d["status"], int(d["id"])))
            return {"ok": True}
        if caminho == "/api/exercicio/video":
            url = (d.get("video_url") or "").strip() or None
            # só http(s): um "javascript:" aqui viraria link ativo na tela do
            # atleta, e o campo é livre para quem tem o PIN
            if url and not re.match(r"^https?://", url, re.I):
                raise ErroPedido("O endereço do vídeo precisa começar com http:// ou https://")
            con.execute("UPDATE exercicios SET video_url=? WHERE nome=?",
                        (url, d["nome"]))
            return {"ok": True, "video_url": url}
        if caminho == "/api/exercicio/dica":
            con.execute("UPDATE exercicios SET dica=? WHERE nome=?",
                        (d.get("dica") or "", d["nome"]))
            return {"ok": True}
        if caminho == "/api/testes":
            con.execute("INSERT INTO testes (atleta_id,data,tipo,exercicio,valor,unidade)"
                        " VALUES (?,?,?,?,?,?)",
                        (int(d["atleta_id"]), d.get("data") or date.today().isoformat(),
                         d["tipo"], d["exercicio"], float(d["valor"]),
                         d.get("unidade") or "kg"))
            return {"ok": True}
        if caminho == "/api/sql":
            return consultar(self.server.caminho_db, d.get("sql") or "")
        raise ErroPedido("Rota desconhecida: " + caminho, 404)

    def _delete(self, con, caminho):
        self._treinador(con)
        m = re.match(r"^/api/prescricoes/(\d+)$", caminho)
        if m:
            con.execute("DELETE FROM prescricoes WHERE id=?", (int(m.group(1)),))
            return {"ok": True}
        raise ErroPedido("Rota desconhecida: " + caminho, 404)


def main():
    p = argparse.ArgumentParser(description="ELASE — sistema de treinamento")
    p.add_argument("--porta", type=int, default=8000)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--db", default=banco.CAMINHO)
    args = p.parse_args()

    banco.criar(args.db)
    srv = ThreadingHTTPServer((args.host, args.porta), Handler)
    srv.caminho_db = args.db
    with banco.conectar(args.db) as con:
        cfg = banco.config(con)
        n = con.execute("SELECT COUNT(*) c FROM atletas").fetchone()["c"]
    print(f"\n  ELASE · {cfg['equipe']} · {cfg['categoria']}")
    print(f"  banco: {args.db}")
    print(f"  elenco: {n} atleta(s) · macrociclo desde {cfg['macro_inicio']}")
    print(f"  PIN do preparador: {cfg['pin_treinador']}  (troque na aba Config)")
    print(f"\n  → http://{args.host}:{args.porta}\n")
    print("  Ctrl+C para parar.\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  Parado.\n")


if __name__ == "__main__":
    main()
