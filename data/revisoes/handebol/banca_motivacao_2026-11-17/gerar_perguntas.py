"""Perguntas para a banca a partir da leitura integral de 20 textos completos.

    python3 gerar_perguntas.py <pasta_saida>
"""
import re
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
FONTE = "Times New Roman"
doc = Document()
st = doc.styles["Normal"]
st.font.name, st.font.size = FONTE, Pt(12)
s0 = doc.sections[0]
s0.page_height, s0.page_width = Cm(29.7), Cm(21.0)
s0.left_margin, s0.right_margin, s0.top_margin, s0.bottom_margin = Cm(3), Cm(2), Cm(2.5), Cm(2)


def par(txt, tam=12, alinhar=WD_ALIGN_PARAGRAPH.JUSTIFY, recuo=True, antes=0, depois=6, linha=1.3):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment, pf.line_spacing, pf.space_before, pf.space_after = alinhar, linha, Pt(antes), Pt(depois)
    if recuo:
        pf.first_line_indent = Cm(1.0)
    for i, parte in enumerate(re.split(r"\*\*", txt)):
        r = p.add_run(parte)
        r.font.name, r.font.size, r.bold = FONTE, Pt(tam), bool(i % 2)
    return p


def h(txt, tam=12.5):
    par(f"**{txt}**", tam, WD_ALIGN_PARAGRAPH.LEFT, False, antes=10, depois=4)


def item(txt, marca="•", tam=12):
    p = par(f"{marca}  {txt}", tam, recuo=False, depois=3)
    p.paragraph_format.left_indent = Cm(0.7)
    p.paragraph_format.first_line_indent = Cm(-0.5)


par("**PERGUNTAS PARA A BANCA**", 15, WD_ALIGN_PARAGRAPH.CENTER, False, depois=2)
par("**Motivação autodeterminada de atletas adolescentes de handebol: uma revisão sistemática**", 12.5,
    WD_ALIGN_PARAGRAPH.CENTER, False, depois=2, linha=1.1)
par("Defesa em 17/11/2026, às 11h, no Auditório. Material de apoio do Prof. Ms. Mateus De Luca.", 11,
    WD_ALIGN_PARAGRAPH.CENTER, False, depois=12)

h("Como este material foi feito")
par("As perguntas partem da leitura integral de 20 estudos primários sobre motivação de atletas jovens de handebol, "
    "todos com texto completo de acesso aberto, entre os 37 que a base do Lape reúne sobre o tema. Cada problema "
    "apontado tem origem no próprio artigo, com o trecho e a seção registrados nos relatórios de leitura; quando a "
    "constatação depende de um cálculo de verificação (por exemplo, F a partir de R², ou teste t a partir de médias e "
    "desvios-padrão), isso é indicado como verificação aritmética. O texto da revisão em defesa não foi lido; por isso, "
    "as perguntas indagam como a revisão tratou cada ponto, e não afirmam o que ela fez.")

