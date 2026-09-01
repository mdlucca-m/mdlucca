# -*- coding: utf-8 -*-
"""Anexo metodológico: modelagem preditiva e o estudo mapeado no CRISP-DM."""
import os, sys
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"_docx_base.py")).read())
import sqlite3
def jd(n): return json.load(open(os.path.join(DADOS,n+".json"),encoding='utf-8'))
ML=jd("V2_ml"); ML2=jd("V2_ml2"); ML3=jd("V2_ml3"); CD=jd("V2_crispdm")
CO=jd("V2_conf"); QA=jd("V2_qual"); TEJ=jd("V2_te"); PS=jd("V2_psico")
def n_(x,d=3):
    if x is None or (isinstance(x,float) and x!=x): return "—"
    return f"{x:.{d}f}".replace('.',',').replace('-','−')
def pf_(p,d=3):
    if p is None: return "—"
    return "< 0,001" if p<0.001 else f"{p:.{d}f}".replace('.',',')

para("ANEXO METODOLÓGICO", indent=False, bold=True, size=14,
     align=WD_ALIGN_PARAGRAPH.CENTER, after=6, spacing=1.15)
para("Modelagem preditiva, limiares de mudança e o processo do estudo mapeado nas seis fases do CRISP-DM",
     indent=False, italic=True, size=11, align=WD_ALIGN_PARAGRAPH.CENTER, after=18, spacing=1.15)

head("1 OBJETIVO")
para("O monitoramento psicológico só se converte em prática quando alcança a escala de decisão da comissão "
     "técnica, que é diária e individual. Revisões recentes da perspectiva de treinadores mostram que o dado é "
     "procurado para reduzir lesão, ajustar o programa e sustentar o rendimento, e que a sua utilidade percebida "
     "depende da devolutiva oferecida ao atleta (TIMMERMAN; ABBISS; LAWLER, 2024; WOOLMER; MORRIS; NOON, 2025). A "
     "analítica esportiva, por sua vez, ganhou sofisticação computacional sem resolver a tradução do modelo em "
     "conduta interpretável (LOBO, 2026). Neste intervalo se situa o presente anexo.")
para("Os dois artigos descrevem o comportamento das dimensões do humor ao longo do microciclo terminal e "
     "submetem cada contraste a três vias de análise. Este anexo responde a outra pergunta, de natureza "
     "operacional: a medida da manhã antecipa o estado da noite do mesmo dia? A pergunta interessa à comissão "
     "técnica porque o horizonte de decisão é de horas: a informação da manhã precisa servir à sessão que começa depois "
     "dela.")
para("O anexo cumpre também uma segunda função. A modelagem preditiva sobre amostra pequena produz números "
     "otimistas com facilidade, e o registro do que foi feito para evitá-los importa tanto quanto o resultado. "
     "A seção 5 organiza o estudo inteiro nas seis fases do CRISP-DM (CHAPMAN et al., 2000) e separa, em cada "
     "fase, o que coube à automação e o que permaneceu decisão humana.")

head("1.1 O processo completo, em um mapa", lvl=2)
para("O leitor que chega a este anexo pelos dois artigos precisa reconstruir mentalmente uma cadeia longa: "
     "o que foi coletado, como o dado foi limpo, que unidade de análise foi adotada, quais pareamentos "
     "sustentam cada teste e onde a modelagem se encaixa. A Figura 1 apresenta essa cadeia inteira em cinco "
     "etapas, do export do formulário às saídas, com os números de cada passagem e o circuito de "
     "reconferência que a fecha.")
figura(os.path.join(S,"M3fig.png"), fig(),
       "Do formulário ao resultado: coleta, limpeza e auditoria, unidades de análise, pareamentos e análises.",
       w=16.5)
para("A Figura 2 desdobra a etapa de modelagem em um framework próprio. Ele responde a três perguntas em "
     "sequência: o que se mede e em que instante do dia, o que protege a inferência de produzir otimismo, e "
     "o que o resultado permite dizer. A separação temporal entre a manhã, o estímulo do dia e a noite é a "
     "condição que torna a previsão não circular; as quatro salvaguardas da faixa central são o que impede "
     "que um desempenho aparente se confunda com memorização do atleta.")
