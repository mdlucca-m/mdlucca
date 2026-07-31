# -*- coding: utf-8 -*-
import base64, os, json
IMG='/tmp/docimg/'
def im(k):
    with open(IMG+k+'.jpg','rb') as f: return 'data:image/jpeg;base64,'+base64.b64encode(f.read()).decode()
mod=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/modelagem/resultados_modelagem.json'))
adv=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/analises_avancadas/resultados.json'))
conf=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/confiabilidade_invariancia/resultados_confiabilidade.json'))
pred=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/preditiva/resultados_preditiva.json'))

CSS="""
@page{size:A4;margin:18mm 16mm}
*{box-sizing:border-box}
html,body{margin:0;font-family:'Helvetica Neue',Arial,sans-serif;color:#16273D;line-height:1.5;font-size:10.5pt}
h1,h2,h3{font-family:Georgia,'Times New Roman',serif;color:#122438;line-height:1.2}
h1{font-size:23pt;margin:0 0 2pt}
.sub{color:#5B6B82;font-size:11pt;margin:0}
h2{font-size:15pt;margin:0 0 6pt;padding-bottom:4pt;border-bottom:2px solid #0E8C86}
h3{font-size:12pt;margin:14pt 0 4pt;color:#245C8B}
.eyebrow{font-family:ui-monospace,monospace;font-size:8pt;letter-spacing:.15em;text-transform:uppercase;color:#0E8C86;margin-bottom:3pt}
section{page-break-before:always;padding-top:2pt}
section.first{page-break-before:auto}
p{margin:0 0 7pt;text-align:justify}
figure{margin:8pt 0;page-break-inside:avoid}
figure img{width:100%;border:1px solid #E1E8F0;border-radius:5px}
figcaption{font-size:8.5pt;color:#5B6B82;font-style:italic;margin-top:3pt}
figcaption b{color:#122438;font-style:normal}
.kpis{display:flex;flex-wrap:wrap;gap:8pt;margin:12pt 0}
.kpi{flex:1;min-width:90pt;background:#F4F7FB;border:1px solid #E1E8F0;border-radius:7px;padding:8pt 10pt}
.kpi b{display:block;font-family:Georgia,serif;font-size:16pt;color:#245C8B}
.kpi span{font-size:7.5pt;text-transform:uppercase;letter-spacing:.05em;color:#5B6B82}
table{border-collapse:collapse;width:100%;font-size:8.7pt;margin:7pt 0;page-break-inside:avoid}
th,td{border-bottom:1px solid #E1E8F0;padding:3.5pt 6pt;text-align:left}
th{color:#5B6B82;font-weight:700;border-bottom:1.5px solid #B9C6D6}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.two{display:flex;gap:10pt}.two figure{flex:1}
.lead{font-size:11pt;color:#28405c}
.tag{display:inline-block;background:#EAF4F2;color:#0E8C86;font-size:7.5pt;padding:1.5pt 6pt;border-radius:20px;font-family:ui-monospace,monospace;margin-right:3pt}
.cover{page-break-after:always;padding-top:40pt}
.cover .rule{height:3px;background:#0E8C86;width:70pt;margin:14pt 0}
.foot{color:#8798AE;font-size:8pt;margin-top:26pt}
"""

def tbl(head, rows):
    h='<tr>'+''.join(f'<th class="{"n" if i>0 else ""}">{c}</th>' for i,c in enumerate(head))+'</tr>'
    b=''.join('<tr>'+''.join(f'<td class="{"n" if i>0 else ""}">{c}</td>' for i,c in enumerate(r))+'</tr>' for r in rows)
    return f'<table>{h}{b}</table>'

