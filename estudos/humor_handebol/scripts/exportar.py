# -*- coding: utf-8 -*-
"""Exporta cada tabela e vista da base para CSV, e um dicionário de dados em Markdown."""
import sqlite3, csv, os
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAI=os.path.join(RAIZ,"base","csv"); os.makedirs(SAI, exist_ok=True)
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite")); cx.row_factory=sqlite3.Row
objs=[r[0] for r in cx.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') "
      "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'busca%' ORDER BY type DESC, name")]
linhas=[]
for o in objs:
    rs=cx.execute(f"SELECT * FROM {o}").fetchall()
    if not rs: linhas.append((o,0,0)); continue
    with open(os.path.join(SAI,f"{o}.csv"),'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(rs[0].keys())
        for r in rs: w.writerow(list(r))
    linhas.append((o,len(rs),len(rs[0].keys())))
DESC={'atleta':'Um registro por atleta, com assiduidade.',
 'dia':'Os sete dias do microciclo, com estímulo, carga e janela de coleta observada.',
 'variavel':'Metadados de cada variável: família, amplitude, direção e norma.',
 'registro':'Cada formulário respondido, com momento (pré, pós, único) e período do dia.',
 'atleta_dia':'A unidade de análise adotada: um valor por atleta e por dia, com escore T, perfil e faixa.',
 'pre_pos':'Pares manhã/noite em formato longo, com delta.',
 'serie_diaria':'Série de cada variável com erro-padrão, suavização, derivadas, piso de ruído e choque.',
 'serie_perfil':'O mesmo para a prevalência de cada perfil e faixa.',
 'resultado':'Todo resultado estatístico do estudo em formato longo e consultável.',
 'prevalencia':'Prevalências por unidade de análise, por dia e por estímulo.',
 'unidade_analise':'As quatro unidades que circulavam nos manuscritos e o viés de cada uma.',
 'auditoria':'Os seis achados da auditoria, com causa, correção e impacto.',
 'referencia':'Referências com DOI e ligação, quando localizados.',
 'fonte':'As planilhas de origem, com papel e soma de verificação.',
 'aba':'Cada aba das planilhas, categorizada.',
 'celula':'Acervo célula a célula, com nomes de atletas removidos.',
 'v_significativos':'Vista: apenas os resultados significativos.',
 'v_confronto_vias':'Vista: a mesma hipótese pelas três vias de análise.',
 'v_painel_dia':'Vista: o painel dia a dia.'}
with open(os.path.join(RAIZ,"base","DICIONARIO.md"),'w',encoding='utf-8') as f:
    f.write("# Dicionário de dados\n\nBase única: `base/humor_handebol.sqlite`. "
            "Os CSV em `base/csv/` são exportações fiéis das tabelas e vistas.\n\n")
    f.write("| Objeto | Linhas | Colunas | O que é |\n|---|---:|---:|---|\n")
    for o,n,c in linhas:
        f.write(f"| `{o}` | {n} | {c} | {DESC.get(o,'—')} |\n")
    f.write("\n## Colunas por tabela\n")
    for o,_,_ in linhas:
        cols=[r[1] for r in cx.execute(f"PRAGMA table_info({o})")]
        if cols: f.write(f"\n**`{o}`** — {', '.join('`'+c+'`' for c in cols)}\n")
print(f"exportadas {sum(1 for _,n,_ in linhas if n)} tabelas para {SAI}")
for o,n,c in linhas: print(f"   {o:20} {n:>7} linhas")
cx.close()
