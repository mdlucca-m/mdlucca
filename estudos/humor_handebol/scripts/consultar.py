#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consulta a base única do estudo.

  ./consultar.py buscar "piso de ruído"        busca textual em tudo
  ./consultar.py resultado --variavel Vigor    resultados de uma variável
  ./consultar.py resultado --sig               só o que é significativo
  ./consultar.py confronto                     não paramétrica × paramétrica × modelo misto
  ./consultar.py dia                           painel dia a dia
  ./consultar.py perfil --recorte estimulo     prevalências
  ./consultar.py serie Vigor                   série diária com piso, derivadas e choques
  ./consultar.py auditoria                     achados da auditoria
  ./consultar.py abas --categoria análise      o que existe no acervo
  ./consultar.py sql "SELECT ..."              consulta livre
  ./consultar.py resumo                        visão geral da base
"""
import sqlite3, os, sys, argparse, textwrap
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB=os.path.join(RAIZ,"base","humor_handebol.sqlite")
def conectar():
    cx=sqlite3.connect(f"file:{DB}?mode=ro", uri=True); cx.row_factory=sqlite3.Row; return cx
def br(v,n=3):
    if v is None: return "—"
    if isinstance(v,float): return f"{v:.{n}f}".replace('.',',')
    return str(v)
def tabela(rows, larg=None):
    if not rows: print("  (nada encontrado)"); return
    cols=rows[0].keys()
    L={c:max(len(c), *(len(br(r[c])) for r in rows)) for c in cols}
    if larg: L={c:min(L[c],larg) for c in L}
    print("  "+" │ ".join(c[:L[c]].ljust(L[c]) for c in cols))
    print("  "+"─┼─".join("─"*L[c] for c in cols))
    for r in rows:
        print("  "+" │ ".join(br(r[c])[:L[c]].ljust(L[c]) for c in cols))
    print(f"  ({len(rows)} linha{'s' if len(rows)!=1 else ''})")
def main():
    ap=argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp=ap.add_subparsers(dest='cmd')
    b=sp.add_parser('buscar'); b.add_argument('termo', nargs='+'); b.add_argument('--limite',type=int,default=20)
    b.add_argument('--origem', choices=['acervo','resultado','auditoria'])
    r=sp.add_parser('resultado')
    for a in ['--variavel','--dominio','--via','--recorte','--artigo']: r.add_argument(a)
    r.add_argument('--sig', action='store_true'); r.add_argument('--limite',type=int,default=40)
    sp.add_parser('confronto'); sp.add_parser('dia'); sp.add_parser('auditoria'); sp.add_parser('resumo')
    sp.add_parser('unidades')
    pf=sp.add_parser('perfil'); pf.add_argument('--recorte', default='dia'); pf.add_argument('--unidade', default='U-AD')
    se=sp.add_parser('serie'); se.add_argument('variavel')
    ab=sp.add_parser('abas'); ab.add_argument('--categoria'); ab.add_argument('--arquivo')
    sq=sp.add_parser('sql'); sq.add_argument('query')
    a=ap.parse_args()
    if not a.cmd: ap.print_help(); return
    cx=conectar()
    if a.cmd=='buscar':
        q=' '.join(a.termo)
        w="WHERE busca MATCH ?"+(" AND origem=?" if a.origem else "")
        par=[q]+([a.origem] if a.origem else [])+[a.limite]
        rows=cx.execute(f"""SELECT origem, arquivo, aba, categoria, chave,
                             substr(texto,1,150) AS trecho FROM busca {w}
                             ORDER BY rank LIMIT ?""", par).fetchall()
        tabela(rows, larg=48)
    elif a.cmd=='resultado':
        w=[]; p=[]
        for campo,val in [('variavel',a.variavel),('dominio',a.dominio),('via',a.via),
                          ('recorte',a.recorte),('artigo',a.artigo)]:
            if val: w.append(f"{campo} LIKE ?"); p.append(f"%{val}%")
        if a.sig: w.append("significativo=1")
        q="SELECT variavel,recorte,via,teste,rotulo_estatistica,estatistica,p,p_ajustado,rotulo_efeito,efeito,n FROM resultado"
        if w: q+=" WHERE "+" AND ".join(w)
        q+=" ORDER BY dominio, variavel LIMIT ?"; p.append(a.limite)
        tabela(cx.execute(q,p).fetchall(), larg=34)
    elif a.cmd=='confronto':
        tabela(cx.execute("""SELECT variavel,
            ROUND(MAX(CASE WHEN via='não paramétrica' AND teste='Friedman' THEN p END),4) AS friedman,
            ROUND(MAX(CASE WHEN via='paramétrica' THEN p END),4) AS anova_gg,
            ROUND(MAX(CASE WHEN via='modelo misto' THEN p END),4) AS misto,
            CASE WHEN (MAX(CASE WHEN via='não paramétrica' AND teste='Friedman' THEN p END)<0.05)
                    = (MAX(CASE WHEN via='modelo misto' THEN p END)<0.05) THEN 'sim' ELSE 'NÃO' END AS concordam
            FROM resultado WHERE dominio='tendência' AND recorte IN ('D1..D7','efeito linear do dia')
            GROUP BY variavel""").fetchall())
    elif a.cmd=='dia': tabela(cx.execute("SELECT * FROM v_painel_dia").fetchall())
    elif a.cmd=='auditoria':
        for r in cx.execute("SELECT * FROM auditoria ORDER BY id"):
            print(f"\n[{r['id']}] {r['gravidade'].upper()} — {r['titulo']}")
            for campo in ['achado','correcao','impacto']:
                print(textwrap.fill(f"  {campo}: {r[campo]}", 100, subsequent_indent='    '))
    elif a.cmd=='unidades':
        tabela(cx.execute("SELECT sigla,nome,n,usada_em FROM unidade_analise").fetchall(), larg=44)
    elif a.cmd=='perfil':
        tabela(cx.execute("""SELECT recorte, perfil, ROUND(prevalencia,1) AS pct, n FROM prevalencia
                             WHERE recorte_tipo=? AND unidade=? ORDER BY perfil, recorte""",
                          (a.recorte,a.unidade)).fetchall())
    elif a.cmd=='serie':
        tabela(cx.execute("""SELECT dia, ROUND(media,2) media, ROUND(erro_padrao,3) ep,
               ROUND(suavizado,2) suavizado, ROUND(derivada1,3) d1, ROUND(derivada2,3) d2,
               ROUND(piso_ruido,3) piso, e_choque FROM serie_diaria WHERE variavel=? ORDER BY dia""",
               (a.variavel,)).fetchall())
    elif a.cmd=='abas':
        w=[]; p=[]
        if a.categoria: w.append("a.categoria=?"); p.append(a.categoria)
        if a.arquivo: w.append("f.arquivo LIKE ?"); p.append(f"%{a.arquivo}%")
        q="""SELECT f.papel, a.nome, a.categoria, a.linhas, a.colunas FROM aba a JOIN fonte f ON f.id=a.fonte_id"""
        if w: q+=" WHERE "+" AND ".join(w)
        tabela(cx.execute(q+" ORDER BY a.linhas DESC LIMIT 60",p).fetchall(), larg=40)
    elif a.cmd=='sql': tabela(cx.execute(a.query).fetchall(), larg=44)
    elif a.cmd=='resumo':
        for t in ['atleta','dia','registro','atleta_dia','pre_pos','resultado','prevalencia',
                  'serie_diaria','serie_perfil','auditoria','aba','celula','busca']:
            print(f"  {t:14} {cx.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>8}")
        print()
        tabela(cx.execute("""SELECT dominio, via, COUNT(*) n, SUM(significativo) significativos
                             FROM resultado GROUP BY dominio, via ORDER BY 3 DESC""").fetchall())
    cx.close()
main()
