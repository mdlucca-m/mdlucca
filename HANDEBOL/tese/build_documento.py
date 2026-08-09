# -*- coding: utf-8 -*-
import base64, os, json
IMG='/tmp/docimg/'
def im(k):
    with open(IMG+k+'.jpg','rb') as f: return 'data:image/jpeg;base64,'+base64.b64encode(f.read()).decode()
mod=json.load(open('/home/user/mdlucca/HANDEBOL/modelagem/resultados_modelagem.json'))
adv=json.load(open('/home/user/mdlucca/HANDEBOL/analises_avancadas/resultados.json'))
conf=json.load(open('/home/user/mdlucca/HANDEBOL/confiabilidade_invariancia/resultados_confiabilidade.json'))
pred=json.load(open('/home/user/mdlucca/HANDEBOL/preditiva/resultados_preditiva.json'))
pv=json.load(open('/home/user/mdlucca/HANDEBOL/perfil_variabilidade/resultados_perfil_variabilidade.json'))
mt=json.load(open('/home/user/mdlucca/HANDEBOL/modelo_teorico/resultados_modelo_teorico.json'))
dh=json.load(open('/home/user/mdlucca/HANDEBOL/dias_hiit/resultados_dias_hiit.json'))
oq=json.load(open('/home/user/mdlucca/HANDEBOL/outros_questionarios/resultados_outros_questionarios.json'))
sn=json.load(open('/home/user/mdlucca/HANDEBOL/sonolencia/resultados_sonolencia.json'))
rocd=json.load(open('/home/user/mdlucca/HANDEBOL/roc_derivadas/resultados_roc_derivadas.json'))
dvar=json.load(open('/home/user/mdlucca/HANDEBOL/derivadas_variaveis/resultados_derivadas_variaveis.json'))