LAB={'PTH':'PTH (TMD)','FadFis':'Fadiga física','Fadiga':'Fadiga','Vigor':'Vigor','FadMen':'Fadiga mental','Tensão':'Tensão','Depressão':'Depressão','Raiva':'Raiva','Confusão':'Confusão'}
A=mod['A_resposta_aguda']; rowsA=[[LAB[r['y']],f"{r['b_pos']:+.2f}",f"{r['dz']:+.2f}",f"{r['p_FDR']:.3f}","sim" if r['signif_FDR'] else "—"] for r in A if 'dz' in r]
C=mod['C_efeito_HIIT_nivel_dia']; rowsC=[[LAB[c['y']],f"{c['efeito_HIIT']:+.2f}",f"{c['p']:.3f}"] for c in C]
bfname={'FadFis':'Fadiga física','esc_vigor':'Vigor','PTH':'PTH','esc_fadiga':'Fadiga','esc_confusao':'Confusão','esc_tensao':'Tensão','esc_depressao':'Depressão','esc_raiva':'Raiva','FadMen':'Fadiga mental'}
bf=adv['bayes_JZS_agregado_por_atleta']; rowsBF=[[bfname.get(k,k),f"{v['t']:+.2f}",f"{v['BF10']:.2f}" if v['BF10']<100 else f"{v['BF10']:.0f}"] for k,v in sorted(bf.items(),key=lambda kv:-kv[1]['BF10'])]
_vd=lambda r:('sim' if r['adequada'] else ('limítrofe' if r['ic_atinge_070'] else 'não'))
rowsRel=[[r['sub'],f"{r['alpha']:.2f}".replace('.',','),f"[{r['alpha_ic'][0]:.2f}; {r['alpha_ic'][1]:.2f}]".replace('.',','),(f"{r['omega']:.2f}".replace('.',',') if r['omega'] else '—'),f"{r['r_inter_item']:.2f}".replace('.',','),_vd(r)] for r in sorted(conf['A_confiabilidade'],key=lambda r:-r['alpha'])]
_inv=conf['B_invariancia']
_tphi=str(round(_inv['tucker_phi'],3)).replace('.',',')
_cfipre=str(_inv['CFI_pre']).replace('.',','); _cfipos=str(_inv['CFI_pos']).replace('.',',')
_fnum=lambda v,d=3:(f"{v:+.{d}f}".replace('.',',') if v<0 else f"+{v:.{d}f}".replace('.',','))
rowsPred=[]
for _t,_o in pred['A_regressao'].items():
    for _r in _o['resultados']:
        rowsPred.append([_o['label'],_r['preditores'],_fnum(_r['R2']),f"{_r['RMSE']:.2f}".replace('.',','),_r['modelo']])
_g=pred['ganho_contexto']; _cl=pred['B_classificacao']
_dPTH=str(_g['PTH']['delta_contexto']).replace('.',','); _dFF=str(_g['FadFis']['delta_contexto']).replace('.',','); _dVI=str(_g['Vigor']['delta_contexto']).replace('.',',')
_aucB=str(_cl['auc_baseline_fadfis_pre']).replace('.',','); _aucL=str(_cl['auc_perfil_logistica']).replace('.',',')
_imp=', '.join(i['feature'] for i in _cl['importancia'][:4])

def fig(k,cap): return f'<figure><img src="{im(k)}"><figcaption>{cap}</figcaption></figure>'

H=f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>{CSS}</style></head><body>

<div class="cover">
 <div class="eyebrow">Estudo · Humor & carga interna · Handebol</div>
 <h1>BRUMS × HIIT no handebol</h1>
 <p class="sub">Documento completo com todas as figuras — auditoria, modelagem e psicometria</p>
 <div class="rule"></div>
 <p class="lead">Monitoramento do humor (Escala de Humor de Brunel) e da carga interna (FC/PSE) de 27 atletas de handebol ao longo de um microciclo de sete dias com três sessões de HIIT. Reúne, em um só documento, a reprodução independente das análises, a modelagem estatística com o atleta como unidade e a confirmação psicométrica.</p>
 <div class="kpis">
  <div class="kpi"><b>27</b><span>atletas</span></div>
  <div class="kpi"><b>456</b><span>observações</span></div>
  <div class="kpi"><b>135</b><span>pares pré/pós</span></div>
  <div class="kpi"><b>77/84</b><span>checagens exatas</span></div>
 </div>
 <p><span class="tag">auditoria</span><span class="tag">modelos mistos</span><span class="tag">CFA · HTMT · TRI</span><span class="tag">Bayes</span><span class="tag">carga interna</span><span class="tag">reprodutível</span></p>
 <p class="foot">Atletas anonimizados (A01–A27). Elaboração do autor · 2026. Figuras geradas a partir dos dados reais; números reproduzidos por código.</p>
</div>

