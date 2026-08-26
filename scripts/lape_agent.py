#!/usr/bin/env python3
"""Console dos agentes digitais do LAPE.

    python3 scripts/lape_agent.py rastreador          # busca nas bases externas
    python3 scripts/lape_agent.py curador             # ciclo completo + painel
    python3 scripts/lape_agent.py api --port 8000     # sobe a API REST
    python3 scripts/lape_agent.py revisar --list      # descobertas pendentes
    python3 scripts/lape_agent.py status              # resumo do banco

Agentes:
  rastreador  vai as bases bibliograficas (OpenAlex, Crossref, PubMed,
              Scopus, Web of Science) e traz metadados, citacoes e
              publicacoes novas dos integrantes.
  curador     mantem o banco: carrega planilhas e Lattes, consolida,
              valida, recalcula os indicadores e publica o painel HTML.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lape import config
from lape.db import Database


def cmd_rastreador(args: argparse.Namespace) -> int:
    from lape.agents import tracker

    db = Database(args.db)
    db.migrate()
    tasks = tuple(args.tarefas) if args.tarefas else tracker.TASKS
    result = tracker.run(db, tasks, verbose=True, limit=args.limite,
                         since_year=args.desde)
    db.close()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


def cmd_curador(args: argparse.Namespace) -> int:
    from lape.agents import curator

    db = Database(args.db)
    if not args.sem_backup:
        backup = db.backup()
        if backup:
            print(f"  backup: {backup.name}")
    db.migrate()
    result = curator.run(
        db, raw_dir=args.raw, output=args.report, window=args.janela,
        with_tracker=not args.offline, auto_accept=args.aceitar_automatico, verbose=True,
    )
    db.close()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


def cmd_api(args: argparse.Namespace) -> int:
    from lape import api

    api.serve(host=args.host, port=args.port, db_path=args.db, report_path=args.report)
    return 0


def cmd_revisar(args: argparse.Namespace) -> int:
    from lape.agents import curator

    db = Database(args.db)
    db.migrate()
    if args.list or (not args.aceitar and not args.ignorar and not args.auto):
        rows = db.dicts(
            "SELECT id, year, citations, journal, substr(title, 1, 70) AS titulo"
            " FROM discoveries WHERE status = 'pendente'"
            " ORDER BY COALESCE(citations, 0) DESC LIMIT ?", (args.limite or 50,))
        if not rows:
            print("Nenhuma descoberta pendente. Rode: lape_agent.py rastreador")
        for row in rows:
            print(f"  [{row['id']:4d}] {row['year'] or '????'} "
                  f"({row['citations'] or 0:4d} cit.) {row['titulo']}")
    for discovery_id in args.aceitar or []:
        print(curator.review_discovery(db, discovery_id, "aceitar")["status"], discovery_id)
    for discovery_id in args.ignorar or []:
        print(curator.review_discovery(db, discovery_id, "ignorar")["status"], discovery_id)
    if args.auto:
        print(f"aceitas automaticamente: {curator.auto_review(db)['accepted']}")
    db.close()
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    from lape.agents import curator

    db = Database(args.db)
    db.migrate()
    counts = db.dicts("SELECT status, COUNT(*) AS n FROM articles GROUP BY status ORDER BY n DESC")
    print(f"Banco: {args.db}")
    print(f"  artigos ....... {db.scalar('SELECT COUNT(*) FROM articles')}")
    for row in counts:
        print(f"      {row['status']:14s} {row['n']}")
    print(f"  integrantes ... {db.scalar('SELECT COUNT(*) FROM members')}")
    print(f"  submissoes .... {db.scalar('SELECT COUNT(*) FROM submissions')}")
    print(f"  atividades .... {db.scalar('SELECT COUNT(*) FROM events')}")
    pending = db.scalar("SELECT COUNT(*) FROM discoveries WHERE status = 'pendente'")
    print(f"  descobertas ... {pending} pendentes")
    validation = curator.validate(db)
    print("\nLacunas:")
    for issue in validation["issues"]:
        mark = "ok" if not issue["n"] else "->"
        print(f"  {mark} {issue['label']}: {issue['n']}")
    if validation["duplicate_members"]:
        print("\nPossiveis duplicatas de integrantes"
              " (consolide na coluna 'Variacoes' da aba Integrantes):")
        for pair in validation["duplicate_members"][:15]:
            print(f"  - {pair['a']} / {pair['b']}  ({pair['motivo']})")
    db.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", type=Path, default=config.DB_PATH)
    subparsers = parser.add_subparsers(dest="comando", required=True)

    tracker_parser = subparsers.add_parser(
        "rastreador", aliases=["tracker"], help="busca informacao nas bases externas")
    tracker_parser.add_argument("tarefas", nargs="*",
                                choices=["descobrir", "enriquecer", "citar"], default=None)
    tracker_parser.add_argument("--limite", type=int, default=None)
    tracker_parser.add_argument("--desde", type=int, default=None,
                                help="ano inicial da descoberta (padrao: janela de analise)")
    tracker_parser.add_argument("--json", action="store_true")
    tracker_parser.set_defaults(func=cmd_rastreador)

    curator_parser = subparsers.add_parser(
        "curador", aliases=["curator"], help="carrega, consolida, valida e publica")
    curator_parser.add_argument("--raw", type=Path, default=config.RAW_DIR)
    curator_parser.add_argument("--report", type=Path, default=config.REPORT_PATH)
    curator_parser.add_argument("--janela", type=int, default=config.WINDOW_YEARS)
    curator_parser.add_argument("--offline", action="store_true",
                                help="nao consulta as bases externas")
    curator_parser.add_argument("--aceitar-automatico", action="store_true",
                                help="promove descobertas com 2+ autores ja cadastrados")
    curator_parser.add_argument("--sem-backup", action="store_true")
    curator_parser.add_argument("--json", action="store_true")
    curator_parser.set_defaults(func=cmd_curador)

    api_parser = subparsers.add_parser("api", aliases=["serve"], help="sobe a API REST")
    api_parser.add_argument("--host", default="127.0.0.1")
    api_parser.add_argument("--port", type=int, default=8000)
    api_parser.add_argument("--report", type=Path, default=config.REPORT_PATH)
    api_parser.set_defaults(func=cmd_api)

    review_parser = subparsers.add_parser("revisar", help="revisa as descobertas do rastreador")
    review_parser.add_argument("--list", action="store_true")
    review_parser.add_argument("--aceitar", type=int, nargs="*")
    review_parser.add_argument("--ignorar", type=int, nargs="*")
    review_parser.add_argument("--auto", action="store_true",
                               help="aceita as que tiverem 2+ autores ja cadastrados")
    review_parser.add_argument("--limite", type=int, default=50)
    review_parser.set_defaults(func=cmd_revisar)

    status_parser = subparsers.add_parser("status", help="resumo do banco e das lacunas")
    status_parser.set_defaults(func=cmd_status)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
