#!/usr/bin/env python3
"""Console dos agentes digitais do LAPE.

    python3 scripts/lape_agent.py rastreador          # busca nas bases externas
    python3 scripts/lape_agent.py curador             # ciclo completo + painel
    python3 scripts/lape_agent.py api --port 8000     # sobe o site + API
    python3 scripts/lape_agent.py usuarios --criar "Nome" email@udesc.br --perfil admin
    python3 scripts/lape_agent.py revisar --list      # descobertas pendentes
    python3 scripts/lape_agent.py lake                # bronze -> ouro -> historico
    python3 scripts/lape_agent.py demo                # massa de teste + painel de demo
    python3 scripts/lape_agent.py publicar            # confere o que falta para ir ao ar
    python3 scripts/lape_agent.py autor "Fulano" --conferir   # producao pela PubMed
    python3 scripts/lape_agent.py identificar         # DOI, PMID, PMC e acesso aberto
    python3 scripts/lape_agent.py lattes --conferir    # ve o que o Lattes traria
    python3 scripts/lape_agent.py planilha            # reescreve a planilha do laboratorio
    python3 scripts/lape_agent.py status              # resumo do banco
    python3 scripts/lape_agent.py rag indexar --banco # indexa o corpus para busca semantica
    python3 scripts/lape_agent.py rag buscar "..."    # busca semantica no corpus
    python3 scripts/lape_agent.py rag mcp             # servidor MCP para clientes de I.A.

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


def cmd_publicar(args: argparse.Namespace) -> int:
    """Confere o que falta para expor o serviço fora desta máquina."""
    from lape import preflight

    db = Database(args.db)
    db.migrate()
    achados = preflight.conferir(db)
    db.close()
    if args.json:
        print(json.dumps(preflight.resumo(achados), ensure_ascii=False, indent=2))
        return 0 if preflight.resumo(achados)["pronto"] else 1
    pronto = preflight.imprimir(achados)
    print()
    print("Passo a passo completo: README → Publicar na nuvem — custo zero")
    return 0 if pronto else 1


def cmd_identificar(args: argparse.Namespace) -> int:
    """Acha DOI, PMID, PMC e acesso aberto dos artigos ja cadastrados."""
    from lape.agents import tracker

    db = Database(args.db)
    db.migrate()
    try:
        antes = db.dicts(
            "SELECT COUNT(*) AS n,"
            "       SUM(CASE WHEN doi IS NOT NULL AND TRIM(doi) <> '' THEN 1 ELSE 0 END) AS doi,"
            "       SUM(CASE WHEN pmid IS NOT NULL THEN 1 ELSE 0 END) AS pmid,"
            "       SUM(CASE WHEN pmc IS NOT NULL THEN 1 ELSE 0 END) AS pmc,"
            "       SUM(CASE WHEN open_access = 1 THEN 1 ELSE 0 END) AS aberto"
            "  FROM articles")[0]
        print(f"Antes: {antes['n']} artigos — {antes['doi'] or 0} com DOI,"
              f" {antes['pmid'] or 0} com PMID, {antes['pmc'] or 0} com PMC,"
              f" {antes['aberto'] or 0} em acesso aberto")
        if args.conferir:
            pendentes = db.scalar(
                "SELECT COUNT(*) FROM articles WHERE doi IS NULL"
                "   OR TRIM(COALESCE(doi, '')) = '' OR pmid IS NULL OR oa_status IS NULL")
            print()
            print(f"{pendentes} artigo(s) seriam consultados nas bases. Nada foi gravado.")
            print("Para procurar de verdade, rode o mesmo comando sem --conferir.")
            return 0
        print()
        resultado = tracker.identificar(db, limit=args.limite, verbose=True)
        depois = db.dicts(
            "SELECT SUM(CASE WHEN doi IS NOT NULL AND TRIM(doi) <> '' THEN 1 ELSE 0 END) AS doi,"
            "       SUM(CASE WHEN pmid IS NOT NULL THEN 1 ELSE 0 END) AS pmid,"
            "       SUM(CASE WHEN pmc IS NOT NULL THEN 1 ELSE 0 END) AS pmc,"
            "       SUM(CASE WHEN open_access = 1 THEN 1 ELSE 0 END) AS aberto"
            "  FROM articles")[0]
    finally:
        db.close()
    print()
    print(f"  com DOI ........... {antes['doi'] or 0} → {depois['doi'] or 0}")
    print(f"  com PMID .......... {antes['pmid'] or 0} → {depois['pmid'] or 0}")
    print(f"  com PMC ........... {antes['pmc'] or 0} → {depois['pmc'] or 0}"
          f"   (texto completo livre)")
    print(f"  em acesso aberto .. {antes['aberto'] or 0} → {depois['aberto'] or 0}")
    for erro in resultado["erros"][:5]:
        print(f"  ! {erro}")
    return 0


def cmd_autor(args: argparse.Namespace) -> int:
    """Traz a producao de um pesquisador das bases publicas."""
    from lape import ingest_autor, variaveis

    nomes = [n.strip() for n in args.nomes if n.strip()]
    afiliacao = args.afiliacao
    if not nomes:
        # Sem nome, vale a lista que o laboratorio ja pediu -- e o caso
        # comum. Errar aqui era pedir para a pessoa digitar de novo o que
        # o sistema ja sabe.
        nomes = [p["nome"] for p in ingest_autor.PESQUISADORES]
        afiliacao = afiliacao or ingest_autor.PESQUISADORES[0].get("afiliacao")
        print("Sem nome informado: trazendo quem está na lista do laboratório —")
        print("  " + ", ".join(nomes))

    achados = []
    for nome in nomes:
        print(f"\nProcurando {nome}…")
        try:
            achado = ingest_autor.buscar(nome, afiliacao, args.desde, args.limite)
        except Exception as exc:
            print(f"  ! não consegui buscar ({type(exc).__name__}: {exc})")
            print("    a busca sai desta máquina para a PubMed — confira a internet")
            continue
        resumo = ingest_autor.resumir(achado)
        achados.append((nome, achado, resumo))
        print(f"  busca ............. {resumo['termo']}")
        print(f"  encontrados ....... {resumo['encontrados']}"
              f"  ({resumo['com_doi']} com DOI, {resumo['com_resumo']} com resumo)")
        if resumo["primeiro_ano"]:
            print(f"  período ........... {resumo['primeiro_ano']}–{resumo['ultimo_ano']}"
                  f"  ({resumo['anos_com_producao']} anos com produção)")
        if resumo["revistas"]:
            print("  onde mais publica .")
            for revista, n in resumo["revistas"][:5]:
                print(f"      {n:3}  {revista[:58]}")
        if resumo["paises"]:
            print(f"  países ............ "
                  f"{', '.join(f'{p} ({n})' for p, n in resumo['paises'][:6])}")

    if not achados:
        return 1
    if args.conferir:
        print()
        print(f"Conferência apenas — nada foi gravado. Seriam lidos "
              f"{sum(r['encontrados'] for _, _, r in achados)} artigo(s).")
        print("Confira se é a pessoa certa (revista e país costumam entregar) e,")
        print("se estiver, rode o mesmo comando sem --conferir.")
        return 0

    db = Database(args.db)
    db.migrate()
    try:
        antes = int(db.scalar("SELECT COUNT(*) FROM articles") or 0)
        for nome, achado, _ in achados:
            resultado = ingest_autor.importar(db, achado, quem=nome)
            print(f"\n  {nome}: {resultado['novos']} novo(s),"
                  f" {resultado['ja_havia']} já estava(m) no banco")
        depois = int(db.scalar("SELECT COUNT(*) FROM articles") or 0)
        variaveis.instalar(db)
        marcacao = variaveis.marcar_artigos(db)
    finally:
        db.close()
    print()
    print(f"  artigos no banco ... {antes} → {depois}  (+{depois - antes})")
    print(f"  variáveis marcadas . {marcacao['ligacoes']} ligação(ões)"
          f" em {marcacao['com_variavel']} artigo(s)")
    return 0


def cmd_lattes(args: argparse.Namespace) -> int:
    """Importa o Lattes de pessoas escolhidas -- e so delas."""
    from lape import ingest_lattes

    arquivos = [Path(a) for a in (args.arquivos or [])]
    if not arquivos:
        arquivos = ingest_lattes.discover_lattes_files(args.de or config.RAW_DIR)
    pedidos = [p.strip() for p in (args.somente or "").split(",") if p.strip()]
    if pedidos:
        arquivos = ingest_lattes.filtrar(arquivos, pedidos)

    if not arquivos:
        print("Nenhum currículo encontrado.")
        print()
        print("Como obter o XML (o CNPq não deixa baixar por programa —")
        print("é preciso resolver o captcha no navegador):")
        print("  1. abra o currículo em lattes.cnpq.br")
        print("  2. clique no ícone XML, no alto à direita")
        print("  3. salve o .zip em data/raw/ com o nome da pessoa, por exemplo")
        print("     data/raw/lattes_alexandro_andrade.zip")
        return 1

    print(f"{len(arquivos)} currículo(s):")
    total_novos = 0
    for caminho in arquivos:
        try:
            resumo = ingest_lattes.confere(caminho)
        except Exception as exc:
            print(f"  ! {caminho.name}: não consegui ler ({exc})")
            continue
        print()
        print(f"  {resumo['de_quem']}  ({caminho.name})")
        print(f"    artigos ............ {resumo['artigos']}"
              f"  ({resumo['publicados']} publicados, {resumo['com_doi']} com DOI)")
        print(f"    trabalhos em evento  {resumo['eventos']}")
        if resumo["primeiro_ano"]:
            print(f"    período ............ {resumo['primeiro_ano']}–{resumo['ultimo_ano']}"
                  f"  ({resumo['anos_com_producao']} anos com produção)")
        if resumo["nomes_de_citacao"]:
            print(f"    cita-se como ....... {'; '.join(resumo['nomes_de_citacao'][:4])}")
        total_novos += resumo["artigos"]

    if args.conferir:
        print()
        print(f"Conferência apenas — nada foi gravado. Seriam lidos {total_novos} artigo(s).")
        print("Para importar de verdade, rode o mesmo comando sem --conferir.")
        return 0

    db = Database(args.db)
    db.migrate()
    try:
        antes = int(db.scalar("SELECT COUNT(*) FROM articles") or 0)
        resultado = ingest_lattes.ingest_all(db, verbose=True, arquivos=arquivos,
                                             somente=None)
        depois = int(db.scalar("SELECT COUNT(*) FROM articles") or 0)
        # o vocabulario passa sobre o que chegou: sem isso, os artigos novos
        # entram no painel sem variavel nenhuma
        from lape import variaveis

        variaveis.instalar(db)
        marcacao = variaveis.marcar_artigos(db)
    finally:
        db.close()
    print()
    print(f"Importado de: {', '.join(resultado['de_quem']) or '—'}")
    print(f"  artigos no banco ... {antes} → {depois}  (+{depois - antes})")
    print(f"  trabalhos em evento  {resultado['events']}")
    print(f"  variáveis marcadas . {marcacao['ligacoes']} ligação(ões)"
          f" em {marcacao['com_variavel']} artigo(s)")
    return 0


def cmd_app(args: argparse.Namespace) -> int:
    """O painel em forma de aplicativo de celular, para mostrar a alguem."""
    from lape import celular

    db = Database(args.db)
    db.migrate()
    try:
        resultado = celular.escrever(db, args.para)
    finally:
        db.close()
    print(f"  arquivo ........... {resultado['arquivo']}")
    print(f"  tamanho ........... {resultado['bytes'] // 1024} kB"
          f"  ({resultado['artigos']} artigos)")
    print()
    print("  Abre no celular como aplicativo: abas embaixo, uma tela por aba.")
    print("  E um RETRATO -- nao esta ao vivo e nao grava. Pode mandar por")
    print("  WhatsApp ou e-mail; abre sozinho, sem internet.")
    return 0


def cmd_instantaneo(args: argparse.Namespace) -> int:
    """Uma pagina so, com tudo dentro, para abrir longe do laboratorio."""
    from lape import instantaneo

    db = Database(args.db)
    db.migrate()
    try:
        resultado = instantaneo.escrever(db, args.para)
    finally:
        db.close()
    print(f"  arquivo ........... {resultado['arquivo']}")
    print(f"  tamanho ........... {resultado['bytes'] // 1024} kB")
    print()
    print("  Abre com dois cliques, sem servidor e sem internet. E um RETRATO:")
    print("  nao esta ao vivo e nao grava nada -- a data esta escrita no topo.")
    return 0


def cmd_planilha(args: argparse.Namespace) -> int:
    """A planilha do laboratorio -- a mesma que a API reescreve sozinha."""
    from lape import planilha

    db = Database(args.db)
    db.migrate()
    try:
        if args.onde:
            resumo = planilha.resumo(db, db_path=args.db)
            print(f"  arquivo ........... {resumo['arquivo']}")
            print(f"  existe ............ {'sim' if resumo['existe'] else 'ainda não'}"
                  f"  ({resumo['bytes'] // 1024} kB)")
            print(f"  atualizada em ..... {resumo['atualizada_em'] or 'nunca'}")
            if resumo["motivo"]:
                print(f"  motivo ............ {resumo['motivo']}")
            print(f"  agora .............. {resumo['pendente']}")
            return 0
        if args.para:
            alvo = planilha.gerar(db, destino=args.para)
            print(f"Planilha escrita em: {alvo}")
            return 0
        feita = planilha.rodar(db, forcar=args.forcar, db_path=args.db)
    finally:
        db.close()
    if not feita.get("gerou"):
        print(f"Planilha não reescrita: {feita['motivo']}.")
        print("Para reescrever assim mesmo: --forcar")
        return 0
    print(f"Planilha atualizada: {feita['arquivo']}")
    print(f"  motivo: {feita['motivo']}")
    return 0


def cmd_backup(args: argparse.Namespace) -> int:
    """Copia de seguranca do banco -- a mesma que a API faz sozinha."""
    from lape import backup

    if args.restaurar:
        destino = args.para or Path(args.db).with_name("db-restaurado.sqlite")
        conferido = backup.restaurar(Path(args.restaurar), destino)
        print(f"Cópia restaurada em: {conferido['destino']}")
        print(f"  integridade: {conferido['integridade']}")
        for tabela, quantos in conferido["conteudo"].items():
            print(f"  {tabela:<12} {quantos if quantos is not None else '—'}")
        print()
        print("O banco em uso NÃO foi tocado. Para trocar, com o serviço parado:")
        print(f"  mv {destino} {args.db}")
        return 0

    db = Database(args.db)
    db.migrate()
    try:
        if args.listar:
            resumo = backup.resumo(db, db_path=args.db)
            print(f"  pasta ............. {resumo['pasta']}")
            print(f"  cópias guardadas .. {resumo['copias']}"
                  f"  ({resumo['bytes_guardados'] // 1024} kB)")
            print(f"  última ............ {resumo['ultima'] or 'nenhuma'}")
            if resumo["motivo_da_ultima"]:
                print(f"  motivo ............ {resumo['motivo_da_ultima']}")
            print(f"  pendente agora .... {resumo['pendente'] or 'não'}")
            for arquivo in backup.copias(args.db)[:10]:
                print(f"    {arquivo.name}  {arquivo.stat().st_size // 1024} kB")
            return 0
        feito = backup.rodar(db, forcar=args.forcar, db_path=args.db)
    finally:
        db.close()
    if feito is None:
        print("Nada mudou desde a última cópia e ela ainda é recente. Nenhuma cópia feita.")
        print("Para copiar assim mesmo: --forcar")
        return 0
    print(f"Cópia feita: {feito['arquivo']}  ({feito['bytes'] // 1024} kB)")
    print(f"  motivo: {feito['motivo']}")
    if feito["apagadas"]:
        print(f"  cópias antigas apagadas: {feito['apagadas']}")
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

    publish_parser = subparsers.add_parser(
        "publicar", aliases=["conferir"],
        help="confere o que falta para publicar o serviço na internet")
    publish_parser.add_argument("--json", action="store_true")
    publish_parser.set_defaults(func=cmd_publicar)

    backup_parser = subparsers.add_parser(
        "backup", help="copia de seguranca do banco (a API tambem faz sozinha)")
    backup_parser.add_argument("--forcar", action="store_true",
                               help="copia mesmo sem mudanca desde a ultima")
    backup_parser.add_argument("--listar", action="store_true",
                               help="mostra as copias guardadas, sem copiar nada")
    backup_parser.add_argument("--restaurar", type=Path, metavar="ARQUIVO",
                               help="descompacta e confere uma copia (nao troca o banco em uso)")
    backup_parser.add_argument("--para", type=Path, metavar="DESTINO",
                               help="onde escrever a copia restaurada")
    backup_parser.set_defaults(func=cmd_backup)

    ident_parser = subparsers.add_parser(
        "identificar", help="acha DOI, PMID, PMC e acesso aberto dos artigos")
    ident_parser.add_argument("--limite", type=int, help="quantos artigos consultar")
    ident_parser.add_argument("--conferir", action="store_true",
                              help="diz quantos seriam consultados, sem procurar nada")
    ident_parser.set_defaults(func=cmd_identificar)

    autor_parser = subparsers.add_parser(
        "autor", help="traz a producao de um pesquisador da PubMed")
    autor_parser.add_argument("nomes", nargs="*", help="nome completo, um ou varios")
    autor_parser.add_argument("--afiliacao", default="",
                              help="filtro de afiliacao: sem ele, o nome traz gente demais")
    autor_parser.add_argument("--desde", type=int, help="ano inicial")
    autor_parser.add_argument("--limite", type=int, default=400,
                              help="teto de artigos por pessoa")
    autor_parser.add_argument("--conferir", action="store_true",
                              help="mostra o que seria importado, sem gravar nada")
    autor_parser.set_defaults(func=cmd_autor)

    lattes_parser = subparsers.add_parser(
        "lattes", help="importa o curriculo Lattes de pessoas escolhidas")
    lattes_parser.add_argument("arquivos", nargs="*",
                               help="os .zip/.xml a importar (padrao: procura em data/raw)")
    lattes_parser.add_argument("--somente", default="",
                               help="nomes separados por virgula: 'Andrade,Vilarino'")
    lattes_parser.add_argument("--de", type=Path, metavar="PASTA",
                               help="onde procurar os curriculos")
    lattes_parser.add_argument("--conferir", action="store_true",
                               help="mostra o que seria importado, sem gravar nada")
    lattes_parser.set_defaults(func=cmd_lattes)

    planilha_parser = subparsers.add_parser(
        "planilha", help="reescreve a planilha do laboratorio (a API tambem faz sozinha)")
    planilha_parser.add_argument("--forcar", action="store_true",
                                 help="reescreve mesmo sem cadastro novo")
    planilha_parser.add_argument("--onde", action="store_true",
                                 help="mostra o caminho e a data, sem escrever nada")
    planilha_parser.add_argument("--para", type=Path, metavar="ARQUIVO",
                                 help="escreve num caminho escolhido, sem mexer na planilha oficial")
    planilha_parser.set_defaults(func=cmd_planilha)

    app_parser = subparsers.add_parser(
        "app", help="o painel em forma de aplicativo de celular, para mostrar")
    app_parser.add_argument(
        "--para", type=Path, default=Path("docs/lape-app.html"),
        metavar="ARQUIVO", help="onde gravar (padrao: docs/lape-app.html)")
    app_parser.set_defaults(func=cmd_app)

    instantaneo_parser = subparsers.add_parser(
        "instantaneo",
        help="gera uma pagina unica do painel, para abrir longe do laboratorio")
    instantaneo_parser.add_argument(
        "--para", type=Path, default=Path("docs/panorama-instantaneo.html"),
        metavar="ARQUIVO", help="onde gravar (padrao: docs/panorama-instantaneo.html)")
    instantaneo_parser.set_defaults(func=cmd_instantaneo)

    status_parser = subparsers.add_parser("status", help="resumo do banco e das lacunas")
    status_parser.set_defaults(func=cmd_status)

    from lape.rag.cli import build_parser as build_rag_parser
    build_rag_parser(subparsers)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
