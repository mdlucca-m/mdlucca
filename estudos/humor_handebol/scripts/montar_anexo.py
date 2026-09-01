# -*- coding: utf-8 -*-
"""Anexo metodológico: modelagem preditiva e o estudo mapeado no CRISP-DM."""
import os, sys
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"_docx_base.py")).read())
import sqlite3
def jd(n): return json.load(open(os.path.join(DADOS,n+".json"),encoding='utf-8'))
ML=jd("V2_ml"); ML2=jd("V2_ml2"); ML3=jd("V2_ml3"); CD=jd("V2_crispdm")
def n_(x,d=3):
    if x is None or (isinstance(x,float) and x!=x): return "—"
    return f"{x:.{d}f}".replace('.',',').replace('-','−')
def pf_(p,d=3):
    if p is None: return "—"
    return "< 0,001" if p<0.001 else f"{p:.{d}f}".replace('.',',')

para("ANEXO METODOLÓGICO", indent=False, bold=True, size=14,
     align=WD_ALIGN_PARAGRAPH.CENTER, after=6, spacing=1.15)
para("Modelagem preditiva sobre a base do microciclo terminal e o estudo mapeado nas seis fases do CRISP-DM",
     indent=False, italic=True, size=11, align=WD_ALIGN_PARAGRAPH.CENTER, after=18, spacing=1.15)

head("1 OBJETIVO")
para("Os dois artigos descrevem o comportamento das dimensões do humor ao longo do microciclo terminal e "
     "submetem cada contraste a três vias de análise. Este anexo responde a outra pergunta, de natureza "
     "operacional: a medida da manhã antecipa o estado da noite do mesmo dia? A pergunta interessa à comissão "
     "técnica porque o horizonte de decisão é de horas — a informação da manhã precisa servir à sessão que "
     "começa depois dela.")
para("O anexo cumpre também uma segunda função. A modelagem preditiva sobre amostra pequena produz números "
     "otimistas com facilidade, e o registro do que foi feito para evitá-los importa tanto quanto o resultado. "
     "A seção 5 organiza o estudo inteiro nas seis fases do CRISP-DM (CHAPMAN et al., 2000) e separa, em cada "
     "fase, o que coube à automação e o que permaneceu decisão humana.")

head("2 MÉTODO")
head("2.1 Unidade, alvo e preditores", lvl=2)
para(f"A unidade é o par atleta-dia com medida da manhã e medida da noite, o que produz {ML['n']} observações "
     f"de {ML['atletas']} atletas. O desfecho é binário: o atleta termina o dia classificado em um dos três "
     "perfis da faixa de risco — barbatana de tubarão, iceberg invertido ou everest invertido. A taxa de "
     f"eventos é de {n_(ML['eventos']/ML['n']*100,1)}% ({ML['eventos']} de {ML['n']}).")
para("Os preditores vêm exclusivamente da medida da manhã: as seis subescalas do BRUMS, a perturbação total "
     "do humor, a fadiga física e a mental, a sonolência de Epworth, o estresse percebido, o indicador de já "
     "estar na faixa de risco pela manhã, o dia do microciclo, as horas de treino do dia, a carga acumulada e "
     "o tipo de estímulo. Alvo e preditores ficam separados no tempo, de modo que a previsão não é circular.")
head("2.2 Validação e linhas de base", lvl=2)
para("A validação é cruzada, estratificada e agrupada por atleta: nenhum atleta aparece ao mesmo tempo no "
     "conjunto de treino e no de teste. A distinção não é formal. Com 27 atletas e sete dias, uma divisão por "
     "linha permitiria ao modelo reconhecer o atleta em vez de aprender a regra, e a área sob a curva subiria "
     "sem que nada tivesse sido aprendido. Os intervalos de confiança vêm de reamostragem agrupada, pelo mesmo "
     "motivo.")
