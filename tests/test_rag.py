#!/usr/bin/env python3
"""Testes da camada de recuperacao semantica.

    python3 -m unittest tests.test_rag -v

O que se persegue aqui e a falha silenciosa. Um RAG quebra de um jeito
particularmente traicoeiro: ele nunca lanca excecao, apenas devolve o
trecho errado, e quem le a resposta nao tem como saber. Por isso os
testes cobrem, mais do que o caminho feliz, as tres formas de mentir sem
erro — indice vazio que devolve resposta, mudanca de modelo que compara
vetores incomparaveis, e conteudo alterado que fica com o vetor velho.
"""
from __future__ import annotations

import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402

from lape.rag import chunk, index, search  # noqa: E402
from lape.rag.embed import HashEmbedder, get_embedder, normalizar  # noqa: E402
from lape.rag.store import Filtro, SqliteStore  # noqa: E402

TEXTO_A = """Introdução

O humor é um estado afetivo difuso que responde à carga de treino antes que o
desempenho caia. A Escala de Humor de Brunel reúne seis subescalas.

Método

Participaram 27 atletas de handebol masculino de primeira divisão nacional.
A coleta ocorreu ao longo de sete dias consecutivos de pré-temporada.

Resultados

O vigor caiu 3,15 pontos entre o primeiro e o último dia. A fadiga subiu
3,19 pontos no mesmo intervalo, com tamanho de efeito pareado de 0,72.
"""

TEXTO_B = """Introdução

A carga de treino no handebol distribui-se de forma desigual entre jogadores.

Resultados

A restituição noturna devolveu 72,3% do custo diurno da fadiga física.
O saldo diário ficou em 0,47 ponto acumulado por dia.
"""


def _store(tmp: Path) -> tuple[sqlite3.Connection, SqliteStore]:
    conn = sqlite3.connect(tmp / "t.sqlite")
    conn.row_factory = sqlite3.Row
    s = SqliteStore(conn)
    s.ensure_schema()
    return conn, s


def _doc(uri: str, texto: str, **kw) -> chunk.Document:
    return chunk.Document(uri=uri, text=texto, kind=kw.pop("kind", "tese"), **kw)


class TestChunking(unittest.TestCase):
    def test_detecta_secoes(self):
        trechos = chunk.split(TEXTO_A, limite=400, sobreposicao=0)
        secoes = {t.section for t in trechos if t.section}
        self.assertIn("Introdução", secoes)
        self.assertIn("Método", secoes)
        self.assertIn("Resultados", secoes)

    def test_respeita_o_limite(self):
        longo = "Uma frase de tamanho medio. " * 400
        trechos = chunk.split(longo, limite=500, sobreposicao=50)
        self.assertTrue(trechos)
        # A sobreposicao acrescenta caracteres; a folga cobre isso sem
        # permitir que um trecho dobre de tamanho.
        for t in trechos:
            self.assertLessEqual(len(t.text), 500 + 50 + 120, t.text[:60])

    def test_offsets_avancam(self):
        trechos = chunk.split(TEXTO_A, limite=300, sobreposicao=0)
        for anterior, seguinte in zip(trechos, trechos[1:]):
            self.assertLessEqual(anterior.char_start, seguinte.char_start)

    def test_formato_nao_suportado_falha_claro(self):
        with tempfile.TemporaryDirectory() as tmp:
            alvo = Path(tmp) / "planilha.xlsx"
            alvo.write_bytes(b"nada")
            with self.assertRaises(chunk.ExtractionError) as ctx:
                chunk.from_path(alvo)
            self.assertIn("xlsx", str(ctx.exception))


class TestEmbedder(unittest.TestCase):
    def test_vetores_normalizados(self):
        v = HashEmbedder(64).embed_documents(["um texto", "outro texto"])
        np.testing.assert_allclose(np.linalg.norm(v, axis=1), 1.0, atol=1e-5)

    def test_deterministico(self):
        a = HashEmbedder(64).embed_query("fadiga física")
        b = HashEmbedder(64).embed_query("fadiga física")
        np.testing.assert_allclose(a, b)

    def test_hash_se_declara_nao_semantico(self):
        self.assertFalse(HashEmbedder().semantic)

    def test_backend_nomeado_falha_alto(self):
        """Quem pede voyage sem chave precisa saber; cair no hash em silencio
        produziria busca ruim sem nenhum sinal."""
        from lape.rag.embed import EmbeddingError, VoyageEmbedder
        with self.assertRaises(EmbeddingError):
            VoyageEmbedder(api_key="")


