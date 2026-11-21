"""Protocolo de potência de membros inferiores e superiores pré-jogo no handebol (docx).

    python3 gerar_protocolo_potencia.py <saida.docx>

Todas as afirmações sobre estudos vêm dos resumos lidos (Crossref, Europe PMC e PubMed, 21/11/2026).
Doses marcadas como "sugestão prática" não vêm dos estudos.
"""
import re
import sys

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SAIDA = sys.argv[1]
d = Document()
for s in d.sections:
    s.top_margin, s.left_margin, s.bottom_margin, s.right_margin = Cm(3), Cm(3), Cm(2), Cm(2)
st = d.styles["Normal"]
st.font.name, st.font.size = "Times New Roman", Pt(12)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.line_spacing = 1.5
st.paragraph_format.space_after = Pt(6)
AZUL = RGBColor(0x1F, 0x3B, 0x57)


def runs(p, texto, tam=None):
    for i, parte in enumerate(re.split(r"\*\*", texto)):
        if parte:
            r = p.add_run(parte)
            r.bold = i % 2 == 1
            if tam:
                r.font.size = Pt(tam)
    return p


def par(texto, recuo=True, alin=WD_ALIGN_PARAGRAPH.JUSTIFY, tam=None):
    p = d.add_paragraph()
    p.alignment = alin
    if recuo:
        p.paragraph_format.first_line_indent = Cm(1.25)
    return runs(p, texto, tam)


def tit(texto, nivel=1):
    p = d.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(texto)
    r.bold = True
    r.font.size = Pt(12)
    if nivel == 1:
        r.font.color.rgb = AZUL
    return p


def item(texto):
    p = d.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return runs(p, texto)


def sombra(cel, cor):
    tcpr = cel._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), cor)
    tcpr.append(sh)


def tabela(cab, linhas, larg, tam=9.5):
    t = d.add_table(rows=1, cols=len(cab))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblpr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblpr.append(lay)
    for j, c in enumerate(cab):
        cel = t.rows[0].cells[j]
        cel.text = ""
        p = cel.paragraphs[0]
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(c)
        r.bold, r.font.size = True, Pt(tam)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        sombra(cel, "1F3B57")
    trpr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trpr.append(th)
    for i, lin in enumerate(linhas):
        cels = t.add_row().cells
        for j, v in enumerate(lin):
            cels[j].text = ""
            p = cels[j].paragraphs[0]
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)
            runs(p, v, tam)
            if i % 2:
                sombra(cels[j], "F4F6F9")
    for row in t.rows:
        for j, w in enumerate(larg):
            row.cells[j].width = Cm(w)
    for j, w in enumerate(larg):
        t.columns[j].width = Cm(w)
    return t


def legenda(texto):
    p = d.add_paragraph()
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(10)
    runs(p, texto, 11)


def nota(texto):
    p = d.add_paragraph()
    p.paragraph_format.line_spacing = 1.0
    runs(p, texto, 10)


# ------------------------------------------------------------------ capa curta
p = d.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("PROTOCOLO DE POTÊNCIA DE MEMBROS INFERIORES E SUPERIORES PRÉ-JOGO NO HANDEBOL")
r.bold, r.font.size = True, Pt(14)
r.font.color.rgb = AZUL
par("Proposta aplicada com base nas evidências disponíveis", recuo=False, alin=WD_ALIGN_PARAGRAPH.CENTER)
par("Laboratório de Psicologia do Esporte e do Exercício (Lape/UDESC) · novembro de 2026", recuo=False,
    alin=WD_ALIGN_PARAGRAPH.CENTER, tam=11)

# ------------------------------------------------------------------ ficha de quadra
tit("Ficha de quadra (resumo do protocolo)")
par("Tempo total de 25 minutos, com término cerca de 9 minutos antes do início do jogo (T). Equipamento: cones, "
    "caixa ou degrau de 20 a 30 cm, elásticos de resistência média e alta e bolas. Doses identificadas como "
    "sugestão prática não vêm dos estudos e devem ser ajustadas nos treinos.", tam=11)
