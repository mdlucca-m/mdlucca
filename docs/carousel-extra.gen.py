# -*- coding: utf-8 -*-
import os, subprocess

OUT = "/home/user/mdlucca/docs"
SCR = "/tmp/claude-0/-home-user-mdlucca/13041629-7f48-5aad-b301-dadbbfdb4546/scratchpad"
CHROME = "/opt/pw-browsers/chromium"

TOKENS = r"""
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
  a{color:inherit;}
  .eyebrow .dot{color:var(--faint);}
  .eyebrow.clay{color:var(--clay);}
  h1 em{font-style:italic; color:var(--emerald);}
  h2 em{font-style:italic; color:var(--emerald);}
  h2 .clayw{color:var(--clay); font-style:italic;}
  .sub b{color:var(--clay); font-style:italic;}
  .sub .em{color:var(--emerald); font-style:italic;}
  .lead .m{color:var(--muted);} .lead .em{color:var(--emerald); font-weight:700;} .lead .clay{color:var(--clay); font-weight:700;}
  .arg .hl{color:var(--emerald); font-style:italic;} .arg .clayw{color:var(--clay); font-style:italic;}
"""

# ---------------- SQUARE 1080x1080 CSS ----------------
SQ = r"""
<style>
%TOKENS%
  html,body{width:1080px;height:1080px;overflow:hidden;}
  body{background:radial-gradient(120% 80% at 82% -10%, #1a2a22 0%, rgba(26,42,34,0) 55%),linear-gradient(160deg,var(--bg2) 0%, var(--bg) 62%);color:var(--ink);font-family:var(--sans);position:relative;overflow:hidden;}
  .pitch{position:absolute;inset:0;pointer-events:none;opacity:.5;}
  .frame{position:absolute;top:28px;left:28px;right:28px;bottom:28px;border:1.5px solid var(--line2);border-radius:22px;}
  .stage{position:absolute;top:28px;left:28px;right:28px;bottom:28px;}
  .content{position:absolute;top:44px;left:52px;right:52px;bottom:98px;display:flex;flex-direction:column;justify-content:center;gap:20px;}
  .eyebrow{font-family:var(--mono);font-size:15px;letter-spacing:.18em;text-transform:uppercase;color:var(--emerald);}
  h1{font-family:var(--serif);font-weight:700;font-size:74px;line-height:.96;letter-spacing:-.015em;color:var(--ink);}
  h2{font-family:var(--serif);font-weight:700;font-size:47px;line-height:1.03;letter-spacing:-.012em;color:var(--ink);}
  .mt14{margin-top:14px;} .mt16{margin-top:16px;} .mt18{margin-top:18px;} .mt22{margin-top:22px;}
  .sub{font-family:var(--serif);font-size:23px;line-height:1.32;color:var(--muted);max-width:33ch;}
  .lead{font-size:20px;line-height:1.4;color:var(--ink);}
  .trio{display:flex;gap:13px;}
  .stat{flex:1;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 17px;}
  .stat .n{font-family:var(--serif);font-weight:700;font-size:40px;line-height:1;color:var(--emerald);font-variant-numeric:tabular-nums;}
  .stat .n small{font-size:.42em;color:var(--muted);font-weight:400;}
  .stat .l{margin-top:9px;font-size:14px;line-height:1.32;color:var(--muted);}
  .chart{display:flex;flex-direction:column;}
  .crow{display:grid;grid-template-columns:1fr auto;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--line);}
  .crow:first-child{border-top:1px solid var(--line);}
  .crow .nm{font-size:19px;color:var(--ink);}
  .crow .nm small{display:block;font-family:var(--mono);font-size:12px;color:var(--faint);letter-spacing:.03em;margin-top:2px;text-transform:uppercase;}
  .crow .track{grid-column:1 / -1;position:relative;height:10px;background:#1d2822;border-radius:99px;overflow:hidden;margin-top:3px;}
  .crow .fill{position:absolute;inset:0 auto 0 0;border-radius:99px;background:linear-gradient(90deg,var(--emerald),#2f9a86);}
  .crow .v{font-family:var(--mono);font-size:20px;font-weight:700;color:var(--emerald);font-variant-numeric:tabular-nums;white-space:nowrap;}
  .grp{margin-top:16px;}
  .grp .gl{font-family:var(--mono);font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--clay);margin-bottom:6px;}
  .rows{border-top:1px solid var(--line);}
  .row{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:8px 2px;border-bottom:1px solid var(--line);}
  .row .sport{font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);}
  .row .param{font-size:20px;color:var(--ink);margin-top:1px;font-weight:600;}
  .row .d{font-family:var(--mono);font-size:22px;font-weight:700;color:var(--emerald);white-space:nowrap;font-variant-numeric:tabular-nums;}
  .scards{display:flex;flex-direction:column;gap:10px;}
  .sc{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 17px;display:flex;align-items:center;justify-content:space-between;gap:16px;}
  .sc.flag{border-color:rgba(233,146,79,.5);background:linear-gradient(90deg,rgba(233,146,79,.12),rgba(233,146,79,0));}
  .sc .k{font-size:17px;color:var(--muted);max-width:26ch;} .sc .k b{color:var(--ink);}
  .sc .val{font-family:var(--mono);font-size:20px;font-weight:700;text-align:right;white-space:nowrap;}
  .sc .val .ref{color:var(--faint);font-weight:400;font-size:.8em;} .sc .val.alt{color:var(--emerald);} .sc.flag .val{color:var(--clay);}
  .arg{font-family:var(--serif);font-size:25px;line-height:1.28;color:var(--ink);}
  .honest{margin-top:12px;font-family:var(--mono);font-size:13px;line-height:1.48;color:var(--faint);}
  .honest b{color:var(--muted);}
  .srcline{margin-top:8px;padding-top:14px;border-top:1px solid var(--line);display:flex;align-items:flex-end;justify-content:space-between;gap:18px;}
  .srcline .src{font-family:var(--mono);font-size:12.5px;line-height:1.45;color:#8b968c;max-width:66ch;} .srcline .src i{color:var(--muted);font-style:italic;}
  .srcline .pg{font-family:var(--mono);font-size:13px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);white-space:nowrap;} .srcline .pg b{color:var(--emerald);}
  .swipe{font-family:var(--mono);font-size:15px;letter-spacing:.13em;text-transform:uppercase;color:var(--clay);}
  .kick-row{display:flex;align-items:center;gap:12px;font-family:var(--mono);font-size:17px;color:var(--muted);}
  .kick-row .big{font-family:var(--serif);font-size:34px;color:var(--emerald);font-weight:700;}
  .kick-row .bigc{font-family:var(--serif);font-size:34px;color:var(--clay);font-weight:700;}
</style>
""".replace("%TOKENS%", TOKENS)

