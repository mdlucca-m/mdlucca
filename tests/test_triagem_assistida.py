#!/usr/bin/env python3
"""Testes do assistente da triagem.

    python3 -m unittest tests.test_triagem_assistida -v

O que se persegue aqui: (1) o assistente ajuda de verdade -- aprende com as
decisoes da pessoa e poe os provaveis incluidos na frente; (2) nao vaza --
o voto de um revisor nunca influencia a fila do outro; (3) nao decide --
nada vira decisao sem a pessoa registrar.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import revisao, triagem_assistida as ta  # noqa: E402
from lape.db import Database  # noqa: E402

RELEVANTES = [
    "Mood states and performance in elite handball players",
    "Profile of mood states in female handball athletes across a season",
    "Humor and anxiety in youth handball players: a cohort study",
    "Mood and recovery in professional handball goalkeepers",
    "Psychological mood responses to training load in handball teams",
]
IRRELEVANTES = [
    "Chemotherapy outcomes in breast cancer patients",
    "Soil microbiome diversity in agricultural fields",
    "Deep learning for protein structure prediction",
    "Hypertension management in elderly primary care patients",
    "Economic effects of tariffs on steel imports",
]


def _ris(titulos: list[str], resumos: bool = True) -> str:
    blocos = []
    for i, t in enumerate(titulos):
        ab = f"AB  - Study of {t.lower()} with participants and measured outcomes.\n" if resumos else ""
        blocos.append(f"TY  - JOUR\nTI  - {t}\nAU  - Autor, N.\nPY  - 2021\nDO  - 10.1000/x.{abs(hash(t)) % 10**8}\n{ab}ER  -\n")
    return "\n".join(blocos)


class BaseAssistente(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        self.rev = revisao.criar(self.db, "rev-a", "Humor em handebol", reviewers_needed=2)
        self.ana = self._membro("Ana")
        self.beto = self._membro("Beto")
        revisao.equipe(self.db, self.rev, self.ana)
        revisao.equipe(self.db, self.rev, self.beto)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _membro(self, nome):
        self.db.execute("INSERT INTO members (full_name, name_key, role, active) VALUES (?, ?, 'integrante', 1)",
                        (nome, nome.lower()))
        self.db.conn.commit()
        return self.db.scalar("SELECT id FROM members WHERE full_name = ?", (nome,))

    def importar(self, titulos, resumos=True):
        revisao.importar(self.db, self.rev, _ris(titulos, resumos), "x.ris")

    def decidir_todos(self, quem, relevantes, irrelevantes):
        # intercala: relevantes e irrelevantes alternados, como na vida real
        linhas = self.db.dicts("SELECT id, title FROM refs WHERE review_id = ? ORDER BY id", (self.rev,))
        rel = [l for l in linhas if l["title"] in relevantes]
        irr = [l for l in linhas if l["title"] in irrelevantes]
        ordem = []
        while rel or irr:
            if rel:
                ordem.append(rel.pop(0))
            if irr:
                ordem.append(irr.pop(0))
        for r in ordem:
            if r["title"] in relevantes:
                revisao.decidir(self.db, r["id"], quem, "incluir")
            elif r["title"] in irrelevantes:
                revisao.decidir(self.db, r["id"], quem, "excluir")


class TestPerfil(unittest.TestCase):
    def codigos(self, **ref):
        return {s["codigo"] for s in ta.perfil(ref)["sinais"]}

    def test_protocolo_e_sinal_de_alerta_com_motivo(self):
        p = ta.perfil({"title": "Study protocol for a randomised trial of mood in handball",
                       "abstract": "x" * 400})
        protocolo = [s for s in p["sinais"] if s["codigo"] == "protocolo"][0]
        self.assertEqual(protocolo["tom"], "alerta")
        self.assertEqual(protocolo["motivo"], "delineamento")

    def test_ensaio_randomizado_e_reconhecido_em_portugues(self):
        self.assertIn("ensaio", self.codigos(title="Ensaio clínico randomizado com atletas",
                                             abstract="x" * 400))

    def test_sem_resumo_e_resumo_curto(self):
        self.assertIn("sem_resumo", self.codigos(title="Algo"))
        self.assertIn("resumo_curto", self.codigos(title="Algo", abstract="curto"))
        self.assertNotIn("resumo_curto", self.codigos(title="Algo", abstract="x" * 400))

    def test_n_amostral_vem_do_texto(self):
        self.assertEqual(ta.perfil({"title": "t", "abstract": "A total of 48 athletes took part."})["n_amostra"], 48)
        self.assertEqual(ta.perfil({"title": "t", "abstract": "Sample (n = 120)."})["n_amostra"], 120)

    def test_editorial_carta_e_errata_sao_alerta(self):
        for titulo in ("Letter to the editor: on mood", "Erratum to mood paper", "Editorial: sport psychology"):
            p = ta.perfil({"title": titulo, "abstract": "x" * 400})
            self.assertTrue(any(s["tom"] == "alerta" for s in p["sinais"]), titulo)


class TestCriterios(unittest.TestCase):
    CRIT = [
        {"id": 1, "kind": "incluir", "grupo": "populacao", "label": "Atletas de handebol",
         "keywords": "handebol*; handball", "motivo_code": None},
        {"id": 2, "kind": "excluir", "grupo": "outro", "label": "Estudos com animais",
         "keywords": "rats; mice; murine", "motivo_code": "populacao"},
    ]

    def test_achou_ou_nao_achou_com_os_termos(self):
        r = ta.avaliar_criterios({"title": "Mood in handball players", "abstract": "Some text."}, self.CRIT)
        self.assertEqual(r[0]["estado"], "sim")
        self.assertEqual(r[0]["termos"], ["handball"])
        self.assertEqual(r[1]["estado"], "nao")

    def test_curinga_casa_o_radical(self):
        r = ta.avaliar_criterios({"title": "Handebolistas em ação", "abstract": "texto"}, self.CRIT)
        self.assertEqual(r[0]["estado"], "sim")   # 'handebolistas' comeca com o radical
        r = ta.avaliar_criterios({"title": "Handebol de praia", "abstract": "texto"}, self.CRIT)
        self.assertEqual(r[0]["estado"], "sim")

    def test_sem_resumo_ausencia_nao_e_evidencia(self):
        r = ta.avaliar_criterios({"title": "Titulo qualquer", "abstract": None}, self.CRIT)
        self.assertEqual(r[0]["estado"], "sem_dado")

    def test_palavra_inteira_nao_casa_pedaco(self):
        crit = [{"id": 1, "kind": "excluir", "grupo": "outro", "label": "Ratos", "keywords": "rat",
                 "motivo_code": None}]
        r = ta.avaliar_criterios({"title": "Strategy and performance", "abstract": "texto"}, crit)
        self.assertEqual(r[0]["estado"], "nao")


class TestModeloEFila(BaseAssistente):
    def test_sem_decisoes_o_modelo_nao_entra(self):
        self.importar(RELEVANTES + IRRELEVANTES)
        fila = ta.fila_assistida(self.db, self.rev, self.ana)
        self.assertEqual(len(fila), 10)
        self.assertFalse(any(r["assist"]["modelo_ativo"] for r in fila))

    def test_aprende_com_as_decisoes_e_poe_os_provaveis_na_frente(self):
        self.importar(RELEVANTES * 1 + IRRELEVANTES)
        # treina com o que ja foi lido (mais registros do mesmo tipo)
        extras_r = [f"Mood and handball players study number {i}" for i in range(12)]
        extras_i = [f"Cancer chemotherapy patients trial number {i}" for i in range(12)]
        self.importar(extras_r + extras_i)
        self.decidir_todos(self.ana, set(extras_r), set(extras_i))
        fila = ta.fila_assistida(self.db, self.rev, self.ana, limite=50)
        self.assertEqual(len(fila), 10)               # so as nao lidas
        self.assertTrue(all(r["assist"]["modelo_ativo"] for r in fila))
        primeiros = {r["title"] for r in fila[:5]}
        self.assertEqual(primeiros, set(RELEVANTES))  # os relevantes vieram primeiro
        self.assertGreater(fila[0]["assist"]["estrelas"], fila[-1]["assist"]["estrelas"])

    def test_ordem_cronologica_mantem_a_importacao(self):
        self.importar(RELEVANTES + IRRELEVANTES)
        fila = ta.fila_assistida(self.db, self.rev, self.ana, ordem="cronologica")
        self.assertEqual([r["id"] for r in fila], sorted(r["id"] for r in fila))

    def test_o_voto_de_um_revisor_nao_muda_a_fila_do_outro(self):
        # o vazamento que este teste guarda: treinar com o voto alheio
        self.importar(RELEVANTES + IRRELEVANTES)
        antes = [(r["id"], r["assist"]["p"]) for r in ta.fila_assistida(self.db, self.rev, self.beto)]
        extras_r = [f"Mood and handball players study number {i}" for i in range(12)]
        extras_i = [f"Cancer chemotherapy patients trial number {i}" for i in range(12)]
        self.importar(extras_r + extras_i)
        self.decidir_todos(self.ana, set(extras_r), set(extras_i))
        ids_antes = {i for i, _ in antes}
        depois = {r["id"]: r["assist"] for r in ta.fila_assistida(self.db, self.rev, self.beto, limite=200)
                  if r["id"] in ids_antes}
        for rid, p in antes:
            self.assertEqual(depois[rid]["p"], p)
            self.assertFalse(depois[rid]["modelo_ativo"])

    def test_a_fila_nao_traz_o_que_a_pessoa_ja_decidiu(self):
        self.importar(RELEVANTES)
        ref = self.db.dicts("SELECT id FROM refs ORDER BY id")[0]["id"]
        revisao.decidir(self.db, ref, self.ana, "incluir")
        self.assertNotIn(ref, [r["id"] for r in ta.fila_assistida(self.db, self.rev, self.ana)])
        self.assertIn(ref, [r["id"] for r in ta.fila_assistida(self.db, self.rev, self.beto)])


class TestCriteriosNaFila(BaseAssistente):
    def setUp(self):
        super().setUp()
        ta.salvar_criterios(self.db, self.rev, [
            {"kind": "incluir", "grupo": "populacao", "label": "Handebol", "keywords": "handball; handebol*"},
            {"kind": "excluir", "grupo": "delineamento", "label": "Ratos", "keywords": "rats; mice",
             "motivo_code": "populacao"},
        ])

    def test_criterio_de_exclusao_derruba_a_relevancia_e_sugere_o_motivo(self):
        self.importar(["Mood in handball players", "Mood in rats after handball-like training"])
        fila = {r["title"]: r["assist"] for r in ta.fila_assistida(self.db, self.rev, self.ana)}
        bom, ruim = fila["Mood in handball players"], fila["Mood in rats after handball-like training"]
        self.assertGreater(bom["p"], ruim["p"])
        self.assertTrue(any("exclusão" in x for x in ruim["porque"]))

    def test_sem_nenhum_criterio_de_populacao_achado_sugere_exclusao_com_motivo(self):
        self.importar(["Soil microbiome diversity in agricultural fields; rats and mice included in alerta"])
        a = ta.fila_assistida(self.db, self.rev, self.ana)[0]["assist"]
        self.assertIsNotNone(a["sugestao"])
        self.assertEqual(a["sugestao"]["decisao"], "excluir")
        self.assertEqual(a["sugestao"]["motivo"], "populacao")
        motivo_id = self.db.scalar("SELECT id FROM exclusion_reasons WHERE review_id = ? AND code = 'populacao'",
                                   (self.rev,))
        self.assertEqual(a["sugestao"]["motivo_id"], motivo_id)

    def test_salvar_troca_o_conjunto(self):
        ta.salvar_criterios(self.db, self.rev, [{"kind": "incluir", "label": "So um", "keywords": "x"}])
        self.assertEqual([c["label"] for c in ta.criterios(self.db, self.rev)], ["So um"])

    def test_assistente_nunca_decide_sozinho(self):
        self.importar(["Soil rats and mice microbiome", "Mood in handball players"])
        ta.fila_assistida(self.db, self.rev, self.ana)
        ta.lote(self.db, self.rev, self.ana, "excluir")
        ta.painel(self.db, self.rev, self.ana)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM screenings"), 0)


class TestPainelELote(BaseAssistente):
    def treinar(self, n=12):
        extras_r = [f"Mood and handball players study number {i}" for i in range(n)]
        extras_i = [f"Cancer chemotherapy patients trial number {i}" for i in range(n)]
        self.importar(extras_r + extras_i)
        self.decidir_todos(self.ana, set(extras_r), set(extras_i))

    def test_painel_sem_treino_explica_o_que_falta(self):
        self.importar(RELEVANTES + IRRELEVANTES)
        p = ta.painel(self.db, self.rev, self.ana)
        self.assertFalse(p["treino"]["modelo_ativo"])
        self.assertFalse(p["regra_de_parada"]["pode_parar"])
        self.assertIn("Faltam decisões", p["regra_de_parada"]["motivo"])
        self.assertEqual(p["pendentes"], 10)

    def test_painel_com_treino_mede_qualidade_e_estima_recall(self):
        self.importar(RELEVANTES + IRRELEVANTES)
        self.treinar()
        p = ta.painel(self.db, self.rev, self.ana)
        self.assertTrue(p["treino"]["modelo_ativo"])
        self.assertIsNotNone(p["qualidade"])
        self.assertGreaterEqual(p["qualidade"]["auc"], 0.9)
        self.assertGreater(p["incluidos_esperados"], 3)       # os 5 relevantes ainda na fila
        self.assertLess(p["recall_estimado"], 1.0)
        self.assertEqual(sum(p["faixas_estrelas"]), p["pendentes"])

    def test_regra_de_parada_exige_sequencia_e_pouco_esperado(self):
        # so irrelevantes na fila depois de treino + muitas exclusoes seguidas
        self.importar([f"Cancer chemotherapy patients final check {i}" for i in range(5)])
        self.treinar(n=40)
        # a ultima decisao de cada lado vem na ordem de id; garante uma sequencia longa de excluidos
        for i in range(35):
            self.importar([f"Cancer chemotherapy patients extra seguida {i}"])
        self.decidir_todos(self.ana, set(), {f"Cancer chemotherapy patients extra seguida {i}" for i in range(35)})
        p = ta.painel(self.db, self.rev, self.ana)
        self.assertGreaterEqual(p["excluidas_seguidas"], 30)
        self.assertTrue(p["regra_de_parada"]["pode_parar"], p["regra_de_parada"])

    def test_lote_so_traz_alta_confianca_e_nao_grava(self):
        self.importar(RELEVANTES + IRRELEVANTES)
        self.treinar()
        itens = ta.lote(self.db, self.rev, self.ana, "excluir")
        self.assertTrue(itens)
        self.assertTrue(all(i["p"] <= 0.08 and i["decisao"] == "excluir" for i in itens))
        self.assertTrue(set(i["title"] for i in itens) <= set(IRRELEVANTES))
        antes = self.db.scalar("SELECT COUNT(*) FROM screenings")
        ta.lote(self.db, self.rev, self.ana, "excluir")
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM screenings"), antes)


from tests.test_triagem import BaseWeb, RIS  # noqa: E402


class TestRotasDoAssistente(BaseWeb):
    def setUp(self):
        self.ana = self.entrar("ana@udesc.br")
        self.beto = self.entrar("beto@udesc.br")
        self.code = f"as-{self._testMethodName}"[:40]
        self.chamar("/api/revisoes", self.ana, {"titulo": "Humor", "codigo": self.code, "avaliadores": 2})
        self.chamar(f"/api/revisoes/{self.code}/importar", self.ana, {"nome": "s.ris", "conteudo": RIS})

    def test_fila_assistida_traz_estrelas_e_sinais(self):
        status, r = self.chamar(f"/api/revisoes/{self.code}/fila?assist=1&ordem=relevancia", self.ana)
        self.assertEqual(status, 200)
        a = r["fila"][0]["assist"]
        self.assertIn("estrelas", a)
        self.assertIn("criterios", a)
        self.assertIn("sinais", a)

    def test_fila_comum_continua_sem_assistente(self):
        r = self.chamar(f"/api/revisoes/{self.code}/fila", self.ana)[1]
        self.assertNotIn("assist", r["fila"][0])

    def test_so_a_coordenacao_grava_criterios(self):
        corpo = {"criterios": [{"kind": "incluir", "grupo": "populacao", "label": "Handebol", "keywords": "handebol"}]}
        self.assertEqual(self.chamar(f"/api/revisoes/{self.code}/criterios", self.beto, corpo)[0], 403)
        status, r = self.chamar(f"/api/revisoes/{self.code}/criterios", self.ana, corpo)
        self.assertEqual(status, 200)
        self.assertEqual(r["criterios"][0]["label"], "Handebol")
        self.assertEqual(self.chamar(f"/api/revisoes/{self.code}/criterios", self.beto)[1]["criterios"][0]["label"],
                         "Handebol")

    def test_painel_e_lote_respondem(self):
        status, p = self.chamar(f"/api/revisoes/{self.code}/assistente", self.beto)
        self.assertEqual(status, 200)
        self.assertEqual(p["pendentes"], 10)
        status, lote = self.chamar(f"/api/revisoes/{self.code}/lote?tipo=excluir", self.beto)
        self.assertEqual(status, 200)
        self.assertEqual(lote["itens"], [])
        self.assertEqual(self.chamar(f"/api/revisoes/{self.code}/lote?tipo=xyz", self.beto)[0], 400)


if __name__ == "__main__":
    unittest.main()