legenda("Quadro 1: Sequência do aquecimento de potência pré-jogo")
tabela(["Bloco e horário", "Conteúdo", "Dose", "Objetivo"], [
    ["**1. Geral**\nT−34 a T−28 (6 min)", "Corrida leve; deslocamentos laterais, para trás e skipping; mobilidade dinâmica de "
     "quadril, tornozelo e coluna torácica com amplitude crescente", "2 + 2 + 2 min", "Elevar a temperatura e preparar a "
     "amplitude sem perda de força"],
    ["**2. Ombro e tronco**\nT−28 a T−24 (4 min)", "Rotação interna e externa do ombro e fortalecimento escapular com "
     "elástico, mobilidade torácica (modelo OSTRC); estabilidade do tronco e exercícios de equilíbrio", "1 série de 8 a 10 "
     "repetições de cada (sugestão prática)", "Preparar o ombro de arremesso e ativar o tronco"],
    ["**3. Potência de membros inferiores**\nT−24 a T−19 (5 min)", "3 saltos com contramovimento progressivos; drop jump "
     "unilateral vertical (caixa de 20 a 30 cm); salto unilateral horizontal com saída lateral", "2 séries de 3 por perna "
     "em cada salto, com 60 s entre séries (sugestão prática)", "Salto do arremesso (vertical) e mudança de direção "
     "(horizontal)"],
    ["**4. Potência de membros superiores**\nT−19 a T−15 (4 min)", "Desenvolvimento acima da cabeça com elástico de "
     "resistência alta: 3 s de isometria seguidos de subida explosiva; depois, recuperação passiva ou passes leves", "2 séries "
     "(3 repetições por série como sugestão prática) e 4 min até os arremessos", "Velocidade de arremesso sem elevar o "
     "esforço percebido"],
    ["**5. Específico**\nT−15 a T−9 (6 min)", "Arremessos progressivos por posição; 2 sprints de 10 m com mudança de "
     "direção; jogo reduzido 3 contra 3", "3 arremessos a cerca de 70%, 3 a 85% e 3 a 4 máximos; jogo reduzido em 2 blocos "
     "de 2 min com 1 min de pausa", "Transferir a potência para as ações do jogo"],
    ["**Transição**\nT−9 a T0", "Agasalho ou roupa aquecida; preleção; reativação curta à beira da quadra entre T−4 e T−2",
     "3 saltos, 2 sprints de 5 m e 1 série de elástico", "Manter a temperatura e a prontidão"],
], [3.2, 6.0, 3.6, 3.2], tam=9)
nota("Nota: T, início do jogo. OSTRC, programa de prevenção de lesões do ombro do Oslo Sports Trauma Research Center "
     "(ANDERSSON et al., 2017). Intervalo e reservas: seção 6.")

# ------------------------------------------------------------------ 1 objetivo
tit("1 Objetivo")
par("Propor um aquecimento pré-jogo para o handebol que eleve a potência de membros inferiores (salto, sprint e mudança "
    "de direção) e de membros superiores (velocidade de arremesso), aplicável na quadra, no tempo disponível antes de "
    "jogos oficiais e sem cargas que exijam sala de musculação. A proposta se apoia no fenômeno da melhora de desempenho "
    "após uma atividade de condicionamento, conhecido como potencialização pós-ativação, e nos estudos de aquecimento "
    "realizados com atletas de handebol.")

# ------------------------------------------------------------------ 2 método
tit("2 Como a evidência foi levantada")
par("A busca foi feita no PubMed em 21/11/2026 com a expressão abaixo e retornou 37 registros. Ela foi complementada "
    "por buscas no Crossref com os termos handebol, aquecimento, potencialização pós-ativação, salto, sprint e "
    "arremesso, e por revisões sistemáticas sobre aquecimento e potencialização em esportes coletivos.")
p = d.add_paragraph()
p.paragraph_format.line_spacing = 1.0
runs(p, '("handball"[tiab] OR "team handball"[tiab]) AND ("Warm-Up Exercise"[Mesh] OR "warm-up"[tiab] OR "warm up"[tiab] '
        'OR "post-activation"[tiab] OR "postactivation"[tiab] OR potentiation[tiab] OR "conditioning activity"[tiab]) AND '
        '(jump*[tiab] OR sprint*[tiab] OR throw*[tiab] OR "change of direction"[tiab] OR power[tiab])', 10)
par("Foram incluídos estudos com atletas de handebol que testaram o efeito agudo de aquecimentos ou atividades de "
    "condicionamento sobre salto, sprint, mudança de direção ou arremesso, além de revisões sistemáticas sobre o tema e "
    "um estudo de arremesso no softbol, pela escassez de dados sobre membros superiores. Fundamentam o documento 26 "
    "trabalhos, cujos resumos foram lidos: 19 com atletas de handebol, 6 revisões e 1 com atletas de softbol. Este documento não é uma "
    "revisão sistemática: não houve triagem em dupla nem avaliação da qualidade dos estudos, e cada estudo é citado apenas "
    "pelo que o seu resumo afirma. O Quadro 3 resume os estudos.")

# ------------------------------------------------------------------ 3 evidências
tit("3 O que a evidência mostra")
tit("3.1 Aquecimento geral, alongamento e duração", 2)
par("Um aquecimento ativo eleva a temperatura e o metabolismo e prepara o músculo para a tarefa seguinte (MCGOWAN et al., "
    "2015). A recomendação geral é começar com atividade aeróbia submáxima, seguir com alongamento dinâmico de grande "
    "amplitude e terminar com atividades específicas do esporte; o alongamento estático, quando usado, deve ser curto, com "
    "menos de 90 s no total por grupo muscular (BEHM; CHAOUACHI, 2011). Em jogadoras de handebol, o alongamento dinâmico "
    "melhorou a potência em sprints repetidos em relação ao estático e à ausência de alongamento (ZMIJEWSKI et al., 2020), "
    "e o alongamento estático do ombro reduziu a distância do arremesso de medicine ball, efeito que desapareceu quando "
    "exercícios de aquecimento foram somados ao alongamento (MASCARIN et al., 2015).")
