# -*- coding: utf-8 -*-
import os, subprocess

OUT = "/home/user/mdlucca/docs"
SCR = "/tmp/claude-0/-home-user-mdlucca/13041629-7f48-5aad-b301-dadbbfdb4546/scratchpad"
CHROME = "/opt/pw-browsers/chromium"

CSS = r"""
<meta charset="utf-8" />
<style>
  :root{
    --bg:#0E1512; --bg2:#121B17;
    --ink:#EEF1EA; --muted:#9BA69C; --faint:#6C776D;
    --line:#243029; --line2:#2E3B32; --panel:#16211B;
    --emerald:#3ECB98; --clay:#E9924F;
    --serif:"DejaVu Serif","Liberation Serif",Georgia,serif;
    --sans:"DejaVu Sans","Liberation Sans",system-ui,sans-serif;
    --mono:"DejaVu Sans Mono",ui-monospace,monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  html{background:#0E1512;}
  html,body{width:1080px;height:1350px;overflow:hidden;}
  body{
    background:
      radial-gradient(120% 80% at 82% -8%, #1a2a22 0%, rgba(26,42,34,0) 55%),
      linear-gradient(160deg,var(--bg2) 0%, var(--bg) 62%);
    color:var(--ink); font-family:var(--sans);
    position:relative; overflow:hidden;
  }
  .pitch{position:absolute; inset:0; pointer-events:none; opacity:.5;}
  .frame{position:absolute; top:34px; left:34px; right:34px; bottom:34px; border:1.5px solid var(--line2); border-radius:26px;}
  .stage{position:absolute; top:34px; left:34px; right:34px; bottom:34px; padding:52px 66px 54px; display:flex; flex-direction:column; justify-content:space-between;}

  .eyebrow{font-family:var(--mono); font-size:18px; letter-spacing:.2em; text-transform:uppercase; color:var(--emerald);}
  .eyebrow .dot{color:var(--faint);}
  .eyebrow.clay{color:var(--clay);}

  h1{font-family:var(--serif); font-weight:700; font-size:92px; line-height:.95; letter-spacing:-.015em; color:var(--ink);}
  h1 em{font-style:italic; color:var(--emerald);}
  h2{font-family:var(--serif); font-weight:700; font-size:60px; line-height:1.02; letter-spacing:-.012em; color:var(--ink);}
  h2 em{font-style:italic; color:var(--emerald);}
  h2 .clayw{color:var(--clay); font-style:italic;}
  .mt16{margin-top:16px;} .mt20{margin-top:20px;} .mt26{margin-top:26px;} .mt34{margin-top:34px;}

  .sub{font-family:var(--serif); font-size:28px; line-height:1.32; color:var(--muted); max-width:33ch;}
  .sub b{color:var(--clay); font-style:italic;}
  .sub .em{color:var(--emerald); font-style:italic;}

  .lead{font-size:24px; line-height:1.42; color:var(--ink);}
  .lead .m{color:var(--muted);}
  .lead .em{color:var(--emerald); font-weight:700;}
  .lead .clay{color:var(--clay); font-weight:700;}

  /* stat trio */
  .trio{display:flex; gap:16px;}
  .stat{flex:1; background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:22px 22px;}
  .stat .n{font-family:var(--serif); font-weight:700; font-size:52px; line-height:1; color:var(--emerald); font-variant-numeric:tabular-nums;}
  .stat .n small{font-size:.42em; color:var(--muted); font-weight:400;}
  .stat .l{margin-top:12px; font-size:17px; line-height:1.35; color:var(--muted);}

  /* bar chart */
  .chart{display:flex; flex-direction:column; gap:0;}
  .crow{display:grid; grid-template-columns:1fr auto; align-items:center; gap:14px; padding:15px 0; border-bottom:1px solid var(--line);}
  .crow:first-child{border-top:1px solid var(--line);}
  .crow .nm{font-size:22px; color:var(--ink);}
  .crow .nm small{display:block; font-family:var(--mono); font-size:14px; color:var(--faint); letter-spacing:.03em; margin-top:2px; text-transform:uppercase;}
  .crow .track{grid-column:1 / -1; position:relative; height:12px; background:#1d2822; border-radius:99px; overflow:hidden; margin-top:4px;}
  .crow .fill{position:absolute; inset:0 auto 0 0; border-radius:99px; background:linear-gradient(90deg,var(--emerald),#2f9a86);}
  .crow .v{font-family:var(--mono); font-size:24px; font-weight:700; color:var(--emerald); font-variant-numeric:tabular-nums; white-space:nowrap;}

  /* grouped adaptation list */
  .grp{margin-top:22px;}
  .grp .gl{font-family:var(--mono); font-size:15px; letter-spacing:.13em; text-transform:uppercase; color:var(--clay); margin-bottom:8px;}
  .rows{border-top:1px solid var(--line);}
  .row{display:flex; align-items:center; justify-content:space-between; gap:20px; padding:12px 2px; border-bottom:1px solid var(--line);}
  .row .sport{font-family:var(--mono); font-size:14px; letter-spacing:.13em; text-transform:uppercase; color:var(--muted);}
  .row .param{font-size:23px; color:var(--ink); margin-top:2px; font-weight:600;}
  .row .d{font-family:var(--mono); font-size:26px; font-weight:700; color:var(--emerald); white-space:nowrap; font-variant-numeric:tabular-nums;}

  /* scaling cards (slide 4) */
  .scards{display:flex; flex-direction:column; gap:12px;}
  .sc{background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:16px 20px; display:flex; align-items:center; justify-content:space-between; gap:18px;}
  .sc.flag{border-color:rgba(233,146,79,.5); background:linear-gradient(90deg,rgba(233,146,79,.12),rgba(233,146,79,0));}
  .sc .k{font-size:20px; color:var(--muted); max-width:26ch;}
  .sc .k b{color:var(--ink);}
  .sc .val{font-family:var(--mono); font-size:23px; font-weight:700; text-align:right; white-space:nowrap;}
  .sc .val .ref{color:var(--faint); font-weight:400; font-size:.8em;}
  .sc .val.alt{color:var(--emerald);}
  .sc.flag .val{color:var(--clay);}

  .arg{font-family:var(--serif); font-size:30px; line-height:1.3; color:var(--ink);}
  .arg .hl{color:var(--emerald); font-style:italic;}
  .arg .clayw{color:var(--clay); font-style:italic;}

  .honest{margin-top:16px; font-family:var(--mono); font-size:15px; line-height:1.5; color:var(--faint); letter-spacing:.01em;}
  .honest b{color:var(--muted);}

  .cta{margin-top:14px; display:inline-block; font-family:var(--mono); font-size:17px; letter-spacing:.06em; color:var(--clay); border:1px solid rgba(233,146,79,.5); border-radius:99px; padding:10px 20px;}

  /* footer strip */
  .foot{display:flex; align-items:flex-end; justify-content:space-between; gap:20px; margin-top:20px; padding-top:16px; border-top:1px solid var(--line);}
  .foot .src{font-family:var(--mono); font-size:13.5px; line-height:1.5; color:var(--faint); letter-spacing:.005em; max-width:72ch;}
  .foot .src i{color:var(--muted); font-style:italic;}
  .foot .pg{font-family:var(--mono); font-size:15px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted); white-space:nowrap; text-align:right;}
  .foot .pg b{color:var(--emerald);}

  .swipe{font-family:var(--mono); font-size:18px; letter-spacing:.14em; text-transform:uppercase; color:var(--clay);}
  .kick-row{display:flex; align-items:center; gap:14px; font-family:var(--mono); font-size:20px; color:var(--muted);}
  .kick-row .big{font-family:var(--serif); font-size:40px; color:var(--emerald); font-weight:700;}
  .kick-row .bigc{font-family:var(--serif); font-size:40px; color:var(--clay); font-weight:700;}
</style>
"""

