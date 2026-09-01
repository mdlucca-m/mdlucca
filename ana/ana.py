#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A Ana pela linha de comando — as mesmas ferramentas do servidor MCP, sem cliente.

  ./ana.py orientar                       o mapa: o que existe e por onde entrar
  ./ana.py resultado --variavel Vigor --sig
  ./ana.py serie Vigor
  ./ana.py confronto
  ./ana.py perfil --recorte estimulo
  ./ana.py auditoria
  ./ana.py qualidade --parte discrepantes
  ./ana.py otimizar --parte precos
  ./ana.py modelo --parte diagnostico
  ./ana.py referencia --termo Terry
  ./ana.py buscar "piso de ruído"
  ./ana.py sql "SELECT ..."
  ./ana.py lembrar "periódico alvo" "Frontiers in Psychology, seção Sport Psychology"
  ./ana.py recordar --escopo handebol
  ./ana.py esquecer "periódico alvo"
"""
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ana_mcp import Servidor

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd")
    sp.add_parser("orientar")
    r = sp.add_parser("resultado")
    for a in ("--variavel", "--dominio", "--via", "--recorte", "--artigo"): r.add_argument(a)
    r.add_argument("--sig", action="store_true"); r.add_argument("--limite", type=int, default=40)
    se = sp.add_parser("serie"); se.add_argument("variavel")
    sp.add_parser("confronto"); sp.add_parser("auditoria")
    pf = sp.add_parser("perfil"); pf.add_argument("--recorte", default="dia"); pf.add_argument("--unidade", default="U-AD")
    mo = sp.add_parser("modelo")
    mo.add_argument("--parte", default="tudo", choices=["desempenho", "arvore", "diagnostico", "crispdm", "tudo"])
    qa = sp.add_parser("qualidade")
    qa.add_argument("--parte", default="tudo", choices=["dicionario","formulas","confronto","faltantes",
        "categoricas","univariada","discrepantes","achados","reconferencia","tudo"])
    qa.add_argument("--variavel")
    ot = sp.add_parser("otimizar")
    ot.add_argument("--parte", default="tudo",
                    choices=["modelo","solucao","precos","fronteira","sensibilidade","tudo"])
    rf = sp.add_parser("referencia"); rf.add_argument("--termo"); rf.add_argument("--limite", type=int, default=20)
    bu = sp.add_parser("buscar"); bu.add_argument("termo", nargs="+")
    bu.add_argument("--origem", choices=["acervo", "resultado", "auditoria"]); bu.add_argument("--limite", type=int, default=20)
    sq = sp.add_parser("sql"); sq.add_argument("consulta"); sq.add_argument("--limite", type=int, default=50)
    le = sp.add_parser("lembrar"); le.add_argument("chave"); le.add_argument("valor"); le.add_argument("--escopo", default="geral")
    re_ = sp.add_parser("recordar"); re_.add_argument("--termo"); re_.add_argument("--escopo")
    es = sp.add_parser("esquecer"); es.add_argument("chave")
    a = ap.parse_args()
    if not a.cmd: ap.print_help(); return 0

    args = {k: v for k, v in vars(a).items() if k != "cmd" and v not in (None, False)}
    if a.cmd == "buscar": args["termo"] = " ".join(a.termo)
    if a.cmd == "resultado" and args.pop("sig", False): args["significativo"] = True

    s = Servidor()
    saida = s._chamar("ana_" + a.cmd, args)
    print(saida["content"][0]["text"])
    return 1 if saida.get("isError") else 0

if __name__ == "__main__":
    sys.exit(main())