h("1. Seis achados que atravessam os estudos")
ACH = [
    "**Poucos estudos medem a teoria da autodeterminação.** Dos 20 estudos lidos, apenas 8 medem regulações, "
    "índice de autodeterminação ou necessidades psicológicas básicas: Sánchez Oliva et al. (2010), Lukwu e Guzmán "
    "(2011), Martínez-Moreno (2017), Alesi et al. (2019), Freire et al. (2023), Malfa et al. (2025), Bugten et al. "
    "(2026, apenas necessidades) e Saket et al. (2026). Os outros 12 medem clima motivacional e orientações de meta "
    "(teoria das metas de realização), medo do fracasso, ansiedade, características psicológicas (CPRD), motivos de "
    "participação ou grit.",
    "**Amostras repetidas.** Os mesmos 127 jogadores de Extremadura aparecem em Sánchez Miguel et al. (2009) e Sánchez "
    "Oliva et al. (2010), com descrição idêntica e sem citação cruzada. Os mesmos 479 juvenis do Campeonato de Espanha de "
    "Seleções Territoriais (janeiro de 2016, Almería) aparecem em pelo menos cinco artigos: Ruiz-Sánchez et al. (2017), "
    "Gómez-López et al. (2018), Alesi et al. (2019), Gómez-López et al. (2019) e Gómez-López et al. (2020), quatro deles "
    "com o mesmo protocolo de ética (Universidad de Murcia, 1494/2017). Os mesmos 149 jogadores de Murcia aparecem em "
    "Gómez-López et al. (2021, Anuario de Psicología) e Gómez-López et al. (2021, Summa Psicológica), com resultados "
    "opostos para a mesma relação. Bugten et al. (2026) declara usar a mesma amostra de outros dois manuscritos, e "
    "Coutinho et al. (2025) usa o banco de um estudo anterior. Contados como independentes, esses 20 artigos "
    "representam bem menos amostras distintas.",
    "**Faixa etária fora da adolescência.** Sánchez-Sáez et al. (2022) avaliou crianças de 8 a 11 anos; Malfa et al. "
    "(2025), de 9 a 12 anos; Granero-Gallegos et al. (2017), de 12 a 28 anos (média de 18,2); e um quarto da amostra de "
    "Karacsony e Krupanszki (2023) tinha 19 ou 20 anos.",
    "**Inconsistências estatísticas e de relato.** Foram encontradas divergências entre resumo, texto e tabelas, ou "
    "valores aritmeticamente incompatíveis, em pelo menos 14 dos 20 estudos. Exemplos: médias de tarefa e ego trocadas "
    "entre texto e tabela (2009); graus de liberdade incompatíveis com a amostra e correlação canônica da segunda função "
    "maior que a da primeira (2017); índices de ajuste incoerentes, com χ²/gl informado de 2,07 quando 21,14/21 ≈ 1,01 "
    "(2018); graus de liberdade do modelo estrutural menores que os do modelo de medida (2020); R² de 0,32 com F de 4,88 "
    "em 1 e 147 graus de liberdade, quando o F esperado seria de cerca de 69 (Summa Psicológica, 2021); e, em Saket et al. "
    "(2026), diferenças iniciais entre os grupos que contradizem a equivalência declarada.",
    "**Instrumentos fora do contexto ou sem confiabilidade na amostra.** Malfa et al. (2025) usou o BREQ-2, feito para "
    "o exercício físico, e escalas de Educação Física; Alesi et al. (2019) usou itens de necessidades redigidos para "
    "programas de academia e um item de compromisso sobre futebol; Lukwu e Guzmán (2011) usou uma escala de clima de "
    "Educação Física e uma medida de compromisso criada para o estudo; Saket et al. (2026) não informa os valores de "
    "alfa da SMS-28 na amostra; Greblo Jurakić et al. (2026) manteve no escore de ego uma subescala com alfa de 0,38.",
    "**Ética com menores.** Em Martínez-Moreno (2017), o consentimento foi assinado por delegados das federações; Lukwu "
    "e Guzmán (2011) e Karacsony e Krupanszki (2023) não relatam consentimento dos pais nem comitê de ética; em Saket et "
    "al. (2026), o código apresentado como aprovação ética coincide com o identificador do laboratório de um coautor; e "
    "em Gómez-López et al. (2018) a aprovação de 2017 é posterior à coleta de janeiro de 2016 relatada em outro artigo "
    "da mesma amostra."]
for a in ACH:
    item(a)

h("2. Perguntas prioritárias (ordem sugerida)")
PRI = [
    "Qual foi o critério operacional para considerar que um estudo mede **motivação autodeterminada**? Estudos que "
    "medem apenas clima motivacional, orientações de meta, medo do fracasso ou grit foram incluídos? Se sim, em que "
    "parte da síntese entram e com que justificativa?",
    "Como a revisão identificou e tratou as **amostras repetidas** (os 127 de Extremadura, os 479 do Campeonato de "
    "Espanha, os 149 de Murcia, as 50 jogadoras norueguesas)? Houve contato com os autores? Qual é o número de amostras "
    "independentes, e não de artigos, que sustenta as conclusões?",
    "Qual faixa etária definiu **adolescente**, e como foram tratados os estudos com crianças de 8 a 12 anos, com "
    "amostras de 12 a 28 anos ou com participantes de 19 e 20 anos? Foi feita análise de sensibilidade sem esses "
    "estudos?",
    "Qual ferramenta avaliou o **risco de viés** dos estudos transversais e dos quase-experimentais? Ela captou erros de "
    "análise e de relato, como graus de liberdade impossíveis, índices de ajuste incoerentes e divergências entre "
    "resumo, texto e tabelas, ou apenas itens de delineamento?",
    "Quando resumo, texto e tabela discordavam, **qual valor foi extraído**, e isso ficou registrado?",
    "Como a revisão sintetizou as **duas intervenções**? Em Malfa et al. (2025), a motivação autônoma e o índice de "
    "autodeterminação diminuíram no grupo experimental, e o efeito multivariado não foi significativo (p = 0,068); em "
    "Saket et al. (2026), os grupos já diferiam no início, e pela tabela o controle melhorou mais no teste de equilíbrio. "
    "A revisão considera alguma delas evidência favorável?",
    "Como foram tratados os **instrumentos fora do contexto esportivo** (BREQ-2, escalas de Educação Física, itens de "
    "academia) e o uso do **índice de autodeterminação** no lugar das regulações separadas, com fórmulas diferentes "
    "entre os estudos?",
    "Que **conclusão prática** a revisão permite para o treinador das categorias de base, se a maior parte da evidência "
    "é transversal, vem de poucos grupos de pesquisa espanhóis e tem as fragilidades acima?"]
