# -*- coding: utf-8 -*-
"""Monta o gerador da planilha v2 a partir do gerador v1 + as partes novas."""
import io, os
BASE = os.path.dirname(os.path.abspath(__file__))
V1 = open(os.path.join(BASE, "..", "gerar_planilha_volei.py"), encoding="utf-8").read()
L = V1.split("\n")

def bloco(nome):
    """Retorna (inicio, fim) das linhas do bloco '# N) NOME' incluindo a moldura."""
    i = next(k for k, l in enumerate(L) if l.startswith("# ") and nome in l)
    return i - 1, i + 1

A_end, _ = bloco("3) CADASTRO DE ATLETAS")
C_start, _ = bloco("4) BIBLIOTECA DE EXERCÍCIOS")
C_end, _ = bloco("15) DADOS DE EXEMPLO")
A = "\n".join(L[:A_end])
C = "\n".join(L[C_start:C_end])

# --------------------------------------------------------------- patches A --
A = A.replace("from openpyxl.chart import BarChart, LineChart, PieChart, Reference",
              "from openpyxl.chart import BarChart, LineChart, PieChart, ScatterChart, Reference, Series\n"
              "from openpyxl.chart.marker import Marker")
A = A.replace("CAD_F, CAD_L   = 7, 66      # Cadastro (60 atletas)",
              "CAD_F, CAD_L   = 8, 47      # Cadastro (40 atletas)")
NOVAS_LISTAS = '''
 ("Perna de Impulsão",  ["Esquerda","Direita","Ambas"]),
 ("Escolaridade",       ["Ensino Fundamental incompleto","Ensino Fundamental completo","Ensino Médio incompleto",
                         "Ensino Médio completo","Superior em andamento","Superior completo","Pós-graduação"]),
 ("Situação de Estudo", ["Cursando","Concluído","Trancado","Não estuda","—"]),
 ("Turno",              ["Manhã","Tarde","Noite","Matutino","Vespertino","Noturno","Integral","EAD","—"]),
 ("Sim/Não",            ["Sim","Não"]),
 ("Classe Econômica",   ["A","B1","B2","C1","C2","D-E"]),
 ("Tipo de Moradia",    ["Própria","Alugada","Cedida","Financiada","Alojamento do clube"]),
 ("Reside com",         ["Família","Cônjuge","Sozinho","Amigos / Colegas","Alojamento do clube","República"]),
 ("Transporte",         ["A pé","Bicicleta","Transporte público","Transporte do clube","Carro próprio","Moto",
                         "Aplicativo / Carona"]),
 ("Nível Competitivo",  ["Municipal","Estadual","Superliga C","Superliga B","Superliga A","Seleção nacional",
                         "Clube no exterior","Atleta em formação"]),
 ("Tipo Sanguíneo",     ["A+","A-","B+","B-","AB+","AB-","O+","O-","Não sabe"]),
 ("Região Corporal",    ["Ombro","Cotovelo","Punho / Mão","Coluna cervical","Coluna lombar","Quadril","Coxa",
                         "Joelho","Perna","Tornozelo","Pé","—"]),
 ("Método de 1RM",      ["Direto (1RM real)","Estimado por repetições","Estimado por velocidade (VBT)",
                         "Carga máxima em treino"]),
 ("Origem do Salto",    ["Pliometria","Treino de quadra","Jogo","Musculação"]),
 ("Superfície",         ["Quadra (madeira)","Quadra (sintética)","Grama","Areia","Aquático","Colchão / Tatame"]),
 ("Ref. VBT",           ["Agachamento","Supino","Terra","—"]),
 ("Objetivo de Força",  ["Força Máxima","Força-Velocidade","Potência","Velocidade-Força","Hipertrofia","Pliometria",
                         "Preventivo","Aquecimento","Core","Velocidade"]),
 ("Bloco de Treino",    ["Acumulação","Transmutação","Realização","Descarga"]),
]
'''
assert A.count('("Momento do Teste",') == 1
i = A.index('("Momento do Teste",')
j = A.index("\n]\n", i)
A = A[:j] + NOVAS_LISTAS.rstrip("\n")[:-1].rstrip() + "\n]\n" + A[j + 3:]
A = A.replace('       "Edite/complemente as opções abaixo — elas alimentam automaticamente todos os menus suspensos da planilha.", 22, GREY_T)',
              '       "Edite/complemente as opções abaixo — elas alimentam automaticamente todos os menus suspensos da planilha.", 42, GREY_T)')