PITCH = r"""
<svg class="pitch" viewBox="0 0 1080 1350" preserveAspectRatio="none" aria-hidden="true">
  <circle cx="1010" cy="150" r="240" fill="none" stroke="#2b3a30" stroke-width="1.5"/>
  <circle cx="70" cy="1230" r="300" fill="none" stroke="#2b3a30" stroke-width="1.5"/>
  <line x1="540" y1="120" x2="540" y2="1316" stroke="#1f2c26" stroke-width="1.2"/>
</svg>
<div class="frame"></div>
"""

def foot(src, num):
    return f"""<div class="foot">
      <div class="src">{src}</div>
      <div class="pg"><b>{num}</b> / 04</div>
    </div>"""

def slide(top, mid, footer):
    return f"""{CSS}{PITCH}<div class="stage">
      <div>{top}</div>
      <div>{mid}</div>
      {footer}
    </div>"""

# ---------------- SLIDE 1 — Capa ----------------
s1_top = """
  <div class="eyebrow">Dossiê <span class="dot">·</span> Ciência do esporte &amp; gênero</div>
  <h1 class="mt26">A regra<br />não é <em>neutra</em>.</h1>
"""
s1_mid = """
  <p class="sub">Por que quase todo esporte muda as medidas para as mulheres — e por que <b>o futebol é a exceção.</b></p>
  <div class="kick-row mt34"><span class="big">5</span> esportes adaptam a régua <span style="color:var(--faint)">·</span> <span class="bigc">1</span> se recusa</div>
"""
s1_foot = f"""<div class="foot">
      <div class="src swipe">arraste para os dados →</div>
      <div class="pg"><b>01</b> / 04</div>
    </div>"""