figura(os.path.join(S,"M4fig.png"), fig(),
       "Framework do estudo de modelagem: o eixo temporal do dia, as salvaguardas da inferência e o alcance "
       "de cada resultado.", w=16.5)

head("2 MÉTODO")
head("2.1 Unidade, alvo e preditores", lvl=2)
para(f"A unidade é o par atleta-dia com medida da manhã e medida da noite, o que produz {ML['n']} observações "
     f"de {ML['atletas']} atletas. O desfecho é binário: o atleta termina o dia classificado em um dos três perfis da faixa de risco, a saber, barbatana de tubarão, "
     "iceberg invertido ou everest invertido. A taxa de "
     f"eventos é de {n_(ML['eventos']/ML['n']*100,1)}% ({ML['eventos']} de {ML['n']}).")
para("Os preditores vêm exclusivamente da medida da manhã: as seis subescalas do BRUMS, a perturbação total "
     "do humor, a fadiga física e a mental, a sonolência de Epworth, o estresse percebido, o indicador de já "
     "estar na faixa de risco pela manhã, o dia do microciclo, as horas de treino do dia, a carga acumulada e "
     "o tipo de estímulo. Alvo e preditores ficam separados no tempo, de modo que a previsão não é circular.")
head("2.2 Integridade da base usada na modelagem", lvl=2)
para("A modelagem herda a base dos dois artigos, e com ela as duas auditorias que a precederam. A primeira "
     "fixou a procedência e declarou a unidade de análise. A segunda desceu ao nível do item: os nove escores "
     f"calculados foram reconstruídos por fórmula e confrontados com a base de origem em "
     f"{format(sum(c['n_comparado'] for c in QA['CONFRONTO']),',').replace(',','.')} conferências, sem divergência, e nenhum dos 456 "
     "registros apresenta valor fora do domínio admissível da sua escala.")
para("Duas consequências recaem sobre este anexo. A primeira é que a sonolência de Epworth, que entra como "
     "preditor, teve o domínio corrigido de zero a vinte e quatro para zero a dezoito: o formulário aplicou "
     "seis das oito situações da escala, e o rótulo da coluna de origem estava incorreto. A correção não "
     "altera nenhum valor observado, apenas o intervalo declarado. A segunda é que o número de pares "      f"disponíveis para a modelagem ({ML['n']}) foi confirmado por "
     "recálculo independente, junto com a "
     f"contagem de atletas e de eventos.")
para(f"A reconferência abrangeu {CO['total']} valores dos três documentos, recalculados por um caminho de "
     "código que parte do item do formulário em vez das colunas já pontuadas. Todos coincidem dentro da "
     "tolerância adotada.")

head("2.3 Validação e linhas de base", lvl=2)
para("A validação é cruzada, estratificada e agrupada por atleta: nenhum atleta aparece ao mesmo tempo no "
     "conjunto de treino e no de teste. A distinção não é formal. Com 27 atletas e sete dias, uma divisão por "
     "linha permitiria ao modelo reconhecer o atleta em vez de aprender a regra, e a área sob a curva subiria "
     "sem que nada tivesse sido aprendido. Os intervalos de confiança vêm de reamostragem agrupada, pelo mesmo "
     "motivo.")
para("Dois modelos triviais entram na comparação como referência obrigatória. O primeiro atribui a todos a "
     "classe majoritária. O segundo aplica a regra que qualquer preparador aplicaria de cabeça: quem amanhece "
     f"na faixa de risco termina o dia na faixa de risco. Essa regra acerta {n_(ML['regra_trivial']*100,1)}% dos "
     "casos, e é contra ela, e não contra o acaso, que os modelos precisam mostrar ganho.")
head("2.4 Modelos", lvl=2)
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
caption(f"Tabela {tab()} – Desempenho dos modelos e das duas linhas de base, com validação agrupada por atleta")
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
figura(os.path.join(S,"M1fig.png"), fig(),
       "Área sob a curva dos modelos e das linhas de base, na amostra completa e no subgrupo acionável")