<section class="first">
 <div class="eyebrow">1 · Desenho</div><h2>O desenho do estudo</h2>
 <p>Estudo observacional longitudinal de medidas repetidas. Cada atleta foi avaliado em vários momentos (pré e pós-treino) ao longo de sete dias (21–27/04/2024), com o HIIT aplicado nos dias 2, 4 e 7. A unidade de análise é o atleta — coletas repetidas são aninhadas, e tratá-las como independentes (pseudorreplicação) inflaria a significância. Toda a inferência deste documento respeita essa estrutura.</p>
 {fig('desenho_analitico','<b>Desenho analítico (visual abstract).</b> Amostra, microciclo, instrumentos, fluxo de dados e o achado-chave de cada etapa do pipeline — com mini-gráficos reais (piso, dz, iceberg, ΔPTH, Bayes, tipologia).')}
 {fig('infog','<b>Infográfico do desenho.</b> Versão condensada: amostra, instrumentos, microciclo e funil de coletas.')}
 {fig('fig_master_estudo','<b>Esquema-mestre.</b> Desenho, amostra, instrumentos e o que aconteceu no microciclo.')}
</section>

<section>
 <div class="eyebrow">2 · Arquitetura analítica</div><h2>Framework: da medida à decisão</h2>
 <p>A análise é hierárquica: primeiro a <b>qualidade da medida</b> (confiabilidade, estrutura, efeito piso), depois a <b>resposta</b> (aguda e acumulada) e por fim a <b>modelagem robusta</b> (efeitos mistos, multivariada, Bayes). A leitura de fundo é o modelo <i>fitness–fadiga</i>: o balanço entre frescor (vigor) e custo (fadiga).</p>
 <div class="two">{fig('fig_framework_hierarquico','<b>Framework hierárquico</b> das análises.')}{fig('fig_fitness_fadiga_analogico','<b>Modelo fitness–fadiga</b> (analógico).')}</div>
</section>

<section>
 <div class="eyebrow">3 · Qualidade da medida</div><h2>Estrutura, discriminância e informação dos itens</h2>
 <p>A análise fatorial confirmatória de seis fatores (estimador DWLS) tem ajuste aceitável: <b>CFI 0,921 · TLI 0,908 · RMSEA 0,055</b> (χ²(237)=562,9). As cargas são altas na maioria das subescalas; o ponto fraco é a <b>tensão</b>, degradada pelos itens de piso (o item apavorado tem 100% no piso e carga ≈ 0) — a mesma fragilidade psicométrica identificada na auditoria.</p>
 {fig('A1_cfa_cargas','<b>CFA (DWLS).</b> Cargas padronizadas por subescala; linha tracejada em 0,40.')}
 <p>A validade discriminante entre subescalas foi avaliada por <b>HTMT</b> sobre correlações policóricas: o máximo é <b>0,846</b> (tensão–confusão), abaixo do limiar de 0,85 — discriminância sustentada, com o par tensão–confusão no limite (proximidade conceitual e piso da tensão).</p>
 <div class="two">{fig('A2_htmt','<b>HTMT</b> (correlações policóricas).')}{fig('A3_grm','<b>TRI/GRM.</b> Discriminação (a) por item.')}</div>
 <p>A <b>consistência interna</b> por subescala (α de Cronbach com IC95%, ω de McDonald e r inter-item) reproduz a tabela de confiabilidade do manuscrito: raiva, depressão e fadiga são confiáveis com folga (α e ω acima de 0,80); vigor e confusão ficam <i>limítrofes</i> (α &lt; 0,70 mas o IC alcança 0,70, e o ω sobe para 0,78 e 0,68); a <b>tensão</b> é a única frágil (α 0,43), reflexo do severo efeito piso. Onde o IC do α cruza 0,70 a subescala não é reprovada — apenas medida com menos precisão nesta amostra.</p>
 {tbl(['Subescala','α','IC95% (α)','ω','r inter-item','α≥0,70?'],rowsRel)}
 <p>A <b>invariância de medida</b> pré→pós foi verificada comparando as cargas fatoriais estimadas no pré e no pós: o coeficiente de congruência de Tucker φ = {_tphi} (≥ 0,95), com CFI por grupo de {_cfipre} e {_cfipos}. A escala mede o mesmo construto da mesma forma antes e depois do microciclo — condição para interpretar a mudança pré→pós como mudança de <b>estado</b>, e não deriva psicométrica do instrumento.</p>
 <p>As distribuições são majoritariamente <b>assimétricas e não-normais</b> (efeito piso nas subescalas negativas). Por isso, além dos testes paramétricos, reportam-se os não-paramétricos: as duas famílias <b>concordam em todas as variáveis</b>.</p>
 {fig('descr','<b>Descritivas e testes.</b> A: forma/normalidade (assimetria por variável); B: concordância entre t pareado (paramétrico) e Wilcoxon (não-paramétrico).')}
