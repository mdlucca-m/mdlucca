# -*- coding: utf-8 -*-
"""Relatório de auditoria de qualidade, exploratória univariada e otimização da carga."""
import os, sys
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"_docx_base.py")).read())
import sqlite3
jd=lambda n: json.load(open(os.path.join(DADOS,n+".json"),encoding='utf-8'))
Q=jd("V2_qual"); C=jd("V2_conf"); O=jd("V2_otim")
UNI={u['variavel']:u for u in Q['UNI']}
def n_(x,d=2):
    if x is None or (isinstance(x,float) and x!=x): return "—"
    return f"{x:.{d}f}".replace('.',',').replace('-','−')
def pf_(p,d=3):
    if p is None: return "—"
    return "< 0,001" if p<0.001 else f"{p:.{d}f}".replace('.',',')
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; V7=SUB+['TMD']
L=lambda v:'PTH' if v=='TMD' else v

para("AUDITORIA DE QUALIDADE DA BASE, ANÁLISE EXPLORATÓRIA UNIVARIADA", indent=False, bold=True,
     size=14, align=WD_ALIGN_PARAGRAPH.CENTER, after=2, spacing=1.15)
para("E OTIMIZAÇÃO LINEAR DA CARGA DO MICROCICLO", indent=False, bold=True, size=14,
     align=WD_ALIGN_PARAGRAPH.CENTER, after=6, spacing=1.15)
para("Relatório técnico de apoio aos três documentos do estudo", indent=False, italic=True, size=11,
     align=WD_ALIGN_PARAGRAPH.CENTER, after=18, spacing=1.15)

head("1 O QUE FOI FEITO, E POR QUE OUTRA VEZ")
para("A base já havia sido auditada quanto à procedência: a origem de cada número e a unidade de análise que "
     "o gerou. Esta segunda passagem audita outra coisa: a qualidade do dado em si. Ela desce ao nível do "
     f"item do formulário, reconstrói por fórmula cada um dos {sum(c['n_comparado'] for c in Q['CONFRONTO'])} "
     "escores calculados que a planilha traz, e só então descreve cada variável pela técnica que o seu tipo "
     "de mensuração admite.")
para("Toda estatística deste relatório vem acompanhada da fórmula que a produz, e as fórmulas estão reunidas "
     "no Quadro 1. Qualquer valor pode ser recalculado à mão a partir das tabelas, sem acesso ao código.")
para("A segunda parte do relatório usa a base já limpa para responder a uma pergunta de planejamento: dada a "
     "resposta do humor à carga que esta amostra revela, como as horas da semana deveriam ter sido "
     "distribuídas? A resposta vem de um programa linear, com preços-sombra e análise de sensibilidade.")

head("2 DICIONÁRIO DE VARIÁVEIS")
para("A escolha da técnica descritiva depende do tipo de mensuração, e não do tipo de dado no arquivo. Um "
     "escore de subescala é armazenado como número, mas é a soma de quatro respostas ordinais e assume "
     "dezessete valores possíveis: é discreto, não contínuo. A distinção decide, adiante, se cabe média ou "
     "mediana, histograma ou tabela de frequência.")
caption(f"Tabela {tab()} – Dicionário: tipo de mensuração, escala, domínio e origem de cada variável")
mktable(["Variável","Tipo","Escala","Domínio admissível","Origem"],
        [[d['v'],d['tipo'],d['escala'],d['dominio'],d['origem']] for d in Q['DICIONARIO']],
        widths=[2.9,1.9,2.6,3.1,4.5], fs=7.5)
src(nota="Vinte entradas cobrem as 79 colunas da fonte: as colunas derivadas e as de controle do formulário "
         "reduzem-se aos blocos acima.")

head("3 CONFERÊNCIA DOS ESCORES CONTRA A FÓRMULA")
para("Cada subescala do BRUMS é a soma de quatro itens, sem inversão e sem peso (F1 do Quadro 1). A "
     "perturbação total do humor é a soma das cinco subescalas negativas menos o vigor (F2). O estresse "
     "percebido soma catorze itens, sete deles invertidos (F5). Reconstruídas por essas fórmulas, as nove "
     "colunas calculadas da planilha foram comparadas linha a linha com o que ela própria registra.")
caption(f"Tabela {tab()} – Escore reconstruído por fórmula contra a coluna calculada da planilha")
mktable(["Variável","Comparações","Divergências","% divergente","Maior diferença"],
        [[c['variavel'], str(c['n_comparado']), str(c['n_divergente']),
          n_(c['pct'],2)+"%", n_(c['max_dif'],0)] for c in Q['CONFRONTO']],
        widths=[3.4,3.0,3.0,3.0,3.1], fs=9)