for i, q in enumerate(PRI, 1):
    item(q, f"{i}.")

h("3. Perguntas por estudo")
EST = [
    ("Sánchez Miguel et al. (2009), Retos", "127 jogadores de 11 a 16 anos, Extremadura; transversal; só teoria das metas de realização.",
     ["O estudo não tem nenhuma medida da teoria da autodeterminação (POSQ, PeerMCYSQ, PMCSQ-2 e PISQ). Por que foi incluído?",
      "A Tabela 1 traz tarefa 2,96 e ego 4,38, enquanto o texto diz o contrário (4,38 e 2,96). Qual valor foi extraído?",
      "A amostra é idêntica à de Sánchez Oliva et al. (2010). Como a revisão evitou contar os mesmos participantes duas vezes?"]),
    ("Sánchez Oliva et al. (2010), e-balonmano.com", "Mesmos 127 jogadores; SMS, necessidades (EMM) e deportividade.",
     ["A medida de necessidades era um manuscrito inédito, validado numa amostra de 1.897 atletas com média e desvio de idade idênticos aos desta amostra (12,37 ± 1,48). Como isso foi pontuado?",
      "Os desfechos das regressões foram escolhidos pela maior variância explicada. Isso foi tratado como relato seletivo?",
      "Vários alfas ficaram abaixo de 0,70 (identificada 0,60; autonomia 0,62). Como a confiabilidade entrou na avaliação?"]),
    ("Lukwu e Guzmán (2011), RICYDE", "302 jogadores de 14 a 18 anos; coorte de 12 meses; clima, necessidades, índice de autodeterminação e compromisso.",
     ["O estudo não informa quantos dos 302 abandonaram nem as perdas no contato telefônico após 12 meses. Como foi avaliado o viés de atrito?",
      "Os autores relatam que necessidades e índice de autodeterminação não diferenciaram quem abandonou, mas o modelo estrutural confirma a sequência teórica, com 4% da adesão explicada. Qual desses achados a revisão reporta?",
      "A escala de clima é atribuída a um instrumento de Educação Física, e o compromisso foi medido por instrumento criado para o estudo. Isso foi considerado?"]),
    ("Granero-Gallegos et al. (2017), Frontiers in Psychology", "159 jogadores de 12 a 28 anos; só teoria das metas de realização.",
     ["Com idades de 12 a 28 anos e nenhuma medida da teoria da autodeterminação, como o estudo passou nos critérios? Os dados dos menores de 18 anos eram separáveis?",
      "Os graus de liberdade F(7,101) são incompatíveis com n = 159, e a segunda correlação canônica (0,80) é maior que a primeira (0,78). A revisão usou os tamanhos de efeito relatados (η² = 0,26 para diversão)?"]),
    ("Martínez-Moreno (2017), e-balonmano.com", "495 jogadores de 12 a 16 anos de seleções autonômicas; BRSQ.",
     ["O resumo informa 495 participantes, mas os graus de liberdade indicam cerca de 482. Qual n foi extraído?",
      "O consentimento foi assinado por delegados das federações, sem pais nem comitê de ética, com participantes de 12 a 16 anos. Como a ética entrou na avaliação?",
      "O artigo chama de perfil autodeterminado uma amostra com amotivação de 3,17 e regulação externa de 3,35 numa escala de 1 a 7, sem análise de perfis. A revisão reproduz essa interpretação?"]),
    ("Ruiz-Sánchez, Gómez-López e Granero-Gallegos (2017), e-balonmano.com", "479 juvenis do Campeonato de Espanha, janeiro de 2016; clima e medo do fracasso.",
     ["Que dado deste estudo responde à pergunta sobre motivação autodeterminada, se só há PMCSQ-2 e medo do fracasso?",
      "Os autores chamam de forte associação correlações de 0,24 a 0,42. A magnitude foi reclassificada por critério explícito?"]),
    ("Gómez-López et al. (2018), IJERPH", "444 dos mesmos 479 juvenis; clima, crenças de habilidade e causas do sucesso.",
     ["Os índices de ajuste são aritmeticamente incoerentes (χ² de 21,14 com 21 graus de liberdade apresentado como χ²/gl de 2,07 e p < 0,00), e há β de 0,80 para uma correlação bruta de 0,31. A avaliação de risco de viés captou isso?",
      "A aprovação ética é de 2017, e a coleta da mesma amostra ocorreu em janeiro de 2016. Como isso foi avaliado?"]),
    ("Alesi et al. (2019), IJERPH", "Mesmos 479 juvenis; clima, necessidades (BPNES), SMS com índice de autodeterminação e compromisso.",
     ["O estudo é um dos poucos com medidas da teoria. Como a revisão tratou a falta de alfa da SMS na amostra, os itens de necessidades redigidos para programas de academia e o item de compromisso sobre futebol?",
      "O resumo fala em necessidades como autonomia e competência, mas o modelo usa só um escore global. Que desfecho foi extraído?",
      "O teste de Bollen-Stine rejeitou o modelo (p ≤ 0,001), descrito como de bom ajuste. Isso pesou na avaliação?"]),
    ("Gómez-López, Ruiz-Sánchez e Granero-Gallegos (2019), IJERPH", "Mesmos 479 juvenis; clima do treinador e dos pares e medo do fracasso.",
     ["A discussão afirma que o clima de tarefa dos pares predisse a motivação intrínseca, variável que o estudo não mediu. A revisão percebeu?",
      "O alfa do clima de maestria é 0,87 aqui e 0,82 em outros artigos da mesma amostra. Que valor foi usado?"]),
    ("Gómez-López et al. (2020), IJERPH", "Mesmos 479 juvenis; clima, medo do fracasso e ansiedade (CSAI-2R).",
     ["Os graus de liberdade do modelo estrutural (295) são menores que os do modelo de medida (543), o que é impossível num modelo aninhado, e o IC de β = −0,22 exclui o zero, embora o efeito seja descrito como não significativo. A revisão verificou essa coerência?",
      "As médias do mesmo PMCSQ-2 na mesma amostra são 3,17 e 1,63 aqui, e 3,98 e 2,71 em Alesi et al. (2019). Como explicar?"]),
    ("Gómez-López, González-Hernández e Granero-Gallegos (2021), Anuario de Psicología", "149 jogadores de Murcia; CPRD e clima dos pares.",
     ["O texto relata correlação de −0,28 entre clima de ego e controle do estresse, e a Tabela 2 traz −0,05. Qual valor foi extraído?",
      "Este estudo e o de Summa Psicológica (2021) usam os mesmos 149 jogadores, com resultados opostos para clima de ego dos pares e habilidade mental (positivo aqui, −0,85 no outro). Como isso foi sintetizado?"]),
    ("Gómez-López, Muñoz-Villena e González-Hernández (2021), Summa Psicológica", "Mesmos 149 jogadores; CPRD e clima do treinador e dos pares.",
     ["R² de 0,32 com F(1,147) de 4,88, e β de −0,62 com R² de 0,23, são incompatíveis. Que nota de risco de viés o estudo recebeu?",
      "Sem medida da teoria, o desfecho motivacional extraído foi a subescala de motivação do CPRD (alfa 0,68)?"]),
    ("Freire et al. (2023), Human Movement", "301 escolares de 14 a 17 anos de quatro modalidades, Pernambuco; SMS-II; só 24 de handebol.",
     ["Com 24 atletas de handebol e sem dados de motivação por modalidade, o que a revisão extraiu sobre o handebol? Os critérios previam estudos multiesportivos?",
      "O cluster chamado de alta qualidade da relação treinador-atleta tem escores moderados pelo critério do próprio artigo (z de 0,35 a 0,39). Isso foi considerado?"]),
    ("Sánchez-Sáez et al. (2022), Retos", "35 crianças de 8 a 11 anos; mini-handebol de praia; só pós-teste.",
     ["Como um estudo com crianças de 8 a 11 anos, sem medida da teoria e sem grupo controle, passou nos critérios de idade e de variável estudada?",
      "A data de recebimento (fevereiro de 2020) é anterior à coleta (dezembro de 2020). Isso entrou na avaliação de integridade?"]),
    ("Karacsony e Krupanszki (2023), Physical Education Theory and Methodology", "190 jogadores húngaros de 12 a 20 anos; questionário de motivos de participação.",
     ["A variável motivação é um item de 1 a 7 dividido em três grupos, sem escore da teoria. Que critério de elegibilidade o estudo cumpriu?",
      "As Tabelas 3 e 9 trazem totais idênticos (2,88 ± 2,011) para variáveis diferentes, e erros-padrão e p divergem entre texto e tabelas. Que valores foram extraídos?"]),
    ("Coutinho et al. (2025), Sports", "336 meninos de 13 a 16 anos de cinco modalidades, 35 de handebol; clima parental e grit.",
     ["Os dados do handebol foram extraídos separadamente? Para pai e perseverança, R² de 0,289 com n = 35 corresponde a p de cerca de 0,01, e não ao 0,061 relatado; isso muda a conclusão de efeito nulo no handebol.",
      "O artigo usa o mesmo banco de um estudo anterior sobre medo do fracasso. A revisão verificou a sobreposição?"]),
    ("Malfa et al. (2025), Sportis", "63 jogadores de 9 a 12 anos; intervenção ludocompreensiva de 7 semanas; necessidades, BREQ-2 e índice de autodeterminação.",
     ["A amostra tem média de 10,6 anos. Como atende ao critério de adolescentes?",
      "O artigo não informa o n por grupo, e os graus de liberdade F(11,35) indicam cerca de 48 casos analisados, e não 63. Como isso entrou na avaliação de dados faltantes?",
      "No grupo experimental, a motivação autônoma e o índice de autodeterminação diminuíram, e o ganho de conhecimento se deve à queda do controle. A revisão classificou o estudo como favorável ou desfavorável?"]),
    ("Bugten et al. (2026), preprint", "50 jogadoras norueguesas de 14 a 16 anos; necessidades por sessão, prazer e carga física.",
     ["O estudo mede só a satisfação das necessidades, sem regulações. Entrou como evidência sobre motivação autodeterminada ou sobre seus antecedentes?",
      "É um preprint, com amostra declaradamente compartilhada com outros dois manuscritos e tabelas apenas em suplemento. A revisão buscou a versão publicada e evitou a contagem dupla?"]),
    ("Greblo Jurakić, Bojić-Ćaćić e Ljubičić (2026), Frontiers in Sports and Active Living", "522 jogadores croatas de 14 a 17 anos; clima e bem-estar.",
     ["O estudo mede só clima motivacional e bem-estar. Qual o argumento para incluí-lo?",
      "Os n variam de 186 a 220 para a mesma variável, contra 522 participantes, sem tratamento de dados faltantes descrito, e o escore de ego inclui uma subescala com alfa de 0,38. A avaliação captou isso?"]),
    ("Saket et al. (2026), Frontiers in Psychology", "36 jogadoras cadetes tunisianas; relaxamento progressivo com imagética, 8 semanas; SMS-28.",
     ["A Tabela 2 mostra diferenças iniciais no equilíbrio (105,67 contra 101,28; p ≈ 0,03) e na regulação introjetada (16,94 contra 14,56; p < 0,001), contra a afirmação de equivalência. A revisão conferiu a equivalência pelas tabelas?",
      "O pós-teste do controle no equilíbrio é 101,49 no texto e 104,32 na tabela; pela tabela, o controle melhora mais. Que valores foram extraídos?",
      "O artigo trata a regulação introjetada como integrada ao self, embora ela seja uma regulação controlada, e não informa os alfas da SMS-28 na amostra. Isso pesou na avaliação das conclusões?"])]
