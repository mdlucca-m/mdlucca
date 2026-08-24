# -*- coding: utf-8 -*-
"""Segmentação das sessões do microciclo e normalização das cargas.

AUDITORIA (confirmada na fonte — aba "Comparativo Dia x Horas" de
resultados_handebol.xlsx e "Desenho do Estudo" de Avaliacoes_2024.xlsx):

  Dia | Horas | Sessões | Conteúdo
  1   | 1,5   | 1       | Técnico/tático
  2   | 2,5   | 2       | HIIT + Técnico/tático
  3   | 4,5   | 3       | Técnico/tático + Força + Amistoso
  4   | 2,5   | 2       | HIIT + Técnico/tático
  5   | 5,0   | 3       | Técnico/tático + Força + Amistoso
  6   | 5,0   | 3       | Técnico/tático + Força + Técnico/tático
  7   | 2,0   | 2       | HIIT + Técnico/tático

Problema que isto resolve: o `day_type` do silver é UM rótulo por dia
(D2/D4/D7='HIIT', D3/D5='Jogo', D6='Forca', D1='Baseline'). Ele nomeia a sessão
DEFINIDORA e COLAPSA os dias multissessão — p.ex. D6 é 2×técnico + 1×força
(não "Força pura") e os dias "Jogo" são técnico+força+amistoso. Para normalizar
e equacionar cargas é preciso o nível SESSÃO × PERÍODO.

Camadas de carga (transparentes):
  1) VOLUME (medido, do plano): duração em minutos por sessão/dia; carga
     acumulada em horas — reproduz a coluna da fonte.
  2) sRPE PLANEJADA (Foster: duração×RPE) — o RPE por tipo é NOMINAL/ajustável:
     HIIT ancorado no PSE MEDIDO (silver.hiit ≈ 6,7); Amistoso/Técnico/Força em
     valores de referência de handebol (8/5/6), a serem substituídos pelo RPE
     real por sessão quando disponível. Só o HIIT tem carga interna medida por
     atleta; as demais são planejadas.
  3) Índices semanais: monotonia (média/DP das cargas diárias) e strain
     (carga total × monotonia) de Foster.

Gera em gold:
  an_sessoes      — uma linha por sessão (dia, período, tipo, duração, sRPE)
  an_carga_dia    — carga diária agregada (min, horas, acum., sRPE, por tipo)
  an_load_payload — JSON para o painel (sessões + carga + índices + auditoria)
"""
from __future__ import annotations
import json
import numpy as np, pandas as pd
import lh

# período: M=manhã, V=vespertino (tarde), N=noite. Estrutura CONFIRMADA na fonte.
SESSIONS = [
    (1, "21/04", "N", "TT", 90), (2, "22/04", "V", "HIIT", 60), (2, "22/04", "V", "TT", 90),
    (3, "23/04", "M", "TT", 90), (3, "23/04", "V", "TF", 60), (3, "23/04", "V", "AM", 120),
    (4, "24/04", "V", "HIIT", 60), (4, "24/04", "V", "TT", 90),
    (5, "25/04", "M", "TT", 90), (5, "25/04", "V", "TF", 90), (5, "25/04", "V", "AM", 120),
    (6, "26/04", "M", "TT", 120), (6, "26/04", "V", "TF", 90), (6, "26/04", "V", "TT", 90),
    (7, "27/04", "M", "HIIT", 30), (7, "27/04", "M", "TT", 90),
]
TIPO_LAB = {"TT": "Técnico/tático", "TF": "Força", "AM": "Amistoso", "HIIT": "HIIT"}
PER_LAB = {"M": "Manhã", "V": "Tarde", "N": "Noite"}
# RPE nominal por tipo (0–10) — AJUSTÁVEL; HIIT calibrado ao PSE medido.
RPE_NOM = {"HIIT": 6.7, "AM": 8.0, "TT": 5.0, "TF": 6.0}
# rótulo colapsado atual (para reconciliação)
DAY_TYPE_ATUAL = {1: "Baseline", 2: "HIIT", 3: "Jogo", 4: "HIIT", 5: "Jogo", 6: "Forca", 7: "HIIT"}


def _hiit_pse():
    """PSE médio medido das sessões de HIIT (silver.hiit), para calibrar o RPE nominal."""
    try:
        h = lh.read_delta("silver", "hiit")
        return round(float(h["PSE"].mean()), 2)
    except Exception:
        return None


