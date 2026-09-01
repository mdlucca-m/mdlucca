# -*- coding: utf-8 -*-
"""Reinjeta os dados e as telas adicionais no painel, de forma idempotente.

O painel é um arquivo único. Este montador troca três coisas no lugar:
  1. o bloco window.__DADOS__, a partir de painel/dados.json;
  2. o botão de navegação, o título e a ordem de teclado da tela de modelos;
  3. o corpo da tela, a partir de painel/_tela_modelos.js.
Rodar duas vezes produz o mesmo arquivo.
"""
import os, re, json
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P=os.path.join(RAIZ,"painel","painel.html")
s=open(P,encoding='utf-8').read(); orig=len(s)

# 1. dados
d=open(os.path.join(RAIZ,"painel","dados.json"),encoding='utf-8').read().strip()
i=s.index('window.__DADOS__='); j=s.index('</script>',i)
s=s[:i]+'window.__DADOS__='+d+';'+s[j:]

# 2. navegação
BOTAO='''      <div class="grupo">Modelos</div>
      <button data-tela="modelos">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 3v5M12 8 6 12v3M12 8l6 4v3"/><circle cx="12" cy="3" r="1.6"/><rect x="3" y="15" width="6" height="5" rx="1.5"/><rect x="15" y="15" width="6" height="5" rx="1.5"/></svg>
        <span class="rot">Modelos e CRISP-DM</span></button>
'''
if 'data-tela="modelos"' not in s:
    a=s.index('      <div class="grupo">Evidência</div>')
    s=s[:a]+BOTAO+s[a:]

BOTAO_Q='''      <button data-tela="qualidade">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 19V5M4 19h16"/><rect x="7" y="11" width="3" height="5" rx="1"/><rect x="12" y="8" width="3" height="8" rx="1"/><path d="M17.5 6.5 20 9l-2.5 2.5"/></svg>
        <span class="rot">Qualidade e otimização</span></button>
'''
if 'data-tela="qualidade"' not in s:
    a=s.index('      <button data-tela="base">')
    s=s[:a]+BOTAO_Q+s[a:]
if 'qualidade:[' not in s:
    s=s.replace(" base:['Base de dados'",
      " qualidade:['Qualidade dos dados e otimização da carga','Auditoria do dado em si, exploratória univariada e programação linear'],\n base:['Base de dados'",1)

# 3. título e ordem
if 'modelos:[' not in s:
    s=s.replace(" auditoria:['Auditoria de procedência'",
      " modelos:['Modelos e CRISP-DM','Árvores de decisão sobre a base, e o estudo mapeado nas seis fases'],\n auditoria:['Auditoria de procedência'",1)
import re as _re
s=_re.sub(r"const ordem=\[[^\]]*\];",
          "const ordem=['visao','mapa','a1','a2','modelos','auditoria','qualidade','base','refs','automacao'];", s)

# 3b. correções pontuais nas telas originais, todas idempotentes
PATCHES=[
 # a tabela de gravidade não previa os achados de qualidade
 ("const GRAV={'crítica':'cr','alta':'cr','média':'at','baixa':'neu'};",
  "const GRAV={'crítica':'cr','alta':'cr','média':'at','baixa':'neu','nenhuma':'bom','método':'neu'};"),
 # o título falava em seis achados; agora são doze, de duas passagens
 ("c2.append(el('h3',{txt:'Os seis achados e o que foi feito com cada um'}));",
  "c2.append(el('h3',{txt:`Os ${D.auditoria.length} achados e o que foi feito com cada um`}),\n"
  "    el('p',{class:'leg',txt:'D1 a D6 vêm da auditoria de procedência, que pergunta de onde vem cada número. "
  "Q1 a Q6 vêm da auditoria de qualidade, que pergunta se o número está certo. A tela de qualidade abre cada "
  "um deles.'}));"),
 # o mapa de navegação não listava as duas telas novas
 ("""   ['auditoria','Auditoria','As quatro unidades de análise e os seis achados com correção e impacto','#E0952B'],""",
  """   ['modelos','Modelos e CRISP-DM','Árvore de decisão sobre a base, desempenho contra as linhas de base, diagnóstico de reversão à média e as seis fases do CRISP-DM','#8A4FBF'],
   ['qualidade','Qualidade e otimização','Auditoria do dado em si, exploratória univariada por tipo de variável, triagem de discrepantes e a programação linear da carga','#0F6E5C'],
   ['auditoria','Auditoria','As quatro unidades de análise e os doze achados das duas passagens, com correção e impacto','#E0952B'],"""),
 # a cadeia passou de seis a oito etapas
 ("""   ['5 · acervo e busca','recolhe as 218 abas das planilhas, resolve os DOI, indexa a busca','#C1440E'],
   ['6 · figuras e artigos','gera as 15 figuras e monta os dois documentos','#8A4FBF']];""",
  """   ['5 · acervo e busca','recolhe as 218 abas das planilhas, resolve os DOI, indexa a busca','#C1440E'],
   ['6 · qualidade e otimização','audita o dado desde o item, reconfere os três documentos e resolve o programa linear da carga','#0F6E5C'],
   ['7 · modelos','árvores, floresta, XGBoost, diagnóstico de reversão à média e o mapa CRISP-DM','#8A4FBF'],
   ['8 · figuras e documentos','gera as 21 figuras e monta os quatro documentos','#A31E52']];"""),
 ("el('p',{class:'leg',txt:'Da planilha de origem ao .docx dos dois artigos, sem etapa manual.'})",
  "el('p',{class:'leg',txt:'Da planilha de origem ao .docx dos quatro documentos, sem etapa manual.'})"),
]
for velho,novo in PATCHES:
    if novo in s: continue
    if velho not in s:
        raise SystemExit(f"trecho a corrigir não encontrado no painel: {velho[:70]}…")
    s=s.replace(velho,novo,1)

# 4. corpo das telas adicionais
for arq,marca in [("_tela_modelos.js","modelos"),("_tela_qualidade.js","qualidade")]:
    tela=open(os.path.join(RAIZ,"painel",arq),encoding='utf-8').read()
    INI=f'/* <<< tela {marca} >>> */'; FIM=f'/* <<< fim tela {marca} >>> */'
    bloco=INI+'\n'+tela+'\n'+FIM
    if INI in s:
        s=re.sub(re.escape(INI)+r'.*?'+re.escape(FIM), lambda m: bloco, s, flags=re.S)
    else:
        anc='/* ============================ roteamento ============================ */'
        k=s.index(anc); s=s[:k]+bloco+'\n\n'+s[k:]

open(P,'w',encoding='utf-8').write(s)
print(f"painel montado: {orig/1024:.0f} KB → {len(s)/1024:.0f} KB")
for t in ['modelos','qualidade','auditoria','base']:
    marca='data-tela="%s"'%t
    print("   tela %-10s nav=%s  título=%s"%(t, marca in s, (t+":[") in s))