for nome, desc, qs in EST:
    par(f"**{nome}.** {desc}", 11.5, WD_ALIGN_PARAGRAPH.LEFT, False, antes=6, depois=2)
    for q in qs:
        item(q, "–", 11.5)

h("4. Quadro-resumo dos 20 estudos")
sec = doc.add_section()
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(2)
QUADRO = [
    ["Estudo", "Mede a TAD?", "Faixa etária", "Amostra compartilhada", "Principal problema"],
    ["Sánchez Miguel et al. (2009)", "Não", "11–16", "Sim (127)", "Médias trocadas entre texto e tabela"],
    ["Sánchez Oliva et al. (2010)", "Sim (SMS, necessidades)", "11–16", "Sim (127)", "Validação inédita; seleção post hoc de desfechos"],
    ["Lukwu e Guzmán (2011)", "Sim (índice, necessidades)", "14–18", "Não verificado", "Atrito não relatado; medidas ad hoc"],
    ["Granero-Gallegos et al. (2017)", "Não", "12–28", "Não", "Graus de liberdade e correlação canônica impossíveis"],
    ["Martínez-Moreno (2017)", "Sim (BRSQ)", "12–16", "Não verificado", "N incoerente; consentimento por delegados"],
    ["Ruiz-Sánchez et al. (2017)", "Não", "16–17", "Sim (479)", "Sobreinterpretação de correlações"],
    ["Gómez-López et al. (2018)", "Não", "16–17", "Sim (479)", "Índices de ajuste incoerentes; ética posterior à coleta"],
    ["Alesi et al. (2019)", "Sim (SMS, necessidades)", "16–17", "Sim (479)", "Itens de academia e de futebol; modelo rejeitado"],
    ["Gómez-López et al. (2019)", "Não", "16–17", "Sim (479)", "Discussão cita variável não medida"],
    ["Gómez-López et al. (2020)", "Não", "16–17", "Sim (479)", "Graus de liberdade impossíveis"],
    ["Gómez-López et al. (2021, Anuario)", "Não", "13–17", "Sim (149)", "Texto e tabela divergem"],
    ["Gómez-López et al. (2021, Summa)", "Não", "14–17", "Sim (149)", "F, R² e β incompatíveis; resultado oposto ao par"],
    ["Freire et al. (2023)", "Sim (SMS-II)", "14–17", "Possível", "Só 24 de handebol, sem análise por modalidade"],
    ["Sánchez-Sáez et al. (2022)", "Não", "8–11", "Não", "Crianças; sem controle"],
    ["Karacsony e Krupanszki (2023)", "Não", "12–20", "Não", "Tabelas duplicadas; motivação em item único"],
    ["Coutinho et al. (2025)", "Não", "13–16", "Sim (banco anterior)", "p do handebol incompatível com R²"],
    ["Malfa et al. (2025)", "Sim (BREQ-2, necessidades)", "9–12", "Não", "Crianças; piora da motivação autônoma; n analisado"],
    ["Bugten et al. (2026)", "Parcial (só necessidades)", "14–16", "Sim (declarada)", "Preprint; linguagem causal"],
    ["Greblo Jurakić et al. (2026)", "Não", "14–17", "Não", "Dados faltantes; subescala com alfa de 0,38"],
    ["Saket et al. (2026)", "Sim (SMS-28)", "15–16", "Não", "Grupos diferentes no início; texto e tabela divergem"]]
