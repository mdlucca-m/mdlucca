# -*- coding: utf-8 -*-
import base64, os, json
IMG='/tmp/docimg/'
def im(k):
    with open(IMG+k+'.jpg','rb') as f: return 'data:image/jpeg;base64,'+base64.b64encode(f.read()).decode()
mod=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/modelagem/resultados_modelagem.json'))
adv=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/analises_avancadas/resultados.json'))
conf=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/confiabilidade_invariancia/resultados_confiabilidade.json'))
pred=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/preditiva/resultados_preditiva.json'))
pv=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/perfil_variabilidade/resultados_perfil_variabilidade.json'))
mt=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/modelo_teorico/resultados_modelo_teorico.json'))
dh=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/dias_hiit/resultados_dias_hiit.json'))
oq=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/outros_questionarios/resultados_outros_questionarios.json'))
sn=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/sonolencia/resultados_sonolencia.json'))
rocd=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/roc_derivadas/resultados_roc_derivadas.json'))
dvar=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/derivadas_variaveis/resultados_derivadas_variaveis.json'))

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
html{scroll-behavior:smooth}
section{scroll-margin-top:12pt}
.toolbar{display:flex;flex-wrap:wrap;gap:6pt;margin:0 0 12pt}
.toolbar button{font-family:'Helvetica Neue',Arial,sans-serif;font-size:8.5pt;font-weight:700;color:#122438;background:#F4F7FB;border:1px solid #CBD6E4;border-radius:7px;padding:6pt 11pt;cursor:pointer}
.toolbar button:hover{border-color:#0E8C86;color:#0E8C86}
.toolbar .ok{color:#0E8C86;border-color:#0E8C86}
.toc{background:#F7FAFD;border:1px solid #E1E8F0;border-radius:10px;padding:12pt 16pt;margin:0 0 8pt;page-break-after:always}
.toc-h{font-family:Georgia,serif;font-size:14pt;color:#122438;margin-bottom:8pt}
.toc ol{margin:0;padding:0;list-style:none;columns:2;column-gap:24pt}
.toc li{margin:0 0 4pt;break-inside:avoid}
.toc a{text-decoration:none;color:#16273D;display:flex;gap:7pt;align-items:baseline}
.toc a:hover .toc-t{color:#0E8C86;text-decoration:underline}
.toc-n{font-family:ui-monospace,monospace;font-size:8pt;color:#0E8C86;min-width:16pt}
.toc-t{font-size:9.5pt}
.toc-ey{font-family:ui-monospace,monospace;font-size:6.6pt;color:#8798AE;text-transform:uppercase;letter-spacing:.08em}
.backtop{position:fixed;right:16px;bottom:16px;z-index:50;background:#0E8C86;color:#fff;border:none;border-radius:50%;width:42px;height:42px;font-size:18px;cursor:pointer;box-shadow:0 4px 14px -4px rgba(0,0,0,.45)}
@media print{.toolbar,.backtop{display:none !important}}
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
rowsVar=[[v['var'],f"{v['pct_entre']:.1f}".replace('.',','),('—' if v['CV_intra'] is None else f"{v['CV_intra']:.1f}".replace('.',','))] for v in sorted(pv['variabilidade'],key=lambda v:-v['pct_entre'])]
_pf=pv['perfil']; _icb=_pf['iceberg_prev']
_chi=f"χ²({_pf['quiquadrado']['df']}) = {_pf['quiquadrado']['chi2']:.2f}".replace('.',','); _pchi=str(_pf['quiquadrado']['p']).replace('.',','); _cv=str(_pf['quiquadrado']['cramer_V']).replace('.',',')
_eta=str(pv['segmentacao']['eta2_PTH_entre_grupos']).replace('.',','); _ic0=f"{_icb['pre']*100:.0f}"; _ic1=f"{_icb['pos']*100:.0f}"
_fnum2=lambda v:('—' if v is None else f"{v:+.2f}".replace('.',','))
# outros questionários
rowsOQ=[[r['inst'],r['escala'],f"{r['M_pre']:.2f}".replace('.',','),f"{r['M_pos']:.2f}".replace('.',','),f"{r['delta']:+.2f}".replace('.',','),f"{r['dz']:+.2f}".replace('.',','),('<0,001' if r['p_FDR']<0.001 else f"{r['p_FDR']:.3f}".replace('.',',')),('sim' if r['sig'] else '—')] for r in oq['A_resposta_aguda']]
_oqtg=['Vigor','Fadiga','PTH']; _oqk=['FadFis','FadMen','EstFis','EstMen']; _oqlab={'FadFis':'Fadiga física','FadMen':'Fadiga mental','EstFis':'Estado físico','EstMen':'Estado mental'}
rowsOQC=[[_oqlab[k]]+[f"{oq['C_convergencia_rmcorr']['matriz'][k][t]:+.2f}".replace('.',',') for t in _oqtg] for k in _oqk]
rowsOQD=[[d['inst'],f"{d['ICC']:.2f}".replace('.',','),('traço' if d['ICC']>=0.5 else 'estado')] for d in oq['D_ICC']]
rowsSN=[[r['item'],f"{r['M_pre']:.2f}".replace('.',','),f"{r['M_pos']:.2f}".replace('.',','),f"{r['delta']:+.2f}".replace('.',','),f"{r['dz']:+.2f}".replace('.',','),('<0,001' if r['wilcoxon_p']<0.001 else f"{r['wilcoxon_p']:.3f}".replace('.',',')),r['direcao']] for r in sn['A_resposta_itens']]
_snA=str(sn['D_alpha']['com_sonolento']).replace('.',','); _snA3=str(sn['D_alpha']['sem_sonolento']).replace('.',','); _snCFA=str(sn.get('carga_CFA_sonolento')).replace('.',',')
rowsRD=[[r['var'],f"{r['AUC_derivada']:.2f}".replace('.',','),f"[{r['IC_derivada'][0]:.2f}; {r['IC_derivada'][1]:.2f}]".replace('.',','),f"{r['AUC_nivel']:.2f}".replace('.',','),f"{r['ganho']:+.2f}".replace('.',',')] for r in rocd['resultados']]
rowsDVb=[[r['var'],f"{r['inclinacao_media']:+.2f}".replace('.',','),f"{r['vel_inicial']:+.2f}".replace('.',','),f"{r['vel_final']:+.2f}".replace('.',','),r['direcao']] for r in dvar['B_derivadas_variaveis']]
rowsDVc=[[r['var'],f"{r['slope_medio']:+.2f}".replace('.',','),f"{r['slope_dp']:.2f}".replace('.',','),f"{r['pct_positivo']:.0f}%"] for r in dvar['C_derivada_individual']]
lim=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/limites_derivadas/resultados_limites_derivadas.json'))
_limL=f"{lim['ajuste']['L']:.2f}".replace('.',','); _limk=f"{lim['ajuste']['k']:.2f}".replace('.',','); _limR2=f"{lim['ajuste']['R2']:.2f}".replace('.',',')
_limD=f"{lim['B_definicao_limite']['f_linha_analitica']:.2f}".replace('.',','); _limTc=f"{lim['D_limites']['modelo_teorico']['ponto_critico_t*']:.2f}".replace('.',',')
robj=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/residuos_coef_psicometria/resultados.json'))
_pnr=lambda v:('<0,001' if v<0.001 else f"{v:.3f}".replace('.',','))
_c2=lambda v:f"{v:+.2f}".replace('.',','); _f2=lambda v:f"{v:.2f}".replace('.',',')
_termpt={'Intercept':'Intercepto','pos':'Pós','dia':'Dia','hiit':'HIIT'}
rowsCoef=[[o['label'],_termpt[f['termo']],_c2(f['beta']),_f2(f['EP']),_f2(f['z']),_pnr(f['p']),f"[{f['ic'][0]:.2f}; {f['ic'][1]:.2f}]".replace('.',',')] for y,o in robj['coeficientes'].items() for f in o['fixos']]
rowsResid=[[robj['coeficientes'][y]['label'],_f2(robj['coeficientes'][y]['ICC']),_pnr(o['shapiro_p']),'sim' if o['residuos_normais'] else 'não',_pnr(o['hetero_p']),'sim' if o['homocedastico'] else 'não'] for y,o in robj['residuos'].items()]
rowsPsi=[[n,_f2(o['alpha']),_f2(o['alpha_ordinal']),_f2(o['omega']),_f2(o['AVE']),_f2(o['CR']),_f2(o['item_total_medio'])] for n,o in robj['psicometria'].items()]
rowsBA=[[b['par'],str(b['n']),_f2(b['r_pearson']),f"{b['bias']:.1f}".replace('.',','),f"[{b['LoA_rm'][0]:.1f}; {b['LoA_rm'][1]:.1f}]".replace('.',',')] for b in robj['bland_altman']]
_afe=robj['afe']; _afeK=_f2(_afe['KMO']); _afeVar=f"{_afe['variancia_cum'][5]*100:.1f}".replace('.',','); _afeBart=_pnr(_afe['bartlett_p'])
_ivj=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/invariancia_multigrupo/resultados.json')); _ivi=_ivj['invariancia']
_ivCFIpre=_f2(_ivj['grupos']['pre']['CFI']); _ivCFIpos=_f2(_ivj['grupos']['pos']['CFI'])
_ivPhi=f"{_ivi['tucker_phi_global']:.3f}".replace('.',','); _ivdCFI=f"{_ivi['delta_CFI']:+.3f}".replace('.',',')
_ivPhiFat=', '.join(f"{k} {v:.3f}".replace('.',',') for k,v in _ivi['tucker_phi_fator'].items())
_ivesc=json.load(open('/home/user/mdlucca/auditoria_brums_hiit/invariancia_multigrupo/resultados_escalar.json'))
_mcCFI=f"{_ivesc['metrico_conjunto']['delta_CFI']:+.3f}".replace('.',','); _mcRMSEA=f"{_ivesc['metrico_conjunto']['delta_RMSEA']:+.3f}".replace('.',',')
_escRMS=f"{_ivesc['escalar']['rms_global']:.3f}".replace('.',','); _kFad=f"{_ivesc['escalar']['kappa_pos']['Fadiga']:+.2f}".replace('.',','); _kVig=f"{_ivesc['escalar']['kappa_pos']['Vigor']:+.2f}".replace('.',',')
_pnum=lambda v:('<0,001' if v<0.001 else f"{v:.3f}".replace('.',','))
rowsDA=[]  # entre dias de HIIT
for _v,_o in dh['A_entre_HIIT'].items():
    _m=_o['friedman']['medias']
    rowsDA.append([_o['label'],_fnum2(_m.get('2')),_fnum2(_m.get('4')),_fnum2(_m.get('7')),_pnum(_o['friedman']['p']),'sim' if _o['friedman']['p']<0.05 else 'não'])
rowsDB=[]  # entre dias sem HIIT
for _v,_o in dh['B_entre_SEM'].items():
    _m=_o['friedman']['medias']
    rowsDB.append([_o['label'],_fnum2(_m.get('1')),_fnum2(_m.get('3')),_fnum2(_m.get('5')),_fnum2(_m.get('6')),_pnum(_o['friedman']['p']),'sim' if _o['friedman']['p']<0.05 else 'não'])
rowsDC=[[c['var'],_fnum2(c['media_HIIT']),_fnum2(c['media_SEM']),f"{c['dz']:+.2f}".replace('.',','),_pnum(c['p_FDR']),'sim' if c['sig'] else 'não'] for c in dh['C_HIIT_vs_SEM']['resultados']]
_nC=dh['C_HIIT_vs_SEM']['n_atletas']
def _mtfx(y,term): return next(f for f in mt['mistos_R2_SE'][y]['fixos'] if f['termo']==term)
rowsMT=[]
for _y in ['PTH','FadFis','Vigor','Fadiga']:
    _o=mt['mistos_R2_SE'][_y]; _p=_mtfx(_y,'pos')
    rowsMT.append([_o['label'],f"{_o['R2_marginal']:.3f}".replace('.',','),f"{_o['R2_condicional']:.3f}".replace('.',','),
                   f"{_o['ICC']:.2f}".replace('.',','),f"{_p['beta']:+.2f}".replace('.',','),f"{_p['SE']:.2f}".replace('.',',')])
_bp=mt['bayesiano_gibbs']['PTH']['posterior']['pos']; _bppth=f"{_bp['media']:.2f}".replace('.',','); _bpci=f"[{_bp['ICr95'][0]:.2f}; {_bp['ICr95'][1]:.2f}]".replace('.',',')
_mv=mt['multivariada']; _pil=str(_mv['MANOVA']['pillai']).replace('.',','); _pilp=str(_mv['MANOVA']['p']).replace('.',','); _psf=str(_mv['PERMANOVA']['pseudo_F']).replace('.',','); _psr=str(_mv['PERMANOVA']['R2']).replace('.',','); _psp=str(_mv['PERMANOVA']['p']).replace('.',',')
_permok='concordam com o teste t em todas as variáveis' if all(r['concordam'] for r in pv['permutacao']) else 'divergem em alguma variável'
_logok='mantêm a decisão' if all(r['decisao_mantem'] for r in pv['sensibilidade']['log']) else 'alteram a decisão'
_outok='mantêm a decisão' if all(r['decisao_mantem'] for r in pv['sensibilidade']['sem_outlier']) else 'alteram a decisão'

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
 <div class="eyebrow">Comparação entre os dias</div><h2>Dias de HIIT entre si, dias sem HIIT entre si e HIIT vs sem</h2>
 <p>Três contrastes sobre a resposta aguda (Δ = pós − pré) por atleta-dia. Entre os <b>dias de HIIT</b> (D2/D4/D7), o teste de Friedman é não significativo em todas as variáveis — as três sessões são um <b>estímulo agudo consistente</b>, sem habituação nem amplificação progressiva.</p>
 {tbl(['Variável','Δ D2','Δ D4','Δ D7','Friedman p','Diferem?'],rowsDA)}
 <p>Entre os <b>dias sem HIIT</b> (D1/D3/D5/D6), os dias técnico-táticos são equivalentes — <b>exceto no PTH</b> (p = 0,029): os dias 1 e 6 perturbam bem mais que os dias 3 e 5. Nem todo dia sem HIIT é igual.</p>
 {tbl(['Variável','Δ D1','Δ D3','Δ D5','Δ D6','Friedman p','Diferem?'],rowsDB)}
 <p>No contraste direto <b>HIIT vs sem HIIT</b> (média do Δ agudo por atleta, n = {_nC}; Wilcoxon + FDR), nenhuma variável difere — o <b>salto agudo pré→pós é semelhante</b> entre os tipos de dia (a fadiga física tende a subir mais no HIIT, dz = 0,38, n.s.). Coerente com a interação Condição×Momento nula (§6): a assinatura do HIIT está no <b>nível do dia</b> e no <b>acúmulo</b> (PTH com pico no D7), não na magnitude da resposta pré→pós.</p>
 {tbl(['Variável','Δ HIIT','Δ SEM','dz','p (FDR)','Difere?'],rowsDC)}
 {fig('diashiit','<b>Comparação entre os dias.</b> A: entre dias de HIIT (equivalentes); B: entre dias sem HIIT (só o PTH difere); C: HIIT vs sem (salto agudo semelhante); D: nível de PTH por dia D1→D7 (pico no D7).')}
</section>

<section>
 <div class="eyebrow">7 · Confirmação multivariada e bayesiana</div><h2>Quão forte é a evidência?</h2>
 <p>O teste de Hotelling T² confirma o efeito multivariado concentrado no eixo vigor+fadiga (F(2,25)=5,59; p=0,010); as seis subescalas juntas ficam no limiar (F(6,21)=2,52; p=0,054). O fechamento bayesiano (fator de Bayes JZS exato) quantifica tanto os efeitos quanto a <b>ausência</b> deles: evidência extrema para a fadiga física (BF₁₀≈2444) e evidência positiva de <b>equivalência</b> para a confusão (BF₁₀≈0,23).</p>
 {tbl(['Desfecho','t','BF₁₀'],rowsBF)}
 {fig('A4_bayes','<b>Fator de Bayes JZS</b> — Δ agudo por desfecho (escala log; direita = efeito, esquerda = equivalência).')}
</section>

<section>
 <div class="eyebrow">Modelo teórico · framework</div><h2>Modelo matemático, R², erro-padrão, bayesiano e multivariada</h2>
 <p>A resposta de humor é formalizada como um balanço <b>fitness–fadiga</b> (Banister) — State(t)=p₀+k₁·g(t)−k₂·h(t) — cuja forma estimável, com o atleta como unidade, é o modelo misto Yᵢⱼₜ = β₀ + β₁·Pós + β₂·Dia + β₃·HIIT + uᵢ + εᵢⱼₜ (uᵢ~N(0,τ²), ε~N(0,σ²); ICC=τ²/(τ²+σ²)). O framework abaixo liga o modelo teórico às três vias de estimação.</p>
 {fig('framework2','<b>Framework.</b> Do modelo teórico (fitness–fadiga) à forma estimável (mistos) e às três vias: R²/erro-padrão (frequentista), Gibbs (bayesiano) e multivariada (MANOVA/PERMANOVA).')}
 <p>O <b>coeficiente de determinação</b> de Nakagawa &amp; Schielzeth separa a explicação dos efeitos fixos (marginal) da explicação total com o indivíduo (condicional). O R² marginal é pequeno (0,06–0,21) mas o condicional chega a 0,58–0,63: <b>a maior parte da variância explicável é individual</b> (ICC 0,47–0,60). Os erros-padrão determinam bem os efeitos do Pós e do HIIT.</p>
 {tbl(['Desfecho','R² marginal','R² condicional','ICC','β(Pós)','SE'],rowsMT)}
 <p>A estimação <b>bayesiana</b> (amostrador de Gibbs, modelo hierárquico conjugado) coincide com a frequentista — para o PTH, posterior β = {_bppth} com ICr95% {_bpci} e P(efeito&gt;0)=1,00 — e a análise <b>multivariada</b> confirma o deslocamento pré→pós do vetor das seis subescalas: MANOVA (Pillai {_pil}; p = {_pilp}) e PERMANOVA pareada (Anderson, 2001; pseudo-F {_psf}; R² {_psr}; p = {_psp}) concordam. Três vias independentes, o mesmo efeito no eixo energia–fadiga.</p>
 {fig('modteo','<b>Modelo teórico — estimativas.</b> A: R² marginal×condicional (Nakagawa); B: efeitos fixos ± erro-padrão (PTH); C: posterior bayesiano vs. frequentista; D: PERMANOVA (nula de permutação).')}
</section>

<section>
 <div class="eyebrow">Robustez · verificações avançadas</div><h2>Resíduos, coeficientes, análise fatorial exploratória e concordância</h2>
 <p>Uma camada final de robustez fecha a modelagem e a psicometria. Os <b>coeficientes</b> dos modelos mistos (y ~ Pós + Dia + HIIT + (1|atleta), REML) trazem β, erro-padrão, z, p e IC95% para cada desfecho — o efeito do pós é positivo e significativo no eixo energético e negativo para o vigor, com o HIIT elevando o nível do dia.</p>
 {tbl(['Desfecho','Termo','β','EP','z','p','IC95%'],rowsCoef)}
 <p>O <b>diagnóstico de resíduos condicionais</b> (y − Xβ − u_atleta) valida os modelos: para a fadiga física os resíduos são aproximadamente normais e sem heterocedasticidade forte; o PTH — assimétrico e com piso/limite — mostra resíduos não-normais e heterocedásticos, o que recomenda cautela e sustenta o uso paralelo de testes não-paramétricos e permutacionais. O ICC (0,47–0,60) confirma a forte componente entre atletas.</p>
 {tbl(['Desfecho','ICC','Shapiro p','Resíduos normais?','Hetero p','Homocedástico?'],rowsResid)}
 {fig('residuos','<b>Coeficientes e resíduos.</b> A: resíduos vs. ajustados; B: Q–Q; C: escala–locação (homocedasticidade); D: histograma; E: coeficiente β(Pós) ± IC95% por desfecho; F: interceptos aleatórios por atleta (BLUPs).')}
 <p>Na <b>psicometria robusta</b>, cada subescala é avaliada por α de Cronbach, α ordinal (Spearman), ω de McDonald, variância média extraída (AVE) e confiabilidade composta (CR). Raiva, depressão e fadiga têm AVE ≥ 0,50 e CR ≥ 0,80 (validade convergente sólida); vigor no limiar; tensão e confusão ficam abaixo (efeito piso), coerente com todo o restante.</p>
 {tbl(['Subescala','α','α ordinal','ω','AVE','CR','item-total'],rowsPsi)}
 {fig('psicorob','<b>Psicometria robusta.</b> Confiabilidade (α, α ordinal, ω, CR) por subescala (linha prática 0,70) e variância média extraída (AVE ≥ 0,50).')}
 <p>A <b>análise fatorial exploratória</b> (KMO {_afeK}; Bartlett p {_afeBart}) confirma a estrutura: por Kaiser retêm-se {_afe['n_fatores_kaiser']} fatores e pela análise paralela de Horn {_afe['n_fatores_paralela']}, com a solução de seis fatores (promax) explicando {_afeVar}% da variância. A matriz de cargas mostra <b>estrutura simples</b> — cada conjunto de quatro itens carrega no seu fator —, corroborando o modelo teórico do BRUMS.</p>
 {fig('afe','<b>AFE e cargas.</b> Esquerda: scree + análise paralela (Horn) e critério de Kaiser; direita: matriz de cargas rotacionada (promax, 6 fatores) — estrutura simples por subescala.')}
 <p>Por fim, a concordância de <b>Bland–Altman</b> entre instrumentos do mesmo construto (reescalados a % do máximo, com limites cientes de medidas repetidas) mostra que eles <b>correlacionam mas não são intercambiáveis</b>: há viés sistemático e limites de concordância largos — convergência de construto, não equivalência de valor absoluto.</p>
 {tbl(['Par de instrumentos','n','r','viés (%)','LoA95% (%)'],rowsBA)}
 {fig('blandaltman','<b>Bland–Altman.</b> Diferença vs. média (% do máximo) com viés e limites de concordância de 95% cientes de medidas repetidas, para pares de instrumentos do mesmo construto.')}
 <p>Por fim, a <b>invariância de medida pré→pós</b> foi testada por AFC multigrupo (semopy) nos quatro fatores confiáveis (tensão e confusão excluídas por variância degenerada). A estrutura <b>configural</b> ajusta-se de forma equivalente nos dois momentos (CFI pré {_ivCFIpre} / pós {_ivCFIpos}); a <b>invariância métrica</b> é sustentada pela congruência das cargas (Tucker φ global {_ivPhi} ≥ 0,95; por fator {_ivPhiFat}), enquanto o teste ΔCFI estrito — com o grupo pós usando as cargas fixadas na solução do pré, mais conservador que o modelo métrico conjunto — fica em {_ivdCFI} (limiar −0,01), indicando apenas um pequeno custo de ajuste. Em conjunto, a mudança pré→pós observada é de <b>estado</b>, não um artefato do instrumento — o mesmo veredito da congruência de Tucker do módulo de confiabilidade.</p>
 {fig('invmg','<b>AFC multigrupo e invariância (pré vs. pós).</b> Esquerda: cargas padronizadas por item nos dois momentos; direita: congruência de Tucker φ por fator (linha 0,95).')}
 <p>Um <b>modelo métrico conjunto</b> (cargas comuns estimadas em conjunto a partir dos dados centrados no grupo, e não fixadas ao pré) confirma a invariância métrica de forma menos conservadora: ΔCFI {_mcCFI} e ΔRMSEA {_mcRMSEA} — bem dentro dos limiares. A <b>invariância escalar</b> foi avaliada decompondo as diferenças de intercepto Δτ = τ_pós − τ_pré em um único deslocamento da média latente por fator (Δτ ≈ λ·Δκ): o viés residual de intercepto é pequeno (RMS {_escRMS}, escala de item 0–4), indicando invariância escalar <b>aproximada</b>. O deslocamento da média latente κ recai exatamente sobre o eixo energético — <b>fadiga {_kFad}</b> e <b>vigor {_kVig}</b> —, ou seja, a mudança pré→pós é um deslocamento verdadeiro do traço, não viés de item; o maior resíduo aparece na fadiga, puxado pelo item "Sonolento" (que já se mostrou na contramão).</p>
 {fig('invesc','<b>Invariância escalar.</b> Esquerda: interceptos por item (referência pré vs. pós); direita: deslocamento da média latente κ por fator (pós − pré) — concentrado em fadiga (↑) e vigor (↓).')}
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
 <div class="eyebrow">Diagnóstico · derivadas</div><h2>Curva ROC das derivadas: a taxa de variação diagnostica menos que o nível</h2>
 <p>Complementando a análise ROC sobre os níveis, testou-se a <b>derivada aguda</b> (Δ = pós − pré, por atleta-dia) como escore para separar dia de HIIT (2/4/7) de dia sem HIIT (1/3/5/6) — 135 pares, IC95% por bootstrap agrupado por atleta. A derivada é um <b>diagnóstico fraco</b> (a melhor é a fadiga física, AUC 0,59; as demais próximas do acaso) e <b>não supera o nível</b>: para o PTH, o nível do dia discrimina bem melhor (0,60) do que a sua derivada (0,50).</p>
 {tbl(['Variável','AUC derivada','IC95% (deriv.)','AUC nível','Ganho'],rowsRD)}
 <p>Confirma, por uma via diagnóstica, o que a interação Condição×Momento e a comparação entre dias já indicavam: o <b>salto agudo</b> (a derivada) é semelhante entre os tipos de dia — a assinatura do HIIT vive no <b>nível diário</b> e no <b>acúmulo</b>, não na velocidade de mudança pontual.</p>
 {fig('rocderiv','<b>ROC das derivadas.</b> A: curvas ROC da derivada aguda por variável; B: AUC da derivada vs. do nível, com IC95% por bootstrap agrupado por atleta.')}
</section>

<section>
 <div class="eyebrow">Derivadas · variável e atleta</div><h2>Velocidade de mudança: derivadas por variável e por atleta</h2>
 <p>Derivando a trajetória diária de cada variável (ajuste cúbico), a <b>velocidade de acúmulo</b> difere: o PTH acumula mais rápido (+0,53/dia), fadiga e fadiga física ~+0,4/dia, a fadiga mental é plana e o vigor cai (−0,28/dia).</p>
 {tbl(['Variável','Inclinação média/dia',"f'(1)","f'(7)",'Direção'],rowsDVb)}
 <p>A <b>derivada individual</b> (inclinação dV/dia de cada atleta) revela a heterogeneidade: a fadiga física acumula em <b>92 %</b> dos atletas com dispersão pequena (DP 0,40) — marcador consistente; o PTH acumula em apenas <b>58 %</b> e com dispersão enorme (DP 1,45) — idiossincrático; o vigor cai na maioria (27 % com derivada positiva).</p>
 {tbl(['Variável','Inclinação média (dV/dia)','DP','% positivas'],rowsDVc)}
 <p>No espaço das taxas de variação, isto reproduz a <b>variância de inclinação aleatória</b> do modelo de crescimento (≈ 1,13 para o PTH; ≈ 0,01 para a fadiga física) e reforça o monitoramento individualizado por tendência.</p>
 {fig('dvar','<b>Derivadas por variável e por atleta.</b> A: trajetórias (z); B: velocidades f′(t); C: derivada média por variável; D: derivada individual por atleta (heterogeneidade).')}
</section>

<section>
 <div class="eyebrow">Cálculo · limites e derivadas</div><h2>Limites e derivadas da trajetória de fadiga</h2>
 <p>Formalizando a trajetória de acúmulo com o cálculo, ajusta-se à fadiga física média diária um modelo <b>saturante</b> f(t)=L−(L−f₁)·e^(−k(t−1)) (L={_limL}; k={_limk}; R²={_limR2}). A <b>derivada</b> f′(t) é a velocidade de acúmulo por dia: em t=2, a razão incremental [f(t₀+h)−f(t₀)]/h converge para f′(2)={_limD} à medida que h→0 — a definição de derivada por limite, verificada numericamente. A derivada é positiva e <b>decrescente</b> (segunda derivada negativa): a fadiga acumula, mas cada vez mais devagar, saturando no <b>limite</b> lim(t→∞) f(t)=L≈{_limL} — um estado estacionário do acúmulo.</p>
 <p>No modelo teórico fitness–fadiga (State(t)=k₁·e^(−t/τ₁)−k₂·e^(−t/τ₂)), a derivada State′(t)=0 define o <b>ponto crítico</b> t*={_limTc} — o nadir do estado (pico de fadiga aguda): antes dele o atleta ainda se recupera, depois relaxa de volta à linha de base (lim(t→∞) State(t)=0). É a leitura em cálculo das três âncoras: acúmulo real, saturação e retorno individual.</p>
 {fig('limites','<b>Limites e derivadas.</b> A: trajetória f(t) e a reta tangente (inclinação = derivada) em t=2; B: definição por limite — a razão incremental → f′(t₀) quando h→0; C: derivada f′(t) (velocidade de acúmulo), positiva e decrescente; D: modelo teórico fitness–fadiga com derivada zero no pico de fadiga (t*) e limite → linha de base.')}
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
 <div class="eyebrow">Perfil · variabilidade · robustez</div><h2>Perfil de humor, variabilidade e verificações de robustez</h2>
 <p>O perfil clássico "iceberg" (vigor acima das subescalas negativas) está presente em <b>{_ic0}%</b> das avaliações pré e cai para <b>{_ic1}%</b> no pós — a sessão erode o perfil, e o teste de independência confirma a associação perfil×momento ({_chi}; p = {_pchi}; V de Cramér = {_cv}).</p>
 {fig('perfil','<b>Perfil e distribuições.</b> A: perfil iceberg pré×pós; B: box plot por subescala; C: histograma do PTH (com inset log); D: dispersão vigor×fadiga por grupo.')}
 <p>Decompondo a variância de cada variável em <b>entre atletas</b> e <b>intra atleta</b>, a maior parte mora entre atletas — sobretudo nas subescalas de afeto negativo (traço-estáveis) e no PTH; a fadiga física é a mais "de estado". A segmentação por agrupamento (20 resilientes / 6 perturbados / 1 extremo) explica <b>η² = {_eta}</b> da variação do PTH entre atletas.</p>
 {tbl(['Variável','% da variância entre atletas','CV intra (%)'],rowsVar)}
 {fig('variab','<b>Variabilidade e robustez.</b> A: componentes de variância (entre×intra); B: variabilidade individual do PTH; C: perfis de grupo (η²='+_eta+'); D: distribuição nula do teste de permutação (fadiga física).')}
 <p><b>Robustez.</b> Três verificações confirmam que as conclusões não dependem de premissas: o teste de <b>permutação</b> (sign-flip pareado, 20 000 reamostragens) {_permok}; a <b>transformação logarítmica</b> das variáveis assimétricas {_logok}; e a <b>exclusão do outlier</b> (A06) {_outok}. Os achados são robustos à família de teste, à forma da distribuição e a casos influentes.</p>
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
 <div class="eyebrow">Outros questionários</div><h2>Autorrelatos externos ao BRUMS: resposta, convergência e estabilidade</h2>
 <p>Além do BRUMS, a coleta incluiu quatro autorrelatos — fadiga física (0–10), fadiga mental (0–10), estado físico (0–4) e estado mental (0–4). Na resposta aguda, os instrumentos <b>físicos</b> movem-se forte e significativamente (fadiga física dz +1,06; estado físico dz −0,93), enquanto os <b>mentais</b> apenas tendem — o mesmo eixo físico/energético do BRUMS.</p>
 {tbl(['Instrumento','Escala','Pré','Pós','Δ','dz','p (FDR)','Sig.?'],rowsOQ)}
 <p>A <b>convergência</b> com o BRUMS foi medida por correlação de medidas repetidas (rm_corr, intra-atleta). Os autorrelatos externos medem as mesmas dimensões que o BRUMS: a fadiga física correlaciona-se fortemente com a subescala Fadiga (r = +0,64) e o estado físico é seu espelho (r = −0,65) e positivo com o vigor (r = +0,47); os instrumentos mentais ancoram-se no PTH. É <b>validade convergente</b> dentro do sujeito.</p>
 {tbl(['Externo','r com Vigor','r com Fadiga','r com PTH'],rowsOQC)}
 <p>Quanto à <b>estabilidade</b> (ICC), os instrumentos mentais são mais "de traço" (ICC 0,60–0,70) e os físicos mais "de estado" (ICC ≈ 0,40), espelhando o BRUMS. Nenhum externo distingue dias de HIIT de dias sem HIIT no salto agudo.</p>
 {tbl(['Instrumento','ICC','Perfil'],rowsOQD)}
 {fig('outrosq','<b>Outros questionários.</b> A: resposta aguda (dz); B: média pré×pós; C: convergência com o BRUMS (rm_corr intra-atleta); D: estabilidade (ICC).')}
</section>

<section>
 <div class="eyebrow">Sonolência</div><h2>O item "Sonolento": sonolência não é fadiga</h2>
 <p>A sonolência foi medida como o item <b>"Sonolento"</b> (3º item da subescala Fadiga). Ele se comporta de forma <b>oposta</b> aos demais: enquanto Esgotado/Exausto/Cansado aumentam significativamente pós-treino, a sonolência <b>diminui</b> (dz −0,55; p = 0,007) — o exercício agudo é <b>ativador/despertador</b>, ainda que eleve a exaustão física. Sonolência e fadiga não são o mesmo construto no plano agudo.</p>
 {tbl(['Item de Fadiga','Pré','Pós','Δ','dz','p','Direção'],rowsSN)}
 <p>Dentro do atleta, o item Sonolento é praticamente <b>ortogonal</b> aos demais itens de fadiga (rm_corr 0,00–0,10) e levemente negativo com o vigor (−0,12). Consistentemente, a confiabilidade da subescala Fadiga <b>sobe de α = {_snA} para {_snA3}</b> quando o item é removido — confirmando a carga fatorial baixa ({_snCFA}) e a discriminação TRI baixa já observadas. Recomenda-se tratar a sonolência à parte da subescala Fadiga (eixo sono↔alerta). Não houve escala dedicada de sonolência/sono na coleta.</p>
 {fig('sono','<b>Sonolência.</b> A: Δ pré→pós dos 4 itens de Fadiga (Sonolento na contramão); B: dz por item; C: rm_corr do Sonolento; D: α da Fadiga com vs sem o item.')}
</section>

<section>
 <div class="eyebrow">Monitoramento · visualizações</div><h2>Painel de monitoramento: gauge, radar, monitoramento diário e bolhas 4D</h2>
 <p>Uma leitura visual reúne as três conclusões-âncora num só painel. Os <b>medidores (gauge)</b> posicionam os indicadores-chave sobre zonas de referência — a fadiga física ancora o eixo (dz 1,06, efeito grande; AUC diagnóstica 0,70), o perfil iceberg recua ao pós (75% das avaliações) e o HTMT máximo (0,846) fica abaixo do corte 0,85. O <b>radar</b> mostra o perfil de humor pré×pós: o vigor achata e a fadiga sobe (erosão do iceberg), com as demais negativas quase paradas. O <b>monitoramento diário</b> segue a carga de humor do eixo energético ao longo do microciclo (D1→D7), com faixas de alerta e os dias de HIIT (2/4/7) marcados — o PTH e a fadiga sobem até o pico no D7, o vigor faz o caminho inverso. O <b>mapa 4D</b> cruza, por variável, resposta aguda (dz), acúmulo (inclinação/dia), individualidade (variância entre atletas) e consenso direcional (% de atletas que acumulam): a fadiga física combina grande resposta e acúmulo homogêneo (bolha pequena e coral), enquanto o PTH acumula de forma idiossincrática (bolha grande) e o vigor ocupa o quadrante negativo.</p>
 {fig('monitoramento','<b>Monitoramento e visualizações.</b> A: medidores (gauge) dos indicadores-chave com zonas de referência; B: radar do perfil de humor pré×pós; C: monitoramento diário da carga de humor D1→D7 (faixas de alerta, dias de HIIT tracejados); D: mapa 4D por variável — resposta × acúmulo × individualidade × consenso direcional.')}
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
# ---- sumário navegável + botões automáticos (pós-processamento) ----
import re as _re
_toc=[]
def _idsec(m):
    attrs=m.group(1) or ''; inner=m.group(2)
    h2=_re.search(r'<h2>(.*?)</h2>', inner, _re.S)
    if not h2: return m.group(0)
    ey=_re.search(r'<div class="eyebrow">(.*?)</div>', inner, _re.S)
    sid='s%d'%(len(_toc)+1)
    title=_re.sub('<.*?>','',h2.group(1)).strip()
    eyt=_re.sub('<.*?>','',ey.group(1)).strip() if ey else ''
    _toc.append((sid,eyt,title))
    return '<section id="%s"%s>%s</section>'%(sid,attrs,inner)
H=_re.sub(r'<section( class="first")?>(.*?)</section>', _idsec, H, flags=_re.S)

_toc_items=''.join(
  '<li><a href="#%s"><span class="toc-n">%d</span><span><span class="toc-ey">%s</span><br><span class="toc-t">%s</span></span></a></li>'
  %(sid,i+1,ey,title) for i,(sid,ey,title) in enumerate(_toc))
_toc_html='<nav class="toc" id="sumario"><div class="toc-h">Sumário</div><ol>%s</ol></nav>'%_toc_items

# dados para os botões automáticos
_csv='variavel,delta,dz,p_FDR,sobrevive_FDR\n'+'\n'.join(
  '%s,%s,%s,%s,%s'%(r['y'],f"{r['b_pos']:.3f}",f"{r['dz']:.3f}",f"{r['p_FDR']:.4f}",('sim' if r['signif_FDR'] else 'nao'))
  for r in A if 'dz' in r)
_kpis={'atletas':27,'observacoes':456,'pares_pre_pos':135,'checagens_exatas':'77/84',
 'dz_fadiga_fisica':next((r['dz'] for r in A if r.get('y')=='FadFis' and 'dz' in r),None),
 'CFI_CFA':adv['CFA_DWLS']['CFI'],'HTMT_max':adv['HTMT_max'],'tucker_phi':conf['B_invariancia']['tucker_phi']}
_cite=('[AUTOR]. Monitoramento psicométrico do humor e da fadiga em atletas de handebol durante um '
 'microciclo de treinamento de alta intensidade (HIIT). [Tese] — [Instituição], 2026.')
import json as _json
_payload=_json.dumps({'kpis':_kpis,'resposta_aguda_csv':_csv,'citacao':_cite}, ensure_ascii=False)

_toolbar=('<div class="toolbar" role="toolbar" aria-label="Ações">'
 '<button onclick="window.print()">🖨 Imprimir / Salvar PDF</button>'
 '<button id="bJSON">⬇ Baixar dados (JSON)</button>'
 '<button id="bCSV">⬇ Baixar tabela (CSV)</button>'
 '<button id="bCite">❝ Copiar citação (ABNT)</button>'
 '<a href="#sumario" style="margin-left:auto"><button>↑ Sumário</button></a>'
 '</div>')

_script=('<button class="backtop" title="Voltar ao topo" '
 'onclick="scrollTo({top:0,behavior:\'smooth\'})">↑</button>'
 '<script>(function(){var D=%s;'
 'function dl(name,txt,mime){var b=new Blob([txt],{type:mime});var u=URL.createObjectURL(b);'
 'var a=document.createElement("a");a.href=u;a.download=name;a.click();URL.revokeObjectURL(u);}'
 'function ok(btn){var t=btn.textContent;btn.textContent="✓ feito";btn.classList.add("ok");'
 'setTimeout(function(){btn.textContent=t;btn.classList.remove("ok");},1600);}'
 'var j=document.getElementById("bJSON");if(j)j.onclick=function(){'
 'dl("BRUMS_HIIT_dados.json",JSON.stringify({kpis:D.kpis,citacao:D.citacao},null,2),"application/json");ok(j);};'
 'var c=document.getElementById("bCSV");if(c)c.onclick=function(){'
 'dl("BRUMS_HIIT_resposta_aguda.csv",D.resposta_aguda_csv,"text/csv");ok(c);};'
 'var e=document.getElementById("bCite");if(e)e.onclick=function(){'
 '(navigator.clipboard&&navigator.clipboard.writeText(D.citacao))?navigator.clipboard.writeText(D.citacao).then(function(){ok(e);}):ok(e);};'
 '})();</script>')%_payload

# injeta toolbar + sumário logo antes da primeira seção; script antes de </body>
H=H.replace('<section id="s1"', _toolbar+_toc_html+'\n<section id="s1"', 1)
H=H.replace('</body></html>', _script+'</body></html>', 1)

open('/tmp/documento.html','w').write(H)
print('documento.html:', os.path.getsize('/tmp/documento.html')//1024,'KB')