class TestIndexacaoEBusca(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.conn, self.store = _store(self.tmp)
        self.emb = HashEmbedder(256)
        index.indexar_documentos(
            self.store,
            [_doc("mem://a", TEXTO_A, title="Estudo A", year=2024),
             _doc("mem://b", TEXTO_B, title="Estudo B", year=2025, kind="article")],
            self.emb, verbose=False)

    def tearDown(self):
        self.conn.close()
        self._tmp.cleanup()

    def test_indexou(self):
        s = self.store.stats()
        self.assertEqual(s["documentos"], 2)
        self.assertGreater(s["trechos"], 0)
        self.assertEqual(s["trechos"], s["vetores"])

    def test_idempotente(self):
        rel = index.indexar_documentos(
            self.store, [_doc("mem://a", TEXTO_A, title="Estudo A", year=2024)],
            self.emb, verbose=False)
        self.assertEqual(rel.indexados, 0)
        self.assertEqual(rel.pulados, 1)

    def test_conteudo_alterado_reindexa(self):
        """O vetor nao pode sobreviver a mudanca do texto."""
        rel = index.indexar_documentos(
            self.store, [_doc("mem://a", TEXTO_A + "\n\nNovo parágrafo com dado novo.",
                              title="Estudo A", year=2024)],
            self.emb, verbose=False)
        self.assertEqual(rel.indexados, 1)

    def test_busca_lexica_encontra(self):
        hits = self.store.search_lexical("restituição noturna", 5)
        self.assertTrue(hits)
        self.assertIn("72,3", " ".join(h.text for h in hits))

    def test_busca_densa_encontra(self):
        q = self.emb.embed_query("o vigor caiu entre o primeiro e o ultimo dia")
        hits = self.store.search_dense(q, 3)
        self.assertTrue(hits)

    def test_hibrida_funde_as_duas(self):
        r = search.buscar(self.store, "fadiga física restituição", k=4,
                          embedder=self.emb)
        self.assertTrue(r.hits)
        self.assertGreater(r.densa, 0)
        self.assertGreater(r.lexica, 0)
        self.assertIsNotNone(r.aviso)      # hash avisa que nao e semantico

    def test_filtro_por_tipo(self):
        r = search.buscar(self.store, "carga de treino", k=5, embedder=self.emb,
                          filtro=Filtro(kinds=["article"]))
        self.assertTrue(r.hits)
        for h in r.hits:
            self.assertEqual(h.kind, "article")

    def test_filtro_por_ano(self):
        r = search.buscar(self.store, "handebol", k=5, embedder=self.emb,
                          filtro=Filtro(anos=(2025, None)))
        for h in r.hits:
            self.assertGreaterEqual(h.year, 2025)

    def test_dimensao_incompativel_grita(self):
        """Trocar de modelo sem reindexar compara coisas incomparaveis. Isso
        precisa falhar alto, e nao devolver um ranking sem sentido."""
        with self.assertRaises(ValueError) as ctx:
            self.store.search_dense(np.zeros(7, dtype=np.float32), 3)
        self.assertIn("reindexe", str(ctx.exception))

    def test_indice_vazio_nao_inventa(self):
        vazio = sqlite3.connect(":memory:")
        s2 = SqliteStore(vazio)
        s2.ensure_schema()
        r = search.buscar(s2, "qualquer coisa", k=5, embedder=self.emb)
        self.assertEqual(r.hits, [])
        vazio.close()

    def test_citacao_rastreavel(self):
        r = search.buscar(self.store, "vigor", k=1, embedder=self.emb)
        cit = r.hits[0].citacao()
        self.assertIn("trecho", cit)
        self.assertTrue(cit.startswith("["))

    def test_contexto_respeita_o_teto(self):
        r = search.buscar(self.store, "handebol", k=8, embedder=self.emb)
        self.assertLessEqual(len(r.contexto(max_chars=300)), 400)

    def test_apagar_documento(self):
        self.assertTrue(self.store.delete_document("mem://b"))
        self.assertEqual(self.store.stats()["documentos"], 1)
        # O gatilho do FTS precisa ter limpado o indice lexico junto.
        self.assertFalse(self.store.search_lexical("restituição noturna", 5))


class TestMCP(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.caminho = Path(self._tmp.name) / "mcp.sqlite"
        conn = sqlite3.connect(self.caminho)
        s = SqliteStore(conn)
        s.ensure_schema()
        index.indexar_documentos(s, [_doc("mem://a", TEXTO_A, title="Estudo A")],
                                 HashEmbedder(256), verbose=False)
        conn.close()
        from lape.rag.mcp_server import Servidor
        self.srv = Servidor(self.caminho)

    def tearDown(self):
        self.srv.conn.close()
        self._tmp.cleanup()

    def _chamar(self, nome, **args):
        r = self.srv.atender({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                              "params": {"name": nome, "arguments": args}})
        return r["result"]

    def test_handshake_ecoa_a_versao_do_cliente(self):
        r = self.srv.atender({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                              "params": {"protocolVersion": "2099-01-01"}})
        self.assertEqual(r["result"]["protocolVersion"], "2099-01-01")

    def test_lista_ferramentas_com_schema(self):
        r = self.srv.atender({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        for f in r["result"]["tools"]:
            self.assertIn("name", f)
            self.assertIn("description", f)
            self.assertEqual(f["inputSchema"]["type"], "object")

    def test_notificacao_nao_responde(self):
        self.assertIsNone(self.srv.atender(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_metodo_desconhecido_vira_erro_de_protocolo(self):
        r = self.srv.atender({"jsonrpc": "2.0", "id": 3, "method": "nao/existe"})
        self.assertEqual(r["error"]["code"], -32601)

    def test_ferramenta_desconhecida_nao_derruba_a_sessao(self):
        """Erro de ferramenta volta como resultado, nunca como erro JSON-RPC:
        o cliente precisa continuar a conversa."""
        r = self._chamar("nao_existe")
        self.assertTrue(r["isError"])
        self.assertIn("content", r)

    def test_busca_devolve_texto(self):
        r = self._chamar("buscar_corpus", consulta="vigor no ultimo dia", k=2)
        self.assertFalse(r["isError"])
        self.assertIn("trecho", r["content"][0]["text"])

    def test_checar_afirmacao_sem_cobertura(self):
        r = self._chamar("checar_afirmacao",
                         afirmacao="zzzz qqqq wwww xxxx yyyy vvvv")
        self.assertIn("COBERTURA", r["content"][0]["text"])

    def test_json_invalido_nao_derruba_o_laco(self):
        entrada = io.StringIO('{"nao e json\n'
                              '{"jsonrpc":"2.0","id":9,"method":"ping"}\n')
        saida = io.StringIO()
        self.srv.servir(entrada, saida)
        linhas = [json.loads(l) for l in saida.getvalue().strip().split("\n")]
        self.assertEqual(linhas[0]["error"]["code"], -32700)
        self.assertEqual(linhas[1]["id"], 9)


class TestLLMDegrada(unittest.TestCase):
    def test_agente_explica_a_falta_da_credencial(self):
        """Sem chave, o agente entrega o contexto recuperado em vez de falhar."""
        from lape.rag.agents import escrita
        from lape.rag.llm import disponivel
        with tempfile.TemporaryDirectory() as tmp:
            conn, store = _store(Path(tmp))
            index.indexar_documentos(store, [_doc("mem://a", TEXTO_A)],
                                     HashEmbedder(256), verbose=False)
            saida = escrita.executar(store, "escreva sobre o vigor", k=2,
                                     embedder=HashEmbedder(256))
            self.assertEqual(saida.agente, "escrita")
            self.assertTrue(saida.texto)
            if not disponivel()[0]:
                self.assertTrue(saida.fontes)
            conn.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestQuedaDeBackend(unittest.TestCase):
    """O 'auto' existe para absorver backend indisponivel. Se ele so apanhasse
    EmbeddingError, uma falha de rede ao baixar os pesos do modelo local
    derrubaria a indexacao inteira — foi o que aconteceu atras de um proxy que
    bloqueia o repositorio de modelos."""

    def test_falha_de_rede_no_local_cai_para_o_seguinte(self):
        from lape.rag import embed

        class FalhaDeRede(Exception):
            pass

        original = embed.LocalEmbedder
        embed.LocalEmbedder = lambda *a, **k: (_ for _ in ()).throw(
            FalhaDeRede("403 Forbidden"))
        try:
            emb = embed.get_embedder("auto", use_cache=False)
            self.assertFalse(emb.semantic)      # caiu no hash, nao explodiu
        finally:
            embed.LocalEmbedder = original

    def test_backend_nomeado_nao_e_absorvido(self):
        from lape.rag import embed
        original = embed.LocalEmbedder
        embed.LocalEmbedder = lambda *a, **k: (_ for _ in ()).throw(
            RuntimeError("403 Forbidden"))
        try:
            with self.assertRaises(RuntimeError):
                embed.get_embedder("local", use_cache=False)
        finally:
            embed.LocalEmbedder = original
