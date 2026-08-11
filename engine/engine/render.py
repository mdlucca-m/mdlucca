"""render.py — transforma um modelo de conteúdo (JSON) em um carrossel HTML autossuficiente.

Sem dependências externas (apenas biblioteca padrão). O HTML gerado embute fontes
(base64) e a folha de estilo, ficando pronto para exportação (PNG/4K/PDF) e publicação.
"""
from __future__ import annotations
import json, html
from pathlib import Path

TPL = Path(__file__).resolve().parent.parent / "templates"


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def _chips(items) -> str:
    """Linha de chips (ex.: construtos integrados numa etapa)."""
    if not items:
        return ""
    return '<div class="chips-mini">' + "".join(f"<span>{esc(x)}</span>" for x in items) + "</div>"


def _cover(c: dict) -> str:
    chips = "".join(
        f'<div class="chip"><b>{esc(x["b"])}</b><span>{esc(x["s"])}</span></div>' for x in c["chips"]
    )
    title = "<br>".join(
        f'<span class="gold">{esc(t)}</span>' if i else esc(t) for i, t in enumerate(c["title"])
    )
    return f'''<section class="slide cover">
  <div class="sky"></div><div class="cover-grad"></div>
  <div class="cover-top">
    <p class="eyebrow"><span>{esc(c["eyebrow"])}</span><span class="eb-rule"></span></p>
    <p class="serif lead">{esc(c["lead"])}</p>
    <h1 class="display">{title}</h1>
    <p class="serif sub">{esc(c["sub"])}</p>
  </div>
  <div class="cover-bottom"><div class="chips">{chips}</div>
    <span class="pg" style="position:static;align-self:flex-start">1 / {{TOTAL}}</span></div>
</section>'''


def _funnel(f: dict) -> str:
    n = len(f["stages"])
    rows = ""
    for i, (name, spec) in enumerate(f["stages"]):
        width = 100 - i * (55 / max(1, n - 1))          # estreita a cada etapa
        col = f"var(--p{spec})"
        rows += (f'<div class="frow" style="width:{width:.0f}%;background:{col}">'
                 f'<span>{esc(name)}</span><b>{spec}</b></div>')
    return f'''<section class="slide">
  <header class="s-head"><h2 class="display sm">{esc(f["title"])}</h2>
    <p class="serif s-sub">{esc(f["sub"])}</p></header>
  <div class="funnel">{rows}</div>
  <p class="src">{esc(f.get("note", "Especificidade crescente (1→5): o foco estreita da base à competição."))}</p>
  <span class="pg">{{PG}} / {{TOTAL}}</span>
</section>'''


def _construct(s: dict) -> str:
    """Lâmina de construto (RFD, força reativa, etc.) — sem medidor de especificidade."""
    tag = f'<span class="spec-lbl" style="color:var(--{s["c"]})">{esc(s["tag"])}</span>' if s.get("tag") else ""
    return f'''<section class="slide">
  <div class="stage" style="--c:var(--{s["c"]})">
    <div class="disc"><b>{esc(s["n"])}</b></div>
    <div>
      <h3 class="st-name">{esc(s["name"])}</h3>
      <div class="kv"><b>O que é</b><span>{esc(s["goal"])}</span></div>
      <div class="kv"><b>Como treinar</b><span>{esc(s["do"])}</span></div>
      <div class="kv why"><b>Por que importa</b><span>{esc(s["why"])}</span></div>
      {tag}
      <p class="src">{esc(s["ref"])} <span class="doi">doi:{esc(s["doi"])}</span></p>
    </div>
  </div>
  <span class="pg">{{PG}} / {{TOTAL}}</span>
</section>'''


