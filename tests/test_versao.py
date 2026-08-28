#!/usr/bin/env python3
"""Que versão está rodando — a pergunta por trás de "não atualizou".

    python3 -m unittest tests.test_versao -v

O sistema atualizado e o sistema velho são idênticos na primeira olhada.
Sem um número na tela, "atualizou?" só se responde abrindo um terminal —
e quem está no computador do laboratório não vai abrir.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api, versao  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"


class TestVersaoDoCodigo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.origem = self.base / "origem"
        self.copia = self.base / "copia"
        self.git("init", "--initial-branch=main", str(self.origem), cwd=self.base)
        (self.origem / "a.txt").write_text("um\n", encoding="utf-8")
        self.git("add", "-A", cwd=self.origem)
        self.commit("primeiro assunto", cwd=self.origem)
        self.git("clone", str(self.origem), str(self.copia), cwd=self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args, cwd):
        return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                              text=True, check=True)

    def commit(self, mensagem, cwd):
        return self.git("-c", "user.email=teste@lape", "-c", "user.name=Teste",
                        "commit", "-m", mensagem, cwd=cwd)

    def ler(self):
        return versao.atual(self.copia, usar_cache=False)

    def test_diz_qual_commit_esta_no_disco(self):
        dados = self.ler()
        self.assertRegex(dados["commit"], r"^[0-9a-f]{7,}$")
        self.assertRegex(dados["data"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(dados["assunto"], "primeiro assunto")
        self.assertEqual(dados["ramo"], "main")

    def test_conta_o_que_o_servidor_ja_tem_e_a_copia_nao(self):
        (self.origem / "a.txt").write_text("dois\n", encoding="utf-8")
        self.git("add", "-A", cwd=self.origem)
        self.commit("segundo assunto", cwd=self.origem)
        self.assertEqual(self.ler()["atrasada"], 0, "sem fetch, nada a declarar")
        self.git("fetch", cwd=self.copia)
        self.assertEqual(self.ler()["atrasada"], 1)

    def test_o_banco_vivo_nao_conta_como_alteracao_local(self):
        # a máquina do laboratório grava no banco o dia inteiro; se isso
        # contasse como "você mexeu no código", a tela acusaria alteração
        # local todos os dias e ninguém mais confiaria no aviso
        (self.copia / "data").mkdir()
        (self.copia / "data" / "db.sqlite").write_bytes(b"cadastro novo")
        self.assertFalse(self.ler()["suja"])
        (self.copia / "a.txt").write_text("mexido\n", encoding="utf-8")
        self.assertTrue(self.ler()["suja"])

    def test_fora_de_um_repositorio_responde_sem_quebrar(self):
        solta = self.base / "solta"
        solta.mkdir()
        dados = versao.atual(solta, usar_cache=False)
        self.assertIsNone(dados["commit"])
        self.assertEqual(versao.resumo(dados), "versão desconhecida")

    def test_o_resumo_cabe_numa_linha(self):
        resumo = versao.resumo(self.ler())
        self.assertIn("versão", resumo)
        self.assertLess(len(resumo), 80)
        self.assertNotIn("\n", resumo)

    def test_o_ramo_so_aparece_quando_nao_e_o_principal(self):
        # no main, dizer "ramo main" é ruído; fora dele, é a explicação
        self.assertNotIn("ramo", versao.resumo(self.ler()))
        self.git("checkout", "-b", "experimento", cwd=self.copia)
        self.assertIn("ramo experimento", versao.resumo(self.ler()))


class TestMarcaNaPagina(unittest.TestCase):
    def test_a_marca_sai_pronta_para_o_rodape(self):
        marca = api._marca_de_versao()
        self.assertIn('class="marca-versao"', marca)
        self.assertIn("versão", marca)

    def test_a_marca_tem_lugar_no_tema(self):
        css = (TEMPLATES / "theme.css").read_text(encoding="utf-8")
        self.assertIn(".marca-versao", css)
        # numa folha impressa a versão é lixo: quem imprime quer a tabela
        self.assertIn(".marca-versao { display: none !important; }",
                      css.replace(".no-print, ", ""))

    def test_o_rodape_entra_em_toda_pagina(self):
        # a substituição é feita no envio, não em cada template: página
        # nova nasce com a marca sem ninguém lembrar de acrescentá-la
        codigo = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        trecho = codigo[codigo.index("def _serve_page"):]
        trecho = trecho[:trecho.index("def _serve_database")]
        self.assertIn("_marca_de_versao()", trecho)
        self.assertIn("</body>", trecho)


if __name__ == "__main__":
    unittest.main(verbosity=2)
