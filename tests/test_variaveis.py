#!/usr/bin/env python3
"""Testes das variáveis do LAPE e da análise das curvas.

    python3 -m unittest tests.test_variaveis -v

Dois perigos governam este arquivo, e os dois são silenciosos.

O primeiro é a marcação automática encher a produção de falso positivo:
"rpe" casa dentro de "properties", e ninguém percebe até a rede temática
ficar cheia de aresta inventada.

O segundo é pior — a análise responder com confiança sobre nada. Com um
único ano de produção, qualquer algoritmo de tendência responde "subindo",
o painel mostra uma ladeira bonita, e quem lê acredita.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import analise, variaveis  # noqa: E402
from lape.db import Database  # noqa: E402


class TestVocabulario(unittest.TestCase):
    def test_todo_codigo_e_unico(self):
        codigos = [c for c, _, _, _, _ in variaveis.VOCABULARIO]
        self.assertEqual(len(codigos), len(set(codigos)))

    def test_todo_grupo_esta_declarado(self):
        for _, rotulo, grupo, _, _ in variaveis.VOCABULARIO:
            with self.subTest(variavel=rotulo):
                self.assertIn(grupo, variaveis.GRUPOS)

    def test_nenhum_sinonimo_curto_demais(self):
        # sinônimo de uma ou duas letras casaria em qualquer lugar
        for codigo, _, _, _, sinonimos in variaveis.VOCABULARIO:
            for sinonimo in sinonimos:
                with self.subTest(variavel=codigo, termo=sinonimo):
                    self.assertGreaterEqual(len(sinonimo), 2)

    def test_todo_icone_existe_no_conjunto_de_icones(self):
        icones = (ROOT / "scripts" / "lape" / "templates" / "icons.js").read_text(
            encoding="utf-8")
        for codigo, _, _, icone, _ in variaveis.VOCABULARIO:
            with self.subTest(variavel=codigo):
                self.assertIn(f"{icone}:", icones, f"ícone inexistente: {icone}")


class TestReconhecimento(unittest.TestCase):
    def codigos(self, titulo, resumo=None, palavras=None):
        return {a["code"] for a in variaveis.reconhecer(titulo, resumo, palavras)}

    def test_acha_o_que_esta_no_titulo(self):
        achados = self.codigos(
            "Efeitos do treinamento resistido sobre a ansiedade em mulheres com fibromialgia")
        self.assertEqual(achados, {"treinamento_resistido", "exercicio", "ansiedade",
                                   "fibromialgia"})

    def test_acha_pelo_instrumento(self):
        # metade dos títulos nunca escreve "humor": escreve "POMS"
        self.assertIn("humor", self.codigos("Aplicação do POMS em atletas"))
        self.assertIn("fibromialgia", self.codigos("Validação do FIQ em português"))
        self.assertIn("sono", self.codigos("PSQI e desempenho"))

    def test_acento_e_maiuscula_nao_atrapalham(self):
        self.assertEqual(self.codigos("ANSIEDADE PRÉ-COMPETITIVA"),
                         self.codigos("ansiedade pre competitiva"))

    def test_nao_casa_dentro_de_outra_palavra(self):
        # o defeito que este teste guarda: "rpe" dentro de "properties",
        # "fm" dentro de "confirm", "tr" dentro de "training"
        for armadilha in ("Properties of the material", "We confirm the finding",
                          "A study of transfer", "Activity of the enzyme"):
            with self.subTest(titulo=armadilha):
                self.assertEqual(self.codigos(armadilha), set(),
                                 f"falso positivo em: {armadilha}")

    def test_o_trecho_mostra_onde_apareceu(self):
        # achado sem evidência obriga a reler o artigo inteiro, e o que
        # obriga a reler não é conferido
        achado = variaveis.reconhecer("Ansiedade em atletas")[0]
        self.assertEqual(achado["onde"], "título")
        self.assertIn("ansiedade", achado["trecho"])

    def test_o_titulo_manda_sobre_o_resumo(self):
        achados = {a["code"]: a for a in variaveis.reconhecer(
            "Ansiedade em atletas", "Este estudo sobre ansiedade e depressão…")}
        self.assertEqual(achados["ansiedade"]["onde"], "título")
        self.assertEqual(achados["depressao"]["onde"], "resumo")

    def test_texto_vazio_nao_inventa_nada(self):
        self.assertEqual(variaveis.reconhecer(None, None, None), [])


class TestPaises(unittest.TestCase):
    def test_le_o_pais_no_fim_da_afiliacao(self):
        self.assertEqual(
            variaveis.pais_da_afiliacao("Univ of Oslo, Dept of Sport, Oslo, Norway")[0],
            "Noruega")

    def test_le_sem_virgula_tambem(self):
        self.assertEqual(variaveis.pais_da_afiliacao("Univ Zagreb Croatia")[0], "Croácia")

    def test_nome_de_cidade_nao_vira_pais(self):
        # ler o texto inteiro traria "New York" como país toda vez que
        # alguém publicasse numa revista de Nova York
        self.assertIsNone(variaveis.pais_da_afiliacao("The New York Times"))

    def test_afiliacao_vazia(self):
        self.assertIsNone(variaveis.pais_da_afiliacao(None))

    def test_todo_pais_tem_coordenada_plausivel(self):
        for chave, (rotulo, lat, lon) in variaveis.PAISES.items():
            with self.subTest(pais=rotulo):
                self.assertTrue(-90 <= lat <= 90, f"{rotulo}: latitude fora do mundo")
                self.assertTrue(-180 <= lon <= 180, f"{rotulo}: longitude fora do mundo")


class TestMarcacaoNoBanco(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        from lape import ingest_excel
        ingest_excel.ingest_articles(self.db, [
            {"title": "Efeitos do treinamento resistido na ansiedade em fibromialgia",
             "authors": "Ana Souza", "status": "Publicado", "year_published": 2024},
            {"title": "Dropout no treinamento resistido", "authors": "Beto Lima",
             "status": "Publicado", "year_published": 2023},
            {"title": "Um título sem nenhuma variável do vocabulário",
             "authors": "Ana Souza", "status": "Publicado", "year_published": 2022},
        ])
        variaveis.instalar(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def artigo(self, pedaco):
        return self.db.scalar("SELECT id FROM articles WHERE title LIKE ?", (f"%{pedaco}%",))

    def test_marca_o_que_reconhece_e_deixa_o_resto(self):
        resultado = variaveis.marcar_artigos(self.db)
        self.assertEqual(resultado["artigos_lidos"], 3)
        self.assertEqual(resultado["com_variavel"], 2)

    def test_um_artigo_pode_ter_varias(self):
        variaveis.marcar_artigos(self.db)
        codigos = {v["code"] for v in variaveis.do_artigo(self.db, self.artigo("ansiedade"))}
        self.assertEqual(codigos, {"treinamento_resistido", "exercicio", "ansiedade",
                                   "fibromialgia"})

    def test_a_marcacao_automatica_se_declara(self):
        variaveis.marcar_artigos(self.db)
        origens = {v["origem"] for v in variaveis.do_artigo(self.db, self.artigo("ansiedade"))}
        self.assertEqual(origens, {"auto"})

    def test_quem_leu_manda_sobre_a_busca(self):
        variaveis.marcar_artigos(self.db)
        alvo = self.artigo("ansiedade")
        variaveis.marcar_artigo_a_mao(self.db, alvo, ["ansiedade", "humor"])
        por_codigo = {v["code"]: v["origem"] for v in variaveis.do_artigo(self.db, alvo)}
        self.assertEqual(por_codigo["ansiedade"], "confirmada")   # já havia, foi confirmada
        self.assertEqual(por_codigo["humor"], "manual")           # acrescentada a mão
        self.assertNotIn("fibromialgia", por_codigo)              # tirada por quem leu

    def test_remarcar_nao_apaga_o_trabalho_humano(self):
        variaveis.marcar_artigos(self.db)
        alvo = self.artigo("ansiedade")
        variaveis.marcar_artigo_a_mao(self.db, alvo, ["humor"])
        variaveis.marcar_artigos(self.db, apenas_novos=False)
        codigos = {v["code"] for v in variaveis.do_artigo(self.db, alvo)}
        self.assertIn("humor", codigos, "a marcação humana foi apagada pela automática")


class TestVariavelPrincipal(unittest.TestCase):
    """Principal x secundária: o assunto DO artigo x o assunto citado nele.

    Sem essa separação a tabela de extração afirma que um artigo estuda
    sete coisas porque o resumo mencionou sete. O critério é onde a
    palavra apareceu — título é tese, resumo é menção.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        from lape import ingest_excel
        ingest_excel.ingest_articles(self.db, [
            {"title": "Ansiedade em atletas de alto rendimento",
             "notes": "Avaliamos também a qualidade do sono e a depressão.",
             "authors": "Ana Souza", "status": "Publicado", "year_published": 2024},
        ])
        variaveis.instalar(self.db)
        variaveis.marcar_artigos(self.db)
        self.alvo = self.db.scalar("SELECT id FROM articles LIMIT 1")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def peso(self):
        return {v["code"]: v["principal"] for v in variaveis.do_artigo(self.db, self.alvo)}

    def test_o_titulo_faz_a_variavel_principal(self):
        self.assertEqual(self.peso()["ansiedade"], 1)

    def test_o_resumo_sozinho_faz_secundaria(self):
        peso = self.peso()
        self.assertEqual(peso["sono"], 0)
        self.assertEqual(peso["depressao"], 0)

    def test_as_principais_vem_primeiro(self):
        pesos = [v["principal"] for v in variaveis.do_artigo(self.db, self.alvo)]
        self.assertEqual(pesos, sorted(pesos, reverse=True))

    def test_quem_leu_marcou_e_principal(self):
        # a mão de quem leu vale mais que qualquer heurística de texto
        variaveis.marcar_artigo_a_mao(self.db, self.alvo, ["humor"])
        self.assertEqual(self.peso()["humor"], 1)

    def test_o_onde_fica_gravado(self):
        ondes = {v["code"]: v["onde"] for v in variaveis.do_artigo(self.db, self.alvo)}
        self.assertEqual(ondes["ansiedade"], "título")
        self.assertEqual(ondes["sono"], "resumo")

    def test_banco_antigo_recupera_o_onde_pelo_trecho(self):
        # marcações gravadas antes da coluna existir só guardavam o lugar
        # no começo do trecho; sem recuperá-lo, tudo viraria secundária
        self.db.execute("UPDATE article_variables SET onde = NULL")
        self.db.conn.commit()
        self.assertEqual(sorted(set(self.peso().values())), [0])
        variaveis.preencher_onde(self.db)
        self.assertEqual(self.peso()["ansiedade"], 1)
        self.assertEqual(self.peso()["sono"], 0)

    def test_a_regra_em_sql_e_a_mesma_em_python(self):
        for v in variaveis.do_artigo(self.db, self.alvo):
            with self.subTest(code=v["code"]):
                self.assertEqual(bool(v["principal"]), variaveis.e_principal(v["onde"]))


