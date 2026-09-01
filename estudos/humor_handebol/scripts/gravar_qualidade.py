# -*- coding: utf-8 -*-
"""Grava na base única o dicionário de variáveis, a auditoria de qualidade,
a reconferência dos artigos e a otimização da carga, e aplica as correções
que a auditoria determinou. Idempotente."""
import os, json, sqlite3
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados")
jd=lambda n: json.load(open(os.path.join(DADOS,n+".json"),encoding='utf-8'))
Q=jd("V2_qual"); C=jd("V2_conf"); O=jd("V2_otim")
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite")); cx.row_factory=sqlite3.Row
cx.executescript("""
DROP TABLE IF EXISTS dicionario;
CREATE TABLE dicionario(
  variavel TEXT PRIMARY KEY, tipo TEXT NOT NULL, escala TEXT, dominio TEXT, origem TEXT);
DROP TABLE IF EXISTS formula;
CREATE TABLE formula(id TEXT PRIMARY KEY, nome TEXT, formula TEXT, nota TEXT);
DROP TABLE IF EXISTS qualidade_numerica;
CREATE TABLE qualidade_numerica(
  variavel TEXT PRIMARY KEY, tipo TEXT, n INTEGER, minimo REAL, q1 REAL, mediana REAL, q3 REAL,
  maximo REAL, media REAL, desvio REAL, erro_padrao REAL, cv REAL, iqr REAL, mad REAL,
  assimetria REAL, curtose REAL, shapiro_w REAL, shapiro_p REAL,
  tukey_inf REAL, tukey_sup REAL, n_tukey_moderado INTEGER, n_tukey_extremo INTEGER,
  n_z3 INTEGER, n_zmod INTEGER, fora_dominio INTEGER, iqr_nulo INTEGER, mad_nulo INTEGER,
  k_sturges INTEGER, k_freedman_diaconis INTEGER, h_freedman_diaconis REAL, pct_no_piso REAL);
DROP TABLE IF EXISTS qualidade_categorica;
CREATE TABLE qualidade_categorica(
  variavel TEXT, nivel TEXT, f INTEGER, pct REAL, f_acum INTEGER, pct_acum REAL,
  PRIMARY KEY(variavel,nivel));
DROP TABLE IF EXISTS qualidade_faltante;
CREATE TABLE qualidade_faltante(
  bloco TEXT, item TEXT, faltantes INTEGER, n INTEGER, completude REAL, PRIMARY KEY(bloco,item));
DROP TABLE IF EXISTS qualidade_cobertura;
CREATE TABLE qualidade_cobertura(
  dia INTEGER PRIMARY KEY, atletas_com_registro INTEGER, atletas_esperados INTEGER,
  registros INTEGER, registros_esperados INTEGER, cobertura_atleta REAL, cobertura_registro REAL);
DROP TABLE IF EXISTS reconferencia;
CREATE TABLE reconferencia(
  bloco TEXT, item TEXT, caminho_a REAL, caminho_b REAL, diferenca REAL, confere INTEGER,
  PRIMARY KEY(bloco,item));
DROP TABLE IF EXISTS otimizacao;
CREATE TABLE otimizacao(
  cenario TEXT, dia INTEGER, horas REAL, fadiga_prevista REAL, vigor_previsto REAL,
  PRIMARY KEY(cenario,dia));
DROP TABLE IF EXISTS otimizacao_restricao;
CREATE TABLE otimizacao_restricao(
  restricao TEXT PRIMARY KEY, tipo TEXT, folga REAL, preco_sombra REAL, ativa INTEGER);
DROP TABLE IF EXISTS otimizacao_fronteira;
CREATE TABLE otimizacao_fronteira(
  carga REAL PRIMARY KEY, viavel INTEGER, vigor_minimo REAL, fadiga_maxima REAL, horas TEXT);
CREATE VIEW IF NOT EXISTS v_qualidade AS
  SELECT d.variavel, d.tipo, d.dominio, q.n, q.mediana, q.iqr, q.shapiro_p,
         q.n_tukey_moderado, q.fora_dominio
    FROM dicionario d LEFT JOIN qualidade_numerica q ON q.variavel = d.variavel;
""")
cx.executemany("INSERT INTO dicionario VALUES(?,?,?,?,?)",
  [(d['v'],d['tipo'],d['escala'],d['dominio'],d['origem']) for d in Q['DICIONARIO']])
cx.executemany("INSERT INTO formula VALUES(?,?,?,?)",
  [(f['id'],f['nome'],f['formula'],f['nota']) for f in Q['FORMULAS']])