S1 = slide(s1_top, s1_mid, s1_foot)

# ---------------- SLIDE 2 — A diferença física ----------------
s2_top = """
  <div class="eyebrow">Dado 01 <span class="dot">·</span> A diferença física</div>
  <h2 class="mt20">Não nasce.<br />Aparece na <em>puberdade</em>.</h2>
"""
s2_mid = """
  <p class="lead"><span class="m">Antes dos 12 anos, meninos e meninas rendem quase igual (~5%). Na puberdade masculina, a testosterona fica</span> <span class="em">15× maior</span> <span class="m">— e abre a vantagem física.</span></p>
  <div class="trio mt26">
    <div class="stat"><div class="n">+12<small>&nbsp;kg</small></div><div class="l">de músculo, no mesmo peso corporal</div></div>
    <div class="stat"><div class="n">15×</div><div class="l">testosterona vs. mulheres, após a puberdade</div></div>
    <div class="stat"><div class="n">10–30<small>%</small></div><div class="l">vantagem de elite, conforme o gesto</div></div>
  </div>
  <div class="chart mt26">
    <div class="crow"><div class="nm">Corrida / Natação <small>velocidade · livre</small></div><div class="v">~11%</div><div class="track"><div class="fill" style="width:37%"></div></div></div>
    <div class="crow"><div class="nm">Saltos <small>vertical · distância</small></div><div class="v">~19–23%</div><div class="track"><div class="fill" style="width:63%"></div></div></div>
    <div class="crow"><div class="nm">Potência / arremesso <small>membros superiores</small></div><div class="v">~25–30%</div><div class="track"><div class="fill" style="width:83%"></div></div></div>
  </div>
"""
s2_foot = foot('Handelsman (2018) · Consensus Statement <i>ACSM</i> (2023) · Atkinson (2024).', '02')
S2 = slide(s2_top, s2_mid, s2_foot)