class TestFiltros(unittest.TestCase):
    def test_a_mediana_movel_ignora_o_pico_isolado(self):
        # um ano em que a banca liberou cinco defesas de uma vez não é
        # uma tendência
        cru = [2, 2, 2, 40, 2, 2, 2]
        suave = analise.mediana_movel(cru)
        self.assertEqual(max(suave), 2)

    def test_a_suavizacao_mantem_a_forma(self):
        crescente = [1, 2, 3, 4, 5, 6]
        suave = analise.suavizar(crescente)
        self.assertTrue(all(b >= a for a, b in zip(suave, suave[1:])))

    def test_o_ruido_e_o_que_sobra(self):
        f = analise.sinal_e_ruido([2, 2, 9, 2, 2, 2, 2])
        self.assertGreater(max(f["ruido"]), 1, "o pico não apareceu como ruído")

    def test_serie_de_um_ano_so_nao_vira_tendencia(self):
        # o defeito que este teste guarda: 19 zeros e um pico produziam
        # "subindo, confiável" — uma ladeira bonita sobre um ponto só
        f = analise.sinal_e_ruido([0] * 19 + [18])
        self.assertFalse(f["confiavel"])
        self.assertIsNone(f["razao_ruido"])
        self.assertIn("1 ano", f["porque"])
        self.assertEqual(
            analise.tendencia(f["suave"], analise.velocidade(f["suave"]),
                              f["anos_com_dado"]),
            "sem série suficiente")