head("3.2 A árvore e o que ela usa", lvl=2)
folhas=[n for n in ML2['ARVORE'] if n['tipo']=='folha']
caption(f"Tabela {tab()} – Folhas da árvore de decisão, ordenadas pelo risco previsto")
mktable(["Caminho da manhã até a folha","n","Risco previsto"],
        [[" e ".join(f['caminho']).replace('.',','), str(f['n']), n_(f['p']*100,0)+"%"]
         for f in sorted(folhas,key=lambda f:-f['p'])],
        widths=[10.5,1.5,3.5], fs=8.5)
src(nota="Profundidade máxima de três e mínimo de doze pares por folha. Os limiares estão nas unidades brutas "
         "de cada instrumento.")
imp=ML2['IMPORTANCIA'][:5]
para("A importância por permutação, medida fora da amostra, concentra-se em duas variáveis: a perturbação "
     f"total do humor pela manhã, cuja permuta derruba a AUC em {n_(imp[0]['media'])}, e a tensão pela manhã, "
     f"que derruba {n_(imp[1]['media'])}. As demais somam pouco, pois a terceira colocada, a fadiga pela manhã, "      f"responde por apenas "
     "{n_(imp[2]['media'])}, e o indicador de já estar em risco pela "
     f"manhã, que sustenta a regra trivial, aparece com apenas {n_([e for e in ML2['IMPORTANCIA'] if 'risco' in e['var'].lower()][0]['media'])}. "
     "O modelo, em outras palavras, não reproduz a regra trivial por outro caminho.")

head("3.3 Diagnóstico: achado ou aritmética do desenho?", lvl=2)
para("O primeiro corte da árvore é contraintuitivo. Ele separa pela perturbação total do humor e atribui maior "
     "risco vespertino a quem amanhece com o escore mais favorável. Antes de qualquer leitura clínica, a "
     "hipótese concorrente precisa ser afastada: quem amanhece no piso da escala só tem para onde subir, e o corte poderia refletir reversão à média em vez de risco.")
rv=sorted(ML3['REVERSAO'],key=lambda e:e['rho'])
caption(f"Tabela {tab()} – Reversão à média: correlação entre o valor da manhã e a própria variação até a noite")
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
figura(os.path.join(S,"M2fig.png"), fig(),
       "Reversão à média por dimensão e contribuição da tensão matinal em modelos aninhados")
para("A leitura substantiva é a seguinte. Alguma tensão pela manhã protege; a ausência completa de tensão em "
     "atleta que amanhece muito favorável antecede a queda vespertina. O achado converge com o que os dois "
     "artigos observam por outra via: neste elenco, a tensão se comporta como ativação, e não como sofrimento.")

head("3.4 Do modelo ao limiar: a mudança mínima importante", lvl=2)
para("O modelo preditivo entrega uma probabilidade, e a comissão técnica precisa de um número que se aplique "
     "sem computador. A ponte entre os dois é a mudança mínima importante ancorada: em vez de partir da "
     "distribuição, parte do desfecho clínico e pergunta qual variação o acompanha. Tomada como âncora a "
     "entrada na faixa de risco entre a manhã e a noite, restrita a quem amanhece fora dela, o resultado "
     "aparece na Tabela abaixo.")
_MMI={m['variavel']:m for m in TEJ['MMI']}; _ET={t['variavel']:t for t in TEJ['TE']}
caption(f"Tabela {tab()} – Mudança mínima importante ancorada na entrada em risco, e a sua leitura contra o erro típico")
mktable(["Variável","AUC da variação","Ponto de corte","Sensibilidade","Especificidade","Corte ÷ erro típico",
         "Supera a menor mudança relevante"],
        [[('PTH' if v=='TMD' else v), n_(_MMI[v]['auc'],3),
          (n_(_MMI[v]['corte'],1) if _MMI[v]['discrimina'] else "não discrimina"),
          (n_(_MMI[v]['sens'],2) if _MMI[v]['discrimina'] else "—"),
          (n_(_MMI[v]['espec'],2) if _MMI[v]['discrimina'] else "—"),
          (n_(_MMI[v]['corte_sobre_et']) if _MMI[v]['discrimina'] else "—"),
          (("sim" if _MMI[v]['supera_mmr'] else "não") if _MMI[v]['discrimina'] else "—")]
         for v in ['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão','TMD']],
        widths=[2.0,2.4,2.3,2.2,2.4,2.3,3.0], fs=8)