def pitch(w, h):
    return f"""<svg class="pitch" viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true">
  <circle cx="{w-70}" cy="{int(h*0.11)}" r="{int(h*0.18)}" fill="none" stroke="#2b3a30" stroke-width="1.5"/>
  <circle cx="70" cy="{int(h*0.9)}" r="{int(h*0.22)}" fill="none" stroke="#2b3a30" stroke-width="1.5"/>
  <line x1="{w//2}" y1="{int(h*0.09)}" x2="{w//2}" y2="{h-20}" stroke="#1f2c26" stroke-width="1.2"/>
</svg>
<div class="frame"></div>"""

def srcline(src, num):
    return f'<div class="srcline"><span class="src">{src}</span><span class="pg"><b>{num}</b> / 04</span></div>'

# ---- shared content blocks (same copy as the portrait carousel) ----
C1_top = '<div><div class="eyebrow">Dossiê <span class="dot">·</span> Ciência do esporte &amp; gênero</div><h1 class="mt18">A regra<br />não é <em>neutra</em>.</h1></div>'
C1_mid = '<div><p class="sub">Por que quase todo esporte muda as medidas para as mulheres — e por que <b>o futebol é a exceção.</b></p><div class="kick-row mt22"><span class="big">5</span> adaptam a régua <span style="color:var(--faint)">·</span> <span class="bigc">1</span> se recusa</div></div>'
C1_foot = '<div class="srcline"><span class="src swipe" style="color:var(--clay)">arraste para os dados →</span><span class="pg"><b>01</b> / 04</span></div>'

