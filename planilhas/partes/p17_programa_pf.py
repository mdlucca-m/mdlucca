# ============================================================================
# 17) PROGRAMA PF — documento "Preparação Física 2026/2027" do usuário
# ============================================================================
wsPF = wb.create_sheet("Programa PF")
banner(wsPF, "PROGRAMA DE PREPARAÇÃO FÍSICA 2026/2027 — SÉRIES 1 A 8",
       "Reprodução fiel do documento original (Adulto e Sub-19, fases Básica 1.1, 1.2, 2.1 e 3.1). As colunas "
       "%1RM, Carga e Pausa são sugestões editáveis; o restante é o conteúdo do documento.", 14, GOLD)
larguras(wsPF, {"A":8,"B":13,"C":11,"D":13,"E":12,"F":9,"G":22,"H":7,"I":46,"J":9,"K":16,"L":11,"M":11,"N":26})
PF_H = ["Série","Temporada","Categoria","Fase","Objetivo","Bloco","Esquema (séries/reps)","Ordem","Exercício",
        "Nº de Séries","Repetições","%1RM Sug.","Carga (kg)","Observações"]
cab_tabela(wsPF, 6, PF_H)

# (série, temporada, categoria, fase, objetivo, bloco, esquema, [exercícios])
PROGRAMA = [
 (1,"2026/2027","Adulto","Básica 1.1","Força","Core","3x25",
  ["Abdominal reto com braços esticados","Dorsal perdigueiro"]),
 (1,"2026/2027","Adulto","Básica 1.1","Força","Braço","8/8/6/6",
  ["Armação de braço","Supino deitado com halteres","Puxada alta"]),
 (1,"2026/2027","Adulto","Básica 1.1","Força","Perna","8/8/6/6",
  ["Agachamento profundo","Stiff com barra","Afundo lateral sem passada"]),
 (2,"2027","Adulto","Básica 1.1","Força","Core","3x25",
  ["Abdominal cruzado esticado","Dorsal reto"]),
 (2,"2027","Adulto","Básica 1.1","Força","Braço","8/8/6/6",
  ["Remada unilateral na polia","Bíceps / Tríceps","Pullover deitado com haltere"]),
 (2,"2027","Adulto","Básica 1.1","Força","Perna","8/8/6/6",
  ["Afundo frontal sem passada","Flexão de joelho unilateral","Agachamento sumô no minitramp"]),
 (3,"2026","Sub-19","Fase 1.2","Força 1","Braço","carga alta – 8/8/6",
  ["Supino sentado","Remada serrote","Pullover na polia"]),
 (3,"2026","Sub-19","Fase 1.2","Força 1","Perna","carga alta – 8/8/6",
  ["Agachamento profundo","Stiff","Afundo lateral com tornozeleira"]),
 (3,"2026","Sub-19","Fase 1.2","Força 1","Core","3x25",
  ["Abdominal infra","Dorsal perdigueiro"]),
 (4,"2026","Sub-19","Fase 1.2","Força 1","Braço","carga alta – 8/8/6",
  ["Tríceps / Bíceps","Puxada alta","Cross-over"]),
 (4,"2026","Sub-19","Fase 1.2","Força 1","Perna","carga alta – 8/8/6",
  ["Elevação de calcanhares","Afundo frontal sem passada com tornozeleira","Flexão de joelhos (unilateral)"]),
 (4,"2026","Sub-19","Fase 1.2","Força 1","Core","3x25",
  ["Abdominal reto","Dorsal reto"]),
 (5,"2026","Sub-19","Fase 2.1","Potência","Braço","carga alta menos – 10/8/6",
  ["Supino sentado","Remada unilateral na polia","Pullover na polia"]),
 (5,"2026","Sub-19","Fase 2.1","Potência","Perna","carga alta menos – 10/8/6",
  ["Agachamento","Stiff","Salto no caixote"]),
 (5,"2026","Sub-19","Fase 2.1","Potência","Core","3x20",
  ["Abdominal cruzado com anilha"]),
 (6,"2026","Sub-19","Fase 2.1","Potência","Braço","carga alta menos – 10/8/6",
  ["Tríceps / Bíceps","Puxada alta","Arremesso de bola"]),
 (6,"2026","Sub-19","Fase 2.1","Potência","Perna","carga alta menos – 10/8/6",
  ["Elevação de calcanhares","Salto unilateral com sobrepeso","Flexão de joelhos"]),
 (6,"2026","Sub-19","Fase 2.1","Potência","Core","3x20",
  ["Abdominal remador com anilha"]),
 (7,"2026","Sub-19","Fase 3.1","Força 3","Braço","carga alta – 8/8/6/6",
  ["Tríceps","Remada unilateral na polia (perna contrária à frente)","Pullover com haltere no banco"]),
 (7,"2026","Sub-19","Fase 3.1","Força 3","Perna","carga alta – 8/8/6/6",
  ["Agachamento profundo","Stiff","Afundo lateral com sobrepeso"]),
 (7,"2026","Sub-19","Fase 3.1","Força 3","Core","3x25",
  ["Abdominal cruzado com anilha de 20"]),
 (8,"2026","Sub-19","Fase 3.1","Força 3","Braço","carga alta – 8/8/6/6",
  ["Bíceps","Puxada alta","Cross-over supino"]),
 (8,"2026","Sub-19","Fase 3.1","Força 3","Perna","carga alta – 8/8/6/6",
  ["Elevação de calcanhares","Afundo frontal com sobrepeso (sem passada)","Flexão de joelhos"]),
 (8,"2026","Sub-19","Fase 3.1","Força 3","Core","3x25",
  ["Abdominal reto canivete"]),
]
PCT_OBJ = {"Força": 0.75, "Força 1": 0.80, "Potência": 0.65, "Força 3": 0.85}
PAUSA_BLOCO = {"Core": 45, "Braço": 120, "Perna": 150}
PF_F = 7
r = PF_F
COR_SERIE = {1: LIGHT, 2: LIGHT2}
for serie, temp, cat, fase, obj, bloco, esq, exs in PROGRAMA:
    if "x" in esq:
        nser = int(esq.split("x")[0])
        reps = esq.split("x")[1]
    else:
        partes_esq = esq.split("–")[-1].strip()
        nser = len(partes_esq.split("/"))
        reps = partes_esq
    for i, ex in enumerate(exs, start=1):
        wsPF.cell(r, 1, serie); wsPF.cell(r, 2, temp); wsPF.cell(r, 3, cat)
        wsPF.cell(r, 4, fase); wsPF.cell(r, 5, obj); wsPF.cell(r, 6, bloco)
        wsPF.cell(r, 7, esq); wsPF.cell(r, 8, i); wsPF.cell(r, 9, ex)
        wsPF.cell(r, 10, nser); wsPF.cell(r, 11, reps)
        if bloco != "Core":
            wsPF.cell(r, 12, PCT_OBJ[obj])
        wsPF.cell(r, 14, "Do documento original")
        r += 1