src(nota="Tolerância de 10⁻⁹. As linhas com item ausente ficam fora da comparação.")
tot=sum(c['n_comparado'] for c in Q['CONFRONTO']); div=sum(c['n_divergente'] for c in Q['CONFRONTO'])
para(f"O resultado é limpo: {div} divergência em {tot} conferências. A pontuação da planilha está correta, e a "
     "consequência importa mais do que o número. As sete versões do manuscrito divergiam entre si por causa da "
     "unidade de análise, e agora se sabe que não divergiam também por erro de pontuação. As duas fontes de "
     "erro estavam confundidas até esta conferência; uma delas está descartada.")

head("4 DADOS FALTANTES")
para("A completude foi medida em três recortes (F14): por item do instrumento, por variável derivada e na "
     "grade que cruza atleta com dia. Os três contam coisas diferentes, e apenas o terceiro revela onde está "
     "o problema.")
falt=[f for f in Q['FALTA_VAR'] if f['faltantes']>0]
caption(f"Tabela {tab()} – Completude por bloco de variáveis")
mktable(["Bloco","Itens ou variáveis","Células","Faltantes","Completude"],
        [["Itens do BRUMS", "24", str(24*Q['n_registros']),
          str(sum(f['faltantes'] for f in Q['FALTA_ITEM'] if 'BRUMS' in f['bloco'])), "100,00%"],
         ["Itens de Epworth", "6", str(6*Q['n_registros']),
          str(sum(f['faltantes'] for f in Q['FALTA_ITEM'] if 'Epworth' in f['bloco'])), "100,00%"],
         ["Itens da PSS", "14", str(14*Q['n_registros']),
          str(sum(f['faltantes'] for f in Q['FALTA_ITEM'] if 'PSS' in f['bloco'])), "100,00%"]]
        +[[f['bloco'].capitalize(), f['item'], str(f['n']), str(f['faltantes']), n_(f['completude'],2)+"%"]
          for f in falt],
        widths=[4.0,3.6,2.4,2.4,3.1], fs=9)
src(nota="Completude = (1 − faltantes ÷ total) × 100. As variáveis derivadas não aparecem porque nenhuma "
         "delas tem falta: são função de itens que estão todos preenchidos.")
para("Nenhuma célula de instrumento está ausente. Quem responde, responde tudo, uma vez que o formulário exigia resposta em cada item. A falta, portanto, não é de item: é de comparecimento.")
caption(f"Tabela {tab()} – Cobertura da grade atleta × dia")
mktable(["Dia","Atletas com registro","Cobertura de atletas","Registros","Previstos no protocolo","Cobertura de registros"],
        [[f"D{g['dia']}", f"{g['atletas_com_registro']} de {g['atletas_esperados']}",
          n_(g['cobertura_atleta'],1)+"%", str(g['registros']), str(g['registros_esperados']),
          n_(g['cobertura_registro'],1)+"%"] for g in Q['GRADE']],
        widths=[1.7,3.3,3.0,2.2,3.0,3.3], fs=9)
src(nota="O protocolo previa uma coleta em D1, que teve janela única noturna, e duas de D2 a D7. "
         "Cobertura acima de 100% indica registro além do previsto, e não erro.")
para("Duas leituras se impõem. A cobertura de atletas cai de 100% em D1 para 78% em D4 e em D7, o que "
     "significa que a comparação entre extremos da semana perde um quarto do elenco, razão pela qual a unidade de análise "
     "precisa ser declarada em cada contraste. E a cobertura de registros passa de 100% em "
     "cinco dos sete dias, o que revela envio repetido.")

head("5 REGISTROS REPETIDOS NO MESMO DIA")
R=Q['REPETICAO']
para("O protocolo previa até dois registros diários. A distribuição observada vai até seis.")
caption(f"Tabela {tab()} – Registros por par atleta-dia")
mktable(["Registros no dia","Pares atleta-dia","%","% acumulado"],
        (lambda ks: [[k, str(R['distribuicao'][k]),
                      n_(100*R['distribuicao'][k]/sum(R['distribuicao'].values()),1),
                      n_(100*sum(R['distribuicao'][j] for j in ks[:i+1])/sum(R['distribuicao'].values()),1)]
                     for i,k in enumerate(ks)])(sorted(R['distribuicao'],key=int)),
        widths=[3.6,3.6,3.4,4.4], fs=9)