def _stage(s: dict) -> str:
    meter = "".join(f'<i class="{"on" if k < s["spec"] else ""}"></i>' for k in range(5))
    return f'''<section class="slide">
  <div class="stage" style="--c:var(--{s["c"]})">
    <div class="disc"><b>{esc(s["n"])}</b></div>
    <div>
      <h3 class="st-name">{esc(s["name"])}</h3>
      <div class="kv"><b>Objetivo</b><span>{esc(s["goal"])}</span></div>
      <div class="kv"><b>O que treinar</b><span>{esc(s["do"])}</span></div>
      <div class="kv why"><b>Por quê</b><span>{esc(s["why"])}</span></div>
      <div class="meter">{meter}</div>
      <span class="spec-lbl">Especificidade {s["spec"]}/5</span>
      {_chips(s.get("constructs"))}
      <p class="src">{esc(s["ref"])} <span class="doi">doi:{esc(s["doi"])}</span></p>
    </div>
  </div>
  <span class="pg">{{PG}} / {{TOTAL}}</span>
</section>'''


def _periodization(p: dict) -> str:
    models = "".join(
        f'''<div class="model" style="--c:var(--{m["c"]})">
        <span class="m-tag">{esc(m["tag"])}</span>
        <p class="m-def">{esc(m["def"])}</p>
        <p class="m-best">Melhor para: <b>{esc(m["best"])}</b></p></div>''' for m in p["models"]
    )
    return f'''<section class="slide">
  <header class="s-head"><h2 class="display sm">{esc(p["title"])}</h2>
    <p class="serif s-sub">{esc(p["sub"])}</p></header>
  <div class="rule"></div>
  <div class="models">{models}</div>
  <p class="src">{esc(p["note"])} — {esc(p["ref"])} <span class="doi">doi:{esc(p["doi"])}</span></p>
  <span class="pg">{{PG}} / {{TOTAL}}</span>
</section>'''


def _refs(d: dict, verified: dict | None) -> str:
    items = ""
    for r in d["refs"]:
        ok = ""
        if verified is not None:
            st = verified.get(r["doi"])
            ok = ' <span class="ok">✓ DOI</span>' if st else ' <span class="doi">(não verificado)</span>'
        items += (f'<li><b>{esc(r["who"])}</b> · {esc(r["src"])} — {esc(r["note"])} '
                  f'<span class="doi">{esc(r["doi"])}</span>{ok}</li>')
    a = d["author"]
    return f'''<section class="slide">
  <header class="s-head"><h2 class="display sm"><span class="gold">●</span> Base científica</h2>
    <p class="serif s-sub">referências verificadas — DOI conferido.</p></header>
  <div class="rule"></div>
  <ul class="reflist">{items}</ul>
  <p class="closing">A base é invisível — mas é ela que sustenta a especificidade.</p>
  <footer class="author"><div><p class="name">{esc(a["name"])}</p><p class="role">{esc(a["role"])}</p></div>
    <span class="wordmark">{esc(a["wordmark"])}</span></footer>
  <span class="pg">{{PG}} / {{TOTAL}}</span>
</section>'''


def build_html(content: dict, verified: dict | None = None) -> str:
    """Monta o HTML completo do carrossel a partir do modelo de conteúdo."""
    slides = [_cover(content["cover"])]
    if content.get("funnel"):
        slides.append(_funnel(content["funnel"]))
    stage_renderer = _construct if content.get("stage_type") == "construct" else _stage
    slides += [stage_renderer(s) for s in content["stages"]]
    if content.get("periodization"):
        slides.append(_periodization(content["periodization"]))
    slides.append(_refs(content, verified))

    total = len(slides)
    out = []
    for i, s in enumerate(slides):
        out.append(s.replace("{TOTAL}", str(total)).replace("{PG}", str(i + 1)))
    body = "\n".join(out)

    fontface = (TPL / "fontface.css").read_text(encoding="utf-8")
    base = (TPL / "base.css").read_text(encoding="utf-8")
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(content["title"])} — De Lucca</title>
<style>{fontface}
{base}</style></head><body><main class="deck">
{body}
</main></body></html>'''


def render_file(content_path: str, out_path: str, verified: dict | None = None) -> str:
    content = json.loads(Path(content_path).read_text(encoding="utf-8"))
    htmlout = build_html(content, verified)
    Path(out_path).write_text(htmlout, encoding="utf-8")
    return out_path


if __name__ == "__main__":
    import sys
    cp = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parent.parent / "content/caminho.json")
    op = sys.argv[2] if len(sys.argv) > 2 else "dist/caminho.html"
    Path(op).parent.mkdir(parents=True, exist_ok=True)
    print("HTML ->", render_file(cp, op))