cx.executemany("INSERT INTO qualidade_numerica VALUES(" + ",".join("?"*31) + ")",
  [(u['variavel'],u['tipo'],u['n'],u['minimo'],u['q1'],u['mediana'],u['q3'],u['maximo'],
    u['media'],u['desvio'],u['erro_padrao'],u['cv'],u['iqr'],u['mad'],u['assimetria'],u['curtose'],
    u['shapiro_W'],u['shapiro_p'],u['tukey_moderado'][0],u['tukey_moderado'][1],
    u['n_tukey_moderado'],u['n_tukey_extremo'],u['n_z3'],u['n_zmod'],u.get('fora_do_dominio'),
    int(u['iqr_nulo']),int(u['mad_nulo']),u['k_sturges'],u['k_fd'],u['h_freedman_diaconis'],
    u['pct_no_piso']) for u in Q['UNI']])
cx.executemany("INSERT INTO qualidade_categorica VALUES(?,?,?,?,?,?)",
  [(nome,l['nivel'],l['f'],l['pct'],l['f_acum'],l['pct_acum'])
   for nome,t in Q['FREQ'].items() for l in t['linhas']])
cx.executemany("INSERT INTO qualidade_faltante VALUES(?,?,?,?,?)",
  [(f['bloco'],f['item'],f['faltantes'],f['n'],f['completude']) for f in Q['FALTA_ITEM']+Q['FALTA_VAR']])
cx.executemany("INSERT INTO qualidade_cobertura VALUES(?,?,?,?,?,?,?)",
  [(g['dia'],g['atletas_com_registro'],g['atletas_esperados'],g['registros'],
    g['registros_esperados'],g['cobertura_atleta'],g['cobertura_registro']) for g in Q['GRADE']])
cx.executemany("INSERT INTO reconferencia VALUES(?,?,?,?,?,?)",
  [(c['bloco'],c['item'],c['caminho_a'],c['caminho_b'],c['diferenca'],int(c['confere']))
   for c in C['CONF']])
for cen,chave in [('I · redistribuição','PROGRAMA_I'),('II · teto de recuperação','PROGRAMA_II'),
                  ('observado','OBSERVADO')]:
    s=O[chave]
    cx.executemany("INSERT INTO otimizacao VALUES(?,?,?,?,?)",
      [(cen,d+1,s['horas'][d],s['fadiga'][d],s['vigor'][d]) for d in range(7)])
cx.executemany("INSERT INTO otimizacao_restricao VALUES(?,?,?,?,?)",
  [(a['restricao'],'desigualdade',a['folga'],a['preco_sombra'],int(a['ativa'])) for a in O['ATIVAS']]
  +[(e['restricao'],'igualdade',None,e['preco_sombra'],1) for e in O['EQ']])
cx.executemany("INSERT INTO otimizacao_fronteira VALUES(?,?,?,?,?)",
  [(f['carga'], int(f.get('viavel') is not False), f.get('vigor_minimo'), f.get('fadiga_maxima'),
    json.dumps(f.get('horas'))) for f in O['FRONTEIRA']])

# --- correções que a auditoria determinou ---
CORR=[]
antes=cx.execute("SELECT maximo FROM variavel WHERE variavel='Epworth'").fetchone()[0]
if antes!=18.0:
    cx.execute("UPDATE variavel SET maximo=18.0, rotulo='Sonolência diurna (Epworth, 6 itens)' "
               "WHERE variavel='Epworth'")
    CORR.append(f"variavel.Epworth: máximo {antes} → 18,0 e rótulo passa a declarar a aplicação de seis itens")
for i in Q['INCONS']:
    cx.execute("INSERT OR REPLACE INTO auditoria VALUES(?,?,?,?,?,?)",
        (i['id'], i['titulo'], i['achado'], i['correcao'],
         f"{i['n']} de {i['de']}", i['gravidade']))
CORR.append(f"auditoria: {len(Q['INCONS'])} achados de qualidade acrescentados (Q1 a Q6)")
cx.commit()
print("gravado na base única:")
for t in ['dicionario','formula','qualidade_numerica','qualidade_categorica','qualidade_faltante',
          'qualidade_cobertura','reconferencia','otimizacao','otimizacao_restricao','otimizacao_fronteira']:
    print(f"   {t:<24} {cx.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>4} linhas")
print(f"   auditoria                {cx.execute('SELECT COUNT(*) FROM auditoria').fetchone()[0]:>4} linhas")
print("\ncorreções aplicadas:")
for c in CORR: print("   ·", c)
cx.close()
