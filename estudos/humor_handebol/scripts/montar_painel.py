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

# 3. título e ordem
if 'modelos:[' not in s:
    s=s.replace(" auditoria:['Auditoria de procedência'",
      " modelos:['Modelos e CRISP-DM','Árvores de decisão sobre a base, e o estudo mapeado nas seis fases'],\n auditoria:['Auditoria de procedência'",1)
s=s.replace("const ordem=['visao','mapa','a1','a2','auditoria','base','refs','automacao'];",
            "const ordem=['visao','mapa','a1','a2','modelos','auditoria','base','refs','automacao'];")

# 4. corpo da tela
tela=open(os.path.join(RAIZ,"painel","_tela_modelos.js"),encoding='utf-8').read()
INI='/* <<< tela modelos >>> */'; FIM='/* <<< fim tela modelos >>> */'
bloco=INI+'\n'+tela+'\n'+FIM
if INI in s:
    s=re.sub(re.escape(INI)+r'.*?'+re.escape(FIM), lambda m: bloco, s, flags=re.S)
else:
    anc='/* ============================ roteamento ============================ */'
    k=s.index(anc); s=s[:k]+bloco+'\n\n'+s[k:]

open(P,'w',encoding='utf-8').write(s)
print(f"painel montado: {orig/1024:.0f} KB → {len(s)/1024:.0f} KB")
for t in ['modelos','auditoria','base']:
    marca='data-tela="%s"'%t
    print("   tela %-10s nav=%s  título=%s"%(t, marca in s, (t+":[") in s))