def build():
    rows = []
    for dia, data, per, tipo, dur in SESSIONS:
        rpe = RPE_NOM[tipo]
        rows.append(dict(dia=dia, data=data, periodo=per, periodo_lab=PER_LAB[per],
                         tipo=tipo, tipo_lab=TIPO_LAB[tipo], dur_min=dur,
                         rpe_nom=rpe, srpe=round(dur * rpe, 1),
                         medido=(tipo == "HIIT")))
    ses = pd.DataFrame(rows)

    # carga diária
    dias = []
    acum = 0.0
    for dia in range(1, 8):
        g = ses[ses.dia == dia]
        dur = int(g.dur_min.sum()); horas = round(dur / 60, 2)
        acum += horas
        srpe = round(float(g.srpe.sum()), 1)
        comp = " + ".join(TIPO_LAB[t] for t in g.tipo.tolist())
        by = {TIPO_LAB[t]: int(g[g.tipo == t].dur_min.sum()) for t in ["TT", "TF", "AM", "HIIT"] if (g.tipo == t).any()}
        dias.append(dict(dia=dia, data=g.data.iloc[0], n_sessoes=int(len(g)),
                         dur_min=dur, horas=horas, carga_acum_h=round(acum, 1),
                         srpe=srpe, conteudo=comp, por_tipo=by,
                         periodos=sorted(set(g.periodo.tolist())),
                         day_type_atual=DAY_TYPE_ATUAL[dia]))
    carga = pd.DataFrame(dias)

    # índices semanais de Foster (sobre a carga diária sRPE)
    sd = carga.srpe.values
    monotonia = round(float(sd.mean() / (sd.std(ddof=1) or 1)), 2)
    strain = round(float(sd.sum() * monotonia), 0)
    total_h = round(float(carga.horas.sum()), 1)

    payload = {
        "sessoes": ses.to_dict("records"),
        "carga": carga.assign(por_tipo=carga.por_tipo.map(json.dumps)).to_dict("records"),
        "carga_raw": dias,
        "tipos": [{"k": k, "lab": v} for k, v in TIPO_LAB.items()],
        "rpe_nom": RPE_NOM, "hiit_pse_medido": _hiit_pse(),
        "monotonia": monotonia, "strain": strain, "total_h": total_h,
        "total_srpe": round(float(sd.sum()), 0),
        "auditoria": [
            "Estrutura confirmada na fonte (aba 'Comparativo Dia x Horas' e 'Desenho do Estudo').",
            "O day_type atual é um rótulo único por dia e COLAPSA os dias multissessão: D6='Forca' é 2×técnico+1×força; D3/D5='Jogo' são técnico+força+amistoso; D2/D4/D7='HIIT' são HIIT+técnico.",
            "Volume (min/horas) é medido; carga acumulada reproduz a coluna da fonte.",
            "sRPE é PLANEJADA (duração×RPE nominal); só o HIIT tem carga interna medida por atleta (silver.hiit, PSE≈" + str(_hiit_pse()) + "). RPE nominal de técnico/força/amistoso é ajustável.",
            "Recomendação para os modelos: substituir o fator categórico day_type por (a) composição de sessões por período e (b) carga contínua (sRPE/dia e carga acumulada), permitindo separar volume, tipo e acúmulo.",
        ],
    }
    lh.write_delta("gold", "an_sessoes", ses); print("[gold] an_sessoes", ses.shape)
    lh.write_delta("gold", "an_carga_dia", carga.assign(por_tipo=carga.por_tipo.map(json.dumps), periodos=carga.periodos.map(json.dumps)))
    print("[gold] an_carga_dia", carga.shape)
    lh.write_delta("gold", "an_load_payload", pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_load_payload")
    return payload


def run():
    return build()


if __name__ == "__main__":
    p = run()
    print("\n=== carga diária (segmentada) ===")
    for d in p["carga_raw"]:
        print(f"  D{d['dia']} {d['data']}: {d['n_sessoes']}ses · {d['horas']}h · acum {d['carga_acum_h']}h · sRPE {d['srpe']} · {d['conteudo']}  (atual: {d['day_type_atual']})")
    print(f"\n  monotonia={p['monotonia']} · strain={p['strain']} · total {p['total_h']}h · PSE HIIT medido={p['hiit_pse_medido']}")
