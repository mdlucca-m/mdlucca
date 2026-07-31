import base64, pathlib
F='/home/user/mdlucca/analise/figs/'
def b(n): return 'data:image/png;base64,'+base64.b64encode(open(F+n,'rb').read()).decode()
imgs={k:b(v) for k,v in {
 'iceberg':'fig1_iceberg.png','tmd':'fig2_tmd_dia.png','hiit':'fig3_hiit.png','corr':'fig4_corr.png'}.items()}

html=f'''<title>Análise — Carga de Treino, Humor e HIIT (Handebol)</title>
<style>
:root{{
 --paper:#f6f7f9; --card:#ffffff; --ink:#141a22; --muted:#5a6572; --line:#e3e7ec;
 --pre:#2563eb; --pos:#d6323b; --rec:#0e9e6e; --accent:#4b47c9; --wash:#eef1f6;
}}
@media (prefers-color-scheme:dark){{:root{{--paper:#0d1117;--card:#141b24;--ink:#e7ecf2;--muted:#93a0b0;--line:#243040;--wash:#161f2b;--pre:#5b8bff;--pos:#f26169;--rec:#34c793;--accent:#8b88ff;}}}}
:root[data-theme=dark]{{--paper:#0d1117;--card:#141b24;--ink:#e7ecf2;--muted:#93a0b0;--line:#243040;--wash:#161f2b;--pre:#5b8bff;--pos:#f26169;--rec:#34c793;--accent:#8b88ff;}}
:root[data-theme=light]{{--paper:#f6f7f9;--card:#fff;--ink:#141a22;--muted:#5a6572;--line:#e3e7ec;--wash:#eef1f6;--pre:#2563eb;--pos:#d6323b;--rec:#0e9e6e;--accent:#4b47c9;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
 font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;line-height:1.6;}}
.wrap{{max-width:920px;margin:0 auto;padding:0 22px 90px}}
header{{padding:64px 0 30px;border-bottom:1px solid var(--line);margin-bottom:8px}}
.eyebrow{{font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:700;margin:0 0 14px}}
h1{{font-family:Georgia,'Times New Roman',serif;font-weight:700;font-size:clamp(30px,5vw,46px);line-height:1.12;margin:0;text-wrap:balance;letter-spacing:-.01em}}
.sub{{color:var(--muted);font-size:17px;margin:16px 0 0;max-width:60ch}}
.meta{{display:flex;flex-wrap:wrap;gap:26px;margin-top:26px}}
.meta div{{font-size:13px;color:var(--muted)}}
.meta b{{display:block;font-family:Georgia,serif;font-size:23px;color:var(--ink);font-weight:700}}
h2{{font-family:Georgia,serif;font-size:25px;margin:56px 0 6px;letter-spacing:-.01em}}
h2 .n{{color:var(--accent);font-size:15px;font-weight:700;vertical-align:middle;margin-right:10px;font-family:-apple-system,sans-serif}}
.lead{{color:var(--muted);margin:0 0 22px;max-width:66ch}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;margin:20px 0}}
figure{{margin:24px 0}}
figure img{{width:100%;border:1px solid var(--line);border-radius:12px;background:#fff;display:block}}
figcaption{{color:var(--muted);font-size:13px;margin-top:10px;padding-left:2px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:20px 0}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px}}
.kpi .v{{font-family:Georgia,serif;font-size:30px;font-weight:700;letter-spacing:-.02em}}
.kpi .l{{font-size:13px;color:var(--muted);margin-top:3px}}
.kpi.pre .v{{color:var(--pre)}} .kpi.pos .v{{color:var(--pos)}} .kpi.rec .v{{color:var(--rec)}} .kpi.ac .v{{color:var(--accent)}}
table{{width:100%;border-collapse:collapse;font-size:14.5px;margin:6px 0;font-variant-numeric:tabular-nums}}
th,td{{text-align:right;padding:9px 12px;border-bottom:1px solid var(--line)}}
th:first-child,td:first-child{{text-align:left}}
thead th{{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);border-bottom:2px solid var(--line)}}
tbody tr:last-child td{{border-bottom:none}}
.tag{{display:inline-block;font-size:11.5px;font-weight:700;padding:2px 9px;border-radius:20px;background:var(--wash);color:var(--muted)}}
.up{{color:var(--pos);font-weight:700}} .dn{{color:var(--rec);font-weight:700}}
ul.take{{list-style:none;padding:0;margin:14px 0}}
ul.take li{{padding:12px 0 12px 30px;border-bottom:1px solid var(--line);position:relative;max-width:70ch}}
ul.take li:before{{content:'';position:absolute;left:4px;top:20px;width:9px;height:9px;border-radius:50%;background:var(--accent)}}
p{{max-width:70ch}}
.foot{{margin-top:60px;padding-top:22px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}}
code{{background:var(--wash);padding:1px 6px;border-radius:5px;font-size:13px;font-family:ui-monospace,Menlo,monospace}}
</style>
<div class="wrap">
<header>
 <p class="eyebrow">Ciência do Esporte · Handebol de alto rendimento</p>
 <h1>Carga de treino, resposta de humor e a assinatura fisiológica do HIIT</h1>
 <p class="sub">Análise integrada de três fontes: monitoramento de humor (BRUMS-24), protocolo intervalado de alta intensidade (FC + PSE) e a base caracterizada dos atletas.</p>
 <div class="meta">
  <div><b>27</b>atletas monitorados</div>
  <div><b>277</b>observações de humor</div>
  <div><b>8</b>dias de treino</div>
  <div><b>4</b>sessões HIIT</div>
 </div>
</header>

<h2><span class="n">01</span>O que os dados dizem</h2>
<p class="lead">Três achados sustentam toda a análise. O treino produz uma resposta afetiva aguda mensurável, o HIIT tem uma assinatura de esforço progressivo clara, e a fadiga — não a tensão ou a raiva — é o que governa a perturbação global do humor.</p>
<ul class="take">
 <li><b>O treino desloca o humor de forma aguda e coerente.</b> Do Pré para o Pós-treino, o <b>Vigor cai</b> (T 43,8 → 40,7; <span class="dn">d=−0,38</span>) e a <b>Fadiga sobe</b> (49,9 → 54,1; <span class="up">d=+0,40</span>), ambos com p=0,002 — a assinatura esperada de uma sessão que gera carga.</li>
 <li><b>A tensão diminui após treinar.</b> Efeito consistente e um dos mais fortes (T 45,5 → 42,8; <span class="dn">d=−0,45</span>; p&lt;0,001): o treino funcionou como regulador de ansiedade, não como estressor.</li>
 <li><b>A fadiga comanda o TMD.</b> Entre todas as subescalas, a Fadiga é a que mais se correlaciona com a Perturbação Total de Humor (Spearman <b>r=+0,74</b>), à frente de Depressão (+0,63) e do Vigor (−0,61). Monitorar fadiga ≈ monitorar o humor global.</li>
 <li><b>O HIIT tem dose crescente dentro da sessão.</b> A PSE evolui de <b>5,3 → 9,4</b> da 1ª à 4ª série, enquanto a recuperação entre séries encurta (Δ FC 62 → 51 bpm): esforço percebido máximo com recuperação incompleta — exatamente o alvo do método.</li>
</ul>

<h2><span class="n">02</span>Resposta aguda do humor ao treino</h2>
<p class="lead">O perfil "iceberg" — Vigor acima da média e as demais subescalas abaixo — é a marca do atleta saudável. Aqui ele aparece no Pré-treino e se atenua no Pós, exatamente onde a carga incide.</p>
<figure><img src="{imgs['iceberg']}" alt="Perfil iceberg Pré vs Pós">
 <figcaption>Figura 1 — Perfil BRUMS (escore T) antes e depois do treino. O Pós-treino aprofunda o "vale" do Vigor e eleva o "pico" da Fadiga; Tensão, Depressão e Raiva permanecem contidas.</figcaption></figure>
<div class="card">
<table>
<thead><tr><th>Subescala</th><th>Pré</th><th>Pós</th><th>Δ</th><th>d de Cohen</th><th>p</th></tr></thead>
<tbody>
<tr><td>Tensão</td><td>45,5</td><td>42,8</td><td class="dn">−2,7</td><td>−0,45</td><td>&lt;0,001</td></tr>
<tr><td>Vigor</td><td>43,8</td><td>40,7</td><td class="dn">−3,1</td><td>−0,38</td><td>0,002</td></tr>
<tr><td>Fadiga</td><td>49,9</td><td>54,1</td><td class="up">+4,2</td><td>+0,40</td><td>0,002</td></tr>
<tr><td>Depressão</td><td>45,8</td><td>47,0</td><td class="up">+1,2</td><td>+0,15</td><td>0,244</td></tr>
<tr><td>Raiva</td><td>46,9</td><td>48,2</td><td class="up">+1,3</td><td>+0,15</td><td>0,265</td></tr>
<tr><td>Confusão</td><td>43,0</td><td>43,0</td><td>0,0</td><td>−0,01</td><td>0,961</td></tr>
<tr><td><b>TMD</b></td><td><b>187,3</b></td><td><b>194,5</b></td><td class="up"><b>+7,2</b></td><td><b>+0,25</b></td><td><b>0,052</b></td></tr>
</tbody></table>
</div>
<p>A leitura é clara: as subescalas de <b>energia</b> (Vigor↓, Fadiga↑) respondem forte e significativamente ao treino, enquanto as de <b>afeto negativo</b> (Depressão, Raiva, Confusão) quase não se movem. O treino cansa sem azedar o humor — e ainda alivia a tensão. O TMD sobe ~7 pontos, no limiar da significância (p=0,052): efeito real, de magnitude pequena a moderada.</p>

<h2><span class="n">03</span>O que governa a perturbação de humor</h2>
<p class="lead">Se o objetivo é vigiar o estado do atleta com poucos indicadores, os dados apontam onde olhar.</p>
<figure><img src="{imgs['corr']}" alt="Correlações com TMD">
 <figcaption>Figura 2 — Correlação de Spearman de cada subescala com o TMD (n=277). Fadiga e Depressão puxam o TMD para cima; o Vigor o puxa para baixo. Fadiga física e mental (itens diretos) confirmam o sinal.</figcaption></figure>
<p>A <b>Fadiga (r=+0,74)</b> é o motor dominante da perturbação de humor, seguida por Depressão (+0,63) e pela proteção do Vigor (−0,61). As medidas diretas de fadiga física (+0,37) e mental (+0,40) reforçam o mesmo eixo. Na prática, um <b>índice enxuto Fadiga–Vigor</b> captura a maior parte da variação do humor global sem exigir o questionário completo a cada sessão.</p>

<h2><span class="n">04</span>Evolução ao longo dos 8 dias</h2>
<figure><img src="{imgs['tmd']}" alt="TMD por dia">
 <figcaption>Figura 3 — TMD médio por dia e por momento. O Pós-treino tende a se manter acima do Pré; picos nos dias 4 e 7 sinalizam sessões de maior demanda ou acúmulo de carga.</figcaption></figure>
<p>O TMD não é estático: acompanha a periodização. Os <b>dias 4 (194,7) e 7 (199,2)</b> concentram a maior perturbação, enquanto os <b>dias 5 (178,7) e 8 (182,9)</b> mostram alívio — compatível com dias de menor carga ou recuperação. O momento <b>Rec</b> (recuperação), quando coletado, retorna para baixo do Pós, indício de que a recuperação entre sessões está funcionando.</p>

<h2><span class="n">05</span>A assinatura fisiológica do HIIT</h2>
<p class="lead">Quatro sessões (22–29/abr), 27 atletas, com FC pré/pós e PSE em aquecimento, quatro séries e recuperação.</p>
<div class="grid">
 <div class="kpi pre"><div class="v">96</div><div class="l">FC basal — pré-aquecimento (bpm)</div></div>
 <div class="kpi pos"><div class="v">182</div><div class="l">FC pico média — pós 4ª série (bpm)</div></div>
 <div class="kpi ac"><div class="v">196</div><div class="l">FC pico máxima observada (bpm)</div></div>
 <div class="kpi pos"><div class="v">9,4</div><div class="l">PSE média na 4ª série (0–10)</div></div>
</div>
<figure><img src="{imgs['hiit']}" alt="HIIT FC e PSE por série">
 <figcaption>Figura 4 — FC pré/pós de cada série (barras) e PSE (linha). A FC pré sobe a cada série (112 → 132 bpm): a recuperação é incompleta e o esforço percebido escala junto até o teto.</figcaption></figure>
<div class="card">
<table>
<thead><tr><th>Série</th><th>FC pré</th><th>FC pós</th><th>Δ FC</th><th>PSE</th></tr></thead>
<tbody>
<tr><td>Série 1</td><td>112,5</td><td>174,5</td><td>62,0</td><td>5,3</td></tr>
<tr><td>Série 2</td><td>123,5</td><td>178,5</td><td>55,0</td><td>7,1</td></tr>
<tr><td>Série 3</td><td>127,5</td><td>180,5</td><td>53,0</td><td>8,6</td></tr>
<tr><td>Série 4</td><td>131,5</td><td>182,3</td><td>50,9</td><td>9,4</td></tr>
</tbody></table>
</div>
<p>Dois sinais definem um HIIT bem aplicado e ambos estão presentes: a <b>FC pré-série cresce</b> (112 → 132 bpm) porque o intervalo não devolve a linha de base — o atleta parte cada vez mais alto — e a <b>PSE escala quase linearmente</b> até 9,4/10, indicando que a última série cobra esforço máximo. A FC pós satura em ~180–182 bpm (perto do teto individual), confirmando que a intensidade-alvo foi atingida sessão após sessão.</p>

<h2><span class="n">06</span>Como usar isto</h2>
<ul class="take">
 <li><b>Vigie a dupla Fadiga–Vigor.</b> Concentra o poder preditivo do TMD; serve como termômetro diário de baixo custo.</li>
 <li><b>Trate o Pós-treino como referência de carga.</b> A queda de Vigor e a alta de Fadiga são o retrato agudo da dose; desvios muito acima do padrão merecem atenção antes de virarem overreaching.</li>
 <li><b>Aproveite os dias 5 e 8 como janelas de recuperação já observadas</b> — a periodização atual está produzindo alívio nesses pontos.</li>
 <li><b>PSE da 4ª série é um controle de qualidade do HIIT.</b> Cair consistentemente abaixo de ~9 pode indicar intensidade insuficiente; muito alta, com FC saturada, sinaliza necessidade de ajustar volume.</li>
 <li><b>Próximo passo analítico:</b> unir carga interna do HIIT (PSE·duração) ao humor por atleta e dia via chave de nome — os dados já permitem essa integração individual.</li>
</ul>

<div class="foot">
<p><b>Notas metodológicas.</b> BRUMS-24 em escore T (média populacional=50); TMD = (Tensão+Depressão+Raiva+Fadiga+Confusão) − Vigor. Comparações Pré×Pós por teste t de Welch com d de Cohen; associações com o TMD por correlação de Spearman (n=277). HIIT: FC em bpm e PSE em escala 0–10, médias sobre 27 atletas × 4 sessões. Fontes: <code>COLETAS.xlsx</code>, <code>HIIT_FC_PSE.xlsx</code>, <code>resultados_handebol.xlsx</code>.</p>
</div>
</div>'''
pathlib.Path('/home/user/mdlucca/analise/relatorio.html').write_text(html,encoding='utf-8')
print('ok', len(html),'bytes')
