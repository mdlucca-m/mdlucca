"""Tabela de extração (Apêndice B), gerada da base em vez de digitada.

Responde ao achado B6: a versão anterior divergia da biblioteca em 49 das 80
linhas quanto ao tamanho amostral, trazia sexo incompatível com o n, células
truncadas em pleno texto e construtos não sustentados pelo registro.

Regras aqui:
  · nenhum valor é inventado — campo ausente vira "n.d.";
  · nenhum valor é truncado no meio de uma palavra;
  · valores internamente incoerentes são sinalizados, não silenciados;
  · o construto vem do instrumento nomeado quando há um, e é marcado como
    "a confirmar" quando vem apenas do resumo.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from .tabelas import acentuar_pais

# Tamanho amostral no intervalo de anos-calendário é quase certamente o ano
# lido como n (achado G6): "n = 2022" no estudo de temporada inteira.
SUSPEITO_ANO = re.compile(r"^(19[5-9]\d|20[0-4]\d)$")
IDADE = re.compile(r"~?\s*(\d{1,2}(?:[.,]\d)?)\s*anos")
SEXO = {"masculino": "masculino", "feminino": "feminino",
        "ambos os sexos": "ambos", "ambos": "ambos"}
NIVEL = {"elite/internacional": "elite/internacional",
         "nacional/semiprofissional": "nacional/semiprofissional",
         "jovem/base": "jovem/base", "amador/recreacional": "amador/recreacional"}


@dataclass
class Linha:
    estudo: str
    ano: str
    pais: str
    n: str
    idade: str
    sexo: str
    nivel: str
    delineamento: str
    instrumentos: str
    construtos: str
    alertas: str

    def como_lista(self) -> list[str]:
        return [self.estudo, self.ano, self.pais, self.n, self.idade, self.sexo,
                self.nivel, self.delineamento, self.instrumentos,
                self.construtos, self.alertas or "—"]


def _encurtar(texto: str, limite: int = 70) -> str:
    """Corta em fronteira de palavra e sinaliza o corte — nunca no meio."""
    t = " ".join((texto or "").split())
    if len(t) <= limite:
        return t or "n.d."
    corte = t[:limite].rsplit(" ", 1)[0]
    return corte + " […]"


def _amostra(bruto: str | None, alertas: list[str]) -> str:
    if not bruto:
        return "n.d."
    m = re.search(r"(\d+)", bruto)
    if not m:
        return "n.d."
    valor = m.group(1)
    if SUSPEITO_ANO.match(valor):
        alertas.append(f"n = {valor} coincide com ano-calendário; conferir no texto")
        return "a conferir"
    return valor


def _idade(populacao: str | None, alertas: list[str]) -> str:
    if not populacao:
        return "n.d."
    m = IDADE.search(populacao)
    if not m:
        return "n.d."
    valor = float(m.group(1).replace(",", "."))
    if not (5 <= valor <= 45):
        alertas.append(f"idade média de {valor:g} anos é implausível para a amostra")
        return "a conferir"
    return f"{m.group(1)} anos"


def _sexo_e_nivel(populacao: str | None) -> tuple[str, str]:
    if not populacao:
        return "n.d.", "n.d."
    partes = [p.strip().lower() for p in populacao.split(";")]
    sexo = next((SEXO[p] for p in partes if p in SEXO), "n.d.")
    nivel = next((NIVEL[p] for p in partes if p in NIVEL), "n.d.")
    return sexo, nivel


def montar(con: sqlite3.Connection, decisoes: list, limite: int | None = None) -> list[Linha]:
    con.row_factory = sqlite3.Row
    inc = {d.id: d for d in decisoes if d.incluido}
    ordenados = con.execute(
        "SELECT * FROM artigo WHERE id IN (%s) ORDER BY CAST(ano AS INTEGER) DESC, titulo"
        % ",".join(str(i) for i in inc))
    linhas: list[Linha] = []
    for reg in ordenados:
        d = inc[reg["id"]]
        alertas: list[str] = []
        sexo, nivel = _sexo_e_nivel(reg["populacao"])
        n = _amostra(reg["amostra"], alertas)
        idade = _idade(reg["populacao"], alertas)
        # Coerência entre idade e nível declarado: uma amostra de base com
        # média acima de 20 anos indica erro em um dos dois campos.
        m_idade = IDADE.search(reg["populacao"] or "")
        if nivel == "jovem/base" and m_idade and float(
                m_idade.group(1).replace(",", ".")) > 20:
            alertas.append(f"nível 'jovem/base' incompatível com idade média de "
                           f"{m_idade.group(1)} anos")

        if d.instrumentos:
            instr = "; ".join(i.canonico for i in d.instrumentos)
            construtos = "; ".join(sorted({i.familia for i in d.instrumentos}))
        else:
            instr = "não nomeado no resumo"
            construtos = "; ".join(sorted(d.familias)) + " (a confirmar no texto)"

        desenho = (reg["desenho_estudo"] or "").strip()
        if desenho in ("", "Nao especificado no resumo"):
            desenho = "n.d."
            alertas.append("delineamento não declarado no resumo")

        linhas.append(Linha(
            estudo=_encurtar(reg["titulo"], 70),
            ano=reg["ano"] or "n.d.",
            pais=acentuar_pais(reg["pais"]) if reg["pais"] else "n.d.",
            n=n, idade=idade, sexo=sexo, nivel=nivel,
            delineamento=desenho, instrumentos=instr, construtos=construtos,
            alertas="; ".join(alertas)))
        if limite and len(linhas) >= limite:
            break
    return linhas


CABECALHO = ["Estudo", "Ano", "País", "n", "Idade", "Sexo", "Nível",
             "Delineamento", "Instrumento psicométrico", "Construto", "Alertas"]


def diagnostico(linhas: list[Linha]) -> dict:
    return {
        "linhas": len(linhas),
        "com_alerta": sum(1 for l in linhas if l.alertas),
        "n_a_conferir": sum(1 for l in linhas if l.n == "a conferir"),
        "sem_delineamento": sum(1 for l in linhas if l.delineamento == "n.d."),
        "instrumento_nomeado": sum(1 for l in linhas
                                   if l.instrumentos != "não nomeado no resumo"),
        "idade_incoerente": sum(1 for l in linhas if "incompatível" in l.alertas),
    }
