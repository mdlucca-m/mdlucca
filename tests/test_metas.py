#!/usr/bin/env python3
"""Metas do ano: o realizado, a meta e a projeção -- três coisas diferentes.

    python3 -m unittest tests.test_metas -v

O realizado é dado, a meta é decisão e a projeção é palpite. O que se
verifica aqui é sobretudo que a terceira não se apresente como as duas
primeiras: método declarado, faixa em vez de número único, e nenhuma
afirmação sobre o futuro quando não há base para fazê-la.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import metas  # noqa: E402
from lape.db import Database  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
HOJE = date(2026, 9, 11)          # setembro: 69% do ano decorrido


class BaseDasMetas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(Path(self.tmp.name) / "metas.sqlite")
        self.addCleanup(self.db.close)
        self.db.migrate()

    def publicar(self, ano: int, quantos: int, meses=None):
        """Publica `quantos` artigos no ano, nos meses dados (ou sem mês).

        Os meses são percorridos em ordem, e não sorteados. Sorteados, a
        fatia do ano saía diferente em cada ano por acaso, e o teste da
        faixa degenerada nunca chegava a exercitar o caso que ele existe
        para cobrir -- foi o que uma mutação mostrou.
        """
        for i in range(quantos):
            dados = {"title": f"A{ano}-{i}", "title_key": f"a{ano}-{i}",
                     "status": "publicado", "year_published": ano}
            if meses:
                dados["published_on"] = f"{ano}-{meses[i % len(meses)]:02d}-15"
            self.db.insert("articles", dados)
        self.db.conn.commit()

    def publicacoes(self, ano=2026, hoje=HOJE):
        linha = metas.progresso(self.db, ano, hoje=hoje)["indicadores"]
        return [i for i in linha if i["codigo"] == "publicacoes"][0]


class TestAMetaEDecisao(BaseDasMetas):

    def test_sem_meta_o_sistema_nao_inventa_uma(self):
        """Sugerir a meta seria o sistema decidindo o que o laboratório quer."""
        self.publicar(2026, 5)
        item = self.publicacoes()
        self.assertIsNone(item["meta"])
        self.assertIsNone(item["pct"])
        self.assertEqual(item["veredito"], "sem meta declarada")

    def test_a_meta_gravada_volta(self):
        metas.declarar(self.db, 2026, "publicacoes", 15, por="coordenação")
        self.assertEqual(metas.metas_declaradas(self.db, 2026)["publicacoes"], 15)

    def test_apagar_a_meta_devolve_o_indicador_ao_estado_sem_meta(self):
        metas.declarar(self.db, 2026, "publicacoes", 15)
        metas.declarar(self.db, 2026, "publicacoes", None)
        self.assertNotIn("publicacoes", metas.metas_declaradas(self.db, 2026))

    def test_indicador_desconhecido_e_recusado(self):
        with self.assertRaises(ValueError):
            metas.declarar(self.db, 2026, "inventado", 10)

    def test_numero_absurdo_e_recusado(self):
        for valor in (-1, 5000):
            with self.subTest(meta=valor):
                with self.assertRaises(ValueError):
                    metas.declarar(self.db, 2026, "publicacoes", valor)


class TestOQueFaltaFazer(BaseDasMetas):

    def test_diz_quanto_falta_por_mes_e_nao_so_quanto_falta(self):
        """"Faltam 2" não diz o que fazer; "1 por mês até dezembro" diz."""
        self.publicar(2026, 13)
        metas.declarar(self.db, 2026, "publicacoes", 15)
        item = self.publicacoes()
        self.assertEqual(item["faltam"], 2)
        self.assertEqual(item["precisa_por_mes"], round(2 / 3, 2))

    def test_meta_ja_batida_nao_pede_mais_nada(self):
        self.publicar(2026, 16)
        metas.declarar(self.db, 2026, "publicacoes", 15)
        item = self.publicacoes()
        self.assertEqual(item["faltam"], 0)
        self.assertIsNone(item["precisa_por_mes"])
        self.assertEqual(item["veredito"], "alcançada")


class TestAProjecaoDoAno(BaseDasMetas):
    """A parte que é palpite, e que por isso é a mais perigosa da tela."""

    def _historico_sazonal(self):
        # laboratório que publica no fim do ano: em setembro, um terço saiu
        fim_de_ano = [3, 6, 9, 10, 11, 11, 12, 12, 12]
        for ano in range(2019, 2026):
            self.publicar(ano, 9, meses=fim_de_ano)

    def test_usa_o_historico_do_proprio_laboratorio_quando_ele_existe(self):
        """Dividir pelo tempo decorrido supõe um ano uniforme, e ele não é.

        Aceite e publicação andam em lote, e dezembro não se parece com
        fevereiro. Quem sabe a forma do ano deste laboratório é o histórico
        dele -- e a diferença entre os dois métodos muda o número.
        """
        self._historico_sazonal()
        self.publicar(2026, 13, meses=[2, 3, 4, 5, 6, 7, 8, 9])
        item = self.publicacoes()
        self.assertEqual(item["projecao"]["metodo"], "sazonal")
        self.assertGreaterEqual(item["projecao"]["anos_de_base"], metas.ANOS_MINIMOS)
        # a regra proporcional diria ~19; o histórico deste laboratório,
        # que publica no fim do ano, diz bem mais
        self.assertGreater(item["projecao"]["central"], 25)

    def test_sem_historico_com_mes_cai_na_regra_proporcional_e_diz_isso(self):
        """Uma projeção sem método declarado é palpite passando por medida."""
        for ano in range(2019, 2026):
            self.publicar(ano, 12)            # só o ano, sem mês
        self.publicar(2026, 13)
        item = self.publicacoes()
        self.assertEqual(item["projecao"]["metodo"], "linear")

    def test_historico_curto_demais_nao_vira_sazonalidade(self):
        """Dois anos desenham a forma do ano por acaso."""
        for ano in (2024, 2025):
            self.publicar(ano, 12, meses=[1, 4, 7, 10])
        self.publicar(2026, 5, meses=[2, 3])
        self.assertEqual(self.publicacoes()["projecao"]["metodo"], "linear")

    def test_ano_com_poucos_trabalhos_nao_entra_na_base(self):
        for ano in range(2019, 2026):
            self.publicar(ano, metas.POR_ANO_MINIMO - 1, meses=[3, 9])
        self.publicar(2026, 4, meses=[2])
        self.assertEqual(self.publicacoes()["projecao"]["metodo"], "linear")

    def test_a_faixa_nunca_fecha_enquanto_o_ano_nao_acaba(self):
        """Faixa de largura zero é uma afirmação de certeza sobre o futuro.

        Um histórico regular faz a fatia mínima e a máxima coincidirem, e a
        projeção sairia como um número único.
        """
        for ano in range(2019, 2026):
            self.publicar(ano, 12, meses=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        self.publicar(2026, 6, meses=[1, 2, 3, 4, 5, 6])
        projecao = self.publicacoes()["projecao"]
        self.assertEqual(projecao["metodo"], "sazonal")
        self.assertGreater(projecao["ate"], projecao["de"])

    def test_a_faixa_nunca_projeta_menos_do_que_ja_aconteceu(self):
        """O ano não anda para trás."""
        self._historico_sazonal()
        self.publicar(2026, 30, meses=[2, 3, 4])
        projecao = self.publicacoes()["projecao"]
        self.assertGreaterEqual(projecao["de"], 30)

    def test_zero_ate_agora_nao_projeta_zero_para_o_ano(self):
        """De zero eventos não se estima taxa nenhuma.

        Dividir zero pelo tempo decorrido devolve zero, e a tela passava a
        afirmar que o ano termina em zero -- em setembro, com três meses
        pela frente, e com o veredito no passado ("não alcançada"). O teto
        vem da regra de três: nenhum evento em T diz que a taxa está
        abaixo de 3/T, e é isso que ainda cabe no que resta.
        """
        metas.declarar(self.db, 2026, "submissoes", 12)
        cedo = [i for i in metas.progresso(self.db, 2026, hoje=date(2026, 3, 1))["indicadores"]
                if i["codigo"] == "submissoes"][0]
        self.assertGreater(cedo["projecao"]["ate"], 0)
        self.assertEqual(cedo["veredito"], "depende do fim do ano")

        tarde = [i for i in metas.progresso(self.db, 2026, hoje=HOJE)["indicadores"]
                 if i["codigo"] == "submissoes"][0]
        self.assertGreater(tarde["projecao"]["ate"], 0)
        self.assertEqual(tarde["veredito"], "no ritmo atual, não alcança")

    def test_no_ultimo_dia_do_ano_o_zero_e_definitivo(self):
        metas.declarar(self.db, 2026, "submissoes", 12)
        fim = [i for i in metas.progresso(self.db, 2026, hoje=date(2026, 12, 31))["indicadores"]
               if i["codigo"] == "submissoes"][0]
        self.assertEqual(fim["projecao"]["ate"], 0)
        self.assertEqual(fim["veredito"], "não alcançada")

    def test_ano_fechado_nao_e_projetado(self):
        self.publicar(2025, 11)
        item = [i for i in metas.progresso(self.db, 2025, hoje=HOJE)["indicadores"]
                if i["codigo"] == "publicacoes"][0]
        self.assertEqual(item["projecao"]["metodo"], "fechado")
        self.assertEqual(item["projecao"]["de"], item["projecao"]["ate"])


class TestOVeredito(BaseDasMetas):

    def _com_meta(self, feitos, meta, hoje=HOJE):
        for ano in range(2019, 2026):
            self.publicar(ano, 12, meses=[1, 3, 5, 7, 9, 11])
        self.publicar(2026, feitos, meses=[2, 3])
        metas.declarar(self.db, 2026, "publicacoes", meta)
        return self.publicacoes(hoje=hoje)["veredito"]

    def test_muito_atras_diz_que_nao_alcanca(self):
        self.assertEqual(self._com_meta(2, 30), "no ritmo atual, não alcança")

    def test_no_meio_nao_finge_saber(self):
        """Entre o piso e o teto da faixa, a resposta honesta é "depende".

        Com 8 publicados em setembro e este histórico, o ano deve terminar
        entre 8 e 12. Uma meta de 11 cai dentro da faixa: dizer "alcança"
        ou "não alcança" ali seria escolher uma ponta da própria incerteza.
        """
        self.assertEqual(self._com_meta(8, 11), "depende do fim do ano")

    def test_acima_do_teto_da_faixa_diz_que_nao_alcanca(self):
        self.assertEqual(self._com_meta(8, 20), "no ritmo atual, não alcança")

    def test_so_afirma_que_alcanca_quando_ate_o_pior_caso_alcanca(self):
        """O piso da faixa é que decide, não o centro dela.

        Afirmar pelo centro seria escolher a metade otimista da própria
        incerteza -- e a frase que chega na tela é "alcança", sem o "talvez".
        """
        fim_de_ano = [3, 6, 9, 10, 11, 11, 12, 12, 12]
        for ano in range(2019, 2026):
            self.publicar(ano, 9, meses=fim_de_ano)
        self.publicar(2026, 13, meses=[2, 3, 4, 5, 6, 7, 8, 9])
        metas.declarar(self.db, 2026, "publicacoes", 15)
        item = self.publicacoes()
        self.assertGreaterEqual(item["projecao"]["de"], 15)
        self.assertEqual(item["veredito"], "no ritmo atual, alcança")

    def test_em_dezembro_nao_fala_em_ritmo_atual(self):
        """O ano acabou: "no ritmo atual" não cabe mais."""
        self.assertEqual(self._com_meta(3, 30, hoje=date(2026, 12, 31)),
                         "não alcançada")


class TestATelaDoPainel(unittest.TestCase):

    def setUp(self):
        self.js = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
        self.corpo = self.js[self.js.index('view("metas"'):]
        self.corpo = self.corpo[:self.corpo.index('view("explorar"')]

    def test_a_tela_diz_de_onde_veio_a_projecao(self):
        self.assertIn("sazonal", self.corpo)
        self.assertIn("histórico do próprio laboratório", self.corpo)
        self.assertIn("regra proporcional", self.corpo)

    def test_a_projecao_aparece_como_faixa_e_nao_como_numero(self):
        self.assertIn('pj.de + "–" + pj.ate', self.corpo)

    def test_a_escala_cabe_a_meta_e_o_topo_da_faixa(self):
        # senão uma projeção acima da meta sai encostada na borda e parece empate
        self.assertIn("Math.max(i.meta || 0, pj.ate || 0", self.corpo)

    def test_o_veredito_nunca_e_so_cor(self):
        # cor de estado entra com rótulo ao lado, nunca sozinha
        self.assertIn("text: i.veredito", self.corpo)


class TestOResumoNumaPagina(unittest.TestCase):
    """A tela que mostra o laboratório inteiro de uma vez.

    O painel é navegado: vinte e uma telas, uma por vez, cada uma boa para
    trabalhar e nenhuma boa para olhar. Esta é a que responde "como o
    laboratório está" sem obrigar a percorrer seis seções e juntar de
    cabeça -- e o que se cobra aqui é que ela não vire um amontoado de
    números, que é o que ela seria fácil de ser.
    """

    def setUp(self):
        self.js = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
        self.corpo = self.js[self.js.index('view("resumo"'):]
        self.corpo = self.corpo[:self.corpo.index('view("visao"')]

    def test_abre_primeiro(self):
        """Uma tela de visão geral que não é a primeira não é visão geral."""
        bloco = self.js[self.js.index('{ id: "geral"'):]
        bloco = bloco[:bloco.index("},")]
        self.assertIn('views: ["resumo"', bloco)

    def test_cada_cartao_traz_uma_leitura_e_nao_so_o_numero(self):
        """13 publicações é muito ou pouco conforme a meta e o ano anterior.

        Sem a leitura ao lado, cada pessoa interpreta sozinha -- e é aí
        que um painel vira enfeite.
        """
        self.assertGreaterEqual(self.corpo.count("leituraDe("), 4)

    def test_compara_o_ano_com_o_anterior(self):
        self.assertIn("ano - 1", self.corpo)

    def test_mostra_a_projecao_como_faixa(self):
        self.assertIn("metaPub.projecao.de", self.corpo)
        self.assertIn("metaPub.projecao.ate", self.corpo)

    def test_conta_o_que_esta_sem_classificacao(self):
        """O que falta não aparece em gráfico de composição nenhum."""
        self.assertIn("sem linha de pesquisa", self.corpo)
        self.assertIn("sem vínculo declarado", self.corpo)

    def test_separa_pesquisador_de_coautor(self):
        self.assertIn("n_collaborators", self.corpo)
        self.assertIn("ser do grupo", self.corpo)

    def test_sem_citacao_nenhuma_diz_o_que_falta_em_vez_de_tres_zeros(self):
        """Três zeros lado a lado é a ausência de informação ocupando um cartão."""
        self.assertIn("Ainda sem citação registrada", self.corpo)
        self.assertIn("sem DOI", self.corpo)

    def test_sem_linha_classificada_nao_desenha_barra_de_zeros(self):
        """Barra de comprimento zero parece gráfico e não diz nada."""
        self.assertIn("comArtigo.length", self.corpo)

    def test_o_grafico_nao_fica_espremido_numa_coluna(self):
        # gráfico que não se lê é enfeite ocupando o lugar de um número
        self.assertIn('producao.classList.add("largo")', self.corpo)
        css = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
        self.assertIn(".resumo .largo", css)

    def test_avisa_o_manuscrito_parado(self):
        """Ninguém é lembrado do artigo que não deu notícia."""
        self.assertIn("90 dias", self.corpo)


class TestADefinicaoDosGraficos(unittest.TestCase):
    """Gráfico desenhado no tamanho real, e não esticado pelo CSS.

    Todo gráfico era autorado num sistema de 760 pixels e o CSS esticava o
    SVG para a largura do container. Num cartão de 300px isso é escala
    0,39: o rótulo de 10,5px vira 4,1px e o traço de 1px vira 0,4px. É daí
    que vinha o aspecto apagado -- SVG é vetorial, mas vetorial não
    conserta tipografia reduzida a um terço.
    """

    def setUp(self):
        self.charts = (TEMPLATES / "charts.js").read_text(encoding="utf-8")
        self.dash = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")

    def test_nenhum_grafico_tem_largura_fixa(self):
        self.assertNotIn("const W = 760", self.charts)
        self.assertIn("const W = spec.width || 760", self.charts)

    def test_a_propria_biblioteca_mede_o_container(self):
        """O envoltório fica na biblioteca, e não em cada chamada.

        Envolver aqui é o que faz as vinte e três telas herdarem a
        correção de uma vez -- e o que impede a próxima tela de nascer com
        o mesmo defeito.
        """
        self.assertIn("function responsivo(", self.charts)
        self.assertIn("caixa.clientWidth", self.charts)
        self.assertIn("ResizeObserver", self.charts)

    def test_as_formas_largas_saem_envolvidas(self):
        bloco = self.charts[self.charts.rindex("  return {"):]
        for forma in ("columns", "bars", "lines", "area", "scatter", "network"):
            with self.subTest(forma=forma):
                self.assertRegex(bloco, forma + r":\s*responsivo\(")

    def test_as_formas_de_tamanho_proprio_ficam_de_fora(self):
        """Rosca, medidor e radar não são esticados -- são centrados.

        Deixá-los crescer até a largura do cartão é que estragaria.
        """
        bloco = self.charts[self.charts.rindex("  return {"):]
        for forma in ("donut", "gauge", "radar", "sparkline"):
            with self.subTest(forma=forma):
                self.assertNotRegex(bloco, forma + r":\s*responsivo\(")

    def test_o_envoltorio_nao_entra_em_laco(self):
        """Redesenhar troca o conteúdo, o observador acorda de novo.

        Sem um limiar de largura isso não pararia nunca.
        """
        corpo = self.charts[self.charts.index("function responsivo("):]
        corpo = corpo[:corpo.index("\n  return {")]
        self.assertIn("Math.abs(largura - ultima)", corpo)

    def test_quem_passa_largura_desenha_na_hora(self):
        """Quem exporta para imagem não tem container nenhum para medir."""
        corpo = self.charts[self.charts.index("function responsivo("):]
        corpo = corpo[:corpo.index("\n  return {")]
        self.assertIn("if (spec.width) return fn(spec);", corpo)


class TestOsIndicadoresSegmentados(unittest.TestCase):

    def setUp(self):
        self.dash = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
        self.css = (TEMPLATES / "theme.css").read_text(encoding="utf-8")

    def test_o_indicador_mostra_do_que_o_numero_e_feito(self):
        """"116 artigos, mas quantos saíram?" é a pergunta seguinte."""
        self.assertIn("spec.segmentos", self.dash)
        self.assertIn("kpi-seg", self.dash)

    def test_a_composicao_vem_com_legenda(self):
        # cor sozinha não nomeia coisa alguma
        self.assertIn("kpi-seg-leg", self.dash)

    def test_os_pedacos_tem_intervalo_entre_si(self):
        """Sem intervalo, duas cores vizinhas leem-se como uma faixa só."""
        bloco = self.css[self.css.index(".kpi-seg {"):]
        bloco = bloco[:bloco.index("}")]
        self.assertIn("gap: 2px", bloco)

    def test_o_minigrafico_nao_cresce_ate_competir_com_o_numero(self):
        bloco = self.css[self.css.index(".kpi .spark {"):]
        bloco = bloco[:bloco.index("}")]
        self.assertIn("max-width", bloco)

    def test_a_barra_horizontal_aceita_composicao(self):
        charts = (TEMPLATES / "charts.js").read_text(encoding="utf-8")
        corpo = charts[charts.index("function bars(spec)"):]
        corpo = corpo[:corpo.index("function lines(spec)")]
        self.assertIn("item.partes", corpo)
        # o mesmo intervalo de 2px do indicador, pelo mesmo motivo
        self.assertIn("x += pw + 2", corpo)


if __name__ == "__main__":
    unittest.main()