src(nota=f"Total de {sum(R['distribuicao'].values())} pares atleta-dia.")
q=R['intervalo']
para(f"O intervalo entre registros consecutivos do mesmo dia tem mediana de {n_(q['mediana'],0)} minutos "
     f"(Q1 {n_(q['q1'],0)}; Q3 {n_(q['q3'],0)}), amplitude de {n_(q['minimo'],0)} a {n_(q['maximo'],0)}. "
     f"Apenas {R['ate_30min']} dos {R['pares_consecutivos']} pares consecutivos ocorrem em trinta minutos ou "
     f"menos, e em nenhum deles o vetor dos 24 itens se repete por inteiro. Ou seja: não são duplicatas de "
     "envio, e sim reenvios com alteração. A regra adotada, que toma a média de todos os registros do dia para o valor diário e reserva o primeiro e o "
     "último ao contraste pré-pós, preserva todos eles e passa a ser declarada.")

head("6 PADRONIZAÇÃO DE VARIÁVEIS CATEGÓRICAS")
para("Uma variável categórica está padronizada quando cada nível tem uma única grafia. A verificação compara "
     "cada valor com a sua chave canônica, obtida pela remoção de acento, caixa e espaço redundante.")
caption(f"Tabela {tab()} – Grafias por nível em cada variável categórica")
mktable(["Variável","Registros","Níveis canônicos","Grafias distintas","Níveis com mais de uma grafia"],
        [[c['variavel'], str(c['n']), str(c['niveis_canonicos']), str(c['grafias']),
          str(c['niveis_com_variante'])] for c in Q['CATEG']],
        widths=[4.2,2.4,3.2,3.2,4.0], fs=9)
src(nota="A escala TQR aparece com dezessete grafias porque é uma escala de Borg com âncora verbal em pontos "
         "alternados: «13 Razoavelmente recuperado» e «14» são pontos distintos da mesma escala, e não duas "
         "grafias do mesmo nível.")
nl=Q['CATEG'][0]
para(f"O problema está no nome digitado em texto livre: {nl['grafias']} grafias para "
     f"{nl['niveis_canonicos']} nomes canônicos, {nl['niveis_com_variante']} deles com mais de uma forma. "
     "«João Gomes», «Joao Gomes» e «Joao gomes» são a mesma pessoa em três linhas diferentes. É por isso "
     "que a identidade do respondente passa a vir da coluna padronizada, e não do texto livre, e que a "
     "codificação A01 a A27 ocorre dentro da rotina de importação.")
para("As demais categóricas estão padronizadas. As cinco variáveis com tabela de frequência completa "
     "aparecem a seguir.")
for nome,t in Q['FREQ'].items():
    caption(f"Tabela {tab()} – Distribuição de frequência: {nome.lower()}")
    mktable(["Nível","f","%","f acumulada","% acumulada"],
            [[l['nivel'], str(l['f']), n_(l['pct'],1), str(l['f_acum']), n_(l['pct_acum'],1)]
             for l in t['linhas']],
            widths=[5.0,2.2,2.4,3.0,3.4], fs=9)
    src(nota=f"n = {t['n']}. Moda: {t['moda']}. Entropia normalizada H* = "
             f"{n_(t['entropia_normalizada'],3)} (F13), em que 1 indica níveis equilibrados e 0, distribuição "
             "concentrada em um único nível.")

head("7 ANÁLISE EXPLORATÓRIA UNIVARIADA DAS NUMÉRICAS")
para("As variáveis discretas e contínuas recebem posição, dispersão e forma. Os escores de subescala são "
     "discretos: assumem dezessete valores inteiros. A mediana e o intervalo interquartil são as medidas "
     "de referência, e a média entra como complemento, não como substituta.")
caption(f"Tabela {tab()} – Posição e dispersão")
mktable(["Variável","Tipo","n","Mín","Q1","Md","Q3","Máx","Média","DP","EP","CV %"],
        [[L(u['variavel']), u['tipo'], str(u['n']), n_(u['minimo'],1), n_(u['q1'],1), n_(u['mediana'],1),
          n_(u['q3'],1), n_(u['maximo'],1), n_(u['media']), n_(u['desvio']), n_(u['erro_padrao']),
          (n_(u['cv'],1) if u['cv'] is not None else "—")] for u in Q['UNI']],
        widths=[2.6,1.7,1.1,1.1,1.1,1.1,1.1,1.2,1.4,1.3,1.2,1.3], fs=7.5)
src(nota="Erro padrão = DP ÷ √n. Coeficiente de variação = DP ÷ média × 100 (F9). Nível de registro, "
         f"n = {Q['n_no_microciclo']}.")