par("A duração não precisa ser longa. Um aquecimento de 34 minutos não superou um de 17 minutos no desempenho físico de "
    "jogadores de handebol e gerou maior carga percebida, e os atletas com maior carga muscular percebida perderam mais "
    "capacidade de aceleração (ROMARATEZABALA et al., 2018). Em jogadoras, a carga externa do aquecimento pré-jogo "
    "variou entre as posições, maior nas pontas e menor nas pivôs, e representou parcela considerável da carga do dia "
    "de jogo (GARCÍA-SÁNCHEZ et al., 2026).")
tit("3.2 Membros inferiores", 2)
par("Nas revisões, a atividade de condicionamento aumentou a potência, com efeitos maiores em atletas, após múltiplas "
    "séries e em intensidades moderadas (WILSON et al., 2013). A pliometria produziu efeito um pouco maior que as cargas "
    "altas tradicionais e que a isometria máxima, e o efeito surgiu mais cedo após a pliometria; atletas mais fortes e "
    "mais experientes no treino de força responderam mais (SEITZ; HAFF, 2016). A melhora de desempenho minutos após o "
    "estímulo tem mecanismos próprios, como temperatura e ativação muscular, e há pouca evidência de ganho adicional "
    "quando o aquecimento ativo já é completo (BLAZEVICH; BABAULT, 2019).")
par("No handebol, saltos unilaterais em profundidade orientados na vertical melhoraram mais o salto com contramovimento "
    "(6,5% contra 1%), e os orientados na horizontal melhoraram mais a mudança de direção (6,8% contra 1,3%): cada "
    "protocolo favoreceu a tarefa com a mesma direção de força (DELLO IACONO; MARTONE; PADULO, 2016). Três séries de 3 s "
    "de meio agachamento isométrico máximo reduziram o tempo no sprint de 20 m entre o 4.º e o 12.º minuto "
    "(KRZYSZTOFIK et al., 2023). O hip thrust com 50% ou 85% da carga máxima melhorou o sprint aos 4 e aos 8 minutos, mas "
    "a carga de 85% piorou o sprint feito 15 s depois do estímulo (DELLO IACONO; PADULO; SEITZ, 2018). Após agachamento "
    "com carga alta, 12 minutos de pausa resultaram em salto, sprint e agilidade melhores que 4 ou 8 minutos (ISHAK et al., "
    "2022), e o agachamento com cargas crescentes até 90% da máxima melhorou a capacidade de sprints repetidos em "
    "jogadores de elite (OKUNO et al., 2013).")
par("Dois achados pedem cautela. Em atletas de 15 anos de handebol e basquete, três séries de 10 saltos em profundidade "
    "ou de 5 saltos alternados com uma perna reduziram o desempenho explosivo em vez de melhorá-lo (DELLO IACONO et al., "
    "2016). E uma corrida intervalada de alta intensidade até a exaustão reduziu a força explosiva dos membros inferiores, "
    "sem afetar a dos superiores nem o arremesso (SEIPP et al., 2022).")
tit("3.3 Membros superiores", 2)
par("Os resultados para o arremesso são menos consistentes. Em 23 jogadores de uma seleção nacional sub-18, duas séries de "
    "desenvolvimento acima da cabeça com elástico a 90% do máximo, com 3 s de isometria seguidos de subida explosiva e "
    "4 minutos de pausa, aumentaram a velocidade de arremesso em 5,6 km/h sem elevar o esforço percebido; os autores "
    "indicaram o protocolo para o aquecimento pré-jogo, o intervalo e a preparação dos reservas (ELER et al., 2026). Um "
    "aquecimento com exercícios de elástico melhorou a velocidade de arremesso e o arremesso de medicine ball em relação "
    "ao aquecimento tradicional e ao aquecimento com estabilidade do tronco (CHEN et al., 2022). Em atletas de softbol, "
    "exercícios agonistas (supino) e antagonistas (remada curvada), com 2 séries de 4 repetições, e flexões de braço "
    "aumentaram a velocidade ou a distância do arremesso de medicine ball de forma semelhante (PISZ et al., 2023).")
par("Por outro lado, exercícios pliométricos ou isométricos somados ao aquecimento não mudaram a velocidade de arremesso "
    "em relação a um controle com corrida submáxima (ZECCHIN et al., 2026); o supino a 90% da carga máxima e a sobrecarga "
    "excêntrica não aumentaram a velocidade de arremesso (ASENCIO, 2020); e, em jogadoras, dois métodos de pré-ativação "
    "não mudaram a média do grupo, embora a maioria das atletas tenha melhorado individualmente (MARTÍNEZ-GARCÍA et al., "
    "2021). A resposta nos membros superiores é, portanto, individual e deve ser testada em treino.")