</section>

<section>
 <div class="eyebrow">4 · Resposta aguda</div><h2>O que muda do pré para o pós-treino</h2>
 <p>No modelo misto pré→pós (intercepto aleatório por atleta, correção FDR), sobrevivem exatamente as variáveis do <b>eixo energia–fadiga</b>: fadiga física, PTH, fadiga, vigor e fadiga mental. Tensão, depressão, raiva e confusão não sobrevivem à correção.</p>
 {tbl(['Desfecho','b(pós)','dz','p (FDR)','sobrevive'],rowsA)}
 {fig('forest_dz','<b>Tamanho de efeito com IC95%.</b> Testes clássicos (t pareado/Wilcoxon, dz por bootstrap) confirmam o modelo misto — quatro variáveis do eixo energia–fadiga sobrevivem ao FDR.')}
 <div class="two">{fig('M1_resposta_aguda_dz','<b>Tamanhos de efeito (dz)</b> da resposta aguda; * sobrevive ao FDR.')}{fig('pipe_resposta_aguda','<b>Resposta aguda</b> (pipeline, verificação independente).')}</div>
 <figcaption style="margin-top:2pt">Nota: o <i>dz</i> da tabela é agregado por atleta; o <i>dz</i> por observação da Tabela 22 do manuscrito (fadiga física 0,76) usa a DP dos pares — mesmo sinal e significância, denominadores diferentes.</figcaption>
</section>

<section>
 <div class="eyebrow">5 · Acúmulo no microciclo</div><h2>A carga se acumula ao longo da semana</h2>
 <p>Ao longo dos sete dias, a fadiga física acumula de forma robusta (+0,34/dia) e o vigor cai (−0,28/dia); o perfil "iceberg" recua de 71% no Dia 1 para 33% no Dia 7. Para o PTH, a inclinação média é positiva mas a variância das inclinações individuais é alta — a perturbação total acumula de formas muito diferentes entre atletas.</p>
 <div class="two">{fig('pipe_trajetoria','<b>Trajetória diária</b> média (dois passos).')}{fig('pipe_iceberg','<b>Prevalência do perfil iceberg</b> ao longo da semana.')}</div>
 <div class="two">{fig('M2_acumulo_inclinacao','<b>Inclinação por dia</b> (modelo de crescimento com inclinação aleatória).')}{fig('chart_spaghetti','<b>Heterogeneidade</b> — trajetória do PTH por atleta.')}</div>
</section>

<section>
 <div class="eyebrow">6 · Efeito do HIIT</div><h2>Dias de HIIT vs. técnico-tático</h2>
 <p>No nível do dia (modelo misto, dias 2–7), o HIIT eleva o PTH em <b>+2,43</b> (p=0,003) e mexe no eixo energia–fadiga. Porém a interação Condição×Momento é nula para o PTH (p=0,910): o <b>salto agudo</b> pré→pós não difere entre HIIT e técnico-tático — a perturbação vem do nível do dia, não do estímulo agudo específico. A única exceção é a fadiga física, amplificada agudamente pelo HIIT (p=0,035).</p>
 {tbl(['Desfecho','Δ HIIT − sem','p'],rowsC)}
 {fig('M3_efeito_hiit','<b>Efeito do HIIT</b> vs. técnico-tático por desfecho (nível do dia).')}
</section>

