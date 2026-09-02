#!/usr/bin/env python3
"""Testes de quem e quem: grafias do nome, orientacao e quem ja saiu.

    python3 -m unittest tests.test_identidade -v

Uma pessoa assina de varias maneiras, e as bases indexam cada assinatura
como uma entrada diferente. Sem um lugar para dizer "estas quatro grafias
sao a mesma pessoa", a producao de alguem aparece repartida entre
fantasmas -- e o painel anuncia como pesquisador do laboratorio um nome
que ninguem reconhece.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import ingest_autor, ingest_excel, linhas  # noqa: E402
from lape.db import Database  # noqa: E402
from lape.util import author_key  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


class BaseIdentidade(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.caminho = Path(self.tmp.name) / "id.sqlite"
        self.db = Database(self.caminho)
        self.addCleanup(self.db.close)
        self.db.migrate()

    def reabrir(self):
        """Outro processo: e onde o cache em memoria deixa de existir."""
        self.db.conn.commit()
        outro = Database(self.caminho)
        self.addCleanup(outro.close)
        return outro


class TestGrafiasDoNome(BaseIdentidade):

    def test_a_grafia_sobrevive_ao_fim_do_processo(self):
        """Era só cache em memória, e por isso durava uma execução.

        A planilha declarava as variações, a importação daquele momento as
        respeitava, e no processo seguinte estava tudo esquecido. Quem
        preenchia a coluna via funcionar uma vez e nunca mais -- sem nada
        na tela dizendo que o dado não tinha sido guardado.
        """
        pessoa = self.db.member_id("Guilherme Torres Vilarino")
        self.db.register_alias("Torres Vilarino, G", pessoa)
        depois = self.reabrir()
        self.assertEqual(depois.member_id("Torres Vilarino, G", create=False), pessoa)

    def test_as_quatro_grafias_do_vilarino_caem_na_mesma_pessoa(self):
        """As quatro saíram de uma auditoria dos registros da PubMed.

        Duas delas -- as que trazem "Torres Vilarino" -- geram uma chave
        canônica DIFERENTE, porque o programa lê "Torres" como nome próprio
        e não como primeira metade de um sobrenome composto.
        """
        pessoa = self.db.member_id("Guilherme Torres Vilarino")
        for grafia in ("Torres Vilarino, G", "Torres Vilarino, Guilherme",
                       "Torres Vilarino G"):
            self.db.register_alias(grafia, pessoa)
        depois = self.reabrir()
        for grafia in ("Vilarino, Guilherme Torres", "Vilarino, Guilherme T",
                       "Torres Vilarino, Guilherme", "Torres Vilarino, G"):
            with self.subTest(grafia=grafia):
                self.assertEqual(depois.member_id(grafia, create=False), pessoa)

    def test_sem_a_grafia_a_forma_composta_seria_outra_pessoa(self):
        # é o teste que mostra por que a tabela precisa existir
        self.assertNotEqual(author_key("Vilarino, Guilherme Torres"),
                            author_key("Torres Vilarino, G"))

    def test_a_grafia_declarada_ganha_do_palpite_por_sobrenome(self):
        # o que a pessoa escreveu sobre o próprio nome vale mais do que a
        # regra que o programa inventa a partir do sobrenome
        certo = self.db.member_id("Carla Souza")
        self.db.member_id("Marina Andrade")
        self.db.register_alias("Andrade C", certo)
        depois = self.reabrir()
        self.assertEqual(depois.member_id("Andrade C", create=False), certo)

    def test_grafia_que_e_nome_de_outra_pessoa_e_recusada(self):
        """Apontar duas pessoas para a mesma chave é sorteio, não escolha.

        Juntar dois cadastros é destrutivo e tem de ser explícito.
        """
        um = self.db.member_id("Alexandro Andrade")
        dois = self.db.member_id("Guilherme Torres Vilarino")
        with self.assertRaises(ValueError) as caso:
            self.db.register_alias("Alexandro Andrade", dois)
        self.assertIn("outro integrante", str(caso.exception))
        self.assertEqual(self.db.member_id("Alexandro Andrade", create=False), um)

    def test_trocar_a_lista_apaga_o_que_saiu_dela(self):
        # o campo da tela mostra a lista inteira: apagar uma linha ali tem
        # de apagar de verdade, senão a pessoa remove uma grafia errada,
        # salva, e ela continua valendo
        pessoa = self.db.member_id("Guilherme Torres Vilarino")
        self.db.set_aliases(pessoa, "Torres Vilarino G; Vilarino Guilherme")
        self.db.set_aliases(pessoa, "Torres Vilarino G")
        depois = self.reabrir()
        self.assertEqual(depois.member_id("Torres Vilarino G", create=False), pessoa)
        self.assertIsNone(depois.member_id("Vilarino Guilherme", create=False))

    def test_o_proprio_nome_nao_vira_apelido_de_si_mesmo(self):
        """Nem as grafias que já dão a mesma chave canônica.

        "Alexandro Andrade" e "Andrade, A" viram os dois `andrade_a`: a
        chave já resolve, e guardar a linha seria ocupar espaço para não
        decidir nada. Só "Andrade Alexandre" -- outra chave -- é apelido.
        """
        pessoa = self.db.member_id("Alexandro Andrade")
        self.db.set_aliases(pessoa, "Alexandro Andrade; Andrade, A; Andrade Alexandre")
        guardadas = [r["alias"] for r in self.db.dicts(
            "SELECT alias FROM member_aliases WHERE member_id = ?", (pessoa,))]
        self.assertEqual(len(guardadas), 1, guardadas)

    def test_gravar_outro_campo_nao_apaga_as_grafias(self):
        """`in row`, e não `row.get(...)`.

        Sem a distinção entre "a coluna não veio" e "a coluna veio vazia",
        salvar o telefone limparia as variações de nome sem ninguém pedir.
        """
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Guilherme Torres Vilarino", "aliases": "Torres Vilarino G"}])
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Guilherme Torres Vilarino", "phone": "48 99999-0000"}])
        depois = self.reabrir()
        self.assertIsNotNone(depois.member_id("Torres Vilarino G", create=False))

    def test_a_coluna_vazia_apaga_de_proposito(self):
        """Apagar a grafia apaga a LINHA -- não desliga o resto do sistema.

        Depois de apagada, "Torres Vilarino G" ainda pode cair na pessoa
        certa pelo palpite de sobrenome, que é outra regra e continua
        valendo. O que a coluna vazia promete é não guardar mais aquela
        declaração, e é isso que se confere.
        """
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Guilherme Torres Vilarino", "aliases": "Torres Vilarino, G"}])
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM member_aliases"), 1)
        ingest_excel.ingest_members(self.db, [
            {"full_name": "Guilherme Torres Vilarino", "aliases": ""}])
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM member_aliases"), 0)
        depois = self.reabrir()
        self.assertIsNone(depois.member_id("Torres Vilarino, G", create=False))

    def test_a_view_do_pesquisador_devolve_as_grafias(self):
        # sem isto o campo da tela abre vazio mesmo com grafias gravadas,
        # e quem salvar o perfil apaga todas sem perceber
        pessoa = self.db.member_id("Guilherme Torres Vilarino")
        self.db.set_aliases(pessoa, "Torres Vilarino G; Vilarino GT")
        self.db.conn.commit()
        linha = self.db.dicts("SELECT aliases FROM v_researcher WHERE id = ?", (pessoa,))[0]
        self.assertIn("Torres Vilarino G", linha["aliases"])

    def test_o_campo_da_tela_esta_ligado_ao_dado(self):
        """Faltava o `from:`, e sem ele o campo era enfeite.

        Não carregava o que estava gravado, não gravava o que se digitava,
        e a tela ainda respondia "Perfil atualizado".
        """
        html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        trecho = html[html.index('field("Variações"'):]
        self.assertIn('from: "aliases"', trecho[:400])


class TestAsGrafiasDosDoisProfessores(BaseIdentidade):
    """A lista saiu da auditoria da PubMed, não de palpite."""

    def test_os_dois_tem_grafias_declaradas(self):
        for pessoa in ingest_autor.PESQUISADORES:
            with self.subTest(quem=pessoa["nome"]):
                self.assertTrue(pessoa.get("grafias"))

    def test_declarar_junta_tudo_numa_pessoa_so(self):
        for pessoa in ingest_autor.PESQUISADORES:
            ingest_autor.declarar_grafias(self.db, pessoa)
        depois = self.reabrir()
        vilarino = depois.member_id("Guilherme Torres Vilarino", create=False)
        andrade = depois.member_id("Alexandro Andrade", create=False)
        self.assertIsNotNone(vilarino)
        self.assertNotEqual(vilarino, andrade)
        for grafia in ("Torres Vilarino, G", "Vilarino GT", "Vilarino, Guilherme T"):
            with self.subTest(grafia=grafia):
                self.assertEqual(depois.member_id(grafia, create=False), vilarino)
        for grafia in ("Andrade, A", "Andrade A"):
            with self.subTest(grafia=grafia):
                self.assertEqual(depois.member_id(grafia, create=False), andrade)

    def test_declarar_nao_multiplica_integrantes(self):
        for _ in range(3):
            for pessoa in ingest_autor.PESQUISADORES:
                ingest_autor.declarar_grafias(self.db, pessoa)
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM members"), 2)

    def test_as_grafias_entram_antes_da_busca(self):
        # depois seria tarde: os registros da forma composta já teriam
        # criado o integrante fantasma que elas existem para evitar
        fonte = (ROOT / "scripts" / "lape" / "ingest_autor.py").read_text(encoding="utf-8")
        corpo = fonte[fonte.index("def trazer_todos"):]
        self.assertLess(corpo.index("declarar_grafias(db, pessoa)"),
                        corpo.index("trazer(db, pessoa"))


class TestAsLinhasDoLape(BaseIdentidade):

    def test_as_sete_entram(self):
        resultado = linhas.instalar(self.db)
        self.assertEqual(len(resultado["novas"]), 7)
        nomes = [r["name"] for r in self.db.dicts("SELECT name FROM research_lines")]
        for esperado in ("Atividade Física e Saúde", "Psicologia do Exercício",
                         "Psicologia do Esporte",
                         "Qualidade do ar e poluição no exercício e no esporte",
                         "Exercício na saúde física e mental na Fibromialgia",
                         "Exercício na saúde mental no tratamento do câncer",
                         "Exercício na saúde mental no envelhecimento"):
            with self.subTest(linha=esperado):
                self.assertIn(esperado, nomes)

    def test_instalar_de_novo_nao_duplica(self):
        linhas.instalar(self.db)
        segunda = linhas.instalar(self.db)
        self.assertEqual(segunda["novas"], [])
        self.assertEqual(self.db.scalar("SELECT COUNT(*) FROM research_lines"), 7)

    def test_o_nome_que_alguem_reescreveu_fica(self):
        # instalar de novo não pode desfazer o que a coordenação ajustou
        linhas.instalar(self.db)
        self.db.execute("UPDATE research_lines SET name = ? WHERE code = ?",
                        ("Psicologia do Esporte (CEFID)", "psicologia_esporte"))
        self.db.conn.commit()
        linhas.instalar(self.db)
        self.assertEqual(
            self.db.scalar("SELECT name FROM research_lines WHERE code = ?",
                           ("psicologia_esporte",)),
            "Psicologia do Esporte (CEFID)")

    def test_toda_linha_tem_palavras_chave(self):
        # é por elas que a busca da tela encontra a linha
        for codigo, nome, descricao, palavras in linhas.LINHAS:
            with self.subTest(linha=nome):
                self.assertTrue(palavras.strip(), f"{nome} sem palavras-chave")
                self.assertTrue(descricao.strip(), f"{nome} sem descrição")

    def test_o_botao_existe_na_tela(self):
        html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        self.assertIn("/api/research-lines/padrao", html)
        fonte = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        self.assertIn('route_linhas_padrao, "coordenacao"', fonte)


class TestQuemSaiuDoLaboratorio(unittest.TestCase):
    """Sair do laboratório não apaga o que a pessoa escreveu."""

    def test_o_mural_fala_no_presente_e_filtra(self):
        js = (TEMPLATES / "mural.js").read_text(encoding="utf-8")
        corpo = js[js.index("function slideDestaques"):]
        corpo = corpo[:corpo.index("const SLIDES")]
        self.assertIn("m.active !== 0", corpo)
        self.assertIn("!m.left_on", corpo)

    def test_o_painel_e_historico_e_marca_em_vez_de_apagar(self):
        """Apagar falsificaria o passado; não marcar engana o presente."""
        js = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
        corpo = js[js.index('view("equipe"'):]
        corpo = corpo[:corpo.index('view("rede"')]
        self.assertIn("(saiu)", corpo)
        self.assertIn("person.left_on", corpo)

    def test_a_data_de_saida_chega_ao_navegador(self):
        # sem ela no payload, o filtro do mural nunca teria o que ler
        fonte = (ROOT / "scripts" / "lape" / "metrics.py").read_text(encoding="utf-8")
        corpo = fonte[fonte.index("def member_productivity"):]
        corpo = corpo[:corpo.index("\ndef ", 10)]
        self.assertIn("m.left_on", corpo)
        esquema = (ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
        view = esquema[esquema.index("CREATE VIEW IF NOT EXISTS v_researcher"):]
        self.assertIn("m.left_on", view[:3000])


class TestOrientadorSemLista(unittest.TestCase):
    """Um campo que não se pode preencher precisa dizer por quê."""

    def test_a_lista_vazia_explica_onde_se_resolve(self):
        html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        trecho = html[html.index('field("Orientador"'):]
        trecho = trecho[:trecho.index('field("Instituição"')]
        self.assertIn("vazio:", trecho)
        self.assertIn("pós-doutorado", trecho)

    def test_o_select_vazio_se_desliga_e_avisa(self):
        html = (TEMPLATES / "app.html").read_text(encoding="utf-8")
        corpo = html[html.index('} else if (f.type === "select")'):]
        corpo = corpo[:corpo.index('} else if (f.type === "checkbox")')]
        self.assertIn("!options.length && f.vazio", corpo)
        self.assertIn("input.disabled = true", corpo)
