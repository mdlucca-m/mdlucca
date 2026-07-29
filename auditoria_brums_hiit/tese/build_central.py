import base64, os
def img(k):
    with open(f'/tmp/hubimg/{k}.jpg','rb') as f:
        return 'data:image/jpeg;base64,'+base64.b64encode(f.read()).decode()

ANALYST='https://claude.ai/code/artifact/9279ee5b-358f-49c5-8fad-3c05571079fb'
PR='https://github.com/mdlucca-m/mdlucca/pull/1'
GH='https://github.com/mdlucca-m/mdlucca/blob/claude/auditoria-analises-blz1fn/auditoria_brums_hiit/'

CSS = """
*{box-sizing:border-box}
:root{
 --bg:#0c1320; --bg2:#0f1a2c; --panel:#15233c; --panel2:#1b2c49; --line:#263a5c;
 --ink:#eef2fa; --mut:#9fb0ca; --faint:#6a7c9c;
 --teal:#2fd0c0; --coral:#ff8080; --gold:#f2bd52; --blue:#54a8e6; --violet:#b394ff;
 --serif:Georgia,'Iowan Old Style','Palatino Linotype','Times New Roman',serif;
 --sans:system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
 --mono:ui-monospace,'SF Mono',Menlo,Consolas,monospace;
 --maxw:1120px;
}
@media (prefers-color-scheme:light){:root{
 --bg:#f4f7fc; --bg2:#eef3fa; --panel:#ffffff; --panel2:#f5f8fd; --line:#dde5f1;
 --ink:#12233d; --mut:#4a5a76; --faint:#8091ab;
 --teal:#0e9c90; --coral:#d65252; --gold:#b7841c; --blue:#2f7bc0; --violet:#6b4bd0;
}}
:root[data-theme="dark"]{
 --bg:#0c1320; --bg2:#0f1a2c; --panel:#15233c; --panel2:#1b2c49; --line:#263a5c;
 --ink:#eef2fa; --mut:#9fb0ca; --faint:#6a7c9c;
 --teal:#2fd0c0; --coral:#ff8080; --gold:#f2bd52; --blue:#54a8e6; --violet:#b394ff;
}
:root[data-theme="light"]{
 --bg:#f4f7fc; --bg2:#eef3fa; --panel:#ffffff; --panel2:#f5f8fd; --line:#dde5f1;
 --ink:#12233d; --mut:#4a5a76; --faint:#8091ab;
 --teal:#0e9c90; --coral:#d65252; --gold:#b7841c; --blue:#2f7bc0; --violet:#6b4bd0;
}
html,body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 22px}
.eyebrow{font-family:var(--mono);font-size:11.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--teal)}
h1,h2,h3{font-family:var(--serif);font-weight:600;text-wrap:balance;line-height:1.15}
a{color:inherit}
/* hero */
.hero{padding:74px 0 40px;background:radial-gradient(1100px 460px at 78% -8%,rgba(47,208,192,.13),transparent 60%),linear-gradient(180deg,var(--bg2),var(--bg))}
.hero h1{font-size:clamp(30px,5vw,52px);margin:14px 0 0;letter-spacing:-.01em}
.hero .accent{color:var(--teal)}
.lede{color:var(--mut);font-size:clamp(15px,2vw,18.5px);max-width:60ch;margin:18px 0 0}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin:36px 0 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:15px 14px}
.kpi b{display:block;font-family:var(--serif);font-size:26px;color:var(--ink);font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.kpi span{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint)}
@media(max-width:820px){.kpis{grid-template-columns:repeat(3,1fr)}}
@media(max-width:460px){.kpis{grid-template-columns:repeat(2,1fr)}}
/* cta band */
.cta{display:flex;flex-wrap:wrap;align-items:center;gap:18px;justify-content:space-between;margin:34px 0 0;background:linear-gradient(120deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:16px;padding:22px 24px}
.cta .txt{min-width:260px;flex:1}
.cta h3{margin:0 0 4px;font-size:20px}
.cta p{margin:0;color:var(--mut);font-size:13.5px}
.btn{display:inline-flex;align-items:center;gap:9px;background:var(--teal);color:#062018;font-weight:700;font-family:var(--sans);text-decoration:none;padding:13px 20px;border-radius:11px;font-size:14.5px;white-space:nowrap;border:1px solid transparent;transition:transform .12s ease,box-shadow .12s ease}
.btn:hover{transform:translateY(-1px);box-shadow:0 10px 26px -12px rgba(47,208,192,.7)}
.btn.ghost{background:transparent;color:var(--ink);border-color:var(--line);font-weight:600}
.btn:focus-visible{outline:2px solid var(--gold);outline-offset:3px}
/* sections */
section{padding:52px 0}
.seclab{font-family:var(--mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--faint)}
section h2{font-size:clamp(22px,3vw,30px);margin:8px 0 4px}
.sub{color:var(--mut);max-width:64ch;margin:0 0 26px}
/* findings */
.finds{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}
@media(max-width:760px){.finds{grid-template-columns:1fr}}
.find{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px 20px 18px;position:relative}
.find .n{font-family:var(--mono);font-size:12px;color:var(--faint)}
.find h3{font-size:17.5px;margin:6px 0 7px;font-family:var(--sans);font-weight:700}
.find p{margin:0;color:var(--mut);font-size:14px}
.find .tag{font-family:var(--mono);font-size:10.5px;letter-spacing:.05em;padding:3px 8px;border-radius:999px;margin-top:12px;display:inline-block}
.t-teal{background:rgba(47,208,192,.14);color:var(--teal)} .t-coral{background:rgba(255,128,128,.14);color:var(--coral)}
.t-gold{background:rgba(242,189,82,.16);color:var(--gold)} .t-blue{background:rgba(84,168,230,.15);color:var(--blue)}
.t-violet{background:rgba(179,148,255,.16);color:var(--violet)}
/* figures */
figure{margin:0 0 26px;background:var(--panel);border:1px solid var(--line);border-radius:16px;overflow:hidden}
figure img{display:block;width:100%;height:auto}
figcaption{padding:13px 18px;color:var(--mut);font-size:13px;border-top:1px solid var(--line)}
figcaption b{color:var(--ink);font-weight:700}
.figrow{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:760px){.figrow{grid-template-columns:1fr}}
/* deliverables */
.cats{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}
@media(max-width:760px){.cats{grid-template-columns:1fr}}
.cat{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px 20px 8px}
.cat h3{font-family:var(--sans);font-size:15px;font-weight:700;margin:0 0 4px;display:flex;align-items:center;gap:9px}
.cat h3 .dot{width:9px;height:9px;border-radius:3px;flex:none}
.cat>p{color:var(--faint);font-size:12.5px;margin:0 0 12px}
.file{display:flex;align-items:baseline;gap:10px;padding:10px 0;border-top:1px solid var(--line);text-decoration:none}
.file:hover .fn{color:var(--teal)}
.file .fn{font-size:14px;font-weight:600}
.file .fd{color:var(--mut);font-size:12.5px}
.file .ext{font-family:var(--mono);font-size:10px;color:var(--faint);border:1px solid var(--line);padding:2px 6px;border-radius:6px;margin-left:auto;white-space:nowrap}
/* footer */
footer{border-top:1px solid var(--line);padding:34px 0 60px;color:var(--faint);font-size:13px}
footer a{color:var(--mut)}
.note{background:var(--panel2);border:1px solid var(--line);border-left:3px solid var(--gold);border-radius:10px;padding:14px 18px;color:var(--mut);font-size:13.5px;margin-top:22px}
"""

