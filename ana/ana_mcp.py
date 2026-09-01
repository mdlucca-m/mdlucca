#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Servidor MCP da Ana — a assistente pessoal de pesquisa.

Fala JSON-RPC 2.0 sobre stdin e stdout, sem dependência além da biblioteca
padrão. Dá a qualquer cliente MCP acesso de LEITURA à base única do estudo do
handebol, ao acervo das planilhas, aos resultados de modelagem e à memória de
decisões já tomadas.

A base é aberta em modo somente leitura. A única coisa que a Ana escreve é a
própria memória, e só quando lhe pedem.

Registro no cliente:

    {"mcpServers": {"ana": {"command": "python3",
      "args": ["/home/user/mdlucca/ana/ana_mcp.py"]}}}
"""
from __future__ import annotations
import json, os, sqlite3, sys, logging
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import memoria as mem

log = logging.getLogger("ana.mcp")
NOME, VERSAO, PROTOCOLO = "ana", "1.0.0", "2025-06-18"
RAIZ = Path(os.environ.get("HH_RAIZ") or
            Path(__file__).resolve().parent.parent / "estudos" / "humor_handebol")
DB = Path(os.environ.get("ANA_BASE") or RAIZ / "base" / "humor_handebol.sqlite")
DADOS = RAIZ / "dados"

INSTRUCOES = (
    "Base única do estudo de humor em handebol de elite. Antes de afirmar qualquer número "
    "sobre este estudo, consulte a ferramenta correspondente: memória não é fonte, e texto "
    "anterior também não. A unidade canônica é o par atleta-dia (U-AD, n = 166); quando a "
    "resposta depender da unidade, diga qual usou. Comece por `ana_orientar` se não souber "
    "por onde entrar."
)

def _s(x, d=3):
    if x is None: return "—"
    if isinstance(x, float): return f"{x:.{d}f}".replace('.', ',').replace('-', '−')
    return str(x)

def _tab(rows, cols=None, larg=54) -> str:
    if not rows: return "  (nada encontrado)"
    cols = cols or list(rows[0].keys())
    L = {c: min(max(len(c), *(len(_s(r[c])) for r in rows)), larg) for c in cols}
    out = ["  " + " │ ".join(c[:L[c]].ljust(L[c]) for c in cols),
           "  " + "─┼─".join("─" * L[c] for c in cols)]
    for r in rows:
        out.append("  " + " │ ".join(_s(r[c])[:L[c]].ljust(L[c]) for c in cols))
    out.append(f"  ({len(rows)} linha{'s' if len(rows) != 1 else ''})")
    return "\n".join(out)

FERRAMENTAS = [
 {"name": "ana_orientar", "description":
  "Mapa de entrada: o que existe na base, quais unidades de análise, e qual ferramenta usar para cada pergunta. "
  "Chame primeiro quando não souber onde procurar.",
  "inputSchema": {"type": "object", "properties": {}}},
 {"name": "ana_resultado", "description":
  "Resultados estatísticos em formato longo. Filtre por variável, domínio (descritivo, série, não paramétrico, "
  "paramétrico, misto, prevalência), via, recorte ou artigo. Com significativo=true traz só o que passou no ajuste.",
  "inputSchema": {"type": "object", "properties": {
     "variavel": {"type": "string"}, "dominio": {"type": "string"}, "via": {"type": "string"},
     "recorte": {"type": "string"}, "artigo": {"type": "string"},
     "significativo": {"type": "boolean"}, "limite": {"type": "integer", "default": 40}}}},
 {"name": "ana_serie", "description":
  "Série diária de uma variável: média, erro padrão, curva suavizada pelo filtro binomial 1-2-1, primeira e "
  "segunda derivadas normalizadas pelo piso de ruído, e os choques marcados.",
  "inputSchema": {"type": "object", "properties": {"variavel": {"type": "string"}}, "required": ["variavel"]}},
 {"name": "ana_confronto", "description":
  "Onde as três vias — não paramétrica, paramétrica e modelo misto — divergem de veredito sobre a mesma variável. "
  "É a espinha do Artigo 2.",
  "inputSchema": {"type": "object", "properties": {}}},
 {"name": "ana_perfil", "description":
  "Prevalência dos seis perfis de humor por recorte (dia, estímulo, momento). Informe a unidade de análise.",
  "inputSchema": {"type": "object", "properties": {
     "recorte": {"type": "string", "default": "dia"}, "unidade": {"type": "string", "default": "U-AD"}}}},
 {"name": "ana_auditoria", "description":
  "Os achados da auditoria de procedência: por que sete versões do manuscrito divergiam, e o que foi corrigido.",
  "inputSchema": {"type": "object", "properties": {}}},
 {"name": "ana_modelo", "description":
  "Resultados da modelagem: desempenho contra as linhas de base, a árvore legível, importância por permutação, "
  "o subgrupo acionável e o diagnóstico de reversão à média. Sem argumento, traz tudo.",
  "inputSchema": {"type": "object", "properties": {
     "parte": {"type": "string", "enum": ["desempenho", "arvore", "diagnostico", "crispdm", "tudo"],
               "default": "tudo"}}}},
 {"name": "ana_referencia", "description":
  "Referências do estudo com DOI verificado, PubMed e via de acesso aberto quando existe. Filtre por termo.",
  "inputSchema": {"type": "object", "properties": {
     "termo": {"type": "string"}, "limite": {"type": "integer", "default": 20}}}},
 {"name": "ana_buscar", "description":
  "Busca em texto completo sobre tudo: acervo das planilhas, resultados e achados de auditoria. "
  "Use quando não souber em que tabela o número está.",
  "inputSchema": {"type": "object", "properties": {
     "termo": {"type": "string"}, "origem": {"type": "string", "enum": ["acervo", "resultado", "auditoria"]},
     "limite": {"type": "integer", "default": 20}}, "required": ["termo"]}},
 {"name": "ana_sql", "description":
  "Consulta SQL livre, somente leitura, sobre a base única. Use quando as ferramentas prontas não bastarem.",
  "inputSchema": {"type": "object", "properties": {
     "consulta": {"type": "string"}, "limite": {"type": "integer", "default": 50}}, "required": ["consulta"]}},
 {"name": "ana_lembrar", "description":
  "Guarda uma decisão do pesquisador para as próximas sessões. Não guarde números de resultado: eles moram na base.",
  "inputSchema": {"type": "object", "properties": {
     "chave": {"type": "string"}, "valor": {"type": "string"}, "escopo": {"type": "string", "default": "geral"}},
   "required": ["chave", "valor"]}},
 {"name": "ana_recordar", "description":
  "Lê a memória de decisões já tomadas. Sem argumento, lista tudo.",
  "inputSchema": {"type": "object", "properties": {
     "termo": {"type": "string"}, "escopo": {"type": "string"}}}},
 {"name": "ana_esquecer", "description": "Apaga uma lembrança pela chave.",
  "inputSchema": {"type": "object", "properties": {"chave": {"type": "string"}}, "required": ["chave"]}},
]

class Servidor:
    def __init__(self, db: Path | None = None):
        self.db = Path(db or DB)
        self.protocolo = PROTOCOLO
        self._cx: sqlite3.Connection | None = None

    @property
    def cx(self) -> sqlite3.Connection:
        if self._cx is None:
            if not self.db.exists():
                raise FileNotFoundError(f"base não encontrada em {self.db}")
            self._cx = sqlite3.connect(f"file:{self.db}?mode=ro", uri=True)
            self._cx.row_factory = sqlite3.Row
        return self._cx

    def _json(self, nome: str) -> dict:
        p = DADOS / nome
        if not p.exists(): raise FileNotFoundError(f"{p} ainda não foi gerado; rode ./atualizar.sh")
        return json.loads(p.read_text(encoding="utf-8"))

    # -------------------------------------------------------- ferramentas
    def _orientar(self, a) -> str:
        n = {t: self.cx.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
             for t in ["atleta", "registro", "atleta_dia", "pre_pos", "resultado", "aba", "celula", "referencia"]}
        un = self.cx.execute("SELECT * FROM unidade_analise").fetchall()
        return (
         "BASE ÚNICA DO ESTUDO — humor em handebol de elite, 21 a 27 de abril de 2024\n\n"
         f"  {n['atleta']} atletas · {n['registro']} registros · {n['atleta_dia']} pares atleta-dia · "
         f"{n['pre_pos']} medidas pré-pós em formato longo\n"
         f"  {n['resultado']} resultados estatísticos · {n['referencia']} referências · "
         f"{n['aba']} abas e {n['celula']} células de acervo\n\n"
         "UNIDADES DE ANÁLISE — a causa de toda divergência entre versões do manuscrito:\n"
         + _tab(un) + "\n\n"
         "POR ONDE ENTRAR:\n"
         "  «como o vigor se comportou na semana»        → ana_serie\n"
         "  «isso deu significativo?»                    → ana_resultado(significativo=true)\n"
         "  «a conclusão muda conforme o teste?»         → ana_confronto\n"
         "  «quantos atletas em risco no dia 5?»         → ana_perfil\n"
         "  «por que o número era outro antes?»          → ana_auditoria\n"
         "  «dá para prever quem termina mal?»           → ana_modelo\n"
         "  «qual o DOI daquele artigo?»                 → ana_referencia\n"
         "  «onde está esse número?»                     → ana_buscar\n"
         "  «o que já decidimos sobre isso?»             → ana_recordar\n")

    def _resultado(self, a) -> str:
        onde, arg = ["1=1"], []
        for c in ("variavel", "dominio", "via", "recorte", "artigo"):
            if a.get(c): onde.append(f"{c} = ?"); arg.append(a[c])
        if a.get("significativo"): onde.append("significativo = 1")
        lim = max(1, min(int(a.get("limite", 40)), 300))
        r = self.cx.execute(
            "SELECT dominio,via,unidade,variavel,recorte,teste,rotulo_estatistica,estatistica,"
            "p,p_ajustado,rotulo_efeito,efeito,ic_inf,ic_sup,n FROM resultado"
            f" WHERE {' AND '.join(onde)} ORDER BY dominio,variavel,recorte LIMIT ?",
            arg + [lim]).fetchall()
        return _tab(r)

    def _serie(self, a) -> str:
        v = a.get("variavel", "")
        r = self.cx.execute("SELECT * FROM serie_diaria WHERE variavel=? ORDER BY dia", (v,)).fetchall()
        if not r:
            tem = [x[0] for x in self.cx.execute("SELECT DISTINCT variavel FROM serie_diaria")]
            return f"variável «{v}» não está na base. Disponíveis: {', '.join(tem)}"
        piso = r[0]["piso_ruido"]
        ch = [x["dia"] for x in r if x["e_choque"]]
        corpo = _tab(r, ["dia", "media", "erro_padrao", "suavizado", "derivada1", "derivada2"])
        return (f"{v} — série diária sobre o par atleta-dia\n"
                f"  piso de ruído (média dos erros padrão diários): {_s(piso)}\n"
                f"  transições de choque (|derivada primeira| acima do piso): "
                + (", ".join(f"D{c-1}→D{c}" for c in ch) if ch else "nenhuma") + "\n\n" + corpo
                + "\n\n  A derivada está em unidades do piso de ruído: valor 2,0 significa duas vezes o ruído.")

    def _confronto(self, a) -> str:
        r = self.cx.execute("SELECT * FROM v_confronto_vias").fetchall()
        div = [x for x in r if len({(p or 1) < .05 for p in
                                    (x["p_nao_param"], x["p_param"], x["p_misto"]) if p is not None}) > 1]
        return ("Confronto entre as três vias — p de cada rota sobre a mesma variável\n\n" + _tab(r)
                + f"\n\n  Trocam de veredito conforme a via: {len(div)} de {len(r)} contrastes."
                + ("\n  " + "; ".join(f"{x['variavel']} ({x['recorte']})" for x in div) if div else ""))

    def _perfil(self, a) -> str:
        rec, un = a.get("recorte", "dia"), a.get("unidade", "U-AD")
        r = self.cx.execute(
            "SELECT recorte,perfil,prevalencia,n,erro_padrao FROM prevalencia"
            " WHERE recorte_tipo=? AND unidade=? ORDER BY recorte,perfil", (rec, un)).fetchall()
        if not r:
            t = self.cx.execute("SELECT DISTINCT recorte_tipo,unidade FROM prevalencia").fetchall()
            return f"nada para recorte={rec}, unidade={un}. Combinações existentes:\n" + _tab(t)
        return f"Prevalência dos perfis · recorte «{rec}» · unidade {un}\n\n" + _tab(r)

    def _auditoria(self, a) -> str:
        r = self.cx.execute("SELECT id,gravidade,titulo,achado,correcao,impacto FROM auditoria ORDER BY id").fetchall()
        return "\n\n".join(
            f"D{x['id']} · {x['gravidade'].upper()} · {x['titulo']}\n"
            f"  achado:   {x['achado']}\n  correção: {x['correcao']}\n  impacto:  {x['impacto']}" for x in r)

    def _modelo(self, a) -> str:
        parte = a.get("parte", "tudo")
        blocos = []
        if parte in ("desempenho", "tudo"):
            M = self._json("V2_ml.json")
            L = [f"DESEMPENHO — alvo: medida da manhã → faixa de risco à noite",
                 f"  {M['n']} pares · {M['atletas']} atletas · {M['eventos']} eventos "
                 f"({M['eventos']/M['n']*100:.1f}%)".replace('.', ','),
                 f"  regra trivial (já estava em risco de manhã) acerta {M['regra_trivial']*100:.1f}%".replace('.', ','),
                 "", "  modelo                       AUC     IC 95%              ganho sobre a trivial"]
            for k, r in M['RES'].items():
                g = M['GANHO'].get(k)
                gt = (f"{_s(g['m'])}  [{_s(g['ic'][0])}, {_s(g['ic'][1])}]"
                      + ("  ← exclui zero" if g['ic'][0] > 0 else "")) if g else "—"
                L.append(f"  {k:<27} {_s(r['auc'])}  [{_s(r['ic'][0])}, {_s(r['ic'][1])}]   {gt}")
            L.append("\n  Nenhum ganho exclui zero na amostra completa. O achado defensável está no subgrupo.")
            blocos.append("\n".join(L))
        if parte in ("arvore", "tudo"):
            M2 = self._json("V2_ml2.json")
            L = ["ÁRVORE DE DECISÃO — profundidade 3, folha mínima de 12 pares", ""]
            for n in M2['ARVORE']:
                if n['tipo'] == 'folha':
                    L.append(f"  n={n['n']:>3}  risco previsto {n['p']*100:>3.0f}%  ←  {' e '.join(n['caminho'])}")
            L += ["", "IMPORTÂNCIA POR PERMUTAÇÃO (queda de AUC fora da amostra)"]
            for e in M2['IMPORTANCIA'][:8]:
                L.append(f"  {e['var']:<32} {_s(e['media'])} ± {_s(e['dp'])}")
            s = M2['SUBGRUPO']; k0 = list(s)[0]
            L += ["", f"SUBGRUPO ACIONÁVEL — {s[k0]['n']} pares começam fora da faixa de risco, "
                      f"{s[k0]['eventos']} entram até a noite"]
            for k, v in s.items():
                L.append(f"  {k:<22} AUC {_s(v['auc'])}  [{_s(v['ic'][0])}, {_s(v['ic'][1])}]"
                         + ("  ← exclui o acaso" if v['ic'][0] > .5 else ""))
            blocos.append("\n".join(L))
        if parte in ("diagnostico", "tudo"):
            M3 = self._json("V2_ml3.json")
            L = ["DIAGNÓSTICO — a folha mais forte é achado ou aritmética do desenho?", "",
                 "  reversão à média · ρ(valor da manhã, variação manhã→noite)"]
            for e in sorted(M3['REVERSAO'], key=lambda e: e['rho']):
                L.append(f"    {e['variavel']:<11} ρ = {_s(e['rho'])}   p = {_s(e['p'],4)}"
                         + ("   mecânico" if e['mecanico'] else "   sem componente mecânico"))
            L += ["", "  modelos aninhados"]
            for e in M3['ANINHADOS']:
                L.append(f"    {e['modelo']:<32} k={e['k']:>2}  AUC {_s(e['auc'])} ± {_s(e['dp'])}")
            L += ["", "  VEREDICTO", "  " + M3['VEREDICTO']['texto']]
            blocos.append("\n".join(L))
        if parte in ("crispdm", "tudo"):
            C = self._json("V2_crispdm.json")
            L = ["O ESTUDO NAS SEIS FASES DO CRISP-DM", ""]
            for f in C['FASES']:
                L.append(f"  Fase {f['n']} · {f['nome']} — {f['pergunta']}")
                for t in f['feito']: L.append(f"      · {t}")
                L.append(f"      IA como copiloto: {f['copiloto']}")
                L.append(f"      Decisão humana:   {f['humano']}")
                L.append(f"      Artefatos:        {', '.join(f['artefatos'])}\n")
            blocos.append("\n".join(L))
        return "\n\n" + ("\n\n" + "─" * 72 + "\n\n").join(blocos)

    def _referencia(self, a) -> str:
        lim = max(1, min(int(a.get("limite", 20)), 100))
        if a.get("termo"):
            alvo = f"%{a['termo']}%"
            r = self.cx.execute(
                "SELECT id,autores,ano,titulo,veiculo,doi,url_doi,url_pubmed,url_oa FROM referencia"
                " WHERE autores LIKE ? OR titulo LIKE ? OR veiculo LIKE ? ORDER BY id LIMIT ?",
                (alvo, alvo, alvo, lim)).fetchall()
        else:
            r = self.cx.execute(
                "SELECT id,autores,ano,titulo,veiculo,doi,url_doi,url_pubmed,url_oa FROM referencia"
                " ORDER BY id LIMIT ?", (lim,)).fetchall()
        if not r: return "  (nenhuma referência corresponde)"
        L = []
        for x in r:
            L.append(f"[{x['id']}] {x['autores']} ({x['ano']}). {x['titulo']}. {x['veiculo']}.")
            vias = [v for v in (x['url_doi'], x['url_pubmed'], x['url_oa']) if v]
            L.append("      " + ("  ·  ".join(vias) if vias else "sem DOI verificado"))
        return "\n".join(L)

    def _buscar(self, a) -> str:
        lim = max(1, min(int(a.get("limite", 20)), 100))
        onde, arg = ["busca MATCH ?"], [a["termo"]]
        if a.get("origem"): onde.append("origem = ?"); arg.append(a["origem"])
        try:
            r = self.cx.execute(
                f"SELECT origem,arquivo,aba,categoria,chave,snippet(busca,5,'«','»','…',14) texto"
                f" FROM busca WHERE {' AND '.join(onde)} LIMIT ?", arg + [lim]).fetchall()
        except sqlite3.OperationalError as e:
            return f"consulta que o índice não aceita ({e}). Use aspas para frase exata."
        return _tab(r)

    def _sql(self, a) -> str:
        q = (a.get("consulta") or "").strip().rstrip(";")
        if not q.lower().startswith(("select", "with")):
            return "somente SELECT ou WITH: a Ana não escreve na base do estudo."
        lim = max(1, min(int(a.get("limite", 50)), 500))
        try:
            r = self.cx.execute(q).fetchmany(lim)
        except sqlite3.Error as e:
            return f"erro de SQL: {e}"
        return _tab(r)

    def _lembrar(self, a) -> str:
        return mem.lembrar(a["chave"], a["valor"], a.get("escopo", "geral"), origem="Ana")

    def _recordar(self, a) -> str:
        r = mem.recordar(a.get("termo"), a.get("escopo"))
        if not r: return "  (memória vazia para esse filtro)"
        return "\n".join(f"[{x['escopo']}] {x['chave']}  ·  atualizada em {x['atualizada'][:10]}\n    {x['valor']}"
                         for x in r)

    def _esquecer(self, a) -> str:
        return mem.esquecer(a["chave"])

    # -------------------------------------------------------- protocolo
    def _chamar(self, nome: str, args: dict) -> dict:
        acao: Callable[[dict], str] | None = {
            "ana_orientar": self._orientar, "ana_resultado": self._resultado, "ana_serie": self._serie,
            "ana_confronto": self._confronto, "ana_perfil": self._perfil, "ana_auditoria": self._auditoria,
            "ana_modelo": self._modelo, "ana_referencia": self._referencia, "ana_buscar": self._buscar,
            "ana_sql": self._sql, "ana_lembrar": self._lembrar, "ana_recordar": self._recordar,
            "ana_esquecer": self._esquecer,
        }.get(nome)
        if acao is None:
            return _texto(f"ferramenta desconhecida: {nome}", erro=True)
        try:
            return _texto(acao(args))
        except Exception as exc:
            log.exception("falha em %s", nome)
            return _texto(f"{type(exc).__name__}: {exc}", erro=True)

    def atender(self, pedido: dict) -> dict | None:
        metodo, pid = pedido.get("method", ""), pedido.get("id")
        try:
            if metodo == "initialize":
                v = (pedido.get("params") or {}).get("protocolVersion")
                if isinstance(v, str) and v: self.protocolo = v
                return _ok(pid, {"protocolVersion": self.protocolo,
                                 "capabilities": {"tools": {"listChanged": False}},
                                 "serverInfo": {"name": NOME, "version": VERSAO},
                                 "instructions": INSTRUCOES})
            if metodo in ("notifications/initialized", "initialized"): return None
            if metodo == "ping": return _ok(pid, {})
            if metodo == "tools/list": return _ok(pid, {"tools": FERRAMENTAS})
            if metodo == "tools/call":
                p = pedido.get("params") or {}
                return _ok(pid, self._chamar(p.get("name", ""), p.get("arguments") or {}))
            if pid is None: return None
            return _erro(pid, -32601, f"método não suportado: {metodo}")
        except Exception as exc:
            log.exception("falha ao atender %s", metodo)
            return None if pid is None else _erro(pid, -32603, f"{type(exc).__name__}: {exc}")

    def servir(self, entrada=None, saida=None) -> int:
        entrada, saida = entrada or sys.stdin, saida or sys.stdout
        for linha in entrada:
            linha = linha.strip()
            if not linha: continue
            try:
                pedido = json.loads(linha)
            except json.JSONDecodeError as exc:
                _escrever(saida, _erro(None, -32700, f"JSON inválido: {exc}")); continue
            for p in (pedido if isinstance(pedido, list) else [pedido]):
                r = self.atender(p)
                if r is not None: _escrever(saida, r)
        return 0

def _ok(pid, r): return {"jsonrpc": "2.0", "id": pid, "result": r}
def _erro(pid, c, m): return {"jsonrpc": "2.0", "id": pid, "error": {"code": c, "message": m}}
def _texto(t, erro=False): return {"content": [{"type": "text", "text": t}], "isError": erro}
def _escrever(saida, o): saida.write(json.dumps(o, ensure_ascii=False) + "\n"); saida.flush()

def main() -> int:
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr, format="%(levelname)s %(name)s: %(message)s")
    return Servidor().servir()

if __name__ == "__main__":
    sys.exit(main())