CSS="""
@page{size:A4;margin:14mm 12mm}
:root{--bg:#070b16;--card:rgba(14,26,46,.6);--ink:#e8f1ff;--mut:#8aa0c0;--faint:#5a6b86;--line:rgba(120,160,220,.16);--cyan:#22d3ee;--coral:#ff4d6d;--violet:#7c5cff;--gold:#ffd166;--mono:ui-monospace,'SF Mono','Cascadia Code',Menlo,monospace;--sans:system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
html,body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);line-height:1.6;font-size:10.6pt}
canvas#rain{position:fixed;inset:0;width:100vw;height:100vh;z-index:0;pointer-events:none;opacity:.45}
.mesh{position:fixed;inset:-20%;z-index:0;pointer-events:none;filter:blur(90px);opacity:.45;background:radial-gradient(38vw 38vw at 16% 10%,#1a6fb022 0,transparent 60%),radial-gradient(34vw 34vw at 84% 8%,#7c5cff2e 0,transparent 60%),radial-gradient(42vw 42vw at 72% 90%,#ff4d6d22 0,transparent 62%),radial-gradient(40vw 40vw at 8% 84%,#22d3ee22 0,transparent 60%)}
.cur,.cur-ring{position:fixed;top:0;left:0;z-index:60;pointer-events:none;border-radius:50%;mix-blend-mode:screen;transform:translate(-50%,-50%)}
.cur{width:9px;height:9px;background:var(--cyan);box-shadow:0 0 14px 3px #22d3eeaa}
.cur-ring{width:36px;height:36px;border:1.5px solid #7c5cffaa;transition:width .18s,height .18s,border-color .18s,background .18s}
.cur-ring.hot{width:56px;height:56px;border-color:var(--coral);background:#ff4d6d18}
@media(hover:none){.cur,.cur-ring{display:none}}
h1,h2,h3{font-family:var(--sans);line-height:1.15;letter-spacing:-.02em}
h1{font-size:30pt;margin:0 0 4pt;font-weight:850;background:linear-gradient(102deg,#eaf4ff 10%,var(--cyan) 46%,var(--violet) 88%);-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{color:var(--mut);font-size:12pt;margin:0}
h2{font-size:17pt;margin:0 0 8pt;font-weight:800;background:linear-gradient(100deg,#eaf4ff,var(--cyan));-webkit-background-clip:text;background-clip:text;color:transparent;display:inline-block}
h3{font-size:12.5pt;margin:16pt 0 5pt;color:var(--cyan);font-weight:750}
.eyebrow{font-family:var(--mono);font-size:8pt;letter-spacing:.22em;text-transform:uppercase;color:var(--cyan);margin-bottom:4pt}
p{margin:0 0 8pt;text-align:justify;color:#d7e2f2}
b,strong{color:var(--ink)}
figure{margin:10pt 0;page-break-inside:avoid}
figure img{width:100%;border:1px solid var(--line);border-radius:12px;background:#fff}
figcaption{font-size:8.6pt;color:var(--mut);font-style:italic;margin-top:5pt}
figcaption b{color:var(--ink);font-style:normal}
.kpis{display:flex;flex-wrap:wrap;gap:10pt;margin:14pt 0}
.kpi{flex:1;min-width:90pt;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10pt 12pt;backdrop-filter:blur(12px)}
.kpi b{display:block;font-family:var(--mono);font-size:17pt;font-weight:700;background:linear-gradient(180deg,#fff,var(--cyan));-webkit-background-clip:text;background-clip:text;color:transparent}
.kpi span{font-size:7.5pt;text-transform:uppercase;letter-spacing:.05em;color:var(--faint);font-family:var(--mono)}
table{border-collapse:collapse;width:100%;font-size:8.9pt;margin:8pt 0;page-break-inside:avoid}
th,td{border-bottom:1px solid var(--line);padding:4pt 7pt;text-align:left}
th{color:var(--mut);font-weight:700;border-bottom:1.5px solid rgba(120,160,220,.3);font-family:var(--mono);text-transform:uppercase;letter-spacing:.04em;font-size:8pt}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--mono)}
.two{display:flex;gap:12pt}.two figure{flex:1}
.lead{font-size:11.5pt;color:#c4d4ea}
.tag{display:inline-block;background:rgba(124,92,255,.14);color:var(--violet);font-size:7.5pt;padding:2pt 7pt;border-radius:20px;font-family:var(--mono);margin-right:3pt;letter-spacing:.06em}
.note{color:var(--faint);font-size:9pt}
.cover{padding-top:44pt}
.cover .rule{height:3px;background:linear-gradient(90deg,var(--cyan),var(--violet));width:80pt;margin:16pt 0;border:none}
.foot{color:var(--faint);font-size:8pt;margin-top:26pt}
section{scroll-margin-top:16pt}
.toolbar{display:flex;flex-wrap:wrap;gap:7pt;margin:0 0 14pt}
.toolbar button{font-family:var(--sans);font-size:8.7pt;font-weight:700;color:#04121e;background:linear-gradient(135deg,var(--cyan),#2dd4bf);border:none;border-radius:10px;padding:7pt 13pt;cursor:pointer}
.toolbar button:hover{filter:brightness(1.08)}
.toolbar .ok{background:var(--gold)}
.toc{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14pt 18pt;margin:0 0 8pt;backdrop-filter:blur(12px)}
.toc-h{font-family:var(--sans);font-size:15pt;font-weight:800;color:var(--ink);margin-bottom:10pt}
.toc ol{margin:0;padding:0;list-style:none;columns:2;column-gap:26pt}
.toc li{margin:0 0 5pt;break-inside:avoid}
.toc a{text-decoration:none;color:var(--ink);display:flex;gap:8pt;align-items:baseline}
.toc a:hover .toc-t{color:var(--cyan)}
.toc-n{font-family:var(--mono);font-size:8pt;color:var(--cyan);min-width:18pt}
.toc-t{font-size:9.6pt}
.toc-ey{font-family:var(--mono);font-size:6.6pt;color:var(--faint);text-transform:uppercase;letter-spacing:.08em}
.backtop{position:fixed;right:16px;bottom:16px;z-index:50;background:linear-gradient(135deg,var(--cyan),#2dd4bf);color:#04121e;border:none;border-radius:50%;width:44px;height:44px;font-size:18px;cursor:pointer;box-shadow:0 10px 30px -12px #22d3eeaa}
@media screen{.cover,section,.toc,.toolbar{position:relative;z-index:2;max-width:900px;margin-left:auto;margin-right:auto}
 section{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20pt 26pt;margin-top:16pt;backdrop-filter:blur(14px)}
 .cover{background:none;border:none}}
@media print{canvas#rain,.mesh,.cur,.cur-ring,.toolbar,.backtop{display:none !important}
 section{page-break-before:always;padding-top:2pt}section.first{page-break-before:auto}.cover{page-break-after:always}}
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
lim=json.load(open('/home/user/mdlucca/HANDEBOL/limites_derivadas/resultados_limites_derivadas.json'))
_limL=f"{lim['ajuste']['L']:.2f}".replace('.',','); _limk=f"{lim['ajuste']['k']:.2f}".replace('.',','); _limR2=f"{lim['ajuste']['R2']:.2f}".replace('.',',')
_limD=f"{lim['B_definicao_limite']['f_linha_analitica']:.2f}".replace('.',','); _limTc=f"{lim['D_limites']['modelo_teorico']['ponto_critico_t*']:.2f}".replace('.',',')
robj=json.load(open('/home/user/mdlucca/HANDEBOL/residuos_coef_psicometria/resultados.json'))
_pnr=lambda v:('<0,001' if v<0.001 else f"{v:.3f}".replace('.',','))
_c2=lambda v:f"{v:+.2f}".replace('.',','); _f2=lambda v:f"{v:.2f}".replace('.',',')
_termpt={'Intercept':'Intercepto','pos':'Pós','dia':'Dia','hiit':'HIIT'}
rowsCoef=[[o['label'],_termpt[f['termo']],_c2(f['beta']),_f2(f['EP']),_f2(f['z']),_pnr(f['p']),f"[{f['ic'][0]:.2f}; {f['ic'][1]:.2f}]".replace('.',',')] for y,o in robj['coeficientes'].items() for f in o['fixos']]
rowsResid=[[robj['coeficientes'][y]['label'],_f2(robj['coeficientes'][y]['ICC']),_pnr(o['shapiro_p']),'sim' if o['residuos_normais'] else 'não',_pnr(o['hetero_p']),'sim' if o['homocedastico'] else 'não'] for y,o in robj['residuos'].items()]
rowsPsi=[[n,_f2(o['alpha']),_f2(o['alpha_ordinal']),_f2(o['omega']),_f2(o['AVE']),_f2(o['CR']),_f2(o['item_total_medio'])] for n,o in robj['psicometria'].items()]
rowsBA=[[b['par'],str(b['n']),_f2(b['r_pearson']),f"{b['bias']:.1f}".replace('.',','),f"[{b['LoA_rm'][0]:.1f}; {b['LoA_rm'][1]:.1f}]".replace('.',',')] for b in robj['bland_altman']]
_afe=robj['afe']; _afeK=_f2(_afe['KMO']); _afeVar=f"{_afe['variancia_cum'][5]*100:.1f}".replace('.',','); _afeBart=_pnr(_afe['bartlett_p'])
_ivj=json.load(open('/home/user/mdlucca/HANDEBOL/invariancia_multigrupo/resultados.json')); _ivi=_ivj['invariancia']
_ivCFIpre=_f2(_ivj['grupos']['pre']['CFI']); _ivCFIpos=_f2(_ivj['grupos']['pos']['CFI'])
_ivPhi=f"{_ivi['tucker_phi_global']:.3f}".replace('.',','); _ivdCFI=f"{_ivi['delta_CFI']:+.3f}".replace('.',',')
_ivPhiFat=', '.join(f"{k} {v:.3f}".replace('.',',') for k,v in _ivi['tucker_phi_fator'].items())
_ivesc=json.load(open('/home/user/mdlucca/HANDEBOL/invariancia_multigrupo/resultados_escalar.json'))
_mcCFI=f"{_ivesc['metrico_conjunto']['delta_CFI']:+.3f}".replace('.',','); _mcRMSEA=f"{_ivesc['metrico_conjunto']['delta_RMSEA']:+.3f}".replace('.',',')
_escRMS=f"{_ivesc['escalar']['rms_global']:.3f}".replace('.',','); _kFad=f"{_ivesc['escalar']['kappa_pos']['Fadiga']:+.2f}".replace('.',','); _kVig=f"{_ivesc['escalar']['kappa_pos']['Vigor']:+.2f}".replace('.',',')
_ivep=json.load(open('/home/user/mdlucca/HANDEBOL/invariancia_multigrupo/resultados_estrita_parcial.json'))
_epCFIm=f"{_ivep['estrita']['CFI_metrico']:.3f}".replace('.',','); _epCFIe=f"{_ivep['estrita']['CFI_estrito']:.3f}".replace('.',',')
_epdCFI=f"{_ivep['estrita']['delta_CFI']:+.3f}".replace('.',','); _epdRMSEA=f"{_ivep['estrita']['delta_RMSEA']:+.3f}".replace('.',',')
_epLib=' e '.join(_ivep['parcial']['itens_liberados']); _epRMSf=f"{_ivep['parcial']['rms_residuo_full']:.3f}".replace('.',','); _epRMSp=f"{_ivep['parcial']['rms_residuo_parcial']:.3f}".replace('.',',')
_chj=json.load(open('/home/user/mdlucca/HANDEBOL/carga_humor/resultados_carga_humor.json'))
_chP=_chj['preditores_fadiga']['preditores']
_f2c=lambda v:('—' if v is None else f"{v:.2f}".replace('.',','))
rowsCH=[[p['label'],f"{p['AUC']:.2f}".replace('.',','),f"[{p['IC95'][0]:.2f}; {p['IC95'][1]:.2f}]".replace('.',','),
         f"{p['sensibilidade']:.2f}".replace('.',','),f"{p['especificidade']:.2f}".replace('.',','),_f2c(p['ICC21'])] for p in _chP]
_chNa=_chj['preditores_fadiga']['n_alta']; _chNb=_chj['preditores_fadiga']['n_baixa']
_chTopAUC=f"{_chP[0]['AUC']:.2f}".replace('.',','); _chTop2=_chP[1]['label']; _chFadMenICC=_f2c(next(p['ICC21'] for p in _chP if p['var']=='FadMen'))
_chDepICC=_f2c(next(p['ICC21'] for p in _chP if p['var']=='Depressão'))
# acoplamento: pares agudos com p bruto<0.05
_chAgSig=[p for p in _chj['acoplamento']['agudo']['pares'] if p['p_bruto']<0.05]
cpl_n=_chj['acoplamento']['tonico']['n']
try:
    _coer=json.load(open('/home/user/mdlucca/HANDEBOL/tese/resultados_coerencia.json'))
    rowsCOER=[[m['metrica'],str(m['valor']),f"{m['n']}/7 — "+', '.join(m['entregaveis'])] for m in _coer['metricas']]
    _coerN=len(_coer['metricas']); _coerOcc=sum(m['n'] for m in _coer['metricas'])
except Exception:
    rowsCOER=[]; _coerN=0; _coerOcc=0
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

H=f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{CSS}</style></head><body>
<canvas id="rain"></canvas><div class="mesh"></div><div class="cur"></div><div class="cur-ring"></div>

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
 <p>As distribuições são majoritariamente <b>assimétricas e não-normais</b> (efeito piso nas subescalas negativas). Por isso, além dos testes paramétricos, reportam-se os não-paramétricos: as duas famílias <b>concordam em todas as variáveis</b>. A leitura descritiva completa — histogramas, box plots pré×pós, dispersão do eixo energia–fadiga e gráficos Q–Q de normalidade — confirma o deslocamento pré→pós e a não-normalidade que justifica a confirmação por permutação.</p>
 {fig('descrfig','<b>Estatística descritiva.</b> A: histograma da fadiga física (pré vs. pós); B: box plots pré×pós das variáveis-chave; C: dispersão vigor × fadiga (r≈−0,44); D: Q–Q de normalidade do PTH (pré vs. pós, com W de Shapiro–Wilk).')}
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
 <p>Fechando a hierarquia, testou-se a <b>invariância estrita (residual)</b> — fixando, além das cargas, também as variâncias de erro (θ) iguais entre os dois momentos. Como esperado no nível mais restritivo, o ajuste cede um pouco (CFI {_epCFIm} → {_epCFIe}; ΔCFI {_epdCFI}, ΔRMSEA {_epdRMSEA}), ficando <b>no limite</b> do critério ΔCFI ≤ −0,01: a maior parte das variâncias específicas é estável, mas não perfeitamente idêntica pré→pós. O <b>diagnóstico por item</b> localiza a origem da não-invariância: os maiores desvios concentram-se em <b>{_epLib}</b> — o item "Sonolento" (fadiga_3), que carrega o maior resíduo de intercepto e já vinha na contramão do fator, e a incongruência de carga do vigor_4. A <b>invariância parcial</b>, liberando esses dois itens, reduz o viés residual de intercepto de RMS {_epRMSf} para {_epRMSp} (escala de item 0–4): com esses dois parâmetros livres, a equivalência de medida se restabelece e o deslocamento latente pré→pós no eixo energético permanece interpretável como mudança verdadeira de estado. Ou seja, a leve quebra de invariância é <b>local e identificada</b>, não uma falha global do instrumento.</p>
 {fig('investrita','<b>Invariância estrita e parcial.</b> Esquerda: não-invariância por item (|Δλ| de carga e |resíduo de intercepto|; linha de alerta 0,20) — os itens marcados "liberar" são a fonte; direita: CFI combinado ao longo da hierarquia configural → métrica → escalar → estrita.')}
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
 <p>O <b>protocolo de HIIT</b> — 4 × 4 min a <b>104% da velocidade de pico</b> de um teste de campo, com 3 min de intervalo — impôs uma carga quase-máxima e progressiva: a FC de pico das séries chega a <b>~186 bpm</b> (média das séries ~179 bpm), a FC de recuperação (início de cada série, após o intervalo) sobe ao longo da sessão (~124 bpm; deriva cardiovascular, recuperação incompleta) e o PSE final alcança <b>~9,9</b>. As sessões foram equivalentes entre si (FC de pico 184/183/181 bpm nos dias 2/4/7; Friedman n.s.). E, de forma reveladora, a magnitude da carga <b>não</b> prediz a perturbação aguda do humor (r≈−0,05): o custo fisiológico e a resposta psicológica se desacoplam no agudo.</p>
 {fig('hiitprot','<b>Protocolo de HIIT (4 × 4 min a 104% da velocidade de pico, 3 min de intervalo).</b> A: FC ao início (recuperação) e ao fim (pico) de cada série; B: PSE por fase; C: resumo da carga interna — FC máxima, média, de recuperação e PSE.')}
 <div class="two">{fig('pipe_carga_fc_por_fase','<b>FC pré→pós por fase</b> (aquecimento → 4ª série).')}{fig('pipe_carga_pse_fc_sessao','<b>PSE final e FC de pico</b> por sessão.')}</div>
 {fig('pipe_carga_x_humor','<b>Carga interna × humor.</b> PSE médio × Δ PTH agudo por atleta (r≈−0,05, n.s.).')}
 <p>Pela carga por FC (<b>TRIMP</b> de Banister sobre a %HRR), a intensidade foi uniformemente alta (%HRR 0,87–0,91 nas quatro sessões). Sem duração registrada, reporta-se o TRIMP relativo por sessão. Duas leituras convergem com o resto: a carga por FC (TRIMP) e por PSE (Foster) são <b>praticamente independentes</b> neste regime de teto (r≈−0,05), e o TRIMP também <b>não</b> prediz a resposta aguda do humor (r=−0,32; p=0,12).</p>
 {fig('trimp','<b>TRIMP.</b> Carga por sessão (TRIMP vs Foster), concordância entre as duas famílias e TRIMP × resposta do humor.')}
 <p>Reunindo os marcadores por atleta, o <b>acoplamento carga × humor</b> confirma o desacoplamento: nenhum par (PSE, FC, TRIMP × fadiga mental, TMD) é significativo, nem no nível do dia (tônico) nem no agudo — as únicas associações fortes são humor × humor.</p>
 {fig('acopl','<b>Acoplamento carga × humor.</b> Matrizes de correlação entre atletas — tônico (esq.) e agudo (dir.). * p&lt;0,05.')}
</section>

<section>
 <div class="eyebrow">Carga × humor · preditores de fadiga</div><h2>Como PSE, TRIMP e FC se ligam ao perfil de humor — e o que prediz um estado de fadiga</h2>
 <p><b>O quê e por quê.</b> Duas perguntas aplicadas fecham o arco carga→humor. Primeira: a carga interna (PSE, FC de pico, TRIMP) se relaciona com <b>cada</b> dimensão do humor, não só com a fadiga? Segunda: entre todas as variáveis de humor, <b>quais são simultaneamente sensíveis e confiáveis</b> para sinalizar um estado de fadiga alta vs. baixa — a informação que um preparador precisa para decidir carga? Ambas mantêm o <b>atleta como unidade</b> (correlações no nível do atleta, n={cpl_n}), com correção FDR na família de pares e validação por bootstrap agrupado por atleta.</p>
 <p><b>Como PSE, TRIMP e FC se ligam ao humor.</b> Estendendo o acoplamento a todo o perfil (esquerda e centro da figura), o padrão é de <b>desacoplamento</b>: nenhum par carga × humor sobrevive à correção FDR, seja na leitura tônica (média do atleta nos dias de HIIT) ou aguda (Δ pós−pré). Há apenas dois sinais fracos, significativos no p bruto mas não após FDR — no agudo, <b>PSE × Tensão</b> (r = +0,41) e <b>PSE × Confusão</b> (r = +0,40): quando a sessão é percebida como mais dura, sobem transitoriamente a ativação/tensão e a confusão, não a fadiga. A interpretação é coerente com toda a evidência do trabalho e com a literatura de monitoramento: a carga interna <b>prescreve o estímulo</b>, mas a <b>resposta de humor carrega informação que a carga objetiva não captura</b> — exatamente o motivo pelo qual medidas subjetivas superam as objetivas em sensibilidade ao acúmulo de treino (Saw, Main & Gastin, 2016).</p>
 <p><b>Quais variáveis predizem o estado de fadiga.</b> Definindo o alvo como fadiga <b>alta</b> (tercil superior) vs. <b>baixa</b> (tercil inferior) da subescala Fadiga (n = {_chNa}/{_chNb}; PTH excluído por conter aritmeticamente a Fadiga), cada preditor concorrente foi avaliado por AUC (Mann–Whitney, IC95% por bootstrap agrupado por atleta) e, no ponto de Youden, por sensibilidade e especificidade; a <b>confiabilidade</b> foi o ICC(2,1) entre medidas repetidas. A leitura é direta: a <b>fadiga física é o marcador mais sensível</b> (AUC {_chTopAUC}) — seu ICC baixo não é defeito, e sim a assinatura de um bom marcador de <b>estado</b>, que oscila com a carga; a <b>fadiga mental</b> (ICC {_chFadMenICC}) e a <b>depressão</b> (ICC {_chDepICC}) são sensíveis <b>e</b> estáveis, ocupando o quadrante ideal; o <b>vigor</b> é sensível (eixo energético); e a <b>tensão</b>, embora a mais confiável, é <b>cega</b> para fadiga (AUC ≈ 0,54). Por um caminho independente — classificação e ROC —, reencontra-se o eixo energia–fadiga que emergiu dos modelos mistos, da análise fatorial e da invariância.</p>
 {tbl(['Preditor','AUC','IC95%','Sensib.','Especif.','ICC(2,1)'],rowsCH)}
 {fig('cargahumor','<b>Carga interna × perfil de humor e preditores de estado de fadiga.</b> A: acoplamento tônico (nível do atleta); B: acoplamento agudo (Δ pós−pré); † FDR, * p&lt;0,05 bruto. C: sensibilidade (AUC) × confiabilidade (ICC 2,1) de cada preditor — o quadrante superior-direito reúne os marcadores sensíveis e confiáveis.')}
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
 <div class="eyebrow">Discussão integrada</div><h2>Dos objetivos aos achados: uma linha de raciocínio</h2>
 <p>O trabalho perseguiu uma pergunta aplicada e uma metodológica. A aplicada: <b>como um microciclo com HIIT afeta o humor de atletas de handebol de elite</b> — em que magnitude, em quais dimensões, com que confiabilidade de medida e com que utilidade para monitorar e prever. A metodológica: <b>fazê-lo respeitando a estrutura de medidas repetidas</b> (o mesmo atleta medido muitas vezes), condição sem a qual qualquer efeito psicológico pode ser um artefato de pseudo-replicação. Todas as camadas analíticas abaixo servem a essas duas perguntas, e convergem para uma única história.</p>

 <h3>Interpretação estatística — por que acreditamos no efeito</h3>
 <p>A espinha dorsal inferencial são <b>modelos mistos</b> com o atleta como efeito aleatório: eles decompõem a variância em traço (entre atletas), dia e estado (intra-atleta), e é essa decomposição que autoriza falar de "resposta ao treino" sem confundir diferenças estáveis entre pessoas com mudança dentro da pessoa. Sobre essa base, três salvaguardas dão robustez ao veredito: (i) <b>controle de multiplicidade por FDR</b> (Benjamini–Hochberg), porque foram testadas muitas dimensões; (ii) <b>tamanhos de efeito</b> padronizados intra-sujeito (d de Cohen para medidas repetidas, dz) em vez de só valores-p, para separar significância de relevância; e (iii) <b>reamostragem/bootstrap agrupado por atleta</b> para intervalos que herdam a dependência dos dados. O quadro é reforçado por convergência entre famílias que raramente erram juntas: paramétrica (t) e não-paramétrica (Wilcoxon/Friedman) decidem igual, a evidência bayesiana acompanha a frequentista, e a estrutura multivariada (AFC, invariância) sustenta que o instrumento mede o mesmo construto antes e depois. Quando métodos com pressupostos diferentes apontam para o mesmo lugar, o achado é do fenômeno, não do método.</p>

 <h3>Interpretação fisiológica — o custo do estímulo</h3>
 <p>Fisiologicamente, as sessões de HIIT foram <b>quase-máximas</b>: FC de pico de 181–184 bpm, %HRR de 0,87–0,91 e PSE final junto ao teto da escala (9,3–9,6). O corpo pagou um preço alto e homogêneo. A resposta que melhor traduz esse custo no plano do humor é a <b>fadiga física</b>, que sobe com efeito grande (dz ≈ 1,0), acumula ao longo da semana e é a única dimensão amplificada pelo HIIT no agudo — a assinatura psicofísica esperada de um estímulo glicolítico intenso e repetido. O achado fisiologicamente mais informativo, porém, é um <b>desacoplamento</b>: a magnitude da carga interna (PSE, TRIMP, FC) <b>não</b> prediz a perturbação aguda do humor (r ≈ −0,05 no agudo; nada sobrevive à FDR no acoplamento). Num regime de teto, em que todos treinam perto do máximo, a variação relevante do humor deixa de ser explicada pelo custo cardiovascular e passa a depender de fatores individuais de tolerância e recuperação — o que é coerente com a validade ecológica do método sessão-PSE como marcador de <b>estímulo</b>, não de <b>resposta</b> (Haddad et al., 2017).</p>

 <h3>Interpretação psicológica — o humor como estado no eixo energia–fadiga</h3>
 <p>Psicologicamente, a mudança pré→pós é um <b>deslocamento de estado sobre o eixo energia–fadiga</b>: o vigor achata e a fadiga sobe, enquanto tensão, depressão, raiva e confusão quase não se movem — uma <b>erosão do perfil "iceberg"</b> clássico de atletas (Morgan). Que se trata de estado, e não de artefato de medida, é o que a hierarquia de invariância demonstra: a invariância métrica sustenta-se (ΔCFI −0,004 no modelo conjunto; congruência de Tucker φ 0,992), a escalar é aproximada e a estrita fica no limite, com a quebra <b>localizada</b> em um único item — o "Sonolento", que se comporta na contramão (a sonolência <b>cai</b> pós-treino, dz −0,55: o exercício agudo é ativador). O deslocamento da média latente recai exatamente sobre fadiga (+0,56) e vigor (−0,26). Ou seja: o HIIT não muda o significado do questionário; muda o <b>estado</b> que ele mede — e o muda no eixo previsto pela teoria. A leitura casa com a literatura de resposta afetiva ao exercício intenso, em que tensão e depressão tendem a recuar após protocolos intervalados enquanto a resposta afetiva global é modulada pela intensidade e pelo desenho da sessão (Marques et al., 2020; Patten et al., 2022).</p>

 <h3>As perguntas aplicadas, respondidas</h3>
 <p><b>Como o HIIT influencia o humor dos atletas?</b> Ele produz uma resposta <b>real, dirigida e específica</b>: reduz o vigor e eleva a fadiga (sobretudo física), sem inflar as dimensões negativas de tensão/depressão/raiva; o efeito acumula ao longo do microciclo, com pico no dia mais distante da recuperação, e é <b>fortemente individual</b> — há respondedores e não-respondedores, razão pela qual a média esconde tanto quanto revela. <b>Quais variáveis são mais sensíveis e confiáveis para predizer um estado de fadiga alta vs. baixa?</b> A <b>fadiga física</b> é o marcador mais <b>sensível</b> (AUC 0,90); sua baixa estabilidade (ICC 0,28) é a marca de um bom sinal de estado, que deve oscilar com a carga. A <b>fadiga mental</b> e a <b>depressão</b> combinam sensibilidade com estabilidade (ICC 0,72 e 0,79) — úteis quando se quer um marcador confiável dia a dia. O <b>vigor</b> é sensível pelo lado da energia; a <b>tensão</b>, apesar de a mais confiável, é praticamente <b>cega</b> à fadiga. <b>Como PSE, TRIMP e FC se relacionam com o perfil de humor?</b> Fracamente e sem sobreviver à correção — a carga interna define o quanto se treina, mas o humor carrega informação adicional que a carga objetiva não vê; daí a superioridade das medidas subjetivas no monitoramento da resposta ao treino (Saw, Main & Gastin, 2016). Esse desacoplamento não é peculiaridade da amostra: uma revisão sistemática recente de autorrelatos de item único em esportes coletivos encontrou associações com a carga que vão de nulas a, no máximo, moderadas (Duignan et al., 2020); e nossos <b>testes de equivalência (TOST)</b> formalizam o ponto — para os índices centrais, a associação carga↔humor e o contraste HIIT-vs-sem são estatisticamente <b>equivalentes a zero</b>, não apenas "não significativos". A ênfase na fadiga — física e mental — tampouco é arbitrária: revisões e meta-análises recentes mostram que a fadiga mental prejudica de forma consistente o desempenho técnico e físico em esportes coletivos (Yuan et al., 2023; Grgic, Mikulic &amp; Mikulic, 2022), o que dá valor prático a um marcador sensível e confiável desse estado.</p>

 <h3>Limites, derivadas e curvas ROC — o que essas ferramentas acrescentam</h3>
 <p>Três ferramentas menos usuais foram incluídas para responder <b>como</b> a fadiga evolui, e não só <b>se</b> ela muda. Os <b>limites e derivadas</b> tratam a trajetória de fadiga ao longo do microciclo como uma função do tempo: a <b>primeira derivada</b> (velocidade de acúmulo) é positiva e maior em torno dos dias de HIIT, e a leitura de <b>limite</b> (o valor para o qual a fadiga tende ao fim da semana) formaliza a noção de saturação/teto. As <b>curvas ROC</b> traduzem a questão de "separar estados": para distinguir o pós do pré-treino, só a fadiga física alcança discriminação moderada (AUC 0,70), e para distinguir um dia de HIIT de um dia sem HIIT <b>nenhuma</b> variável isolada passa de AUC ≈ 0,58 — porque a variabilidade individual domina a classificação num único dia. A ROC das <b>derivadas</b> fecha o argumento com um achado contra-intuitivo e importante: a <b>taxa de variação diagnostica menos que o nível</b> (o ganho da derivada sobre o nível é nulo ou negativo). Em termos práticos, monitorar "quão cansado o atleta está" é mais informativo do que "quão rápido ele está ficando cansado" — a derivada amplifica ruído de medida. Esse é o tipo de conclusão que só emerge quando se leva o cálculo a sério sobre dados ruidosos e agrupados.</p>

 <h3>Pontos fortes, validade e impactos</h3>
 <p><b>Pontos fortes.</b> A disciplina de <b>atleta-como-unidade</b> em todas as camadas; a <b>triangulação</b> por métodos independentes (frequentista, bayesiano, multivariado, classificação, cálculo); a caracterização psicométrica completa (confiabilidade, AFC, AFE, TRI, invariância configural→estrita/parcial); e a <b>reprodutibilidade</b> ponta-a-ponta por código. <b>Validade.</b> A <b>convergente</b> aparece na correlação intra-sujeito entre o BRUMS e autorrelatos externos (fadiga física r +0,64; estado físico −0,65); a <b>de construto</b>, na invariância de medida pré→pós; a <b>de critério/diagnóstica</b>, nas AUC. <b>Impactos positivos:</b> um protocolo de monitoramento parcimonioso e barato — bastam a fadiga física (sensível) e a fadiga mental/depressão (estáveis) para sinalizar acúmulo —, com base de evidência para individualizar carga e recuperação. <b>Impactos/limites negativos a declarar honestamente:</b> a resposta é tão individual que decisões baseadas na média do grupo podem prejudicar subgrupos; o desacoplamento carga–humor significa que a FC/TRIMP <b>não</b> substituem o autorrelato; e o efeito de teto da carga limita a generalização para microciclos de menor intensidade.</p>

 <h3>Limitações e direções futuras</h3>
 <p><b>Limitações.</b> Delineamento <b>observacional</b> (sem randomização; associações, não causalidade); amostra de 27 atletas de um único contexto de elite, o que limita poder para efeitos individuais e generalização; ausência de <b>duração</b> registrada das sessões (o TRIMP é relativo, por %HRR); um efeito de <b>teto</b> na carga que comprime a variância explicativa; itens com <b>efeito piso</b> (tensão, confusão) que degeneram em partes da modelagem multivariada; e a sonolência medida por um único item, sem escala de sono dedicada. <b>Direções futuras.</b> (1) desenhos com <b>manipulação</b> da carga (dias pareados de alta vs. baixa intensidade) para testar causalidade; (2) séries temporais mais densas por atleta, que viabilizem modelos dinâmicos individuais e o mapeamento de <b>não-respondedores</b>; (3) uma <b>escala de sono/alerta</b> separada, dado que o eixo sono↔alerta se mostrou ortogonal à fadiga; (4) integração de marcadores objetivos de recuperação (VFC, sono actigráfico) para testar se explicam a variância individual que a carga não captura; e (5) validação prospectiva do protocolo de monitoramento parcimonioso (fadiga física + fadiga mental/depressão) contra desfechos de desempenho e lesão.</p>

 <h3>Síntese</h3>
 <p>Em uma frase: <b>o microciclo com HIIT desloca o humor de atletas de elite de forma real e específica sobre o eixo energia–fadiga — erodindo o vigor e elevando a fadiga física —, um efeito de estado (não de medida), fortemente individual e não redutível ao custo cardiovascular da sessão; e o monitoramento eficiente desse estado depende de escolher os marcadores certos: a fadiga física pela sensibilidade, a fadiga mental e a depressão pela confiabilidade.</b> Cada camada analítica — descritiva, mista, multivariada, invariância, cálculo, ROC, preditiva e acoplamento — chega, por caminhos distintos, à mesma conclusão, o que é a melhor evidência de que ela descreve o fenômeno e não o método.</p>
</section>

<section>
 <div class="eyebrow">11 · Reprodutibilidade</div><h2>Pipeline automatizado</h2>
 <p>Todas as análises são reproduzíveis com um comando: dezesseis nós encadeados levam da coleta bruta às tabelas, gráficos, Excel, PDF, relatório e à regeneração do sistema analista interativo. Um gatilho Cron reprocessa tudo a cada nova coleta.</p>
 {fig('workflow','<b>Pipeline (estilo N8N).</b> Início/Cron → ingestão → análises → carga interna → gráficos → exportação → app analista → relatório.')}
 <h3>Coerência entre entregáveis</h3>
 <p>Como todos os entregáveis são gerados por código a partir da <b>mesma fonte</b> (as bases reproduzidas e os JSON dos módulos), os números-chave são idênticos por construção. Uma verificação de <b>coerência cruzada</b> rastreou {_coerN} números-âncora nos sete entregáveis (artigo, documento, manuscrito, central, dashboard, showcase e síntese), confirmando {_coerOcc} ocorrências <b>consistentes</b>, sem divergências — as ausências correspondem apenas a métricas não citadas naquele material (não a valores conflitantes).</p>
 {tbl(['Métrica-âncora','Valor','Entregáveis que citam'],rowsCOER)}
 <p class="note">Divergências aparentes entre módulos correspondem a <b>índices distintos</b> (ex.: a congruência de Tucker φ do módulo de confiabilidade, 0,987, e a do multigrupo, 0,992), e não a inconsistências. Reproduzível: <span style="font-family:var(--mono)">python coerencia_cruzada.py</span>.</p>
 <h3>Conclusão</h3>
 <p>Os planos psicométrico e analítico convergem em cinco pontos. <b>(1)</b> A resposta mora no eixo energia–fadiga: a fadiga física — a variável mais confiável e sem piso — é a de maior resposta aguda (dz ≈ 1), maior acúmulo semanal e a única amplificada pelo HIIT no agudo; a inércia das negativas é efeito piso, não ausência de fenômeno. <b>(2)</b> É mudança de <b>estado</b>, não de medida (invariância métrica sustentada; escalar aproximada; estrita no limite, com quebra local no "Sonolento"). <b>(3)</b> É <b>fortemente individual</b> — a maior parte da variância é traço e só uma minoria de atletas atinge mudança confiável (RCI acima da mínima mudança detectável), o que desqualifica decisões pela média do grupo. <b>(4)</b> O <b>desacoplamento</b> carga↔humor é formal (equivalência por TOST): FC/TRIMP não substituem o autorrelato (Saw et al., 2016; Duignan et al., 2020). <b>(5)</b> O monitoramento eficiente combina a <b>fadiga física</b> (sensibilidade) e a <b>fadiga mental/depressão</b> (confiabilidade) — marcadores cujo valor prático é reforçado pelo impacto da fadiga mental no desempenho (Yuan et al., 2023). Tudo respeitando a estrutura de medidas repetidas — a contribuição metodológica central do trabalho.</p>
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

# animação padrão Showcase: chuva neon + cursor (sem % para não colidir com o format)
_anim='<script>(function(){var R=matchMedia("(prefers-reduced-motion:reduce)").matches,F=matchMedia("(hover:hover) and (pointer:fine)").matches;var cv=document.getElementById("rain"),ctx=cv&&cv.getContext("2d"),d=[],P=Math.min(devicePixelRatio||1,2);function S(){cv.width=innerWidth*P;cv.height=innerHeight*P;ctx.setTransform(P,0,0,P,0,0);var n=Math.round(innerWidth/11);d=[];for(var i=0;i<n;i++)d.push(mk());}function mk(){return{x:Math.random()*innerWidth,y:Math.random()*innerHeight,l:12+Math.random()*22,v:3+Math.random()*5,c:Math.random()<0.5?"#22d3ee":(Math.random()<0.5?"#7c5cff":"#ff4d6d"),a:0.1+Math.random()*0.28};}function dr(){ctx.clearRect(0,0,innerWidth,innerHeight);ctx.lineWidth=1.3;for(var i=0;i<d.length;i++){var o=d[i];ctx.strokeStyle=o.c;ctx.globalAlpha=o.a;ctx.beginPath();ctx.moveTo(o.x,o.y);ctx.lineTo(o.x,o.y+o.l);ctx.stroke();o.y+=o.v;if(o.y>innerHeight){o.y=-o.l;o.x=Math.random()*innerWidth;}}ctx.globalAlpha=1;requestAnimationFrame(dr);}if(cv&&!R){S();addEventListener("resize",S);dr();}else if(cv){cv.style.display="none";}if(F){var dt=document.querySelector(".cur"),rg=document.querySelector(".cur-ring");document.body.style.cursor="none";var mx=innerWidth/2,my=innerHeight/2,rx=mx,ry=my;addEventListener("pointermove",function(e){mx=e.clientX;my=e.clientY;dt.style.left=mx+"px";dt.style.top=my+"px";if(R){rg.style.left=mx+"px";rg.style.top=my+"px";}});if(!R){(function lp(){rx+=(mx-rx)*0.18;ry+=(my-ry)*0.18;rg.style.left=rx+"px";rg.style.top=ry+"px";requestAnimationFrame(lp);})();}var H="a,button,figure,.kpi,.tag";document.addEventListener("pointerover",function(e){if(e.target.closest(H))rg.classList.add("hot");});document.addEventListener("pointerout",function(e){if(e.target.closest(H))rg.classList.remove("hot");});}})();</script>'
# injeta toolbar + sumário logo antes da primeira seção; script antes de </body>
H=H.replace('<section id="s1"', _toolbar+_toc_html+'\n<section id="s1"', 1)
H=H.replace('</body></html>', _script+_anim+'</body></html>', 1)

open('/tmp/documento.html','w').write(H)
print('documento.html:', os.path.getsize('/tmp/documento.html')//1024,'KB')