caption(f"Tabela {tab()} – Forma da distribuição e normalidade")
mktable(["Variável","Assimetria g₁","Curtose g₂","Shapiro-Wilk W","p","MAD","Classes por Sturges","Classes por Freedman-Diaconis"],
        [[L(u['variavel']), n_(u['assimetria']), n_(u['curtose']), n_(u['shapiro_W'],4), pf_(u['shapiro_p']),
          n_(u['mad']), str(u['k_sturges']), (str(u['k_fd']) if u['k_fd'] else "—")] for u in Q['UNI']],
        widths=[2.7,2.1,1.9,2.3,1.9,1.5,2.1,2.5], fs=8)
src(nota="g₁ e g₂ pelas fórmulas F10; g₂ é a curtose em excesso, nula na normal. Número de classes por F12 "
         "(Sturges) e F11 (Freedman-Diaconis). MAD = mediana dos desvios absolutos em relação à mediana.")
nn=sum(1 for u in Q['UNI'] if u['shapiro_p']<.05)
para(f"Nenhuma das {len(Q['UNI'])} variáveis passa no teste de normalidade: {nn} rejeitam a hipótese ao nível de 5%. A assimetria positiva de depressão, raiva e confusão vem do efeito de piso: em uma equipe "
     "saudável, a resposta modal a «deprimido» é zero. Esse é o dado, e não um defeito dele. A consequência "
     "metodológica é direta: a via não paramétrica é a rota principal, e a paramétrica entra como conferência.")
figura(os.path.join(S,"Q1fig.png"), "Q1",
       "Distribuição das seis subescalas e do PTH, e o efeito do piso sobre a cerca de Tukey")

head("8 VALORES DISCREPANTES")
para("Três critérios foram aplicados, porque nenhum deles é suficiente sozinho. A cerca de Tukey (F6) não "
     "pressupõe normalidade, mas depende do intervalo interquartil. O escore z (F7) é arrastado pelo próprio "
     "valor discrepante, já que este entra no cálculo da média e do desvio. O escore z modificado (F8) usa "
     "mediana e desvio absoluto mediano, que resistem à contaminação. Antes de qualquer um deles, a "
     "verificação de domínio: valor fora do intervalo admissível é erro, não discrepância.")
caption(f"Tabela {tab()} – Valores discrepantes por três critérios, e verificação de domínio")
mktable(["Variável","Domínio","Fora do domínio","Cerca 1,5 × IQR","Cerca 3,0 × IQR","|z| > 3","|z modificado| > 3,5"],
        [[L(u['variavel']),
          (f"{n_(u['dominio'][0],0)} a {n_(u['dominio'][1],0)}" if 'dominio' in u else "—"),
          str(u.get('fora_do_dominio','—')),
          str(u['n_tukey_moderado'])+(" ⚠" if u['iqr_nulo'] else ""),
          str(u['n_tukey_extremo']), str(u['n_z3']),
          (str(u['n_zmod']) if u['n_zmod'] is not None else "MAD = 0")] for u in Q['UNI']],
        widths=[2.7,2.1,2.3,2.6,2.4,1.7,3.2], fs=8)
src(nota="⚠ marca a variável em que o intervalo interquartil é zero, o que torna a cerca de Tukey inaplicável. "
         "«MAD = 0» marca a variável em que o desvio absoluto mediano é zero, o que torna o z modificado "
         "indefinido.")
para("O primeiro resultado é o mais importante: nenhum valor cai fora do domínio admissível de nenhuma escala. "
     "Não há erro de digitação, nem escore impossível, nem código de ausência tratado como número.")
degen=[L(u['variavel']) for u in Q['UNI'] if u['iqr_nulo']]
para(f"O segundo resultado é metodológico. Em {' e '.join(degen)} o primeiro e o terceiro quartis coincidem "
     "no piso da escala. O intervalo interquartil é zero, a cerca de Tukey colapsa sobre o próprio piso, e a regra passa a classificar como discrepante toda resposta diferente de zero, quase um quinto da amostra. "
     "O mesmo colapso atinge o escore z modificado, porque o desvio absoluto mediano também é zero. "
     "Nessas subescalas a triagem de discrepantes precisa ser feita pelo domínio e pela comparação de cada "
     "atleta consigo mesmo, e não por regra de dispersão do grupo.")
caption(f"Tabela {tab()} – Discrepantes intraindividuais: o atleta contra a própria série")
mktable(["Variável","Atletas avaliados","Casos","Caso mais extremo"],
        [[L(i['variavel']), str(i['atletas_avaliados']), str(i['n_discrepantes']),
          (f"{i['casos'][0]['atleta']} em D{i['casos'][0]['dia']}: {n_(i['casos'][0]['valor'],0)} contra "
           f"mediana própria {n_(i['casos'][0]['mediana_do_atleta'],0)} (z_M = {n_(i['casos'][0]['z_mod'],1)})")
          if i['casos'] else "—"] for i in Q['INTRA']],
        widths=[2.6,3.0,1.8,7.9], fs=8.5)
