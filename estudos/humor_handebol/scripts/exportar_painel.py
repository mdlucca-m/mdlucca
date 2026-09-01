# -*- coding: utf-8 -*-
"""Gera o pacote de dados do painel, direto da base única."""
import sqlite3, json, os
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite")); cx.row_factory=sqlite3.Row
q=lambda s,*p:[dict(r) for r in cx.execute(s,p)]
D={}
D['dia']=q("SELECT * FROM dia ORDER BY dia")
D['variavel']=q("SELECT * FROM variavel")
D['painel']=q("SELECT * FROM v_painel_dia")
D['serie']=q("SELECT * FROM serie_diaria")
D['serie_perfil']=q("SELECT * FROM serie_perfil")
D['resultado']=q("SELECT id,dominio,via,unidade,variavel,recorte,teste,estatistica,rotulo_estatistica,gl,"
                 "p,p_ajustado,metodo_ajuste,efeito,rotulo_efeito,ic_inf,ic_sup,n,significativo,artigo FROM resultado")
D['prevalencia']=q("SELECT * FROM prevalencia")
D['unidade']=q("SELECT * FROM unidade_analise")
D['auditoria']=q("SELECT * FROM auditoria ORDER BY id")
D['referencia']=q("SELECT id,autores,ano,titulo,veiculo,doi,url_doi,abnt FROM referencia ORDER BY id")
D['confronto']=q("SELECT * FROM v_confronto_vias")
D['atleta']=q("SELECT * FROM atleta ORDER BY atleta")
D['atleta_dia']=q("SELECT atleta,dia,vigor,fadiga,pth,tensao,depressao,raiva,confusao,perfil,faixa FROM atleta_dia")
D['acervo']=q("SELECT f.arquivo, f.papel, a.categoria, COUNT(*) n, SUM(a.linhas) linhas "
              "FROM aba a JOIN fonte f ON f.id=a.fonte_id GROUP BY f.arquivo, a.categoria")
D['contagem']={t:cx.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
               for t in ['atleta','registro','atleta_dia','pre_pos','resultado','aba','celula','busca','referencia']}
sai=os.path.join(RAIZ,"painel"); os.makedirs(sai, exist_ok=True)
p=os.path.join(sai,"dados.json")
json.dump(D, open(p,'w',encoding='utf-8'), ensure_ascii=False, separators=(',',':'))
print("gravado:", p, f"{os.path.getsize(p)/1024:.0f} KB")
for k,v in D.items():
    if isinstance(v,list): print(f"   {k:14} {len(v)}")
cx.close()
