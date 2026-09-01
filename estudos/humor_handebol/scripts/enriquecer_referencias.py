# -*- coding: utf-8 -*-
"""Resolve DOI (Crossref) e PMID (PubMed) para cada referência e grava na base.
Nada é inventado: o que não for encontrado fica nulo e assim aparece no painel."""
import json, re, sqlite3, os, sys, time, urllib.parse, urllib.request, unicodedata
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(RAIZ,"texto"))
import REFS as ET   # ET.REFS: a lista canônica de referências
UA={'User-Agent':'estudo-humor-handebol/1.0 (pesquisa academica)'}
def pega(url, t=25):
    req=urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=t) as r: return json.loads(r.read().decode())
def partes(ref):
    doi=None
    m=re.search(r'DOI:\s*([^\s.]+(?:\.[^\s.]+)*)', ref)
    if m: doi=m.group(1).rstrip('.')
    ano=None
    a=re.findall(r'\b(19|20)\d{2}\b', ref)
    m2=re.findall(r'\b((?:19|20)\d{2})\b', ref)
    if m2: ano=int(m2[-1])
    # título: entre o fim dos autores (primeiro '. ' após maiúsculas) e o próximo '. '
    corpo=re.sub(r'\s*DOI:.*$','',ref)
    m3=re.match(r'^(.*?[a-z]\.)\s+(.+?)\.\s', corpo)
    tit=m3.group(2) if m3 else corpo[:120]
    tit=re.sub(r'\s+',' ',tit).strip()
    return doi, tit, ano
def crossref(tit, ano):
    q=urllib.parse.quote(tit[:220])
    url=f"https://api.crossref.org/works?query.bibliographic={q}&rows=3&select=DOI,title,container-title,issued,is-referenced-by-count"
    try: d=pega(url)
    except Exception as e: return None,None
    def nn(s): return re.sub(r'[^a-z0-9 ]','',unicodedata.normalize('NFKD',s.lower()).encode('ascii','ignore').decode())
    alvo=nn(tit)
    for it in d.get('message',{}).get('items',[]):
        t=(it.get('title') or [''])[0]
        if not t: continue
        if nn(t)[:60]==alvo[:60] or alvo[:45] in nn(t) or nn(t)[:45] in alvo:
            y=None
            try: y=it['issued']['date-parts'][0][0]
            except Exception: pass
            if ano and y and abs(y-ano)>2: continue
            return it['DOI'], (it.get('container-title') or [''])[0]
    return None,None
def pubmed(tit, doi):
    for termo in ([f'{doi}[DOI]'] if doi else [])+[f'{tit[:150]}[Title]']:
        try:
            d=pega("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term="
                   +urllib.parse.quote(termo))
            ids=d.get('esearchresult',{}).get('idlist',[])
            if ids: return ids[0]
        except Exception: pass
        time.sleep(.4)
    return None
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite"))
cx.execute("DELETE FROM referencia")
achou_doi=achou_pmid=0
for i,ref in enumerate(ET.REFS,1):
    doi,tit,ano=partes(ref)
    veic=None
    if not doi:
        doi,veic=crossref(tit,ano); time.sleep(.3)
    pmid=pubmed(tit,doi)
    if doi: achou_doi+=1
    if pmid: achou_pmid+=1
    aut=ref.split('.')[0]
    cx.execute("""INSERT INTO referencia (id,autores,ano,titulo,veiculo,doi,url_doi,pubmed,url_pubmed,
                  open_access,url_oa,abnt,usada_em) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (i,aut,ano,tit,veic,doi,(f"https://doi.org/{doi}" if doi else None),pmid,
       (f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None),
       None,None,ref,'ambos'))
    print(f"  [{i:2}/{len(ET.REFS)}] {'DOI ok ' if doi else 'sem DOI'} {'PMID ok' if pmid else '       '}  {tit[:62]}")
cx.commit()
print(f"\nreferências: {len(ET.REFS)} | com DOI: {achou_doi} | com PubMed: {achou_pmid}")
cx.close()