t = doc.add_table(rows=0, cols=5)
t.style = "Table Grid"
t.alignment = WD_TABLE_ALIGNMENT.CENTER
larg = [5.5, 4.2, 2.3, 4.0, 9.6]
for i, lin in enumerate(QUADRO):
    cs = t.add_row().cells
    for j, v in enumerate(lin):
        cs[j].text = ""
        r = cs[j].paragraphs[0].add_run(v)
        r.font.name, r.font.size, r.bold = FONTE, Pt(9.5), i == 0
        cs[j].width = Cm(larg[j])
        if i == 0:
            sh = OxmlElement("w:shd")
            sh.set(qn("w:val"), "clear")
            sh.set(qn("w:fill"), "E8ECF2")
            cs[j]._tc.get_or_add_tcPr().append(sh)
for j, w in enumerate(larg):
    t.columns[j].width = Cm(w)
lay = OxmlElement("w:tblLayout")
lay.set(qn("w:type"), "fixed")
t._tbl.tblPr.append(lay)
par("TAD: teoria da autodeterminação. Fonte: leitura integral dos textos completos de acesso aberto (pasta "
    "textos_completos). Os quatro textos obtidos depois desta leitura (Sarrazin et al., 2002; Isoard-Gautheur et al., "
    "2012; Gómez-López et al., 2024; Gómez-López, González e Granero-Gallegos, 2021, Journal of Sport and Health "
    "Research) ainda não foram analisados neste nível de detalhe.", 9.5, recuo=False, antes=6, linha=1.0)
arq = OUT / "PERGUNTAS BANCA MOTIVACAO AUTODETERMINADA.docx"
doc.save(arq)
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(OUT), str(arq)],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
print("ok", arq)