class TestDerivadas(unittest.TestCase):
    def test_velocidade_de_uma_reta_e_constante(self):
        vel = analise.velocidade([0, 1, 2, 3, 4, 5])
        self.assertTrue(all(abs(v - 1) < 1e-9 for v in vel))

    def test_aceleracao_de_uma_reta_e_zero(self):
        self.assertTrue(all(a == 0 for a in analise.aceleracao([0, 1, 2, 3, 4, 5])))

    def test_a_inflexao_cai_antes_do_pico(self):
        # é o ponto que interessa diagnosticar: a curva ainda sobe, mas já
        # parou de abrir — e quase sempre passa despercebido
        serie = [1, 2, 4, 7, 11, 14, 16, 17, 17, 16, 14]
        anos = list(range(2016, 2027))
        f = analise.sinal_e_ruido(serie)
        achados = analise.inflexoes(anos, f["suave"])
        self.assertTrue(achados)
        pico = anos[f["suave"].index(max(f["suave"]))]
        desaceleracao = [i for i in achados if i["tipo"] == "desaceleração"]
        self.assertTrue(desaceleracao)
        self.assertLess(desaceleracao[0]["ano"], pico)

    def test_a_leitura_distingue_subida_de_queda(self):
        # "voltou a abrir" escrito sobre uma queda que apenas desacelerou
        # diria o contrário do que aconteceu
        anos = list(range(2016, 2027))
        caindo = analise.sinal_e_ruido([18, 17, 15, 12, 8, 5, 3, 2, 2, 2, 2])
        for achado in analise.inflexoes(anos, caindo["suave"]):
            self.assertIn(achado["tipo"], ("alívio", "aprofundamento"))
            self.assertIn("caía", achado["leitura"])

    def test_o_cruzamento_diz_quem_passou_quem(self):
        anos = list(range(2020, 2026))
        a = {"code": "a", "label": "Sobe", "suave": [1, 2, 3, 4, 5, 6]}
        b = {"code": "b", "label": "Desce", "suave": [6, 5, 4, 3, 2, 1]}
        encontros = analise.cruzamentos(a, b, anos)
        self.assertEqual(len(encontros), 1)
        self.assertEqual(encontros[0]["quem_subiu"], "Sobe")
        self.assertEqual(encontros[0]["quem_desceu"], "Desce")

    def test_curvas_que_nao_se_tocam_nao_geram_cruzamento(self):
        anos = list(range(2020, 2024))
        a = {"code": "a", "label": "A", "suave": [5, 6, 7, 8]}
        b = {"code": "b", "label": "B", "suave": [1, 1, 2, 2]}
        self.assertEqual(analise.cruzamentos(a, b, anos), [])