PASSOS_NOVOS = '''passos = [
 ("1. Listas",           "Opções de todos os menus suspensos (posições, escolaridade, renda, tipos de sessão, superfícies…)."),
 ("2. Cadastro",         "Ficha completa do atleta: identificação, contato, SOCIOECONÔMICO, histórico esportivo e saúde."),
 ("3. Antropometria",    "Avaliações longitudinais no perfil ISAK: dobras, perímetros, diâmetros, % de gordura e somatotipo."),
 ("4. Testes",           "Bateria física: alcances e impulsões, SJ, CMJ, drop jump com RSI, sprint, agilidade e IMTP."),
 ("5. Perfil F-V-P",     "Perfil força-velocidade-potência pelo salto com carga: F0, V0, Pmax e desequilíbrio F-V."),
 ("6. Exercícios",       "Biblioteca com 89 exercícios, incluindo todos os do seu documento de Preparação Física."),
 ("7. Programa PF",      "As 8 séries do seu documento 'Preparação Física 2026/2027', na íntegra."),
 ("8. Macrociclo",       "A temporada dividida em mesociclos, com dinâmica de volume e intensidade."),
 ("9. Mesociclo",        "Microciclos do mesociclo escolhido, com carga prevista × realizada."),
 ("10. Bloco Base",      "PERIODIZAÇÃO EM BLOCOS: as 8 semanas de base (força máxima, LPO, agachamento e pliometria)."),
 ("11. Microciclo",      "A semana de quadra: sessões por dia e distribuição de conteúdos."),
 ("12. Prescrição",      "Prescrição do treino técnico-tático, por equipe ou por atleta."),
 ("13. Prescrição Força","Prescrição e controle do treino de força: %1RM, carga em kg, velocidade-alvo e tonelagem."),
 ("14. Força 1RM",       "Testes de 1RM diretos e estimados; mantém o 1RM ATUAL de cada atleta em cada exercício."),
 ("15. Carga (PSE)",     "Carga interna: duração × PSE, carga aguda, crônica, ACWR e zona de risco."),
 ("16. Saltos",          "Carga de saltos: contatos pliométricos, saltos de quadra e de jogo, com alerta de variação."),
 ("17. Wellness",        "Questionário diário e Índice de Hooper."),
 ("18. Presença",        "Chamada por sessão e percentual de assiduidade."),
 ("19. Atleta",          "ÁREA DO ATLETA: perfil, cargas, monotonia e o treino prescrito para ele."),
 ("20. Painel",          "PAINEL da equipe: indicadores e gráficos de carga, wellness e presença."),
 ("21. KPIs Força",      "PAINEL DE FORÇA: tonelagem, intensidade relativa, contatos, 1RM relativo e evolução do CMJ."),
 ("22. Evidências",      "60 referências científicas que sustentam cada escolha metodológica da planilha."),
]'''
k0 = A.index("passos = [")
k1 = A.index("]\n", A.index('("13. Painel"'))
A = A[:k0] + PASSOS_NOVOS + A[k1 + 1:]

