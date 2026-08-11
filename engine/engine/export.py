"""export.py — renderiza as lâminas do HTML para PNG (1080 e 4K) e monta um PDF.

PNG: usa o exportador Node/Playwright (tools/export-4k.cjs).
PDF: usa Pillow (uma página por lâmina, largura 1080). Ambos são opcionais e
falham de forma limpa se a ferramenta não estiver instalada.
"""
from __future__ import annotations
import subprocess, os, glob
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "tools" / "export-4k.cjs"


def export_png(html_path: str, width: int, out_dir: str) -> list[str]:
    """Exporta cada .slide para PNG de ~`width`px de largura via Playwright."""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    # permite achar o playwright instalado globalmente, se for o caso
    try:
        groot = subprocess.check_output(["npm", "root", "-g"], text=True).strip()
        env["NODE_PATH"] = groot
    except Exception:
        pass
    subprocess.run(["node", str(TOOL), html_path, str(width), out_dir], check=True, env=env)
    return sorted(glob.glob(str(Path(out_dir) / "slide-*.png")))


def build_pdf(png_dir: str, pdf_path: str) -> str | None:
    """Monta um PDF (uma lâmina por página) a partir dos PNGs. Requer Pillow."""
    try:
        from PIL import Image
    except Exception:
        print("Pillow ausente — PDF ignorado (pip install pillow).")
        return None
    files = sorted(glob.glob(str(Path(png_dir) / "slide-*.png")))
    if not files:
        return None
    pages = []
    for f in files:
        im = Image.open(f).convert("RGB")
        w = 1080
        pages.append(im.resize((w, round(im.height * w / im.width))))
    Path(pdf_path).parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(pdf_path, save_all=True, append_images=pages[1:], resolution=150.0)
    return pdf_path