def find(n, title, body, tag, tclass):
    return f'<div class="find"><div class="n">Achado {n}</div><h3>{title}</h3><p>{body}</p><span class="tag {tclass}">{tag}</span></div>'

def file(href, fn, fd, ext):
    return f'<a class="file" href="{href}" target="_blank" rel="noopener"><span><span class="fn">{fn}</span> <span class="fd">— {fd}</span></span><span class="ext">{ext}</span></a>'

html = f"""<style>{CSS}</style>
<div class="hero"><div class="wrap">
 <div class="eyebrow">Estudo · Humor &amp; carga interna · Handebol</div>
 <h1>BRUMS <span class="accent">×</span> HIIT: como o humor responde a um microciclo de alta intensidade — e o quão bem conseguimos medi&#8209;lo</h1>
 <p class="lede">27 atletas, 7 dias, três sessões de HIIT. Auditoria independente das análises, manuscrito padrão&#8209;ouro, sistema analista interativo e um pipeline que reprocessa tudo a cada nova coleta. Esta é a central para ver tudo em um só lugar.</p>
 <div class="kpis">
  <div class="kpi"><b>27</b><span>atletas</span></div>
  <div class="kpi"><b>456</b><span>observações</span></div>
  <div class="kpi"><b>135</b><span>pares pré/pós</span></div>
  <div class="kpi"><b>77<span style="color:var(--faint)">/84</span></b><span>checagens exatas</span></div>
  <div class="kpi"><b>3</b><span>sessões HIIT</span></div>
  <div class="kpi"><b>~183</b><span>FC pico (bpm)</span></div>
 </div>
 <div class="cta">
  <div class="txt"><h3>Sistema Analista — ao vivo</h3><p>Explore os dados com filtros que recalculam tudo: descritiva, inferência, segmentação e carga interna (FC/PSE).</p></div>
  <a class="btn" href="{ANALYST}" target="_blank" rel="noopener">Abrir o sistema interativo →</a>
 </div>
</div></div>

<div class="wrap">

<section>
 <div class="seclab">O que o estudo mostrou</div>
 <h2>Cinco achados</h2>
 <p class="sub">Todos reconciliados com a reanálise estatística (modelo misto, correção de pseudorreplicação por atleta e FDR).</p>
 <div class="finds">
  {find(1,'A medida é heterogênea','A fadiga física é a variável mais confiável e sem efeito piso; já confusão (80% no piso) e depressão (67%) têm variância pequena demais para detectar mudança. Medir bem vem antes de concluir.','qualidade da medida','t-blue')}
  {find(2,'A resposta mora no eixo energia–fadiga','No agudo, o HIIT eleva a fadiga física (dz = 0,76) e reduz o vigor. Três variáveis desse eixo sobrevivem à correção por pseudorreplicação e ao FDR — o resto é ruído ou piso.','resposta aguda','t-coral')}
  {find(3,'O microciclo acumula carga','Há efeito do dia real (modelo misto): o "perfil iceberg" cai de 71% no Dia 1 para 33% no Dia 7. A perturbação total cresce ~0,53 ponto/dia ao longo da semana.','efeito do dia','t-gold')}
  {find(4,'Carga alta ≠ humor pior','As sessões foram quase-máximas (FC de pico 184/183/181 bpm; PSE final 9,3–9,6), mas a magnitude da carga não prediz a perturbação aguda do humor (r ≈ −0,05). O custo fisiológico e a resposta psicológica se desacoplam no agudo.','carga interna','t-teal')}
  {find(5,'A resposta é individual','A tipologia separa 20 atletas resilientes, 6 perturbados e 1 extremo. A média esconde perfis opostos — daí o drill-down por atleta no sistema analista.','segmentação','t-violet')}
 </div>
</section>

<section>
 <div class="seclab">O desenho e a arquitetura analítica</div>
 <h2>Como o estudo foi montado</h2>
 <p class="sub">Do dado bruto à decisão de modelagem, com a etapa de correção da pseudorreplicação em destaque.</p>
 <figure><img src="{img('master')}" alt="Figura-mestre do desenho do estudo"><figcaption><b>Desenho do estudo.</b> Microciclo de 7 dias, coletas pré/pós, três sessões de HIIT (dias 2, 4 e 7) e as medidas de humor (BRUMS) e de carga interna (FC/PSE).</figcaption></figure>
 <div class="figrow">
  <figure><img src="{img('framework')}" alt="Framework analítico hierárquico"><figcaption><b>Framework analítico.</b> Encadeamento hierárquico: medida → resposta → modelagem robusta.</figcaption></figure>
  <figure><img src="{img('analog')}" alt="Analogia fitness-fadiga"><figcaption><b>Modelo fitness–fadiga.</b> Leitura analógica do balanço entre frescor (vigor) e custo (fadiga).</figcaption></figure>
 </div>
</section>

<section>
 <div class="seclab">Evidência visual</div>
 <h2>Os gráficos-chave</h2>
 <p class="sub">Amostras da análise; a versão interativa e filtrável está no sistema analista.</p>
 <div class="figrow">
  <figure><img src="{img('spaghetti')}" alt="Trajetórias de PTH por atleta"><figcaption><b>Heterogeneidade.</b> Trajetória do PTH por atleta ao longo da semana (média destacada).</figcaption></figure>
  <figure><img src="{img('weekly')}" alt="Mudança semanal"><figcaption><b>Acúmulo semanal.</b> Mudança D1→D7 com intervalos de confiança por bootstrap.</figcaption></figure>
  <figure><img src="{img('cluster')}" alt="Tipologia de atletas"><figcaption><b>Tipologia.</b> Perfis médios (z) dos grupos resiliente / perturbado / extremo.</figcaption></figure>
  <figure><img src="{img('network')}" alt="Rede de subescalas"><figcaption><b>Rede.</b> Centralidade das subescalas por correlação parcial.</figcaption></figure>
 </div>
</section>

<section>
 <div class="seclab">Reproduzível com um comando</div>
 <h2>Pipeline automatizado (estilo N8N)</h2>
 <p class="sub">Dezesseis nós encadeados levam da coleta bruta às tabelas, gráficos, Excel, PDF, relatório e à regeneração do próprio sistema analista. Um gatilho Cron reprocessa tudo a cada nova coleta.</p>
 <figure><img src="{img('workflow')}" alt="Diagrama do pipeline N8N"><figcaption><b>Fluxo.</b> Início/Cron → ingestão → análises → carga interna → gráficos → Excel/PDF/HTML → app analista → relatório.</figcaption></figure>
</section>

<section>
 <div class="seclab">Todos os entregáveis</div>
 <h2>Índice do material</h2>
 <p class="sub">Tudo vive em <span style="font-family:var(--mono);font-size:13px">auditoria_brums_hiit/</span> na branch do PR. Os links abaixo abrem cada arquivo no GitHub.</p>
 <div class="cats">
  <div class="cat">
   <h3><span class="dot" style="background:var(--blue)"></span>Manuscrito &amp; tese</h3>
   <p>Documento padrão-ouro, revisão de literatura, objetivos e figuras.</p>
   {file(GH+'ARTIGO_AUDITADO.docx','ARTIGO_AUDITADO.docx','manuscrito corrigido + Apêndice B','DOCX')}
   {file(GH+'tese/TESE_REVISADA.docx','TESE_REVISADA.docx','tese com revisão de literatura integrada','DOCX')}
   {file(GH+'RELATORIO_AUDITORIA.md','RELATORIO_AUDITORIA.md','relatório completo da auditoria','MD')}
  </div>
  <div class="cat">
   <h3><span class="dot" style="background:var(--teal)"></span>Análise interativa</h3>
   <p>Para explorar e compartilhar com os pares.</p>
   <a class="file" href="{ANALYST}" target="_blank" rel="noopener"><span><span class="fn">Sistema Analista</span> <span class="fd">— app ao vivo (6 abas)</span></span><span class="ext">LINK</span></a>
   {file(GH+'tese/Apresentacao_BRUMS_HIIT.html','Apresentação (HTML)','30 slides segmentados','HTML')}
   {file(GH+'dashboard.html','Dashboard','KPIs, achados e insights','HTML')}
  </div>
  <div class="cat">
   <h3><span class="dot" style="background:var(--gold)"></span>Apoio ao orientador</h3>
   <p>Processos e dados limpos, auditáveis.</p>
   {file(GH+'Auditoria_BRUMS_HIIT.xlsx','Auditoria_BRUMS_HIIT.xlsx','7 abas: verificação colorida + tabelas','XLSX')}
   {file(GH+'tese/Apresentacao_BRUMS_HIIT.pptx','Apresentação (PPTX)','25 slides','PPTX')}
   {file(GH+'tese/figuras','figuras/','figura-mestre, framework e gráficos','PNG')}
  </div>
  <div class="cat">
   <h3><span class="dot" style="background:var(--violet)"></span>Automação</h3>
   <p>Pipeline reproduzível e importável no N8N.</p>
   {file(GH+'pipeline/README.md','pipeline/','16 nós · um comando','DIR')}
   {file(GH+'pipeline/workflow_n8n.json','workflow_n8n.json','fluxo importável (Manual + Cron)','JSON')}
   {file(GH+'pipeline/build_appdata.py','build_appdata.py','gerador canônico dos dados','PY')}
  </div>
 </div>
 <div class="note"><b>Privacidade.</b> As bases originais não são versionadas (dados identificáveis); todas as saídas usam atletas anonimizados (A01–A27). Restam para replicação em R (lavaan/mirt/semTools): CFA/WLSMV, TRI/GRM, HTMT policórico e o BF bayesiano exato — internamente consistentes e marcados no Apêndice B.</div>
</section>

</div>
<footer><div class="wrap">
 Central do estudo BRUMS × HIIT no handebol · reprodução independente e material de publicação.<br>
 <a href="{PR}" target="_blank" rel="noopener">Pull request #1 no GitHub →</a> &nbsp;·&nbsp; atletas anonimizados · elaboração do autor · 2026.
</div></footer>
"""
open('/tmp/hub.html','w').write(html)
print('hub.html:', os.path.getsize('/tmp/hub.html')//1024,'KB')