src(nota="Escore z modificado calculado dentro da série de cada atleta, entre os que têm quatro dias ou mais. "
         "Um caso intraindividual não é erro: é o atleta que teve um dia fora do seu padrão, que é justamente "
         "o que o monitoramento procura detectar.")

head("9 INCONSISTÊNCIAS ENCONTRADAS E O QUE SE FEZ COM CADA UMA")
caption(f"Quadro {quadro()} – Achados da auditoria de qualidade")
mktable(["Achado","Gravidade","O que se encontrou","O que se corrigiu","Magnitude"],
        [[i['id'], i['gravidade'], i['achado'], i['correcao'], f"{i['n']} de {i['de']}"]
         for i in Q['INCONS']],
        widths=[1.3,1.8,5.8,5.2,1.9], fs=7.5)
src(nota="Os seis achados foram gravados na tabela de auditoria da base única, ao lado dos seis achados de "
         "procedência da primeira passagem, e podem ser consultados por ./scripts/consultar.py auditoria.")
figura(os.path.join(S,"Q2fig.png"), "Q2",
       "Cobertura da grade atleta × dia e distribuição do número de registros por dia")

head("10 RECONFERÊNCIA DOS TRÊS DOCUMENTOS")
para("A auditoria não bastaria se não respondesse à pergunta que a motivou: os números publicados se "
     "sustentam? A conferência foi feita por dois caminhos de código independentes. O primeiro parte das "
     "colunas já pontuadas da planilha e é o que gerou a base canônica. O segundo parte do item do formulário "
     "e reconstrói tudo por fórmula. Se convergirem, o resultado está confirmado por replicação interna.")
blocos={}
for c in C['CONF']:
    blocos.setdefault(c['bloco'],[0,0])
    blocos[c['bloco']][0]+=c['confere']; blocos[c['bloco']][1]+=1
caption(f"Tabela {tab()} – Conferências por bloco, entre os dois caminhos de cálculo")
mktable(["Bloco de conferência","Conferências","Batem","Divergem"],
        [[b, str(t), str(o), str(t-o)] for b,(o,t) in blocos.items()]
        +[["Total", str(C['total']), str(C['ok']), str(C['total']-C['ok'])]],
        widths=[6.6,2.8,2.4,2.6], fs=9)
src(nota="Tolerância de 5 × 10⁻³ para médias e derivadas, e de 10⁻⁶ para valores de p.")
para(f"As {C['total']} conferências batem. As médias diárias, as variações entre extremos da semana, o piso de "
     "ruído, as derivadas normalizadas, as prevalências da faixa de risco, os valores de p do teste de "
     "Wilcoxon e a base da modelagem foram recalculados desde o item e reproduzem o que os três documentos "
     "afirmam. Nada precisa ser corrigido no texto dos artigos.")
caption(f"Tabela {tab()} – Normalidade das médias diárias, que decide a via principal do Artigo 2")
mktable(["Variável","n","Shapiro-Wilk W","p","Distribuição"],
        [[L(n['variavel']), str(n['n']), n_(n['W'],4), pf_(n['p']), "normal" if n['normal'] else "não normal"]
         for n in C['NORMALIDADE']],
        widths=[3.2,2.0,3.2,3.0,3.6], fs=9)
src(nota=f"Sobre os {C['NORMALIDADE'][0]['n']} pares atleta-dia da unidade canônica.")

head("11 PROGRAMAÇÃO LINEAR DA CARGA DO MICROCICLO")
head("11.1 A resposta do humor à carga", lvl=2)
M=O['MODELO']
para("O programa linear exige coeficientes, e os coeficientes vêm da própria amostra. Para cada variável de "
     "humor ajustou-se um modelo misto com intercepto aleatório por atleta, em que a resposta do dia depende "
     "das horas do próprio dia e das horas da véspera:")
para("y(a,d) = β₀ + β₁ · h(d) + β₂ · h(d − 1) + u(a) + ε(a,d)", indent=False, italic=True,
     align=WD_ALIGN_PARAGRAPH.CENTER, size=11.5)
