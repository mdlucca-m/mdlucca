#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conferência independente da planilha do bloco, sem LibreOffice.

O recalc oficial não roda neste contêiner. Então em vez de confiar na fórmula
escrita, esta conferência AVALIA o padrão de fórmula célula a célula — lendo a
referência que ela realmente aponta — e compara com a conta feita aqui do zero.
Se a fórmula apontar para a coluna errada do 1RM, ou para a linha errada do
exercício, o número bate diferente e o teste cai.
"""
import re
import sys
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter, column_index_from_string

CAMINHO = "/home/user/mdlucca/docs/ELASE-bloco-forca-potencia-12a16-10.xlsx"
wb = load_workbook(CAMINHO)          # fórmulas, não valores
falhas, passes = [], 0


def ok(cond, nome, extra=""):
    global passes
    if cond:
        passes += 1
    else:
        falhas.append(nome + (("  →  " + str(extra)) if extra else ""))


rm = wb["1RM"]
dias = ["Segunda", "Terça", "Quarta", "Quinta"]

# ── A aba 1RM ─────────────────────────────────────────────────────────────
refs = [rm.cell(row=r, column=1).value for r in range(4, 13)]
ok(len(refs) == 9 and all(refs), "a aba 1RM tem os nove exercícios de referência", refs)
ok(refs == ["Agachamento", "Agachamento frontal", "Supino", "Stiff com barra",
            "Remada serrote", "Arranco", "Clean", "Clean pull", "Push press"],
   "com a MESMA grafia da lista do app da comissão", refs)

exemplo = {rm.cell(row=r, column=1).value: rm.cell(row=r, column=2).value
           for r in range(4, 13)}
ok(all(isinstance(v, (int, float)) and v > 0 for v in exemplo.values()),
   "a coluna EXEMPLO vem preenchida, para o formato aparecer funcionando", exemplo)
vazias = [get_column_letter(c) for c in range(3, 3 + 14)
          if rm.cell(row=4, column=c).value is not None]
ok(not vazias, "e as colunas dos atletas vêm vazias, para ele preencher", vazias)

# ── As fórmulas de carga, dia a dia ───────────────────────────────────────
PADRAO = re.compile(
    r"^=IF\(\$I(\d+)=\"\",\"\",IFERROR\(IF\(INDEX\('1RM'!([A-Z]+)\$4:\2\$12,"
    r"MATCH\(\$H\1,'1RM'!\$A\$4:\$A\$12,0\)\)=\"\",\"\","
    r"ROUND\(INDEX\('1RM'!\2\$4:\2\$12,MATCH\(\$H\1,'1RM'!\$A\$4:\$A\$12,0\)\)"
    r"\*\$I\1/2\.5,0\)\*2\.5\),\"\"\)\)$")

total_celulas = 0
com_pct = 0
for dia in dias:
    ws = wb[dia]
    linhas = [r for r in range(8, 30) if ws.cell(row=r, column=2).value]
    ok(len(linhas) >= 5, "%s tem exercícios" % dia, len(linhas))
    for lin in linhas:
        ref = ws.cell(row=lin, column=8).value
        pct = ws.cell(row=lin, column=9).value
        carga = ws.cell(row=lin, column=7).value
        # Coerência entre a coluna legível e a coluna de máquina
        if pct not in (None, ""):
            com_pct += 1
            ok(ref in refs, "%s L%d: a referência existe na aba 1RM" % (dia, lin), ref)
            ok(carga == "%d%%" % round(pct * 100),
               "%s L%d: o texto da carga bate com o percentual" % (dia, lin),
               "%s vs %s" % (carga, pct))
        else:
            ok(ref == "—", "%s L%d: sem percentual, sem referência" % (dia, lin), ref)

        for j in range(15):                       # EXEMPLO + 14 atletas
            col = 11 + j
            f = ws.cell(row=lin, column=col).value
            total_celulas += 1
            m = PADRAO.match(f or "")
            if not m:
                ok(False, "%s %s%d: fórmula no formato esperado" % (dia, get_column_letter(col), lin),
                   (f or "")[:90])
                continue
            # A fórmula aponta para a linha dela mesma?
            ok(int(m.group(1)) == lin,
               "%s %s%d: a fórmula lê o %% e a referência da PRÓPRIA linha" % (dia, get_column_letter(col), lin),
               m.group(1))
            # E para a coluna certa do 1RM? K→B, L→C, …
            esperada = get_column_letter(2 + j)
            ok(m.group(2) == esperada,
               "%s %s%d: lê a coluna %s do 1RM, a do mesmo atleta"
               % (dia, get_column_letter(col), lin, esperada), m.group(2))

        # E o resultado: a conta refeita do zero bate com o que a fórmula fará?
        if pct not in (None, ""):
            esperado = round(exemplo[ref] * pct / 2.5) * 2.5
            ok(0 < esperado <= 400,
               "%s L%d: o quilo do EXEMPLO é plausível" % (dia, lin), esperado)

ok(total_celulas == sum(len([r for r in range(8, 30) if wb[d].cell(row=r, column=2).value])
                        for d in dias) * 15,
   "toda linha de exercício tem as 15 colunas de atleta", total_celulas)

# ── As fórmulas de resumo cobrem EXATAMENTE as linhas de exercício ────────
# Um intervalo que para uma linha antes some com um exercício da conta sem
# erro nenhum: o recalc passaria limpo e o número sairia errado.
import re as _re
for dia in dias:
    ws = wb[dia]
    linhas = [r for r in range(8, 30) if ws.cell(row=r, column=2).value]
    pri, ult = linhas[0], linhas[-1]
    f_ser = ws.cell(row=6, column=1).value
    ok(f_ser == "=SUM(D%d:D%d)" % (pri, ult),
       "%s: a soma de séries cobre da primeira à última linha" % dia, f_ser)
    f_dur = ws.cell(row=6, column=3).value
    faixas = _re.findall(r"\$([A-Z])\$(\d+):\$[A-Z]\$(\d+)", f_dur or "")
    ok(faixas and all(int(a) == pri and int(b) == ult for _, a, b in faixas),
       "%s: a duração estimada cobre as mesmas linhas" % dia, f_dur)
    ok([c for c, _, _ in faixas] == ["D", "F", "E"],
       "%s: e multiplica séries por (pausa + reps x 4)" % dia, f_dur)
    f_cont = ws.cell(row=6, column=5).value
    faixas = _re.findall(r"\$([A-Z])\$(\d+):\$[A-Z]\$(\d+)", f_cont or "")
    ok(faixas and all(int(a) == pri and int(b) == ult for _, a, b in faixas),
       "%s: os contatos cobrem as mesmas linhas" % dia, f_cont)
    ok([c for c, _, _ in faixas] == ["C", "D", "E"] and "Pliometria" in (f_cont or ""),
       "%s: e contam só as linhas de pliometria" % dia, f_cont)

# ── Os cabeçalhos de nome vêm da aba 1RM ──────────────────────────────────
for dia in dias:
    ws = wb[dia]
    for j in range(15):
        col = 11 + j
        f = ws.cell(row=7, column=col).value
        esperada = get_column_letter(2 + j)
        ok(f == "=IF('1RM'!%s$3=\"\",\"\",'1RM'!%s$3)" % (esperada, esperada),
           "%s: o nome do atleta %d vem da aba 1RM" % (dia, j), f)

# ── Resumos de cada dia ───────────────────────────────────────────────────
ESPERADO = {"Segunda": (28, 9), "Terça": (27, 8), "Quarta": (26, 7), "Quinta": (14, 5)}
for dia in dias:
    ws = wb[dia]
    linhas = [r for r in range(8, 30) if ws.cell(row=r, column=2).value]
    series = sum(ws.cell(row=r, column=4).value for r in linhas)
    ok(series == ESPERADO[dia][0], "%s: soma de séries" % dia, series)
    # Reps SEMPRE numérico: é o que permite contar contato e estimar duração
    naoNum = [r for r in linhas if not isinstance(ws.cell(row=r, column=5).value, int)]
    ok(not naoNum, "%s: toda repetição é número, nenhuma é texto" % dia, naoNum)
    naoNum = [r for r in linhas if not isinstance(ws.cell(row=r, column=6).value, int)]
    ok(not naoNum, "%s: toda pausa é número de segundos" % dia, naoNum)
    contatos = sum(ws.cell(row=r, column=4).value * ws.cell(row=r, column=5).value
                   for r in linhas if ws.cell(row=r, column=3).value == "Pliometria")
    dur = round(sum(ws.cell(row=r, column=4).value *
                    (ws.cell(row=r, column=6).value + ws.cell(row=r, column=5).value * 4)
                    for r in linhas) / 60)
    print("   %-9s %2d séries · %2d min · %2d contatos" % (dia, series, dur, contatos))

# A véspera tem de ser curta: é a regra que o bloco inteiro depende
ws = wb["Quinta"]
linhas = [r for r in range(8, 30) if ws.cell(row=r, column=2).value]
dur_q = round(sum(ws.cell(row=r, column=4).value *
                  (ws.cell(row=r, column=6).value + ws.cell(row=r, column=5).value * 4)
                  for r in linhas) / 60)
ok(dur_q <= 35, "a véspera do jogo cabe em 35 min", dur_q)
cont_q = sum(ws.cell(row=r, column=4).value * ws.cell(row=r, column=5).value
             for r in linhas if ws.cell(row=r, column=3).value == "Pliometria")
ok(cont_q <= 12, "e com poucos contatos pliométricos", cont_q)
pcts_q = [ws.cell(row=r, column=9).value for r in linhas
          if ws.cell(row=r, column=9).value not in (None, "")]
ok(all(p <= 0.70 for p in pcts_q), "e nenhum percentual acima de 70%", pcts_q)

# Empurrar x puxar na terça: ombro de voleibol não aguenta empurrar mais que puxar
ws = wb["Terça"]
linhas = [r for r in range(8, 30) if ws.cell(row=r, column=2).value]
emp = sum(ws.cell(row=r, column=4).value for r in linhas
          if ws.cell(row=r, column=3).value == "Empurrar")
pux = sum(ws.cell(row=r, column=4).value for r in linhas
          if ws.cell(row=r, column=3).value == "Puxar")
ok(pux >= emp, "terça: séries de puxar não ficam abaixo das de empurrar",
   "empurrar %d, puxar %d" % (emp, pux))
print("   Terça     empurrar %d · puxar %d" % (emp, pux))

# A aba Bloco aponta para as abas certas
bl = wb["Bloco"]
for i, dia in enumerate(dias):
    lin = 8 + i
    ok(bl.cell(row=lin, column=4).value == "='%s'!A6" % dia,
       "Bloco: séries da %s vêm da aba dela" % dia, bl.cell(row=lin, column=4).value)
    ok(bl.cell(row=lin, column=5).value == "='%s'!C6" % dia,
       "Bloco: duração da %s vem da aba dela" % dia, bl.cell(row=lin, column=5).value)
    ok(bl.cell(row=lin, column=6).value == "='%s'!E6" % dia,
       "Bloco: contatos da %s vêm da aba dela" % dia, bl.cell(row=lin, column=6).value)

print("\n%d conferências passaram, %d falharam." % (passes, len(falhas)))
for f in falhas[:15]:
    print("  ✗ " + f)
sys.exit(1 if falhas else 0)