C2_top = '<div><div class="eyebrow">Dado 01 <span class="dot">·</span> A diferença física</div><h2 class="mt16">Não nasce.<br />Aparece na <em>puberdade</em>.</h2></div>'
C2_mid = ('<div><p class="lead"><span class="m">Antes dos 12 anos, meninos e meninas rendem quase igual (~5%). Na puberdade masculina, a testosterona fica</span> <span class="em">15× maior</span><span class="m">.</span></p>'
  '<div class="trio mt18">'
  '<div class="stat"><div class="n">+12<small>&nbsp;kg</small></div><div class="l">de músculo, no mesmo peso</div></div>'
  '<div class="stat"><div class="n">15×</div><div class="l">testosterona vs. mulheres</div></div>'
  '<div class="stat"><div class="n">10–30<small>%</small></div><div class="l">vantagem de elite</div></div>'
  '</div>'
  '<div class="chart mt18">'
  '<div class="crow"><div class="nm">Corrida / Natação <small>velocidade · livre</small></div><div class="v">~11%</div><div class="track"><div class="fill" style="width:37%"></div></div></div>'
  '<div class="crow"><div class="nm">Saltos <small>vertical · distância</small></div><div class="v">~19–23%</div><div class="track"><div class="fill" style="width:63%"></div></div></div>'
  '<div class="crow"><div class="nm">Potência / arremesso <small>membros superiores</small></div><div class="v">~25–30%</div><div class="track"><div class="fill" style="width:83%"></div></div></div>'
  '</div></div>')
C2_foot = srcline('Handelsman (2018) · Consensus Statement <i>ACSM</i> (2023).', '02')

C3_top = '<div><div class="eyebrow">Dado 02 <span class="dot">·</span> As adaptações</div><h2 class="mt16">Mesma lógica,<br /><em>três famílias</em>.</h2></div>'
C3_mid = ('<div>'
  '<div class="grp"><div class="gl">Mão menor → bola menor</div><div class="rows">'
  '<div class="row"><div><div class="sport">Basquete</div><div class="param">Bola tam. 7 → tam. 6</div></div><div class="d">−40 g</div></div>'
  '<div class="row"><div><div class="sport">Handebol</div><div class="param">Bola H3 → H2</div></div><div class="d">−100 g</div></div></div></div>'
  '<div class="grp"><div class="gl">Menor alcance → obstáculo mais baixo</div><div class="rows">'
  '<div class="row"><div><div class="sport">Voleibol</div><div class="param">Rede 2,43 → 2,24 m</div></div><div class="d">−19 cm</div></div>'
  '<div class="row"><div><div class="sport">Atletismo</div><div class="param">Barreiras (400 m) 91,4 → 76,2 cm</div></div><div class="d">−15 cm</div></div></div></div>'
  '<div class="grp"><div class="gl">Menor força → implemento mais leve</div><div class="rows">'
  '<div class="row"><div><div class="sport">Atletismo</div><div class="param">Peso 7,26 → 4,00 kg</div></div><div class="d">−45%</div></div>'
  '<div class="row"><div><div class="sport">Atletismo</div><div class="param">Dardo 800 → 600 g</div></div><div class="d">−25%</div></div></div></div>'
  '<p class="lead mt18"><span class="m">O princípio é sempre:</span> <span class="em">preservar o gesto técnico</span><span class="m">, ajustando o parâmetro ao corpo da atleta.</span></p>'
  '</div>')
C3_foot = srcline('Regulamentos oficiais · FIVB · FIBA · IHF · World Athletics.', '03')