<section>
 <div class="eyebrow">7 · Confirmação multivariada e bayesiana</div><h2>Quão forte é a evidência?</h2>
 <p>O teste de Hotelling T² confirma o efeito multivariado concentrado no eixo vigor+fadiga (F(2,25)=5,59; p=0,010); as seis subescalas juntas ficam no limiar (F(6,21)=2,52; p=0,054). O fechamento bayesiano (fator de Bayes JZS exato) quantifica tanto os efeitos quanto a <b>ausência</b> deles: evidência extrema para a fadiga física (BF₁₀≈2444) e evidência positiva de <b>equivalência</b> para a confusão (BF₁₀≈0,23).</p>
 {tbl(['Desfecho','t','BF₁₀'],rowsBF)}
 {fig('A4_bayes','<b>Fator de Bayes JZS</b> — Δ agudo por desfecho (escala log; direita = efeito, esquerda = equivalência).')}
</section>

<section>
 <div class="eyebrow">8 · Capacidade diagnóstica</div><h2>Curvas ROC — o que cada variável separa</h2>
 <p>Além do tamanho do efeito, quão bem cada variável <b>discrimina</b> estados? Para separar o pós do pré-treino, só a <b>fadiga física</b> alcança AUC moderada (0,70); PTH e fadiga ficam ~0,61 e as demais próximas de 0,5. Para separar um dia de HIIT de um dia sem HIIT, todas as AUC ficam entre 0,52 e 0,58 — o humor medido num único dia classifica mal o tipo de treino, porque a variabilidade individual domina. AUC com IC95% por bootstrap agrupado por atleta.</p>
 <div class="two">{fig('roc_prepos','<b>ROC pré vs pós.</b> Fadiga física AUC 0,70 — marcador sentinela do estado agudo.')}{fig('roc_hiit','<b>ROC HIIT vs sem.</b> Discriminação fraca (AUC ≤ 0,58) no nível do dia.')}</div>
 <p>A leitura prática reforça a recomendação do estudo: monitorar por <b>tendência</b>, com a fadiga física como sentinela e uma linha de base individual — não classificar um dia isolado por um escore de humor.</p>
</section>

<section>
 <div class="eyebrow">Validação · fora da amostra</div><h2>Análise preditiva: prever o estado pós-treino</h2>
 <p>Todas as análises anteriores são <i>in-sample</i>. Aqui a avaliação é <b>fora da amostra</b>, com validação <b>leave-one-athlete-out</b> ({pred['n_atletas']} dobras; o modelo nunca vê o atleta que prevê) sobre {pred['n_pares']} pares pré→pós — mede a generalização real para um atleta novo. Comparam-se conjuntos de preditores aninhados; o R² é calculado sobre as predições fora-da-dobra acumuladas.</p>
 {tbl(['Alvo','Preditores','R² (fora-da-dobra)','RMSE','Modelo'],rowsPred)}
 <p>O estado pós é <b>modestamente previsível</b> (R² ≈ 0,3–0,4) e o sinal vem quase inteiramente da <b>linha de base do próprio atleta</b>: acrescentar o contexto da sessão (HIIT, dia) ao baseline muda o R² em ≈ 0 (Δ PTH {_dPTH}; fadiga física {_dFF}; vigor {_dVI}). É a <b>confirmação preditiva</b> do desacoplamento carga↔humor — saber que o dia teve HIIT não ajuda a prever o humor pós além do que o estado pré do atleta já diz. Para classificar o "dia perturbado" (fadiga física pós ≥ 7), o perfil de humor pré alcança AUC {_aucL} (contra {_aucB} do baseline simples), com {_imp} entre os principais preditores e o HIIT entre os de menor importância.</p>
 {fig('preditiva','<b>Análise preditiva.</b> A: R² fora-da-dobra por conjunto de preditores; B: AUC do dia perturbado; C: importância das variáveis (HIIT é a menor).')}
</section>

<section>
 <div class="eyebrow">9 · Segmentação</div><h2>A resposta é individual</h2>
 <p>A tipologia por agrupamento separa 20 atletas resilientes, 6 perturbados e 1 extremo — a média esconde perfis opostos. A rede de correlações parciais entre subescalas mostra a depressão como nó de maior centralidade.</p>
 <div class="two">{fig('chart_cluster','<b>Tipologia</b> — perfis médios (z) por grupo.')}{fig('chart_network','<b>Rede</b> de subescalas — centralidade.')}</div>
 {fig('chart_weekly','<b>Mudança semanal</b> D1→D7 com intervalos de confiança por bootstrap.')}
 <p>O agrupamento hierárquico (Ward, sobre os perfis-z das seis subescalas) <b>cross-valida</b> a tipologia por um segundo método: 21 resilientes, 5 perturbados e 1 extremo (A06, o primeiro a se separar). O clustermap mostra os perfis por atleta.</p>
 <div class="two">{fig('dendro','<b>Dendrograma</b> (Ward) dos 27 atletas — corte em 3 grupos.')}{fig('clustermap','<b>Clustermap</b> — perfil z por atleta, ordenado pelo agrupamento.')}</div>