tit("3.4 Final do aquecimento, intervalo e reservas", 2)
par("Encerrar o aquecimento com jogo reduzido de 3 contra 3 (3 blocos de 2 min) trouxe mais benefícios ao salto e às "
    "flexões pliométricas que arremessos específicos, com frequência cardíaca e esforço percebido semelhantes (DELLO "
    "IACONO et al., 2021). Exercícios de equilíbrio e de desequilíbrio no aquecimento produziram saltos mais altos que o "
    "aquecimento tradicional em jogadores de elite da Itália (SIMONELLI et al., 2024). Nos esportes coletivos, uma pausa "
    "de 2 a 10 minutos após o aquecimento antecedeu os melhores desempenhos; roupas aquecidas na transição e no intervalo "
    "ajudaram a manter o sprint e o salto, e, quando a transição passou de 15 minutos, um reaquecimento com tarefas "
    "explosivas curtas foi a melhor estratégia (SILVA et al., 2018). O programa OSTRC de prevenção de lesões do ombro, "
    "aplicado três vezes por semana no aquecimento, reduziu os problemas de ombro em 660 jogadores de elite (ANDERSSON et "
    "al., 2017).")

# ------------------------------------------------------------------ 4 protocolo detalhado
tit("4 Protocolo detalhado")
par("O Quadro 2 descreve cada exercício, a execução e a base de evidência. As opções B e C dos membros inferiores "
    "substituem os saltos quando a equipe preferir estímulos isométricos ou dispuser de equipamento.")
legenda("Quadro 2: Exercícios, execução e base de evidência")
tabela(["Exercício", "Execução e dose", "Base"], [
    ["**Bloco 1.** Corrida e deslocamentos", "Corrida leve 2 min; deslocamentos laterais, para trás e skipping 2 min",
     "Behm e Chaouachi (2011); McGowan et al. (2015)"],
    ["Mobilidade dinâmica", "Balanço de pernas, avanço com rotação do tronco, mobilidade de tornozelo; 2 min com amplitude "
     "crescente; sem alongamento estático prolongado", "Zmijewski et al. (2020); Mascarin et al. (2015)"],
    ["**Bloco 2.** Ombro (modelo OSTRC)", "Rotação interna e externa com elástico, fortalecimento escapular e mobilidade "
     "torácica; 1 série de 8 a 10 de cada (sugestão prática)", "Andersson et al. (2017)"],
    ["Tronco e equilíbrio", "Prancha com alternância de apoios; apoio unipodal com perturbação; 1 série de 20 a 30 s de "
     "cada (sugestão prática)", "Chen et al. (2022); Simonelli et al. (2024)"],
    ["**Bloco 3. Opção A.** Saltos (padrão)", "3 saltos com contramovimento (cerca de 70%, 85% e 100%); drop jump unilateral "
     "vertical de caixa de 20 a 30 cm, 2 × 3 por perna; salto unilateral horizontal com saída lateral, 2 × 3 por perna; "
     "60 s entre séries (dose: sugestão prática de baixo volume)", "Dello Iacono, Martone e Padulo (2016); Seitz e Haff "
     "(2016)"],
    ["**Opção B.** Isometria", "Meio agachamento isométrico máximo contra resistência fixa (barra presa ou cinto), "
     "3 × 3 s; efeito esperado entre 4 e 12 min", "Krzysztofik et al. (2023)"],
    ["**Opção C.** Hip thrust (com equipamento)", "Carga de 50% da máxima, que melhorou o sprint aos 4 e 8 min sem a "
     "queda inicial vista com 85%; volume conforme o teste em treino", "Dello Iacono, Padulo e Seitz (2018)"],
    ["**Bloco 4.** Elástico acima da cabeça (Band-PAPE)", "Elástico de resistência alta (cerca de 90% do máximo com "
     "elástico, definido em treino); 3 s de isometria e subida explosiva; 2 séries (3 repetições como sugestão prática); "
     "4 min até os arremessos", "Eler et al. (2026); Chen et al. (2022)"],
    ["Alternativa sem elástico", "Flexões de braço 2 × 4 e remada com elástico 2 × 4", "Pisz et al. (2023)"],
    ["**Bloco 5.** Arremessos progressivos", "Por posição (pontas, armadores, pivôs); 3 a cerca de 70%, 3 a 85% e 3 a 4 "
     "máximos (sugestão prática)", "Eler et al. (2026)"],
    ["Sprints e mudança de direção", "2 × 10 m com mudança de direção, recuperação completa", "Silva et al. (2018)"],
    ["Jogo reduzido 3 contra 3", "2 blocos de 2 min com 1 min de pausa (adaptado dos 3 blocos do estudo para caber no "
     "tempo)", "Dello Iacono et al. (2021)"],
    ["**Transição**", "Agasalho; reativação entre T−4 e T−2: 3 saltos, 2 sprints de 5 m e 1 série de elástico", "Silva et "
     "al. (2018); Eler et al. (2026)"],
], [4.0, 8.0, 4.0], tam=9)

