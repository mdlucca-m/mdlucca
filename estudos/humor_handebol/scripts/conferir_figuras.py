# -*- coding: utf-8 -*-
"""Confere as chamadas de figura e de tabela no corpo do texto contra as
legendas efetivamente numeradas no documento montado.

Toda referência do tipo «Figura N» ou «Tabela N» no corpo é confrontada com a
legenda de número N. A rotina imprime o par para inspeção e acusa referência a
número inexistente. Erro de cruzamento é a classe de defeito mais fácil de
introduzir quando se acrescenta uma figura no meio de um manuscrito.
"""
import zipfile, re, os, sys, collections
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S=os.path.join(RAIZ,"saida")
DOCS=["ARTIGO_1_DESCRITIVO_HUMOR_HANDEBOL.docx","ARTIGO_2_INFERENCIAL_HUMOR_HANDEBOL.docx",
      "ANEXO_MODELAGEM_CRISP_DM.docx","AUDITORIA_QUALIDADE_E_OTIMIZACAO.docx"]
falhas=0
for nome in DOCS:
    cam=os.path.join(S,nome)
    if not os.path.exists(cam): continue
    x=zipfile.ZipFile(cam).read('word/document.xml').decode('utf-8')
    t=re.sub(r'<[^>]+>','',re.sub(r'</w:p>','\n',x))
    LEG={}
    for l in t.split('\n'):
        m=re.match(r'^(Figura|Tabela|Quadro)\s+(\d+)\s*[–-]\s*(.+)$', l.strip())
        if m: LEG[(m.group(1), int(m.group(2)))]=m.group(3)
    print(f"\n{'='*78}\n{nome}")
    print(f"  legendas: " + ", ".join(f"{k[0]} 1..{max(n for (tp,n) in LEG if tp==k[0])}"
                                      for k in sorted({(a,) for a,_ in LEG})) )
    refs=collections.Counter()
    for l in t.split('\n'):
        if re.match(r'^(Figura|Tabela|Quadro)\s+\d+\s*[–-]', l.strip()): continue   # é legenda
        for m in re.finditer(r'\b(Figura|Tabela|Quadro)s?\s+(\d+)', l):
            refs[(m.group(1), int(m.group(2)))]+=1
    for (tp,n),q in sorted(refs.items()):
        cap=LEG.get((tp,n))
        if cap is None:
            print(f"  ✗ {tp} {n} citada {q}× e não existe no documento"); falhas+=1
        else:
            print(f"  · {tp} {n} ({q}×) → {cap[:88]}")
    orfas=[k for k in LEG if k not in refs]
    for tp,n in sorted(orfas):
        print(f"  ! {tp} {n} existe e nunca é citada no corpo: {LEG[(tp,n)][:70]}")
print(f"\n{'='*78}\nreferências a número inexistente: {falhas}")
sys.exit(1 if falhas else 0)
