#!/usr/bin/env python3
"""Console dos agentes digitais do LAPE.

    python3 scripts/lape_agent.py rastreador          # busca nas bases externas
    python3 scripts/lape_agent.py curador             # ciclo completo + painel
    python3 scripts/lape_agent.py api --port 8000     # sobe o site + API
    python3 scripts/lape_agent.py usuarios --criar "Nome" email@udesc.br --perfil admin
    python3 scripts/lape_agent.py revisar --list      # descobertas pendentes
    python3 scripts/lape_agent.py lake                # bronze -> ouro -> historico
    python3 scripts/lape_agent.py demo                # massa de teste + painel de demo
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
import os
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


def cmd_lake(args: argparse.Namespace) -> int:
    from lape import lake

    db = Database(args.db)
    db.migrate()
    if args.linhagem:
        for row in lake.lineage(db, args.limite or 40):
            print(f"  {row['captured_at']}  {row['layer']:7s} {row['source_path'][:52]:52s}"
                  f" {(row['rows'] if row['rows'] is not None else '-')!s:>7}"
                  f" {row['bytes'] or 0:>9} B")
        db.close()
        return 0
    if args.consultar:
        medida, por = args.consultar[0], (args.consultar[1] if len(args.consultar) > 1 else "linha")
        try:
            result = lake.query(db, medida, por)
        except lake.QueryError as exc:
            print(f"! {exc}")
            db.close()
            return 1
        print(f"{result['measure_label']} por {result['by_label'].lower()}:")
        for row in result["rows"]:
            print(f"  {str(row['dim1'])[:44]:44s} {row['valor']}")
        db.close()
        return 0
    result = lake.run(db, raw_dir=args.raw, with_export=args.exportar)
    db.close()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


def cmd_usuarios(args: argparse.Namespace) -> int:
    from lape import auth

    db = Database(args.db)
    db.migrate()
    try:
        if args.criar:
            nome, login_value = args.criar
            conta = auth.create_account(db, nome, login_value, args.senha, role=args.perfil)
            print(f"Acesso criado: {conta['login']}  (perfil {conta['perfil'] if 'perfil' in conta else args.perfil})")
            if "senha_inicial" in conta:
                print(f"Senha inicial: {conta['senha_inicial']}")
                print("Peca ao integrante para troca-la no primeiro acesso.")
        elif args.redefinir:
            member_id, senha = args.redefinir[0], (args.redefinir[1] if len(args.redefinir) > 1 else None)
            row = db.dicts("SELECT id, full_name, login FROM members WHERE id = ?", (int(member_id),))
            if not row:
                print(f"Integrante {member_id} nao encontrado.")
                return 1
            senha = senha or auth.generate_password()
            auth.set_credentials(db, int(member_id), row[0]["login"] or args.login or "",
                                 senha, args.perfil, must_change=True)
            print(f"Senha de {row[0]['full_name']} redefinida para: {senha}")
        elif args.perfil_de:
            member_id, perfil = args.perfil_de
            db.execute("UPDATE members SET user_role = ? WHERE id = ?", (perfil, int(member_id)))
            db.conn.commit()
            print(f"Integrante {member_id} agora e '{perfil}'.")
        else:
            rows = db.dicts(
                "SELECT id, full_name, login, user_role, active, last_login_at"
                " FROM members WHERE login IS NOT NULL ORDER BY user_role, full_name")
            if not rows:
                print("Nenhum usuario com acesso. Crie o primeiro administrador:")
                print("  python3 scripts/lape_agent.py usuarios"
                      " --criar 'Alexandro Andrade' andrade@udesc.br --perfil admin")
            for row in rows:
                marca = " " if row["active"] else "x"
                print(f"  [{marca}] {row['id']:3d}  {row['user_role']:12s} {row['login']:32s}"
                      f" {row['full_name']}"
                      f"{'  ultimo acesso ' + row['last_login_at'] if row['last_login_at'] else ''}")
    except auth.AuthError as exc:
        print(f"! {exc.message}")
        return 1
    finally:
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
    print(f"  projetos ...... {db.scalar('SELECT COUNT(*) FROM projects')}")
    print(f"  usuarios ...... {db.scalar('SELECT COUNT(*) FROM members WHERE login IS NOT NULL')}"
          " com acesso")
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


def cmd_demo(args: argparse.Namespace) -> int:
    """Gera a massa de teste num banco separado e publica o painel de demonstração."""
    from lape import demo

    # A massa nunca cai no banco de produção por descuido: sem --db explícito
    # (ou com --db apontando para o banco real e sem --forcar), ela vai para
    # data/demo.sqlite. É o que permite gerar a demonstração num laboratório
    # que já tem dados de verdade carregados.
    destino = args.db
    if destino == config.DB_PATH:
        if args.forcar:
            print(f"! gravando no banco de produção {destino}, a seu pedido (--forcar).")
            print("! a massa se soma ao que já existe; faça backup antes.")
        else:
            destino = config.DATA_DIR / "demo.sqlite"
    if destino.exists() and not args.manter:
        destino.unlink()          # massa nova, banco limpo: é o que a torna reproduzível
        for sufixo in ("-wal", "-shm"):
            extra = destino.with_name(destino.name + sufixo)
            if extra.exists():
                extra.unlink()

    print(f"[massa de teste] semente {args.semente} · {args.artigos} artigos")
    print("  Dados fictícios. Nomes, títulos, DOIs e números são inventados.")
    db = Database(destino)
    result = demo.run(db, seed_value=args.semente, n_artigos=args.artigos,
                      report=args.report, verbose=True)
    if args.acesso:
        from lape import auth

        nome, login = args.acesso
        try:
            conta = auth.create_account(db, nome, login, args.senha or "demonstracao123",
                                        role=args.perfil)
            print(f"  acesso: {conta['login']}  (perfil {args.perfil})")
        except auth.AuthError as exc:
            print(f"  ! acesso não criado: {exc}")
    db.close()
    print()
    print("Para navegar com o painel ao vivo (o aviso de massa de teste vai no título):")
    print(f'  LAPE_LAB_NAME="LAPE — MASSA DE TESTE" \\')
    print(f"    python3 scripts/lape_agent.py --db {destino} api --port 8000")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
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

    api_parser = subparsers.add_parser(
        "api", aliases=["serve"], help="sobe o site (painel + area do integrante) e a API")
    api_parser.add_argument("--host", default=os.environ.get("LAPE_HOST", "127.0.0.1"),
                            help="use 0.0.0.0 em container/servidor")
    api_parser.add_argument("--port", type=int,
                            default=int(os.environ.get("PORT")
                                        or os.environ.get("LAPE_PORT") or 8000))
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

    lake_parser = subparsers.add_parser(
        "lake", aliases=["lakehouse"],
        help="camadas bronze/ouro, histórico de indicadores e consultas analíticas")
    lake_parser.add_argument("--raw", type=Path, default=config.RAW_DIR)
    lake_parser.add_argument("--exportar", action="store_true",
                             help="grava a camada ouro em Parquet (ou CSV)")
    lake_parser.add_argument("--linhagem", action="store_true",
                             help="mostra de onde veio cada carga")
    lake_parser.add_argument("--consultar", nargs="+", metavar="MEDIDA [DIMENSAO]",
                             help="ex.: --consultar publicados linha")
    lake_parser.add_argument("--limite", type=int, default=None)
    lake_parser.add_argument("--json", action="store_true")
    lake_parser.set_defaults(func=cmd_lake)

    users_parser = subparsers.add_parser(
        "usuarios", aliases=["users"], help="cria e gerencia os acessos dos integrantes")
    users_parser.add_argument("--criar", nargs=2, metavar=("NOME", "LOGIN"))
    users_parser.add_argument("--senha", default=None,
                              help="senha inicial (em branco: o sistema gera uma)")
    users_parser.add_argument("--perfil", default="integrante",
                              choices=["admin", "coordenacao", "integrante", "leitura"])
    users_parser.add_argument("--redefinir", nargs="+", metavar="ID [SENHA]",
                              help="redefine a senha de um integrante")
    users_parser.add_argument("--perfil-de", nargs=2, metavar=("ID", "PERFIL"),
                              dest="perfil_de")
    users_parser.add_argument("--login", default=None)
    users_parser.set_defaults(func=cmd_usuarios)

    demo_parser = subparsers.add_parser(
        "demo", aliases=["massa"],
        help="gera massa de teste (dados fictícios) num banco separado")
    demo_parser.add_argument("--artigos", type=int, default=160,
                             help="quantos artigos gerar (padrão: 160)")
    demo_parser.add_argument("--semente", type=int, default=20260826,
                             help="mesma semente, mesma massa")
    demo_parser.add_argument("--report", type=Path, default=config.DOCS_DIR / "demo.html")
    demo_parser.add_argument("--manter", action="store_true",
                             help="soma ao banco existente em vez de recomeçar")
    demo_parser.add_argument("--forcar", action="store_true",
                             help="permite gravar no banco de produção (não recomendado)")
    demo_parser.add_argument("--acesso", nargs=2, metavar=("NOME", "LOGIN"),
                             help="já cria um acesso para navegar no painel ao vivo")
    demo_parser.add_argument("--senha", default=None)
    demo_parser.add_argument("--perfil", default="coordenacao",
                             choices=["admin", "coordenacao", "integrante", "leitura"])
    demo_parser.add_argument("--json", action="store_true")
    demo_parser.set_defaults(func=cmd_demo)

    status_parser = subparsers.add_parser("status", help="resumo do banco e das lacunas")
    status_parser.set_defaults(func=cmd_status)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
