#!/usr/bin/env python3
"""Pipeline completo do LAPE: planilhas + Lattes + citacoes -> banco -> painel HTML.

Uso:
    python3 scripts/run_pipeline.py                 # tudo
    python3 scripts/run_pipeline.py --no-citations  # sem consultar Scopus/WoS
    python3 scripts/run_pipeline.py --only-report   # so regenera o HTML
"""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lape import config
from lape.db import Database


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", type=Path, default=config.DB_PATH)
    parser.add_argument("--raw", type=Path, default=config.RAW_DIR)
    parser.add_argument("--report", type=Path, default=config.REPORT_PATH)
    parser.add_argument("--window", type=int, default=config.WINDOW_YEARS,
                        help="janela em anos das analises recentes (padrao: 5)")
    parser.add_argument("--no-excel", action="store_true")
    parser.add_argument("--no-lattes", action="store_true")
    parser.add_argument("--no-citations", action="store_true")
    parser.add_argument("--only-report", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    from lape import ingest_citations, ingest_excel, ingest_lattes, metrics, report

    print(f"LAPE :: banco {args.db}")
    db = Database(args.db)
    if not args.no_backup:
        backup = db.backup()
        if backup:
            print(f"  backup: {backup.name}")
    db.migrate()
    print("  esquema aplicado")

    if not args.only_report:
        if not args.no_excel:
            print("\n[1/3] Planilhas")
            ingest_excel.ingest_all(db, args.raw)
        if not args.no_lattes:
            print("\n[2/3] Curriculo Lattes")
            ingest_lattes.ingest_all(db, args.raw)
            ingest_excel.derive_status(db)
        if not args.no_citations:
            print("\n[3/3] Citacoes (Scopus / Web of Science)")
            try:
                ingest_citations.update_citations(db)
            except Exception as exc:
                print(f"  ! falha ao atualizar citacoes: {exc}")
                traceback.print_exc(limit=1)

    print("\n[painel] Calculando indicadores")
    payload = metrics.build_payload(db, window=args.window)
    path = report.render(payload, args.report)
    over = payload["overview"]
    print(f"  {over['n_articles']} artigos | {over['n_published']} publicados"
          f" | {over['n_members']} integrantes | {over['n_events']} atividades")
    print(f"\nPainel gerado: {path}")
    db.log_ingest("pipeline", target="report", file=str(path), rows_written=over["n_articles"])
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