C4_top = '<div><div class="eyebrow clay">Dado 03 <span class="dot">·</span> O futebol</div><h2 class="mt16">A trave <span class="clayw">de&nbsp;1886</span>.</h2></div>'
C4_mid = ('<div><p class="lead"><span class="m">Gol, bola e campo idênticos aos masculinos. A goleira mede em média</span> <span class="clay">15 cm a menos</span> <span class="m">— mas defende o mesmo gol.</span></p>'
  '<div class="scards mt16">'
  '<div class="sc flag"><div class="k"><b>Gol</b> — atual vs. escala justa pela estatura</div><div class="val">7,32×2,44 <span class="ref">→</span> 6,76×2,25 m</div></div>'
  '<div class="sc"><div class="k"><b>Goleira</b> vs. goleiro (média em Copas)</div><div class="val alt">173,5 <span class="ref">vs</span> 188,9 cm</div></div>'
  '<div class="sc"><div class="k"><b>Campo justo</b> pela fisiologia (VO₂máx / força)</div><div class="val alt">66–77% da área</div></div>'
  '</div>'
  '<p class="arg mt18">Enquanto a régua for a <span class="clayw">deles</span>, o futebol feminino será cópia — <span class="hl">nunca esporte próprio.</span></p>'
  '<div class="honest"><b>Honestidade:</b> a diferença fisiológica é consenso; mudar a trave é proposta publicada, porém debatida. <span style="color:var(--clay)">A trave deveria mudar? Comente. ↓</span></div>'
  '</div>')
C4_foot = srcline('Pedersen et al. (2019) <i>Frontiers in Psychology</i> · <i>ACSM</i> (2023).', '04')

SQ_SLIDES = [
    (C1_top, C1_mid, C1_foot),
    (C2_top, C2_mid, C2_foot),
    (C3_top, C3_mid, C3_foot),
    (C4_top, C4_mid, C4_foot),
]

def render(src_path, png_path, w, h):
    subprocess.run([CHROME,"--headless=new","--no-sandbox","--disable-gpu","--hide-scrollbars",
        "--force-device-scale-factor=2",f"--window-size={w},{h}",
        f"--screenshot={png_path}",f"file://{src_path}"], stderr=subprocess.DEVNULL, check=True)

# render square slides
for i,(top,mid,ft) in enumerate(SQ_SLIDES,1):
    html = f'{SQ}{pitch(1080,1080)}<div class="stage"><div class="content">{top}{mid}{ft}</div></div>'
    sp = os.path.join(SCR,f"sq-{i}.html"); pp = os.path.join(OUT,f"feed-quadrado-{i}.png")
    open(sp,"w").write(html); render(sp,pp,1080,1080)
    print("square",i,os.path.getsize(pp))

