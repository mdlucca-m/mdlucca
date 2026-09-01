# -*- coding: utf-8 -*-
"""Índice de busca textual sobre o acervo e sobre os resultados."""
import sqlite3, os
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite"))
cx.executescript("""
DROP TABLE IF EXISTS busca;
CREATE VIRTUAL TABLE busca USING fts5(
  origem, arquivo, aba, categoria, chave, texto, ref UNINDEXED, tokenize='unicode61 remove_diacritics 2');
""")
n=0
# acervo: uma linha por (aba, linha) com o texto concatenado
cur=cx.execute("""
 SELECT c.aba_id, c.linha, a.nome, a.categoria, f.arquivo,
        GROUP_CONCAT(COALESCE(c.valor_txt, CAST(ROUND(c.valor_num,4) AS TEXT)), ' | ')
 FROM celula c JOIN aba a ON a.id=c.aba_id JOIN fonte f ON f.id=a.fonte_id
 GROUP BY c.aba_id, c.linha""")
lote=[]
for aba_id,linha,aba,cat,arq,txt in cur:
    if not txt: continue
    lote.append(('acervo',arq,aba,cat,f"linha {linha}",txt[:2000],f"{aba_id}:{linha}"))
    if len(lote)>=5000:
        cx.executemany("INSERT INTO busca VALUES (?,?,?,?,?,?,?)",lote); n+=len(lote); lote=[]
if lote: cx.executemany("INSERT INTO busca VALUES (?,?,?,?,?,?,?)",lote); n+=len(lote)
# resultados
for r in cx.execute("""SELECT id,dominio,via,variavel,recorte,teste,estatistica,rotulo_estatistica,
                              p,p_ajustado,efeito,rotulo_efeito,n,artigo FROM resultado"""):
    i,dom,via,var,rec,tes,est,rest,p,pa,ef,ref_,nn,art=r
    txt=(f"{dom} {via} {var} {rec} {tes} {rest}={est} p={p} p_ajustado={pa} {ref_}={ef} n={nn} artigo {art}")
    cx.execute("INSERT INTO busca VALUES ('resultado','base','resultado',?,?,?,?)",
               (dom,f"{var} · {rec}",txt,str(i)))
    n+=1
for r in cx.execute("SELECT id,titulo,achado,correcao,impacto,gravidade FROM auditoria"):
    cx.execute("INSERT INTO busca VALUES ('auditoria','base','auditoria',?,?,?,?)",
               (r[5],r[1],' '.join(str(x) for x in r[1:5]),r[0])); n+=1
cx.commit(); print("índice de busca:",n,"entradas")
cx.close()