</section>

<section>
 <div class="eyebrow">10 · Carga interna</div><h2>Frequência cardíaca, esforço percebido e TRIMP</h2>
 <p>As sessões de HIIT foram quase-máximas: a FC de pico atinge 184/183/181 bpm nos dias 2/4/7 e a FC sobe do aquecimento (~158 bpm) à quarta série (~182 bpm). O PSE final fica próximo do teto da escala (9,3–9,6), sem aumento significativo entre sessões (Friedman n.s.). E, de forma reveladora, a magnitude da carga <b>não</b> prediz a perturbação aguda do humor (r≈−0,05): o custo fisiológico e a resposta psicológica se desacoplam no agudo.</p>
 <div class="two">{fig('pipe_carga_fc_por_fase','<b>FC pré→pós por fase</b> (aquecimento → 4ª série).')}{fig('pipe_carga_pse_fc_sessao','<b>PSE final e FC de pico</b> por sessão.')}</div>
 {fig('pipe_carga_x_humor','<b>Carga interna × humor.</b> PSE médio × Δ PTH agudo por atleta (r≈−0,05, n.s.).')}
 <p>Pela carga por FC (<b>TRIMP</b> de Banister sobre a %HRR), a intensidade foi uniformemente alta (%HRR 0,87–0,91 nas quatro sessões). Sem duração registrada, reporta-se o TRIMP relativo por sessão. Duas leituras convergem com o resto: a carga por FC (TRIMP) e por PSE (Foster) são <b>praticamente independentes</b> neste regime de teto (r≈−0,05), e o TRIMP também <b>não</b> prediz a resposta aguda do humor (r=−0,32; p=0,12).</p>
 {fig('trimp','<b>TRIMP.</b> Carga por sessão (TRIMP vs Foster), concordância entre as duas famílias e TRIMP × resposta do humor.')}
 <p>Reunindo os marcadores por atleta, o <b>acoplamento carga × humor</b> confirma o desacoplamento: nenhum par (PSE, FC, TRIMP × fadiga mental, TMD) é significativo, nem no nível do dia (tônico) nem no agudo — as únicas associações fortes são humor × humor.</p>
 {fig('acopl','<b>Acoplamento carga × humor.</b> Matrizes de correlação entre atletas — tônico (esq.) e agudo (dir.). * p&lt;0,05.')}
</section>

<section>
 <div class="eyebrow">11 · Reprodutibilidade</div><h2>Pipeline automatizado</h2>
 <p>Todas as análises são reproduzíveis com um comando: dezesseis nós encadeados levam da coleta bruta às tabelas, gráficos, Excel, PDF, relatório e à regeneração do sistema analista interativo. Um gatilho Cron reprocessa tudo a cada nova coleta.</p>
 {fig('workflow','<b>Pipeline (estilo N8N).</b> Início/Cron → ingestão → análises → carga interna → gráficos → exportação → app analista → relatório.')}
 <h3>Conclusão</h3>
 <p>Os planos psicométrico e analítico convergem: a variável mais confiável e sem piso — a fadiga física — é também a de maior resposta aguda (dz≈1), maior acúmulo semanal e a única amplificada pelo HIIT no agudo. A resposta de humor ao microciclo é real, mora no eixo energia–fadiga, é fortemente individual e não é função simples do custo cardiovascular da sessão. Tudo respeitando a estrutura de medidas repetidas — a contribuição metodológica central do trabalho.</p>
 <p class="foot">Documento completo · BRUMS × HIIT no handebol · reprodução independente e material de publicação · atletas anonimizados · 2026.</p>
</section>

</body></html>"""
open('/tmp/documento.html','w').write(H)
print('documento.html:', os.path.getsize('/tmp/documento.html')//1024,'KB')
