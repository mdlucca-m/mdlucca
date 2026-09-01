# -*- coding: utf-8 -*-
"""Casa os resultados de busca de literatura com a lista de referências e grava DOI/links.
Só aceita casamento com similaridade alta; o que não casar fica nulo."""
import json, os, re, sys, glob, sqlite3, difflib, unicodedata
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,"/tmp/claude-0/-home-user-mdlucca/4ddb0907-77b2-5876-a286-ef4b6b886e93/scratchpad")
import ET
DIR=os.environ.get("HH_TOOLRES","/root/.claude/projects/-home-user-mdlucca/"
                   "4ddb0907-77b2-5876-a286-ef4b6b886e93/tool-results")
def nn(s):
    s=unicodedata.normalize('NFKD',str(s).lower()).encode('ascii','ignore').decode()
    return re.sub(r'[^a-z0-9 ]',' ',re.sub(r'\s+',' ',s)).strip()
def partes(ref):
    m=re.search(r'DOI:\s*(10\.[^\s,;]+)', ref); doi=m.group(1).rstrip('.') if m else None
    anos=re.findall(r'\b((?:19|20)\d{2})\b', re.sub(r'DOI:.*$','',ref))
    ano=int(anos[-1]) if anos else None
    corpo=re.sub(r'\s*DOI:.*$','',ref).strip()
    segs=re.split(r'(?<=[a-z\)\]])\.\s+|(?<=\.)\s+(?=[A-ZÀ-Ÿ][a-zà-ÿ])', corpo)
    def eh_autor(s):
        L=[c for c in s if c.isalpha()]
        return (not L) or sum(1 for c in L if c.isupper())/len(L)>0.55 or s.strip().endswith('et al')
    i=0
    while i<len(segs) and eh_autor(segs[i]): i+=1
    tit=re.sub(r'^[A-ZÀ-Ÿ][A-ZÀ-Ÿ ,.;]+\s','', (segs[i] if i<len(segs) else corpo[:120]))
    return doi, re.sub(r'\s+',' ',tit).strip(' .'), ano
# ---- coleta de candidatos dos arquivos salvos ----
cands=[]
for p in glob.glob(os.path.join(DIR,"*")):
    try: bruto=open(p,encoding='utf-8').read()
    except Exception: continue
    # alguns arquivos guardam o JSON escapado dentro de um campo de texto
    if '\\"doi\\"' in bruto:
        try: bruto=''.join(b.get('text','') for b in json.loads(bruto)) or bruto
        except Exception: bruto=bruto.replace('\\"','"').replace('\\n','\n')
    for m in re.finditer(r'\{[^{}]*"doi"\s*:\s*"([^"]+)"[^{}]*?"title"\s*:\s*"((?:[^"\\]|\\.)*)"', bruto):
        doi=m.group(1); tit=m.group(2).encode().decode('unicode_escape',errors='ignore')
        ano=None
        janela=bruto[m.end():m.end()+700]
        my=re.search(r'"year"\s*:\s*(\d{4})', janela)
        if my: ano=int(my.group(1))
        jr=re.search(r'"journal"\s*:\s*"([^"]*)"', janela)
        cands.append(dict(doi=doi, titulo=tit, ano=ano, veiculo=jr.group(1) if jr else None))
vistos=set(); C=[]
for c in cands:
    if c['doi'] in vistos: continue
    vistos.add(c['doi']); C.append(c)
print(f"candidatos únicos recolhidos das buscas: {len(C)}")
PREF=('10.3389','10.3390','10.1080','10.1038','10.1007','10.1016','10.1249','10.1519','10.1136',
      '10.1123','10.1055','10.1590','10.1109','10.1093','10.2307','10.1214','10.1037','10.1186',
      '10.5114','10.1002','10.1097','10.5772','10.1080')
RUIM=('10.3410','10.6084','10.17863','10.48550','10.21203','10.13140','10.31234')
# correções verificadas manualmente contra o registro do periódico
FIXO={50:('10.3390/sports11120234','sports',1,'https://doi.org/10.3390/sports11120234')}
DESCARTA={'10.17605/osf.io','10.20944/preprints','10.3410/f','10.6084/m9','10.48550/arxiv','10.17863/cam'}
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite"))
cx.execute("DELETE FROM referencia")
nd=0
for i,ref in enumerate(ET.REFS,1):
    doi,tit,ano=partes(ref); veic=None; escore=1.0 if doi else 0.0
    if not doi:
        alvo=nn(tit); melhor=(0,None)
        for c in C:
            s=difflib.SequenceMatcher(None,alvo,nn(c['titulo'])).ratio()
            if c['doi'].startswith(RUIM): s-=0.12
            if ano and c['ano'] and abs(c['ano']-ano)>1: s-=0.25
            if s>melhor[0]: melhor=(s,c)
        if melhor[0]>=0.80 and not any(melhor[1]['doi'].startswith(x) for x in DESCARTA):
            doi=melhor[1]['doi']; veic=melhor[1]['veiculo']; escore=melhor[0]
    oa=None; url_oa=None
    if i in FIXO: doi,veic,oa,url_oa=FIXO[i]
    if doi: nd+=1
    cx.execute("""INSERT INTO referencia (id,autores,ano,titulo,veiculo,doi,url_doi,pubmed,url_pubmed,
                  open_access,url_oa,abnt,usada_em) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (i, ref.split('.')[0], ano, tit, veic, doi, f"https://doi.org/{doi}" if doi else None,
       None, None, None, None, ref, 'ambos'))
    print(f"  [{i:2}] {'✓' if doi else '·'} {(doi or '—')[:34]:36} {tit[:52]}")
cx.commit()
print(f"\nreferências com DOI: {nd}/{len(ET.REFS)}")
cx.close()