METRICAS_NOVAS = ''' ("Tonelagem", "Séries × repetições × carga usada, em kg. É o volume-carga do treino de força; some por sessão, semana e bloco."),
 ("Intensidade média relativa", "Média dos %1RM prescritos, ponderada pelo número de repetições de cada exercício. Mostra o quanto a semana foi 'pesada' de verdade."),
 ("Perda de velocidade", "Queda percentual da velocidade da barra dentro da série. Limiares ≤ 25% favorecem força; acima de 20–25% favorecem hipertrofia (Hickmott et al., 2022)."),
 ("F0, V0 e Pmax", "Força teórica máxima, velocidade teórica máxima e potência máxima estimadas por regressão linear a partir de saltos com cargas progressivas (Morin & Samozino, 2016)."),
 ("FVimb", "Razão entre a inclinação real do perfil força-velocidade e a inclinação ótima teórica. Abaixo de 90% indica déficit de força; acima de 110%, déficit de velocidade."),
 ("RSI", "Reactive Strength Index: altura do drop jump ÷ tempo de contato com o solo. Mede a qualidade do ciclo alongamento-encurtamento."),
 ("Contatos pliométricos", "Número de aterrissagens por sessão e por semana. É a dose que a meta-análise de Sáez de Villarreal et al. (2009) mostrou determinar o ganho de impulsão."),
 ("Somatotipo", "Endomorfia, mesomorfia e ectomorfia pelo método Heath-Carter, a partir de dobras, perímetros, diâmetros, estatura e massa."),
'''
m0 = A.index("metricas = [")
m1 = A.index("]\n", A.index('("Volume × Intensidade"'))
A = A[:m1] + METRICAS_NOVAS + A[m1:]

# --------------------------------------------------------------- patches C --
C = C.replace("Cadastro!$T$", "Cadastro!$BL$")
for _a, _b in (("$BL${3}:$T${4}","$BL${3}:$BL${4}"),("$BL${0}:$T${1}","$BL${0}:$BL${1}"),
               ("$BL${}:$T${}","$BL${}:$BL${}")):
    C = C.replace(_a, _b)
C = C.replace("Cadastro!$T{1}", "Cadastro!$BL{1}")
C = C.replace("'=IF($A{}=\"\",\"\",Cadastro!$F{})'", "'=IF($A{}=\"\",\"\",Cadastro!$L{})'")
PERFIL_NOVO = '''PERFIL = [("ID","A",None),("Idade","E",'0" anos"'),("Posição","L",None),("Categoria","K",None),
          ("Nº Camisa","J",'0'),("Estatura (cm)","O",'0.0'),("Massa (kg)","P",'0.0'),("IMC","Q",'0.0'),
          ("Dominância","M",None),("Perna de Impulsão","N",None),("Anos de Prática","AT",'0" anos"'),
          ("Status","BL",None)]'''
p0 = C.index("PERFIL = [")
p1 = C.index("]\n", C.index('("Status","T",None)'))
C = C[:p0] + PERFIL_NOVO + C[p1 + 1:]
# troca do bloco de Testes
t0 = C.index("# ============================================================================\n# 12) TESTES FÍSICOS")
t1 = C.index("# ============================================================================\n# 13) ÁREA DO ATLETA")
C = C[:t0] + open(os.path.join(BASE, "p12_testes.py"), encoding="utf-8").read() + "\n" + C[t1:]

PARTES = ["p03_cadastro.py", None, "p16_antropometria.py", "p17_programa_pf.py", "p18_bloco_base.py",
          "p19_forca_1rm.py", "p20_prescricao_forca.py", "p21_perfil_fv.py", "p22_saltos.py",
          "p23_kpis_forca.py", "p24_evidencias.py", "p25_exemplo_save.py"]
out = [A, open(os.path.join(BASE, "p03_cadastro.py"), encoding="utf-8").read(), C]
for nome in PARTES[2:]:
    out.append(open(os.path.join(BASE, nome), encoding="utf-8").read())
FINAL = "\n\n".join(out)
FINAL = FINAL.replace('"""\nGerador da Planilha de Controle e Prescricao de Treinamento - VOLEIBOL',
                      '"""\nGerador da Planilha de Voleibol v2 - FORCA E POTENCIA')
dest = os.path.join(BASE, "..", "gerar_planilha_volei_v2.py")
open(dest, "w", encoding="utf-8").write(FINAL)
import ast; ast.parse(FINAL)
print("gerado:", dest, "-", FINAL.count("\n"), "linhas")