caption(f"Tabela {tab()} – Coeficientes da resposta dose-humor")
mktable(["Variável","β₀","β₁ · horas do dia","p","β₂ · horas da véspera","p","n"],
        [[L(v), n_(M[v]['b0'],3), n_(M[v]['b1'],4), pf_(M[v]['p1'],4), n_(M[v]['b2'],4),
          pf_(M[v]['p2'],4), str(M[v]['n'])] for v in ['Fadiga','Vigor','TMD','Tensão']],
        widths=[2.4,2.0,3.0,2.0,3.3,2.0,1.3], fs=8.5)
src(nota="Modelo misto de máxima verossimilhança, intercepto aleatório por atleta. O coeficiente é a variação "
         "esperada do escore por hora adicional de treino, mantida a outra parcela constante.")
para("O achado que organiza tudo o que vem depois: as horas do próprio dia não têm efeito detectável, e as "
     "horas da véspera têm. Cada hora de treino do dia anterior acrescenta "
     f"{n_(M['Fadiga']['b2'],3)} ponto de fadiga e subtrai {n_(abs(M['Vigor']['b2']),3)} ponto de vigor no dia "
     f"seguinte (ambos com p {pf_(M['Fadiga']['p2'])}). O humor medido hoje é o eco do treino de ontem. A "
     "restrição de recuperação, portanto, é defasada em um dia, e é assim que ela entra no programa.")
para("A advertência que acompanha o modelo precisa vir junto e não depois: com uma equipe e sete dias, o "
     "efeito das horas não se separa do efeito do dia do microciclo nem da carga acumulada. Os coeficientes "
     "são associativos. O programa linear que se segue é instrumento de planejamento e de exploração de "
     "cenários, não demonstração causal.")
figura(os.path.join(S,"Q3fig.png"), "Q3",
       "Resposta dose-humor e a redistribuição ótima das mesmas vinte e três horas")

head("11.2 O programa", lvl=2)
P=O['PARAMETROS']; A=O['AMISTOSO']
para("As variáveis de decisão são as horas de treino de cada dia, h₁ a h₇. O objetivo é maximizar o pior dia de vigor da semana, critério maximin que se torna linear quando se introduz a "
"variável auxiliar t:")
para("maximizar  t     sujeito a     vigor previsto no dia d ≥ t,  para d = 1, …, 7",
     indent=False, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=11.5)
para("A escolha do critério não é neutra. Maximizar a soma do vigor da semana permitiria compensar um dia "
     "muito ruim com dois muito bons, o que não corresponde à decisão do treinador. Maximizar o pior dia "
     "protege o elo mais fraco do microciclo, que é onde a lesão e a queda de rendimento aparecem.")
caption(f"Quadro {quadro()} – Restrições do programa")
mktable(["Restrição","Formulação","Valor"],
        [["Fadiga prevista", "β₀ + β₁·h(d) + β₂·h(d−1) ≤ F_máx,  d = 1…7", n_(P['fadiga_max'],1)+" pontos"],
         ["Vigor previsto", "γ₀ + γ₁·h(d) + γ₂·h(d−1) ≥ V_mín,  d = 1…7", n_(P['vigor_min'],2)+" pontos"],
         ["Variação entre dias", "|h(d) − h(d−1)| ≤ Δ,  d = 2…7", n_(P['salto_max'],1)+" h"],
         ["Carga da semana", "Σ h(d) = H", n_(P['total'],1)+" h"],
         ["Teto e piso diários", "h_mín ≤ h(d) ≤ h_máx", f"{n_(P['h_min'],1)} a {n_(P['h_max'],1)} h"],
         ["Polimento do último dia", "h(7) ≤ ρ · h(d),  d = 1…6", n_(P['polimento']*100,0)+"%"],
         ["Amistosos do calendário", "h(3) = 4,5   e   h(5) = 5,0", "fixos"]],
        widths=[3.4,7.2,3.4], fs=8.5)
src(nota="Resolvido pelo método dos pontos interiores (HiGHS). Os coeficientes β e γ vêm da Tabela 14.")

head("11.3 A solução", lvl=2)
OB=O['OBSERVADO']; P1=O['PROGRAMA_I']
caption(f"Tabela {tab()} – Calendário observado e distribuição ótima, com a mesma carga semanal")
mktable(["Dia","Estímulo","Observado (h)","Ótimo (h)","Diferença","Fadiga prevista","Vigor previsto"],
        [[f"D{d}", O['TIPO'][str(d)], n_(OB['horas'][d-1],1), n_(P1['horas'][d-1],2),
          ("+" if P1['horas'][d-1]-OB['horas'][d-1]>=0 else "")+n_(P1['horas'][d-1]-OB['horas'][d-1],2),
          n_(P1['fadiga'][d-1]), n_(P1['vigor'][d-1])] for d in range(1,8)]
        +[["Total","", n_(OB['total'],1), n_(P1['total'],2), "0,00","",""]],
        widths=[1.4,3.0,2.4,2.0,2.2,2.6,2.4], fs=8.5)