para("Dois modelos triviais entram na comparação como referência obrigatória. O primeiro atribui a todos a "
     "classe majoritária. O segundo aplica a regra que qualquer preparador aplicaria de cabeça: quem amanhece "
     f"na faixa de risco termina o dia na faixa de risco. Essa regra acerta {n_(ML['regra_trivial']*100,1)}% dos "
     "casos, e é contra ela — não contra o acaso — que os modelos precisam mostrar ganho.")
head("2.3 Modelos", lvl=2)
para("Quatro classificadores foram ajustados: árvore de decisão de profundidade três, floresta aleatória, "
     "XGBoost e regressão logística com padronização. Os hiperparâmetros foram fixados em valores conservadores "
     "antes da avaliação, sem busca em grade: com esta amostra, a busca de hiperparâmetros sobre a mesma "
     "partição produziria otimismo que o intervalo de confiança não captura.")

head("3 RESULTADOS")
head("3.1 Desempenho", lvl=2)
ordem=['XGBoost','Árvore de decisão','Random Forest','Regressão logística',
       'Regra: já estava em risco','Classe majoritária']
linhas=[]
for k in ordem:
    r=ML['RES'][k]; g=ML['GANHO'].get(k)
    linhas.append([k, n_(r['auc']), f"[{n_(r['ic'][0])}; {n_(r['ic'][1])}]", n_(r['bacc']),
                   n_(r['sens']), n_(r['espec']), n_(r['brier']),
                   (f"{n_(g['m'])} [{n_(g['ic'][0])}; {n_(g['ic'][1])}]" if g else "—")])
caption("Tabela M1 — Desempenho dos modelos e das duas linhas de base, com validação agrupada por atleta")
mktable(["Modelo","AUC","IC 95% da AUC","Ac. balanc.","Sensib.","Especif.","Brier","Ganho sobre a regra trivial"],
        linhas, widths=[3.4,1.5,2.9,1.8,1.5,1.5,1.4,4.1], fs=8)
src(nota="Acurácia balanceada, sensibilidade e especificidade no ponto de corte de 0,5. O escore de Brier mede "
         "calibração, e valores menores indicam melhor calibração. O ganho é a diferença de AUC em relação à "
         "regra de já estar em risco pela manhã, com intervalo por reamostragem agrupada.")
para("Os três modelos de árvore superam a regra trivial em área sob a curva, e o XGBoost apresenta a maior "
     f"diferença ({n_(ML['GANHO']['XGBoost']['m'])}). O intervalo de confiança desse ganho, contudo, não exclui "
     f"zero (de {n_(ML['GANHO']['XGBoost']['ic'][0])} a {n_(ML['GANHO']['XGBoost']['ic'][1])}), e o mesmo vale "
     "para os demais. Sobre a amostra completa, portanto, a afirmação sustentável é modesta: os modelos não "
     "pioram a regra trivial, e a superioridade aparente permanece dentro da margem de erro de 27 atletas.")
S2=ML2['SUBGRUPO']; k0=list(S2)[0]
para(f"A restrição ao subgrupo acionável muda a conclusão. Dos {ML['n']} pares, {S2[k0]['n']} amanhecem fora da "
     f"faixa de risco, e {S2[k0]['eventos']} deles entram na faixa até a noite "
     f"({n_(S2[k0]['eventos']/S2[k0]['n']*100,1)}%). É o único subgrupo sobre o qual a previsão acrescenta "
     "decisão: sobre quem já amanhece mal, a comissão técnica não precisa de modelo. Nesse recorte, os três "
     "modelos de árvore têm intervalo de confiança que exclui o acaso "
     f"(floresta aleatória, {n_(S2['Random Forest']['auc'])}, de {n_(S2['Random Forest']['ic'][0])} a "
     f"{n_(S2['Random Forest']['ic'][1])}).")
figura(os.path.join(S,"M1fig.png"), "M1",
       "Área sob a curva dos modelos e das linhas de base, na amostra completa e no subgrupo acionável")

head("3.2 A árvore e o que ela usa", lvl=2)
folhas=[n for n in ML2['ARVORE'] if n['tipo']=='folha']
caption("Tabela M2 — Folhas da árvore de decisão, ordenadas pelo risco previsto")
mktable(["Caminho da manhã até a folha","n","Risco previsto"],
        [[" e ".join(f['caminho']).replace('.',','), str(f['n']), n_(f['p']*100,0)+"%"]
         for f in sorted(folhas,key=lambda f:-f['p'])],
        widths=[10.5,1.5,3.5], fs=8.5)