# ------------------------------------------------------------------ 5 intervalo e reservas
tit("5 Intervalo, reservas e retorno ao jogo")
item("**Intervalo.** Nos primeiros minutos, hidratação, orientação tática e agasalho ou roupa aquecida (SILVA et al., "
     "2018). Nos 3 minutos finais, reaquecimento curto: 1 série de elástico acima da cabeça, 3 saltos, 2 sprints de 10 m "
     "e 3 arremessos progressivos (ELER et al., 2026; SILVA et al., 2018).")
item("**Reservas.** Manter agasalho no banco. Ao aviso do técnico, de 3 a 5 minutos antes da entrada: 1 série de "
     "elástico, 3 saltos, 2 sprints curtos e 2 arremessos. Eler et al. (2026) indicaram o protocolo com elástico para "
     "preparar os reservas, mas o efeito nessa situação não foi testado.")
item("**Transição longa.** Se a transição entre o fim do aquecimento e o jogo passar de 15 minutos (atraso, cerimônia), "
     "repetir a reativação curta antes do início (SILVA et al., 2018).")

# ------------------------------------------------------------------ 6 adaptações
tit("6 Adaptações")
item("**Categorias de base (até 16 anos).** Retirar o drop jump e reduzir o volume de saltos, pois três séries de 10 "
     "saltos em profundidade ou de 5 saltos alternados reduziram o desempenho explosivo de atletas de 15 anos (DELLO "
     "IACONO et al., 2016). Priorizar o jogo reduzido no final do aquecimento (DELLO IACONO et al., 2021) e elásticos "
     "de resistência leve a média, sem cargas externas altas.")
item("**Equipes femininas.** As evidências com mulheres no handebol vêm de estudos de alongamento, de pré-ativação dos "
     "membros superiores e de carga do aquecimento (ZMIJEWSKI et al., 2020; MASCARIN et al., 2015; MARTÍNEZ-GARCÍA et al., "
     "2021; GARCÍA-SÁNCHEZ et al., 2026). O protocolo é o mesmo, com atenção à resposta individual nos membros "
     "superiores.")
item("**Posições.** Ajustar o volume de corrida do bloco 5: as pontas acumularam a maior carga externa no aquecimento, "
     "e as pivôs tiveram a maior parcela da carga do jogo concentrada no aquecimento (GARCÍA-SÁNCHEZ et al., 2026).")
item("**Goleiros.** Nenhum estudo localizado testou aquecimento de potência em goleiros. Sugestão prática: blocos 1 e 2, "
     "saltos laterais no lugar dos horizontais no bloco 3 e bolas progressivas em lugar dos arremessos.")
item("**Atletas com dor no ombro.** Retirar o exercício acima da cabeça do bloco 4 e manter o bloco 2.")

# ------------------------------------------------------------------ 7 testar
tit("7 Como testar na equipe antes de usar em jogo oficial")
par("Como a resposta é individual (SEITZ; HAFF, 2016; MARTÍNEZ-GARCÍA et al., 2021) e o ganho sobre um bom aquecimento "
    "pode ser pequeno (BLAZEVICH; BABAULT, 2019; ZECCHIN et al., 2026), recomenda-se testar o protocolo em três treinos "
    "antes de usá-lo em jogo:")
item("comparar o aquecimento habitual da equipe com o protocolo, em dias diferentes e na mesma hora do dia;")
item("medir o salto com contramovimento (tapete de contato ou aplicativo de celular) e a velocidade de arremesso (radar) "
     "de 4 a 8 minutos após cada condição, com três tentativas e registro da melhor;")
item("registrar o esforço percebido do aquecimento (escala de 0 a 10), usada por Eler et al. (2026);")
item("manter o protocolo para os atletas cuja melhora supere a diferença habitual entre as suas próprias tentativas, e "
     "ajustar a dose de quem piorar.")

# ------------------------------------------------------------------ 8 evitar
tit("8 O que evitar")
item("Corrida intervalada intensa ou exaustiva antes do jogo, que reduziu a força explosiva dos membros inferiores "
     "(SEIPP et al., 2022).")
item("Alongamento estático prolongado ou isolado, sem exercícios dinâmicos depois (BEHM; CHAOUACHI, 2011; MASCARIN et "
     "al., 2015).")
item("Cargas máximas próximas do início do jogo: a carga de 85% prejudicou o sprint feito logo depois (DELLO IACONO; "
     "PADULO; SEITZ, 2018), e o agachamento pesado precisou de 12 minutos de pausa (ISHAK et al., 2022).")
item("Aquecimentos longos: 34 minutos não superaram 17 minutos e geraram mais carga percebida (ROMARATEZABALA et al., "
     "2018).")
item("Usar em jogo um estímulo nunca testado em treino.")