class TestPanorama(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "t.sqlite")
        self.db.migrate()
        from lape import ingest_excel
        linhas = []
        for ano in range(2015, 2026):
            for i in range(max(1, (ano - 2014) // 2)):
                linhas.append({
                    "title": f"Treinamento resistido e ansiedade em fibromialgia {ano}-{i}",
                    "authors": "Ana Souza", "status": "Publicado", "year_published": ano})
        ingest_excel.ingest_articles(self.db, linhas)
        variaveis.instalar(self.db)
        variaveis.marcar_artigos(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_a_janela_padrao_sao_vinte_anos(self):
        p = analise.panorama(self.db)
        self.assertEqual(len(p["janela"]["anos"]), analise.JANELA_PADRAO_ANOS)

    def test_a_janela_pode_ser_apertada(self):
        p = analise.panorama(self.db, desde=2020, ate=2025)
        self.assertEqual(p["janela"]["anos"], list(range(2020, 2026)))

    def test_com_serie_de_verdade_ha_tendencia(self):
        p = analise.panorama(self.db, desde=2015, ate=2025)
        ansiedade = next(v for v in p["variaveis"] if v["code"] == "ansiedade")
        self.assertTrue(ansiedade["confiavel"])
        self.assertEqual(ansiedade["tendencia"], "subindo")
        self.assertIsNotNone(ansiedade["crescimento_ao_ano"])

    def test_a_rede_liga_o_que_aparece_junto(self):
        p = analise.panorama(self.db)
        pares = {(a["a"], a["b"]) for a in p["rede"]["arestas"]}
        self.assertIn(("fibromialgia", "ansiedade"), pares | {(b, a) for a, b in pares})

    def test_o_jaccard_corrige_o_que_aparece_em_tudo(self):
        p = analise.panorama(self.db)
        for aresta in p["rede"]["arestas"]:
            self.assertLessEqual(aresta["jaccard"], 1.0)
            self.assertGreater(aresta["jaccard"], 0)

    def test_artigo_sem_ano_e_contado_a_parte(self):
        from lape import ingest_excel
        ingest_excel.ingest_articles(self.db, [
            {"title": "Ansiedade sem data nenhuma", "authors": "X", "status": "Em produção"}])
        variaveis.marcar_artigos(self.db)
        self.assertGreaterEqual(analise.panorama(self.db)["sem_ano"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