src(nota="Profundidade máxima de três e mínimo de doze pares por folha. Os limiares estão nas unidades brutas "
         "de cada instrumento.")
imp=ML2['IMPORTANCIA'][:5]
para("A importância por permutação, medida fora da amostra, concentra-se em duas variáveis: a perturbação "
     f"total do humor pela manhã, cuja permuta derruba a AUC em {n_(imp[0]['media'])}, e a tensão pela manhã, "
     f"que derruba {n_(imp[1]['media'])}. As demais somam pouco — a terceira colocada, a fadiga pela manhã, "
     f"responde por {n_(imp[2]['media'])} — e o indicador de já estar em risco pela "
     f"manhã, que sustenta a regra trivial, aparece com apenas {n_([e for e in ML2['IMPORTANCIA'] if 'risco' in e['var'].lower()][0]['media'])}. "
     "O modelo, em outras palavras, não está reproduzindo a regra trivial por outro caminho.")

head("3.3 Diagnóstico: achado ou aritmética do desenho?", lvl=2)
para("O primeiro corte da árvore é contraintuitivo. Ele separa pela perturbação total do humor e atribui maior "
     "risco vespertino a quem amanhece com o escore mais favorável. Antes de qualquer leitura clínica, a "
     "hipótese concorrente precisa ser afastada: quem amanhece no piso da escala só tem para onde subir, e o "
     "corte poderia estar capturando reversão à média em vez de risco.")
rv=sorted(ML3['REVERSAO'],key=lambda e:e['rho'])
caption("Tabela M3 — Reversão à média: correlação entre o valor da manhã e a própria variação até a noite")
mktable(["Dimensão","ρ de Spearman","p","Componente mecânico"],
        [[e['variavel'], n_(e['rho']), pf_(e['p']), "sim" if e['mecanico'] else "não"] for e in rv],
        widths=[4.5,3.2,3.2,4.1], fs=9)
src(nota="Correlação de Spearman entre o escore da manhã e a diferença entre a noite e a manhã, sobre os "
         f"{ML['n']} pares. Valor negativo e significativo indica movimento em parte mecânico.")
V=ML3['VEREDICTO']
para(f"A perturbação total do humor tem, de fato, componente mecânico (ρ = {n_(V['pth']['rho'])}, p < 0,001), e "
     "a parte do corte que se apoia nela deve ser lida com essa ressalva. A tensão, porém, não tem: a tensão da "
     f"manhã não prediz a própria variação (ρ = {n_(V['tensao']['rho'])}, p = {n_(V['tensao']['p'])}). O segundo "
     "corte da árvore, que usa a tensão, não é subproduto da escala.")
an=ML3['ANINHADOS']
para("A sequência de modelos aninhados confirma a leitura. A perturbação total do humor isolada alcança AUC de "
     f"{n_(an[0]['auc'])}; o acréscimo da tensão matinal a eleva para {n_(an[1]['auc'])}, ganho de "
     f"{n_(V['ganho_tensao'],2)} que nenhuma outra variável reproduz. O modelo com todas as {an[3]['k']} "
     f"variáveis ({n_(an[3]['auc'])}) não supera o de três, o que é esperado com {ML['n']} observações.")
figura(os.path.join(S,"M2fig.png"), "M2",
       "Reversão à média por dimensão e contribuição da tensão matinal em modelos aninhados")
para("A leitura substantiva é a seguinte. Alguma tensão pela manhã protege; a ausência completa de tensão em "
     "atleta que amanhece muito favorável antecede a queda vespertina. O achado converge com o que os dois "
     "artigos observam por outra via: neste elenco, a tensão se comporta como ativação, e não como sofrimento.")