# ------------------------------------------------------------------ 9 lacunas
tit("9 Lacunas da evidência")
item("Nenhum estudo localizado mediu o efeito do aquecimento de potência no desempenho durante o jogo oficial; todos "
     "mediram testes de salto, sprint ou arremesso poucos minutos após o estímulo.")
item("Os estudos de membros superiores com resultado positivo avaliaram homens (ELER et al., 2026; CHEN et al., 2022), "
     "e os dados com jogadoras e categorias de base são escassos e, nos jovens, desfavoráveis aos saltos em profundidade "
     "(DELLO IACONO et al., 2016; MARTÍNEZ-GARCÍA et al., 2021).")
item("Não foram localizados estudos de reaquecimento no intervalo ou de preparação dos reservas no handebol, nem de "
     "aquecimento de potência em goleiros.")
item("Do ponto de vista psicofisiológico, apenas um estudo avaliou a percepção de prontidão para o jogo "
     "(ROMARATEZABALA et al., 2018), e nenhum relacionou o aquecimento de potência à ansiedade pré-competitiva ou ao "
     "humor, tema central das revisões do Lape.")

# ------------------------------------------------------------------ quadro de evidências
tit("10 Quadro de evidências")
legenda("Quadro 3: Estudos que fundamentam o protocolo")
EV = [
    ["Dello Iacono, Martone e Padulo (2016)", "18 jogadores de handebol de elite", "Drop jump unilateral vertical × horizontal",
     "Vertical melhorou mais o salto (6,5% × 1%); horizontal, a mudança de direção (6,8% × 1,3%)"],
    ["Dello Iacono et al. (2016)", "26 atletas de 15 anos (12 de handebol)", "3 × 10 drop jumps ou 3 × 5 saltos alternados",
     "Queda do desempenho explosivo; piora do sprint aos 16 a 30 min"],
    ["Dello Iacono, Padulo e Seitz (2018)", "18 atletas de handebol", "Hip thrust a 50% ou 85% da carga máxima",
     "Sprint melhor aos 4 e 8 min; 85% piorou o sprint aos 15 s"],
    ["Krzysztofik et al. (2023)", "12 atletas de handebol", "3 × 3 s de meio agachamento isométrico máximo",
     "Sprint de 20 m mais rápido do 4.º ao 12.º minuto"],
    ["Ishak et al. (2022)", "17 universitários de handebol", "Agachamento pesado com 4, 8 ou 12 min de pausa",
     "12 min melhoraram salto, sprint e agilidade em relação a 4 e 8 min"],
    ["Okuno et al. (2013)", "12 jogadores de elite", "Meio agachamento até 90% da carga máxima",
     "Melhor e média dos sprints repetidos mais rápidas"],
    ["Eler et al. (2026)", "23 jogadores de seleção nacional sub-18", "Elástico acima da cabeça a 90%, 3 s de isometria, 2 séries",
     "Arremesso 5,6 km/h mais rápido sem aumento do esforço percebido"],
    ["Chen et al. (2022)", "15 universitários de elite", "Aquecimento tradicional × tronco × elástico",
     "Tronco e elástico melhoraram sprint, salto e arremesso; elástico superou no arremesso"],
    ["Zecchin et al. (2026)", "16 jogadores sub-22", "Pliometria × isometria × controle com corrida",
     "Sem diferença na velocidade de arremesso"],
    ["Asencio (2020)", "14 jogadores", "Supino a 90% × sobrecarga excêntrica", "Sem aumento da velocidade de arremesso"],
    ["Martínez-García et al. (2021)", "14 jogadoras", "Resistência variável × isometria no supino unilateral",
     "Sem diferença no grupo; melhora individual na maioria"],
    ["Pisz et al. (2023)", "13 atletas de softbol", "Supino, remada curvada (2 × 4) e flexões",
     "Arremesso de medicine ball mais rápido ou mais longo, sem diferença entre exercícios"],
    ["Dello Iacono et al. (2021)", "12 jogadores jovens de elite", "Final do aquecimento com jogo reduzido 3 contra 3",
     "Mais benefícios no salto e nas flexões pliométricas, com esforço semelhante"],
    ["Simonelli et al. (2024)", "32 jogadores da primeira divisão italiana", "Tradicional × equilíbrio × desequilíbrio",
     "Saltos mais altos com equilíbrio e desequilíbrio"],
    ["Romaratezabala et al. (2018)", "18 jogadores", "Aquecimento de 34 × 17 min",
     "Desempenho semelhante; mais carga percebida no aquecimento longo"],
    ["Zmijewski et al. (2020)", "13 jogadoras jovens", "Alongamento estático × dinâmico × nenhum",
     "Dinâmico melhorou a potência em sprints repetidos"],
    ["Mascarin et al. (2015)", "21 jogadoras de 14 a 18 anos", "Alongamento estático do ombro × aquecimento × ambos",
     "Estático reduziu o arremesso de medicine ball; o aquecimento anulou a perda"],
    ["Seipp et al. (2022)", "14 jogadores bem treinados", "Corrida intervalada até a exaustão",
     "Queda da força explosiva dos membros inferiores; arremesso preservado"],
    ["García-Sánchez et al. (2026)", "22 jogadoras da segunda divisão espanhola", "Carga externa do aquecimento pré-jogo",
     "Carga maior nas pontas e menor nas pivôs; parcela relevante da carga do dia"],
    ["Andersson et al. (2017)", "660 jogadores de elite (45 equipes)", "Programa OSTRC no aquecimento, 3 vezes por semana",
     "Menos problemas de ombro na temporada"],
    ["Seitz e Haff (2016)", "Revisão com 47 estudos", "Fatores da potencialização",
     "Pliometria e múltiplas séries com mais efeito; mais fortes respondem mais"],
    ["Wilson et al. (2013)", "Revisão com 32 estudos", "Fatores da potencialização",
     "Mais efeito em atletas, múltiplas séries e intensidade moderada"],
    ["Silva et al. (2018)", "Revisão com 30 estudos", "Aquecimento, transição e reaquecimento",
     "Roupa aquecida na transição e no intervalo; reaquecimento se a transição passar de 15 min"],
]
tabela(["Estudo", "Participantes", "Protocolo", "Principal resultado"], EV, [3.6, 3.6, 4.2, 4.6], tam=8.5)
nota("Nota: dados extraídos dos resumos. Revisões de apoio sem linha própria: Behm e Chaouachi (2011), Blazevich e "
     "Babault (2019) e McGowan et al. (2015).")

