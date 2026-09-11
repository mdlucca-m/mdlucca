#!/usr/bin/env python3
"""Testes do atalho que sobe o sistema num duplo clique.

    python3 -m unittest tests.test_atalho -v

Nao e capricho: as tres coisas que deram errado ao subir o sistema a mao
foram sempre as mesmas, e nenhuma delas tem a ver com o sistema.

    C:\\Users\\mdluc>\\deploy\\publicar.ps1 -Fixo
    O sistema nao pode encontrar o caminho especificado.

    C:\\Users\\mdluc>git pull
    fatal: not a git repository

    PS C:\\Users\\mdluc> get pull
    O termo 'get' nao e reconhecido...

Janela aberta na pasta errada, "git" digitado como "get", e o PowerShell
recusando o script por politica de execucao. O que estes testes guardam e
que o atalho continua resolvendo as tres -- e que ele chega em Windows com
a quebra de linha que o cmd.exe sabe ler.
"""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATALHO = ROOT / "Subir LAPE.bat"


class TestOAtalhoExiste(unittest.TestCase):

    def test_o_arquivo_esta_na_raiz(self):
        # na raiz de proposito: `%~dp0` aponta para a pasta dele, e e de la
        # que `deploy\publicar.ps1` precisa ser alcancavel
        self.assertTrue(ATALHO.is_file(), f"{ATALHO.name} nao esta na raiz")

    def test_a_quebra_de_linha_e_a_do_windows(self):
        """Com LF puro o cmd.exe engole caractere e erra em outro lugar.

        O erro que aparece na tela nao tem relacao nenhuma com a causa, e
        quem le vai procurar defeito no sistema.
        """
        bruto = ATALHO.read_bytes()
        self.assertIn(b"\r\n", bruto)
        soltos = bruto.replace(b"\r\n", b"")
        self.assertNotIn(b"\n", soltos, "ha linha terminada so com LF")

    def test_o_git_marca_o_arquivo_como_crlf(self):
        """Sem isto o git normaliza conforme a maquina de cada um.

        O arquivo chegaria quebrado justamente em quem vai usa-lo.
        """
        pronto = subprocess.run(
            ["git", "check-attr", "eol", "--", ATALHO.name],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertIn("eol: crlf", pronto.stdout)

    def test_o_arquivo_e_ascii(self):
        # o cmd.exe abre numa pagina de codigo que varia de maquina em
        # maquina; acento vira caractere estranho no meio de um aviso
        ATALHO.read_bytes().decode("ascii")


class TestOAtalhoResolveOsTresTropecos(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.corpo = ATALHO.read_text(encoding="ascii")

    def test_ele_mesmo_entra_na_pasta_certa(self):
        # o tropeco numero um: a janela abre em C:\Users\seu-nome
        self.assertIn('cd /d "%~dp0"', self.corpo)

    def test_passa_por_cima_da_politica_de_execucao(self):
        # o tropeco numero tres: o PowerShell recusa o script
        self.assertIn("-ExecutionPolicy Bypass", self.corpo)

    def test_chama_o_publicar_com_endereco_fixo(self):
        self.assertIn(r'-File "deploy\publicar.ps1" -Fixo', self.corpo)

    def test_o_script_que_ele_chama_existe(self):
        # atalho que aponta para arquivo inexistente falha no duplo clique,
        # que e onde ninguem vai ler a mensagem
        self.assertTrue((ROOT / "deploy" / "publicar.ps1").is_file())

    def test_avisa_quando_foi_copiado_para_fora_da_pasta(self):
        # copiar o .bat para a area de trabalho quebra o `%~dp0`: o aviso
        # diz o que fazer (criar atalho) em vez de so falhar
        self.assertIn('if not exist "deploy\\publicar.ps1"', self.corpo)
        self.assertIn("criar atalho", self.corpo)

    def test_sem_git_o_sistema_ainda_sobe(self):
        """Falta de git nao pode impedir o laboratorio de abrir.

        A maquina do CEFID nao tem administrador, e pode nao ter git. O
        sistema que esta na pasta funciona do mesmo jeito.
        """
        self.assertIn("where git", self.corpo)
        self.assertIn("seguindo sem buscar atualizacao", self.corpo)

    def test_a_atualizacao_nao_desfaz_trabalho_local(self):
        # `--ff-only` recusa em vez de inventar merge no banco vivo, que
        # fica modificado nessa maquina
        self.assertIn("git pull --ff-only", self.corpo)

    def test_a_falha_ao_atualizar_nao_para_a_subida(self):
        self.assertIn("Seguindo com a versao desta", self.corpo)

    def test_a_janela_nao_fecha_sozinha(self):
        """Sem `pause`, a janela fecha e leva o endereco com ela.

        E e ela que mantem o tunel de pe: fechar derruba o site.
        """
        self.assertIn("pause", self.corpo)
        self.assertIn("precisa FICAR ABERTA", self.corpo)

    def test_diz_como_desligar(self):
        self.assertIn("-Parar", self.corpo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