PF_L = r - 1
corpo_tabela(wsPF, PF_F, PF_L, 1, 14)
for rr in range(PF_F, PF_L + 1):
    serie = wsPF.cell(rr, 1).value
    fill = PatternFill("solid", fgColor=LIGHT if serie % 2 else LIGHT2)
    for c in range(1, 15):
        wsPF.cell(rr, c).fill = fill
        wsPF.cell(rr, c).font = Font(name=F, size=9, color=NAVY2)
    for c in (12, 13):
        wsPF.cell(rr, c).fill = PatternFill("solid", fgColor=GOLD_L)
        wsPF.cell(rr, c).font = Font(name=F, size=9, color="0000FF")
    wsPF.cell(rr, 9).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    wsPF.cell(rr, 9).font = Font(name=F, size=9, bold=True, color=NAVY)
    wsPF.cell(rr, 12).number_format = NF_PCT
    wsPF.cell(rr, 13).number_format = '0.0;;""'
    wsPF.cell(rr, 14).alignment = Alignment(horizontal="left", vertical="center", indent=1)
    wsPF.cell(rr, 14).font = Font(name=F, size=8, italic=True, color=GREY_T)
secao(wsPF, PF_L + 2, "COMO ESTE PROGRAMA SE ENCAIXA NA PERIODIZAÇÃO EM BLOCOS (aba Bloco Base)", 14, 1)
MAPA = [
 ("Séries 1 e 2 — Básica 1.1 (Adulto), 8/8/6/6",
  "Bloco de ACUMULAÇÃO — semanas 1 a 4. Volume alto, intensidade moderada (70–80% 1RM). É aqui que entram a técnica "
  "de LPO com carga leve e a pliometria de baixa intensidade."),
 ("Séries 3 e 4 — Fase 1.2 'Força 1', carga alta 8/8/6",
  "Fim da ACUMULAÇÃO e início da TRANSMUTAÇÃO — semanas 4 a 6. Intensidade sobe para 80–88% 1RM no agachamento."),
 ("Séries 5 e 6 — Fase 2.1 'Potência', carga alta menos 10/8/6 (já com salto no caixote e arremesso de bola)",
  "Bloco de TRANSMUTAÇÃO — semanas 6 e 7, incluindo o microciclo de CHOQUE. É o momento do jump squat com 30% 1RM, "
  "do drop jump e do power clean em intensidade alta."),
 ("Séries 7 e 8 — Fase 3.1 'Força 3', carga alta 8/8/6/6",
  "Bloco de REALIZAÇÃO — semana 8 e o mesociclo seguinte. Volume baixo, intensidade ≥ 90% 1RM, pliometria de alta "
  "qualidade e pouco volume."),
]
rr = PF_L + 3
for tit, desc in MAPA:
    c = wsPF.cell(rr, 1, tit)
    wsPF.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=7)
    c.font = Font(name=F, size=9, bold=True, color=NAVY2)
    c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True, indent=1)
    wsPF.merge_cells(start_row=rr, start_column=8, end_row=rr, end_column=14)
    d = wsPF.cell(rr, 8, desc)
    d.font = Font(name=F, size=9)
    d.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True, indent=1)
    for c2 in range(1, 15):
        wsPF.cell(rr, c2).border = BORDER
        if (rr % 2) == 0:
            wsPF.cell(rr, c2).fill = PatternFill("solid", fgColor=LIGHT2)
    wsPF.row_dimensions[rr].height = 34
    rr += 1
wsPF.freeze_panes = "A7"
wsPF.auto_filter.ref = "A6:N{}".format(PF_L)
PF_EXERCICIOS = sorted({ex for *_, exs in PROGRAMA for ex in exs})