src(nota=f"Sobre {TEJ['n_casos_ancora']} pares que amanhecem fora da faixa, dos quais {TEJ['eventos_ancora']} "
         "entram nela até a noite. Ponto de corte pelo índice de Youden; variáveis com área sob a curva "
         "abaixo de 0,60 não recebem corte.")
_f=_MMI['Fadiga']
para(f"O limiar da fadiga é o resultado de maior utilidade prática de todo o estudo. Um aumento de "
     f"{n_(_f['corte'],0)} pontos entre a manhã e a noite identifica a entrada na faixa de risco com "
     f"sensibilidade de {n_(_f['sens'],2)} e especificidade de {n_(_f['espec'],2)}, sobre área sob a curva de "
     f"{n_(_f['auc'],3)}. O corte equivale a {n_(_f['corte_sobre_et'])} vezes o erro típico da medida, de modo "
     "que não se confunde com a oscilação do instrumento. A perturbação total do humor oferece um segundo "
     f"critério, com corte de {n_(_MMI['TMD']['corte'],0)} pontos e área de {n_(_MMI['TMD']['auc'],3)}.")
para("Duas ressalvas delimitam o uso. O corte foi obtido no mesmo conjunto em que é avaliado, sem validação "
     "externa, e por isso a área sob a curva é otimista. E a subescala de tensão, que a análise de "
     "confiabilidade do artigo descritivo mostrou ter alfa de "
     f"{n_([c for c in PS['CONF'] if c['subescala']=='Tensão'][0]['alfa'],3)} neste elenco, não discrimina como âncora, resultado coerente: o marcador protetor identificado pela modelagem é a "
     "apreensão antecipatória do início do dia, não a variação da tensão ao longo dele.")

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
    para("• "+t)

head("5 O ESTUDO NAS SEIS FASES DO CRISP-DM")
para("O CRISP-DM organiza um projeto de análise em seis fases que se retroalimentam (CHAPMAN et al., 2000). "
     "O quadro abaixo mapeia o estudo nessas fases e declara, em cada uma, a divisão entre o que foi automatizado "
     "e o que permaneceu decisão humana. A separação é o ponto: o que a automação decide sozinha não constitui "
     "achado.")
caption(f"Quadro {quadro()} – O estudo nas seis fases do CRISP-DM")
mktable(["Fase","Pergunta da fase","Automação","Decisão humana"],
        [[f"{f['n']} {f['nome']}", f['pergunta'], f['copiloto'], f['humano']] for f in CD['FASES']],
        widths=[2.6,3.8,4.4,4.2], fs=8)
src(nota="A coluna de automação descreve o que foi executado por rotina ou por assistente de programação; a "
         "coluna seguinte, o que exigiu julgamento do pesquisador. Os artefatos correspondentes estão no "
         "repositório do estudo.")
para("Seis regras atravessam as fases, e cada uma nasceu de um erro cometido e corrigido neste estudo:")
for r in CD['REGRAS']:
    para(f"• {r['t']}. {r['d']}")

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
# apenas as obras efetivamente citadas neste anexo
CITADAS=('LOBO','TIMMERMAN','WOOLMER')
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite"))
usadas=[r for r in cx.execute("SELECT abnt,url_doi,autores FROM referencia ORDER BY id")]
cx.close()
para("CHAPMAN, P.; CLINTON, J.; KERBER, R.; KHABAZA, T.; REINARTZ, T.; SHEARER, C.; WIRTH, R. "
     "CRISP-DM 1.0: step-by-step data mining guide. [S. l.]: SPSS Inc., 2000.",
     indent=False, size=11, spacing=1.0, after=6, align=WD_ALIGN_PARAGRAPH.LEFT)
for abnt,doi,aut in usadas:
    if any(k in (aut or '').upper() for k in CITADAS):
        para(abnt + (f" Disponível em: {doi}." if doi else ""), indent=False, size=11, spacing=1.0,
             after=6, align=WD_ALIGN_PARAGRAPH.LEFT)
out=f"{S}/ANEXO_MODELAGEM_CRISP_DM.docx"
doc.save(out); print("salvo:", out)