# ---------------- SLIDE 3 — As adaptações ----------------
s3_top = """
  <div class="eyebrow">Dado 02 <span class="dot">·</span> As adaptações</div>
  <h2 class="mt20">Mesma lógica,<br /><em>três famílias</em>.</h2>
"""
s3_mid = """
  <div class="grp">
    <div class="gl">Mão menor → bola menor</div>
    <div class="rows">
      <div class="row"><div><div class="sport">Basquete</div><div class="param">Bola tam. 7 → tam. 6</div></div><div class="d">−40 g</div></div>
      <div class="row"><div><div class="sport">Handebol</div><div class="param">Bola H3 → H2</div></div><div class="d">−100 g</div></div>
    </div>
  </div>
  <div class="grp">
    <div class="gl">Menor alcance → obstáculo mais baixo</div>
    <div class="rows">
      <div class="row"><div><div class="sport">Voleibol</div><div class="param">Rede 2,43 → 2,24 m</div></div><div class="d">−19 cm</div></div>
      <div class="row"><div><div class="sport">Atletismo</div><div class="param">Barreiras (400 m) 91,4 → 76,2 cm</div></div><div class="d">−15 cm</div></div>
    </div>
  </div>
  <div class="grp">
    <div class="gl">Menor força → implemento mais leve</div>
    <div class="rows">
      <div class="row"><div><div class="sport">Atletismo</div><div class="param">Peso 7,26 → 4,00 kg</div></div><div class="d">−45%</div></div>
      <div class="row"><div><div class="sport">Atletismo</div><div class="param">Dardo 800 → 600 g</div></div><div class="d">−25%</div></div>
    </div>
  </div>
  <p class="lead mt26"><span class="m">O princípio é sempre o mesmo:</span> <span class="em">preservar o gesto técnico</span><span class="m">, ajustando o parâmetro físico ao corpo da atleta.</span></p>
"""
s3_foot = foot('Regulamentos oficiais · FIVB · FIBA · IHF · World Athletics.', '03')
S3 = slide(s3_top, s3_mid, s3_foot)

# ---------------- SLIDE 4 — O outlier futebol ----------------
s4_top = """
  <div class="eyebrow clay">Dado 03 <span class="dot">·</span> O futebol</div>
  <h2 class="mt20">A trave <span class="clayw">de&nbsp;1886</span>.</h2>
"""
s4_mid = """
  <p class="lead"><span class="m">Gol, bola e campo idênticos aos masculinos. A goleira mede em média</span> <span class="clay">15 cm a menos</span> <span class="m">— mas defende o mesmo gol gigante.</span></p>
  <div class="scards mt20">
    <div class="sc flag"><div class="k"><b>Gol</b> — regra atual vs. escala justa pela estatura</div><div class="val">7,32×2,44 <span class="ref">→</span> 6,76×2,25 m</div></div>
    <div class="sc"><div class="k"><b>Goleira</b> vs. goleiro (média em Copas)</div><div class="val alt">173,5 <span class="ref">vs</span> 188,9 cm</div></div>
    <div class="sc"><div class="k"><b>Campo justo</b> pela fisiologia (VO₂máx / força)</div><div class="val alt">66–77% da área</div></div>
  </div>
  <p class="arg mt26">Enquanto a régua for a <span class="clayw">deles</span>, o futebol feminino será cópia — <span class="hl">nunca esporte próprio.</span></p>
  <div class="honest"><b>Honestidade:</b> a diferença fisiológica é consenso científico; mudar a trave é proposta publicada, porém debatida. <span style="color:var(--clay)">A trave deveria mudar? Comente. ↓</span></div>
"""
s4_foot = foot('Pedersen et al. (2019) <i>Frontiers in Psychology</i> · <i>ACSM</i> (2023).', '04')
S4 = slide(s4_top, s4_mid, s4_foot)

slides = [S1, S2, S3, S4]
for i, html in enumerate(slides, 1):
    src = os.path.join(SCR, f"carousel-{i}.html")
    png = os.path.join(OUT, f"carousel-{i}.png")
    with open(src, "w") as f:
        f.write(html)
    subprocess.run([
        CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=2", "--window-size=1080,1350",
        f"--screenshot={png}", f"file://{src}"
    ], stderr=subprocess.DEVNULL, check=True)
    print(f"slide {i}: {os.path.getsize(png)} bytes -> {png}")

print("done")