# ---------------- STORY 1080x1920 ----------------
STORY = r"""
<style>
%TOKENS%
  html,body{width:1080px;height:1920px;overflow:hidden;}
  body{background:radial-gradient(100% 55% at 84% -4%, #1c2e25 0%, rgba(28,46,37,0) 55%),linear-gradient(165deg,var(--bg2) 0%, var(--bg) 60%);color:var(--ink);font-family:var(--sans);position:relative;overflow:hidden;}
  .pitch{position:absolute;inset:0;pointer-events:none;opacity:.5;}
  .frame{position:absolute;top:40px;left:40px;right:40px;bottom:40px;border:1.5px solid var(--line2);border-radius:30px;}
  .stage{position:absolute;top:40px;left:40px;right:40px;bottom:40px;padding:90px 74px 80px;display:grid;grid-template-rows:auto 1fr auto;}
  .stage > *{min-height:0;}
  .eyebrow{font-family:var(--mono);font-size:21px;letter-spacing:.2em;text-transform:uppercase;color:var(--emerald);}
  .eyebrow .dot{color:var(--faint);}
  h1{font-family:var(--serif);font-weight:700;font-size:118px;line-height:.94;letter-spacing:-.02em;color:var(--ink);margin-top:26px;}
  h1 em{font-style:italic;color:var(--emerald);}
  .sub{font-family:var(--serif);font-size:34px;line-height:1.34;color:var(--muted);margin-top:30px;max-width:30ch;}
  .sub b{color:var(--clay);font-style:italic;}
  .kick-row{display:flex;align-items:center;gap:16px;font-family:var(--mono);font-size:24px;color:var(--muted);margin-top:34px;}
  .kick-row .big{font-family:var(--serif);font-size:52px;color:var(--emerald);font-weight:700;}
  .kick-row .bigc{font-family:var(--serif);font-size:52px;color:var(--clay);font-weight:700;}
  .strip{margin-top:20px;align-self:center;}
  .srow{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:17px 2px;border-bottom:1px solid var(--line);}
  .srow:first-child{border-top:1px solid var(--line);}
  .srow .s{font-family:var(--mono);font-size:15px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);}
  .srow .p{font-size:25px;color:var(--ink);font-weight:600;margin-top:2px;}
  .srow .d{font-family:var(--mono);font-size:27px;font-weight:700;color:var(--emerald);white-space:nowrap;font-variant-numeric:tabular-nums;}
  .srow.fut{background:linear-gradient(90deg,rgba(233,146,79,.14),rgba(233,146,79,0));border-left:4px solid var(--clay);margin-left:-20px;padding-left:16px;}
  .srow.fut .s{color:var(--clay);} .srow.fut .d{color:var(--clay);}
  .cta{font-family:var(--mono);font-size:22px;letter-spacing:.1em;text-transform:uppercase;color:var(--clay);border:1px solid rgba(233,146,79,.5);border-radius:99px;padding:16px 30px;display:inline-block;}
  .foot{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin-top:26px;padding-top:20px;border-top:1px solid var(--line);}
  .foot .src{font-family:var(--mono);font-size:16px;line-height:1.5;color:var(--faint);} .foot .src i{color:var(--muted);font-style:italic;}
  .foot .pg{font-family:var(--mono);font-size:17px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);text-align:right;} .foot .pg b{color:var(--emerald);}
</style>
""".replace("%TOKENS%", TOKENS)

story_html = f"""{STORY}{pitch(1080,1920)}<div class="stage">
  <div>
    <div class="eyebrow">Dossiê <span class="dot">·</span> Ciência do esporte &amp; gênero</div>
    <h1>A regra<br />não é <em>neutra</em>.</h1>
    <p class="sub">Quase todo esporte reescreveu suas medidas para o corpo feminino. <b>O futebol, não.</b></p>
    <div class="kick-row"><span class="big">5</span> esportes adaptam a régua <span style="color:var(--faint)">·</span> <span class="bigc">1</span> se recusa</div>
  </div>
  <div class="strip">
    <div class="srow"><div><div class="s">Voleibol</div><div class="p">Rede 2,43 → 2,24 m</div></div><div class="d">−19 cm</div></div>
    <div class="srow"><div><div class="s">Basquete</div><div class="p">Bola tam. 7 → tam. 6</div></div><div class="d">−40 g</div></div>
    <div class="srow"><div><div class="s">Handebol</div><div class="p">Bola H3 → H2</div></div><div class="d">−100 g</div></div>
    <div class="srow"><div><div class="s">Atletismo</div><div class="p">Peso 7,26 → 4,00 kg</div></div><div class="d">−45%</div></div>
    <div class="srow"><div><div class="s">Tênis</div><div class="p">Grand Slam 5 → 3 sets</div></div><div class="d">−2 sets</div></div>
    <div class="srow fut"><div><div class="s">Futebol</div><div class="p">Gol, bola e campo</div></div><div class="d">Δ 0 · IDÊNTICO</div></div>
  </div>
  <div>
    <div class="cta">Veja o carrossel →</div>
    <div class="foot">
      <div class="src">Fisiologia: <i>ACSM</i> (2023).<br />Futebol: Pedersen et al. (2019), <i>Frontiers in Psychology</i>.</div>
      <div class="pg"><b>Dossiê</b><br />A régua é a questão</div>
    </div>
  </div>
</div>"""
sp = os.path.join(SCR,"story.html"); pp = os.path.join(OUT,"story-capa.png")
open(sp,"w").write(story_html); render(sp,pp,1080,1920)
print("story", os.path.getsize(pp))
print("done")
