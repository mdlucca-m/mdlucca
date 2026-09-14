#!/usr/bin/env python3
"""Testes da leitura do arquivo `.env`.

    python3 -m unittest tests.test_config -v

As chaves da Scopus e da Web of Science moram no `.env`, na raiz. Ate
aqui, quem lia esse arquivo eram os SCRIPTS DE SUBIDA -- o `publicar.sh`,
o `publicar.ps1`, o systemd. Cada um a sua maneira, e nenhum deles no
caminho de quem so da um duplo clique no `Abrir LAPE.bat` ou chama
`python scripts/lape_agent.py api` na mao. Nesses caminhos o sistema
subia sem chave nenhuma, e a tela de citacoes dizia "falta configurar"
com a chave escrita a dois palmos dali.

O que estes testes guardam nao e o formato do arquivo: e que a leitura
aconteca no unico lugar por onde TODOS os caminhos passam, e que ler o
arquivo nunca atropele o que ja estava no ambiente.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import config  # noqa: E402


class BaseEnv(unittest.TestCase):
    """Cada teste escreve um `.env` seu e devolve o ambiente como estava."""

    CHAVES = ("SCOPUS_API_KEY", "WOS_API_KEY", "SCOPUS_INST_TOKEN",
              "LAPE_CONTACT_EMAIL", "UMA_QUALQUER")

    def setUp(self):
        self._antes = {k: os.environ.get(k) for k in self.CHAVES}
        for chave in self.CHAVES:
            os.environ.pop(chave, None)
        self.pasta = Path(tempfile.mkdtemp(prefix="lape-env-"))

    def tearDown(self):
        for chave, valor in self._antes.items():
            if valor is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = valor

    def escrever(self, texto: str, nome: str = ".env", bom: bool = False):
        dados = texto.encode("utf-8")
        if bom:
            dados = b"\xef\xbb\xbf" + dados
        (self.pasta / nome).write_bytes(dados)


class TestLeituraDoEnv(BaseEnv):

    def test_as_chaves_do_arquivo_chegam_ao_ambiente(self):
        """O defeito: subir por um caminho que nao le o arquivo.

        Tres scripts de subida liam o `.env`, e nenhum deles e chamado
        pelo atalho da area de trabalho. A leitura precisa morar aqui.
        """
        self.escrever("SCOPUS_API_KEY=chave-da-scopus\nWOS_API_KEY=chave-da-wos\n")
        lido = config._carregar_env(self.pasta)
        self.assertEqual(lido, ".env")
        self.assertEqual(os.environ["SCOPUS_API_KEY"], "chave-da-scopus")
        self.assertEqual(os.environ["WOS_API_KEY"], "chave-da-wos")

    def test_o_ambiente_de_verdade_vence_o_arquivo(self):
        """Quem passou a chave na mao mandou mais do que o arquivo.

        E o que mantem de pe os tres scripts de subida: eles continuam
        pondo as variaveis antes do Python comecar, e o arquivo nao pode
        desfazer isso -- nem o ajuste de quem exporta uma chave so para
        um comando, para testar uma chave nova sem mexer no arquivo.
        """
        os.environ["SCOPUS_API_KEY"] = "veio-do-ambiente"
        self.escrever("SCOPUS_API_KEY=veio-do-arquivo\n")
        config._carregar_env(self.pasta)
        self.assertEqual(os.environ["SCOPUS_API_KEY"], "veio-do-ambiente")

    def test_o_bom_do_bloco_de_notas_nao_come_a_primeira_chave(self):
        """Com BOM, some UMA chave -- e e sempre a de cima.

        Pior do que sumirem todas: some so a primeira, o resto funciona,
        e ninguem desconfia do arquivo. O Bloco de Notas ainda grava o
        BOM, e e com ele que o laboratorio edita o `.env`.
        """
        self.escrever("SCOPUS_API_KEY=primeira\nWOS_API_KEY=segunda\n", bom=True)
        config._carregar_env(self.pasta)
        self.assertEqual(os.environ.get("SCOPUS_API_KEY"), "primeira")
        self.assertEqual([k for k in os.environ if "﻿" in k], [])

    def test_o_arquivo_salvo_como_env_ponto_txt_tambem_serve(self):
        """O Bloco de Notas grava ".env.txt" quando se pede ".env".

        A extensao vem escondida no Explorador, entao o arquivo PARECE
        certo na tela de quem o criou. Recusa-lo seria cobrar do usuario
        um detalhe que o proprio Windows escondeu dele.
        """
        self.escrever("WOS_API_KEY=pela-extensao-escondida\n", nome=".env.txt")
        self.assertEqual(config._carregar_env(self.pasta), ".env.txt")
        self.assertEqual(os.environ["WOS_API_KEY"], "pela-extensao-escondida")

    def test_o_env_de_verdade_ganha_do_env_ponto_txt(self):
        """Havendo os dois, o certo e o que manda."""
        self.escrever("WOS_API_KEY=do-certo\n")
        self.escrever("WOS_API_KEY=do-torto\n", nome=".env.txt")
        self.assertEqual(config._carregar_env(self.pasta), ".env")
        self.assertEqual(os.environ["WOS_API_KEY"], "do-certo")

    def test_aspas_comentario_e_export_nao_entram_no_valor(self):
        """O `.env.example` traz comentarios, e o Linux traz `export`.

        Uma chave com aspas em volta vira uma chave invalida, e a base
        responde 401 -- que a tela mostra como "chave nao aceita". A
        pessoa troca uma chave que estava certa.
        """
        self.escrever('# comentario\n'
                      'export SCOPUS_API_KEY="com-aspas"\n'
                      '\n'
                      "WOS_API_KEY='com-apostrofo'\n"
                      'linha sem igual\n'
                      'LAPE_CONTACT_EMAIL=  espaco@udesc.br  \n')
        config._carregar_env(self.pasta)
        self.assertEqual(os.environ["SCOPUS_API_KEY"], "com-aspas")
        self.assertEqual(os.environ["WOS_API_KEY"], "com-apostrofo")
        self.assertEqual(os.environ["LAPE_CONTACT_EMAIL"], "espaco@udesc.br")
        self.assertNotIn("# comentario", os.environ)

    def test_sem_arquivo_nenhum_nao_quebra_nem_inventa(self):
        """Nao ter `.env` e o caso normal de quem clonou agora."""
        self.assertEqual(config._carregar_env(self.pasta), "")
        self.assertIsNone(os.environ.get("SCOPUS_API_KEY"))


class TestConstantesQueAsBasesLeem(BaseEnv):

    def test_o_email_de_contato_existe_como_constante(self):
        """`sources.py` passa `mailto` em toda consulta -- e ninguem o produzia.

        O parametro estava encanado da ponta a ponta, e a unica chamada
        que o preenchia fazia `getattr(config, "CONTACT_EMAIL", None)`
        numa constante que nao existia. Devolvia None calado, e o
        laboratorio ficava na fila anonima da OpenAlex com o e-mail ja
        escrito no `.env`. O `getattr` com padrao e que escondia: um
        acesso direto teria estourado no primeiro uso.
        """
        self.assertTrue(hasattr(config, "CONTACT_EMAIL"))
        origem = (ROOT / "scripts" / "lape" / "config.py").read_text(encoding="utf-8")
        self.assertIn('LAPE_CONTACT_EMAIL', origem)

    def test_quem_le_citacoes_recebe_o_email(self):
        """A constante so serve se chegar a chamada."""
        origem = (ROOT / "scripts" / "lape" / "ingest_citations.py").read_text(
            encoding="utf-8")
        self.assertIn("CONTACT_EMAIL", origem)


if __name__ == "__main__":
    unittest.main(verbosity=2)