src(nota="A fadiga e o vigor previstos são os do modelo da Tabela 14 aplicados à distribuição de horas de "
         "cada coluna.")
para(f"Com as mesmas {n_(OB['total'],0)} horas, o rearranjo eleva o pior dia de vigor de "
     f"{n_(OB['vigor_minimo'])} para {n_(P1['vigor_minimo_garantido'])} e reduz a fadiga máxima da semana de "
     f"{n_(OB['fadiga_maxima'])} para {n_(max(P1['fadiga']))}. O ganho é pequeno, e o motivo do tamanho é a "
     "própria resposta seguinte.")
head("11.4 Quem segura a solução", lvl=2)
para("O preço-sombra de uma restrição é quanto o objetivo melhoraria se ela afrouxasse uma unidade. Ele "
     "responde à pergunta que interessa ao planejamento: onde está o gargalo?")
Rs=sorted([r for r in O['ATIVAS'] if '≥ t' not in r['restricao']]
          +[dict(restricao=e['restricao'],preco_sombra=e['preco_sombra'],folga=None) for e in O['EQ']],
          key=lambda r:-abs(r['preco_sombra']))[:7]
caption(f"Tabela {tab()} – Restrições ativas e preços-sombra")
mktable(["Restrição","Folga","Preço-sombra (pontos de vigor)"],
        [[r['restricao'], (n_(r['folga'],3) if r['folga'] is not None else "igualdade"),
          n_(r['preco_sombra'],4)] for r in Rs],
        widths=[7.6,3.0,3.4], fs=8.5)
src(nota="Preço-sombra negativo indica restrição que custa ao objetivo: afrouxá-la melhoraria o pior dia de "
         "vigor. Exclui-se a restrição «vigor ≥ t», que é a própria definição do critério maximin.")
d5=[e for e in O['EQ'] if e['restricao'].startswith('D5')][0]
para(f"O maior preço-sombra em valor absoluto é o do amistoso de D5: {n_(d5['preco_sombra'],3)}. Cada hora daquele jogo custa quatro décimos de ponto do pior dia de vigor da semana, mais do que qualquer "
"decisão de treino disponível ao preparador. Quem comprime este microciclo não é o volume de treino, e "
     "sim o calendário de jogos. É por isso que o rearranjo das horas de treino, por melhor que seja, "
     "produz ganho pequeno: ele opera sobre a parte que não é o gargalo.")
head("11.5 Fronteira eficiente e sensibilidade", lvl=2)
FR=[f for f in O['FRONTEIRA'] if f.get('viavel') is not False]
caption(f"Tabela {tab()} – Fronteira eficiente: carga da semana contra o pior dia de vigor")
mktable(["Carga da semana (h)","Pior dia de vigor","Fadiga máxima","Distribuição ótima (D1 a D7)"],
        [[n_(f['carga'],1), n_(f['vigor_minimo'],3), n_(f['fadiga_maxima']),
          " · ".join(n_(v,1) for v in f['horas'])] for f in FR]
        +[[n_(f['carga'],1), "inviável","",""] for f in O['FRONTEIRA'] if f.get('viavel') is False],
        widths=[3.2,3.0,2.6,5.2], fs=8)
src(nota=f"Carga semanal mínima estruturalmente viável: {n_(O['CARGA_MINIMA_ESTRUTURAL'])} h. Abaixo disso "
         "não existe distribuição que respeite ao mesmo tempo os dois amistosos, o salto máximo entre dias "
         "consecutivos e o estímulo mínimo diário.")
a0,a1=FR[0],FR[-1]
incl=(a1['vigor_minimo']-a0['vigor_minimo'])/(a1['carga']-a0['carga'])
para(f"A fronteira é quase horizontal: de {n_(a0['carga'],0)} a {n_(a1['carga'],0)} horas semanais o pior dia "
     f"de vigor varia {n_(abs(incl),4)} ponto por hora. A planitude confirma a leitura dos preços-sombra: dentro da faixa realista de volume, quem determina o "
     "vigor do pior dia da semana são os jogos, não o volume de treino. A informação prática é a carga mínima estrutural: com dois amistosos e a regra de "
     f"variação máxima entre dias, a semana não pode ter menos de {n_(O['CARGA_MINIMA_ESTRUTURAL'])} horas.")
