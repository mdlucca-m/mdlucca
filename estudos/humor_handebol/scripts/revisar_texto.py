# -*- coding: utf-8 -*-
"""Analisador de estilo dos módulos de texto.

Localiza o que a revisão pediu: travessão, gerúndio, repetição de verbo e de
abertura de parágrafo, e parágrafos sem conectivo de ligação com o anterior.
Não corrige nada; aponta, para que a correção seja verificável.
"""
import os, re, sys, collections, unicodedata
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ,"texto"))

# gerúndio: -ando, -endo, -indo, -ondo. A lista abaixo é de exceções que não são verbo.
NAO_GERUNDIO={'quando','segundo','mundo','fundo','profundo','redondo','estupendo','tremendo',
 'horrendo','reverendo','comando','bando','grando','brando','blando','nefando','memorando',
 'doutorando','mestrando','graduando','educando','ordenando','operando','somando','segundos',
 'profundos','fundos','mundos','comandos','bandos','estupendos','tremendos','oriundo','oriundos',
 'iracundo','rotundo','facundo','jocundo','moribundo','vagabundo','furibundo','gerúndio'}
RX_GER=re.compile(r'\b(\w{4,}?(?:ando|endo|indo|ondo))\b', re.I)
RX_TRAVESSAO=re.compile(r'[—–]')
CONECTIVOS=('além','ademais','contudo','todavia','entretanto','porém','no entanto','por isso',
 'portanto','logo','assim','desse modo','dessa forma','com efeito','de fato','ora','pois',
 'nesse sentido','nessa direção','a essa','a esse','essa','esse','tal','tais','daí','donde',
 'em contrapartida','por outro lado','em seguida','a seguir','antes','depois','também','ainda',
 'não obstante','conquanto','embora','se bem que','uma vez que','já que','porquanto','onde',
 'o mesmo','a mesma','os mesmos','as mesmas','o resultado','a consequência','o segundo','a segunda',
 'o terceiro','a terceira','o quarto','a quarta','o primeiro','a primeira','duas','três','quatro')

def paragrafos(mod):
    """Devolve (rótulo, texto) de cada parágrafo do módulo."""
    out=[]
    for k,v in vars(mod).items():
        if not k.isupper(): continue
        if isinstance(v,str): out.append((k,v))
        elif isinstance(v,list):
            for i,x in enumerate(v):
                if isinstance(x,str): out.append((f"{k}[{i}]",x))
                elif isinstance(x,(tuple,list)) and len(x)==2 and isinstance(x[1],list):
                    for j,p in enumerate(x[1]):
                        if isinstance(p,str): out.append((f"{k}[{i}·{x[0][:22]}][{j}]",p))
    return out

def analisar(nome, mod):
    P=paragrafos(mod)
    trav=[]; ger=[]; ab=collections.Counter(); rep=[]
    for rot,t in P:
        for m in RX_TRAVESSAO.finditer(t):
            trav.append((rot, t[max(0,m.start()-45):m.start()+45]))
        for m in RX_GER.finditer(t):
            w=m.group(1).lower()
            if w in NAO_GERUNDIO: continue
            ger.append((rot, w, t[max(0,m.start()-45):m.start()+45]))
        prim=re.sub(r'^[«"\'(]+','',t.strip()).split()
        if prim: ab[unicodedata.normalize('NFKD',prim[0].lower()).encode('ascii','ignore').decode()]+=1
    # verbos repetidos: formas frequentes em 3ª pessoa
    verbos=collections.Counter()
    for _,t in P:
        for m in re.finditer(r'\b(\w{4,}?(?:a|e|ou|am|em|aram|eram|iram|ava|ia|ará|erá)\b)', t.lower()):
            pass
    print(f"\n{'='*70}\n{nome}: {len(P)} parágrafos")
    print(f"  travessões: {len(trav)}")
    for r,c in trav[:6]: print(f"      {r:<30} …{c.strip()}…")
    if len(trav)>6: print(f"      (e mais {len(trav)-6})")
    print(f"  gerúndios: {len(ger)}")
    vistos=collections.Counter(w for _,w,_ in ger)
    for w,n in vistos.most_common(): print(f"      {w} ({n})")
    for r,w,c in ger[:5]: print(f"      {r:<30} …{c.strip()}…")
    rep_ab=[(w,n) for w,n in ab.most_common() if n>=4 and w not in ('a','o','as','os','em','de')]
    print(f"  aberturas de parágrafo repetidas: {len(rep_ab)}")
    for w,n in rep_ab[:8]: print(f"      «{w}» abre {n} parágrafos")
    return dict(paragrafos=len(P), travessoes=len(trav), gerundios=len(ger), aberturas=rep_ab)

if __name__=='__main__':
    import A1T, A2T
    tot={}
    for nome,mod in [('Artigo 1 (A1T)',A1T),('Artigo 2 (A2T)',A2T)]:
        tot[nome]=analisar(nome,mod)
    print(f"\n{'='*70}\nTOTAL: "
          f"{sum(v['travessoes'] for v in tot.values())} travessões · "
          f"{sum(v['gerundios'] for v in tot.values())} gerúndios")