# ------------------------------------------------------------------ referências
tit("Referências")
REFS = [
    "ANDERSSON, S. H.; BAHR, R.; CLARSEN, B.; MYKLEBUST, G. Preventing overuse shoulder injuries among throwing athletes: a cluster-randomised controlled trial in 660 elite handball players. British Journal of Sports Medicine, v. 51, n. 14, p. 1073-1080, 2017. DOI: https://doi.org/10.1136/bjsports-2016-096226.",
    "ASENCIO, P. Does handball throwing velocity increase after an eccentric overload-induced postactivation potentiation? European Journal of Human Movement, v. 44, 2020. DOI: https://doi.org/10.21134/eurjhm.2020.44.543.",
    "BEHM, D. G.; CHAOUACHI, A. A review of the acute effects of static and dynamic stretching on performance. European Journal of Applied Physiology, v. 111, n. 11, p. 2633-2651, 2011. DOI: https://doi.org/10.1007/s00421-011-1879-2.",
    "BLAZEVICH, A. J.; BABAULT, N. Post-activation potentiation versus post-activation performance enhancement in humans: historical perspective, underlying mechanisms, and current issues. Frontiers in Physiology, v. 10, e1359, 2019. DOI: https://doi.org/10.3389/fphys.2019.01359.",
    "CHEN, C. H. et al. Acute effects of different warm-up protocols on sports performance in elite male collegiate handball players. Journal of Strength and Conditioning Research, v. 36, n. 8, p. 2262-2267, 2022. DOI: https://doi.org/10.1519/JSC.0000000000003547.",
    "DELLO IACONO, A. et al. Post-activation potentiation effects on vertical and horizontal explosive performances of young handball and basketball athletes. Journal of Sports Medicine and Physical Fitness, v. 56, n. 12, p. 1455-1464, 2016.",
    "DELLO IACONO, A. et al. Beneficial effects of small-sided games as a conclusive part of warm-up routines in young elite handball players. Journal of Strength and Conditioning Research, v. 35, n. 6, p. 1724-1731, 2021. DOI: https://doi.org/10.1519/JSC.0000000000002983.",
    "DELLO IACONO, A.; MARTONE, D.; PADULO, J. Acute effects of drop-jump protocols on explosive performances of elite handball players. Journal of Strength and Conditioning Research, v. 30, n. 11, p. 3122-3133, 2016. DOI: https://doi.org/10.1519/JSC.0000000000001393.",
    "DELLO IACONO, A.; PADULO, J.; SEITZ, L. D. Loaded hip thrust-based PAP protocol effects on acceleration and sprint performance of handball players. Journal of Sports Sciences, v. 36, n. 11, p. 1269-1276, 2018. DOI: https://doi.org/10.1080/02640414.2017.1374657.",
    "ELER, N. et al. Acute effects of French contrast and post-activation performance enhancement on throwing, jump performance, and training load in handball players. BMC Sports Science, Medicine and Rehabilitation, v. 18, e237, 2026. DOI: https://doi.org/10.1186/s13102-026-01679-9.",
    "GARCÍA-SÁNCHEZ, C. et al. Not all players warm up the same: position-specific external load during standardized pre-match protocol in women's handball. Frontiers in Sports and Active Living, v. 8, e1881325, 2026. DOI: https://doi.org/10.3389/fspor.2026.1881325.",
    "ISHAK, A. et al. The influence of recovery period following a pre-load stimulus on physical performance measures in handball players. PLoS One, v. 17, n. 3, e0249969, 2022. DOI: https://doi.org/10.1371/journal.pone.0249969.",
    "KRZYSZTOFIK, M. et al. Acute effects of isometric conditioning activity on the viscoelastic properties of muscles and sprint and jumping performance in handball players. Journal of Strength and Conditioning Research, v. 37, n. 7, p. 1486-1494, 2023. DOI: https://doi.org/10.1519/JSC.0000000000004404.",
    "MARTÍNEZ-GARCÍA, D. et al. Effects of pre-activation with variable intra-repetition resistance on throwing velocity in female handball players: a methodological proposal. Journal of Human Kinetics, v. 77, p. 235-244, 2021. DOI: https://doi.org/10.2478/hukin-2021-0022.",
    "MASCARIN, N. C. et al. Stretch-induced reductions in throwing performance are attenuated by warm-up before exercise. Journal of Strength and Conditioning Research, v. 29, n. 5, p. 1393-1398, 2015. DOI: https://doi.org/10.1519/JSC.0000000000000752.",
    "MCGOWAN, C. J. et al. Warm-up strategies for sport and exercise: mechanisms and applications. Sports Medicine, v. 45, n. 11, p. 1523-1546, 2015. DOI: https://doi.org/10.1007/s40279-015-0376-x.",
    "OKUNO, N. M. et al. Postactivation potentiation on repeated-sprint ability in elite handball players. Journal of Strength and Conditioning Research, v. 27, n. 3, p. 662-668, 2013. DOI: https://doi.org/10.1519/JSC.0b013e31825bb582.",
    "PISZ, A. et al. Antagonist activation exercises elicit similar post-activation performance enhancement as agonist activities on throwing performance. BMC Sports Science, Medicine and Rehabilitation, v. 15, e44, 2023. DOI: https://doi.org/10.1186/s13102-023-00657-9.",
    "ROMARATEZABALA, E. et al. Influence of warm-up duration on physical performance and psychological perceptions in handball players. Research in Sports Medicine, v. 26, n. 2, p. 230-243, 2018. DOI: https://doi.org/10.1080/15438627.2018.1431536.",
    "SEIPP, D. et al. Acute effects of high-intensity interval running on lower-body and upper-body explosive strength and throwing velocity in handball players. Journal of Strength and Conditioning Research, v. 36, n. 11, p. 3167-3172, 2022. DOI: https://doi.org/10.1519/JSC.0000000000004310.",
    "SEITZ, L. B.; HAFF, G. G. Factors modulating post-activation potentiation of jump, sprint, throw, and upper-body ballistic performances: a systematic review with meta-analysis. Sports Medicine, v. 46, n. 2, p. 231-240, 2016. DOI: https://doi.org/10.1007/s40279-015-0415-7.",
    "SILVA, L. M. et al. Effects of warm-up, post-warm-up, and re-warm-up strategies on explosive efforts in team sports: a systematic review. Sports Medicine, v. 48, n. 10, p. 2285-2299, 2018. DOI: https://doi.org/10.1007/s40279-018-0958-5.",
    "SIMONELLI, C. et al. Acute effects of different warm-up protocols on jump performance in elite male Italian handball players. Applied Sciences, v. 14, n. 23, e11000, 2024. DOI: https://doi.org/10.3390/app142311000.",
    "WILSON, J. M. et al. Meta-analysis of postactivation potentiation and power. Journal of Strength and Conditioning Research, v. 27, n. 3, p. 854-859, 2013. DOI: https://doi.org/10.1519/JSC.0b013e31825c2bdb.",
    "ZECCHIN, A. et al. The effects of different warm-up exercises on throwing velocity in handball players. International Journal of Sports Medicine, v. 47, n. 6, p. 445-452, 2026. DOI: https://doi.org/10.1055/a-2734-1436.",
    "ZMIJEWSKI, P. et al. Acute effects of a static vs. a dynamic stretching warm-up on repeated-sprint performance in female handball players. Journal of Human Kinetics, v. 72, p. 161-172, 2020. DOI: https://doi.org/10.2478/hukin-2019-0043.",
]
for ref in REFS:
    p = d.add_paragraph(ref)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(8)

# conferências de redação
TXT = "\n".join(p.text for p in d.paragraphs) + "\n".join(c.text for t in d.tables for r in t.rows for c in r.cells)
corpo = TXT.split("ANDERSSON, S. H.; BAHR")[0]
for w in ["—", "agenda", "construto", "metanális", "heterogene"]:
    assert w not in corpo, w
ger = [g for g in re.findall(r"\b\w+(?:ando|endo|indo)\b", corpo, re.I)
       if g.lower() not in {"quando", "segundo", "fundo", "mundo", "lindo"}]
assert not ger, ger
d.save(SAIDA)
print("ok", SAIDA)