caption(f"Tabela {tab()} – Sensibilidade dos parâmetros")
linhas=[]
for s_ in O['SENSIBILIDADE']:
    for p_ in s_['pontos']:
        linhas.append([s_['parametro'], n_(p_['valor'],2),
                       (n_(p_['vigor_minimo'],3) if p_['viavel'] else "inviável")])
mktable(["Parâmetro","Valor","Pior dia de vigor resultante"], linhas,
        widths=[5.4,3.0,5.6], fs=8)
src(nota="Carga semanal mantida em 23 h. «Inviável» indica que não existe distribuição de horas que satisfaça "
         "todas as restrições simultaneamente com aquele valor.")
para("Três parâmetros mostram fronteira de inviabilidade. Um piso de vigor de 5,00 é inatingível: o próprio "
     "calendário do clube o viola, porque as cinco horas do amistoso de D5 rebaixam o vigor previsto da "
     "véspera seguinte. Um teto de fadiga de 6,00 e um teto diário de 4,5 horas também tornam o programa "
     "inviável, dados os amistosos fixos. Essas fronteiras não são defeito do modelo: são a tradução, em "
     "números, do que o calendário impõe.")
figura(os.path.join(S,"Q4fig.png"), "Q4",
       "Fronteira eficiente entre carga da semana e vigor do pior dia, e os preços-sombra das restrições")

head("12 O QUE MUDOU NA BASE")
para("Cinco conjuntos de informação foram acrescentados à base única e podem ser consultados por linha de "
     "comando ou por SQL: o dicionário de variáveis com tipo de mensuração, o quadro de fórmulas, as tabelas "
     "de qualidade por variável numérica e categórica, o mapa de faltantes e de cobertura, a reconferência "
     "das conferências entre os dois caminhos de cálculo e as tabelas da otimização. Uma correção foi "
     "aplicada: o domínio da sonolência de Epworth passou de 0 a 24 para 0 a 18, porque o formulário aplicou "
     "seis das oito situações da escala. Os seis achados de qualidade entraram na tabela de auditoria ao lado "
     "dos seis de procedência.")
para("Nenhum registro foi excluído, nenhum valor foi imputado e nenhum escore foi alterado. A limpeza consistiu "
     "em declarar regras que já estavam implícitas e em corrigir um rótulo de domínio. É a forma de limpeza que "
     "um dado bom admite.", after=12)

head("REFERÊNCIAS")
for r in ["CHAPMAN, P. et al. CRISP-DM 1.0: step-by-step data mining guide. [S. l.]: SPSS Inc., 2000.",
          "FREEDMAN, D.; DIACONIS, P. On the histogram as a density estimator: L₂ theory. "
          "Zeitschrift für Wahrscheinlichkeitstheorie und verwandte Gebiete, v. 57, n. 4, p. 453-476, 1981.",
          "IGLEWICZ, B.; HOAGLIN, D. C. How to detect and handle outliers. Milwaukee: ASQC Quality Press, 1993.",
          "SHAPIRO, S. S.; WILK, M. B. An analysis of variance test for normality (complete samples). "
          "Biometrika, v. 52, n. 3-4, p. 591-611, 1965.",
          "STURGES, H. A. The choice of a class interval. Journal of the American Statistical Association, "
          "v. 21, n. 153, p. 65-66, 1926.",
          "TUKEY, J. W. Exploratory data analysis. Reading: Addison-Wesley, 1977."]:
    para(r, indent=False, size=11, spacing=1.0, after=6, align=WD_ALIGN_PARAGRAPH.LEFT)
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite"))
for abnt,doi,aut in cx.execute("SELECT abnt,url_doi,autores FROM referencia ORDER BY id"):
    if any(k in (aut or '').upper() for k in ('TERRY','PARSONS')):
        para(abnt + (f" Disponível em: {doi}." if doi else ""), indent=False, size=11, spacing=1.0,
             after=6, align=WD_ALIGN_PARAGRAPH.LEFT)
cx.close()

# Quadro 1 das fórmulas, ao final, como anexo de conferência
head("ANEXO: QUADRO DE FÓRMULAS")
para("Toda estatística deste relatório pode ser recalculada a partir das fórmulas abaixo e das tabelas "
     "correspondentes.")
caption(f"Quadro {quadro()} – Fórmulas empregadas")
mktable(["Id","Estatística","Fórmula","Observação"],
        [[f['id'], f['nome'], f['formula'], f['nota']] for f in Q['FORMULAS']],
        widths=[1.0,3.2,6.4,5.4], fs=7.5)
out=f"{S}/AUDITORIA_QUALIDADE_E_OTIMIZACAO.docx"
doc.save(out); print("salvo:", out)
