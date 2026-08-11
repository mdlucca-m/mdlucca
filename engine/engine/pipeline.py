"""pipeline.py — orquestra o produto de ponta a ponta.

Fluxo:  conteúdo(JSON) → verificar DOIs (Crossref) → renderizar HTML →
        exportar PNG (1080 + 4K) → montar PDF → relatório.

Uso:
    python -m engine.pipeline --content content/caminho.json --out dist/caminho \\
        [--no-verify] [--no-4k] [--no-pdf]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

# permite rodar tanto como módulo quanto como script direto
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import render, export, verify_refs   # noqa: E402


def run(content_path: str, out_base: str, verify=True, do_4k=True, do_pdf=True) -> dict:
    content = json.loads(Path(content_path).read_text(encoding="utf-8"))
    out = Path(out_base); out.mkdir(parents=True, exist_ok=True)
    report: dict = {"deck": content["id"], "steps": []}

    # 1) verificação de referências (integração Crossref)
    verified = None
    if verify:
        dois = [r["doi"] for r in content["refs"]]
        verified = verify_refs.verify_all(dois)
        ok = sum(1 for v in verified.values() if v)
        report["steps"].append({"verify": f"{ok}/{len(dois)} DOIs confirmados"})
        print(f"[1/4] Verificação: {ok}/{len(dois)} DOIs confirmados no Crossref")
    else:
        print("[1/4] Verificação: pulada")

    # 2) render HTML
    html_path = str(out / f"{content['id']}.html")
    render.render_file(content_path, html_path, verified)
    report["steps"].append({"render": html_path})
    print(f"[2/4] HTML: {html_path}")

    # 3) export PNG (1080 sempre; 4K opcional)
    pngs = {}
    pngs["1080"] = export.export_png(html_path, 1080, str(out / "png-1080"))
    print(f"[3/4] PNG 1080: {len(pngs['1080'])} lâminas")
    if do_4k:
        pngs["4k"] = export.export_png(html_path, 2160, str(out / "png-4k"))
        print(f"      PNG 4K:  {len(pngs['4k'])} lâminas")
    report["steps"].append({"png": {k: len(v) for k, v in pngs.items()}})

    # 4) PDF
    if do_pdf:
        pdf = export.build_pdf(str(out / "png-1080"), str(out / f"{content['id']}.pdf"))
        report["steps"].append({"pdf": pdf})
        print(f"[4/4] PDF: {pdf}")

    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nOK — relatório em", out / "report.json")
    return report


def main():
    ap = argparse.ArgumentParser(description="De Lucca Content Engine — pipeline de geração de carrosséis")
    ap.add_argument("--content", default=str(Path(__file__).parents[1] / "content/caminho.json"))
    ap.add_argument("--out", default="dist/caminho")
    ap.add_argument("--no-verify", action="store_true")
    ap.add_argument("--no-4k", action="store_true")
    ap.add_argument("--no-pdf", action="store_true")
    a = ap.parse_args()
    run(a.content, a.out, verify=not a.no_verify, do_4k=not a.no_4k, do_pdf=not a.no_pdf)


if __name__ == "__main__":
    main()