head("4 O QUE ISTO PERMITE DIZER, E O QUE NÃO PERMITE")
for t in [
 "Permite dizer que, entre atletas que amanhecem fora da faixa de risco, a medida da manhã distingue quem "
 "terminará o dia na faixa com desempenho acima do acaso, e que o marcador que faz essa distinção é a tensão "
 "matinal, não a fadiga nem o vigor.",
 "Não permite dizer que os modelos superam a regra trivial na população de atletas: o intervalo de confiança "
 "do ganho inclui zero em todos os quatro.",
 "Não permite uso individual para decisão de carga. A calibração dos modelos é apenas razoável, e nenhum "
 "limiar operacional foi validado em amostra independente.",
 "Não permite generalização para outros elencos, outros microciclos ou outras fases da temporada. São 27 "
 "atletas de uma equipe em uma semana.",
 "O passo seguinte é a replicação prospectiva em um segundo microciclo, com o limiar fixado antes da coleta.",
]:
    para("— "+t)

head("5 O ESTUDO NAS SEIS FASES DO CRISP-DM")
para("O CRISP-DM organiza um projeto de análise em seis fases que se retroalimentam (CHAPMAN et al., 2000). "
     "O quadro abaixo mapeia o estudo nessas fases e declara, em cada uma, a divisão entre o que foi automatizado "
     "e o que permaneceu decisão humana. A separação é o ponto: o que a automação decide sozinha não constitui "
     "achado.")
caption("Quadro M1 — O estudo nas seis fases do CRISP-DM")
mktable(["Fase","Pergunta da fase","Automação","Decisão humana"],
        [[f"{f['n']} {f['nome']}", f['pergunta'], f['copiloto'], f['humano']] for f in CD['FASES']],
        widths=[2.6,3.8,4.4,4.2], fs=8)
src(nota="A coluna de automação descreve o que foi executado por rotina ou por assistente de programação; a "
         "coluna seguinte, o que exigiu julgamento do pesquisador. Os artefatos correspondentes estão no "
         "repositório do estudo.")
para("Seis regras atravessam as fases, e cada uma nasceu de um erro cometido e corrigido neste estudo:")
for r in CD['REGRAS']:
    para(f"— {r['t']}. {r['d']}")

head("6 REPRODUÇÃO")
para("Toda a cadeia é reconstruída por um comando (atualizar.sh), em sete etapas: base canônica a partir da "
     "fonte-verdade, classificação nos perfis, as três vias de análise, banco único, acervo das planilhas e "
     "índice de busca, modelagem e diagnóstico, exportações e figuras. Os roteiros da modelagem são V2_ml.py, "
     "V2_ml2.py e V2_ml3.py; o mapa das fases é V2_crispdm.py. Os resultados aqui relatados foram lidos desses "
     "arquivos no momento da composição do documento, e não transcritos de versões anteriores.")
para("A base anonimizada e os roteiros podem ser disponibilizados mediante solicitação ao autor correspondente. "
     "As planilhas de origem que contêm identificação nominal não integram o pacote de dados, em nenhuma "
     "hipótese.", after=12)

head("REFERÊNCIAS")
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite"))
usadas=[r for r in cx.execute("SELECT abnt,url_doi,autores FROM referencia ORDER BY id")]
cx.close()
para("CHAPMAN, P.; CLINTON, J.; KERBER, R.; KHABAZA, T.; REINARTZ, T.; SHEARER, C.; WIRTH, R. "
     "CRISP-DM 1.0: step-by-step data mining guide. [S. l.]: SPSS Inc., 2000.",
     indent=False, size=11, spacing=1.0, after=6, align=WD_ALIGN_PARAGRAPH.LEFT)
for abnt,doi,aut in usadas:
    if any(k in (aut or '').upper() for k in ('TERRY','PARSONS','LANE','BEEDIE','MORGAN')):
        para(abnt + (f" Disponível em: {doi}." if doi else ""), indent=False, size=11, spacing=1.0,
             after=6, align=WD_ALIGN_PARAGRAPH.LEFT)
out=f"{S}/ANEXO_MODELAGEM_CRISP_DM.docx"
doc.save(out); print("salvo:", out)
