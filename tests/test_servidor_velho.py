#!/usr/bin/env python3
"""O servidor velho rodando telas novas.

    python3 -m unittest tests.test_servidor_velho -v

As TELAS sao lidas do disco a cada acesso; as ROTAS sao carregadas uma vez,
quando o processo sobe. Depois de um `git pull` sem reiniciar, o navegador
recebe a tela nova e ela bate numa API antiga -- e o erro que aparece e
"rota nao encontrada", que nao diz a ninguem o que fazer.

Aconteceu duas vezes no laboratorio, e as duas custaram gente conferindo
cadastro achando que o sistema tinha quebrado. E um estado que so some
reiniciando, entao quem tem de perceber e o servidor, e nao a pessoa.
"""
from __future__ import annotations

import os
import re
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import api  # noqa: E402

TEMPLATES = ROOT / "scripts" / "lape" / "templates"
APP = (TEMPLATES / "app.html").read_text(encoding="utf-8")
TEMA = (TEMPLATES / "theme.css").read_text(encoding="utf-8")


class TestADeteccao(unittest.TestCase):

    def setUp(self):
        self.alvo = ROOT / "scripts" / "lape" / "classificar.py"
        st = self.alvo.stat()
        self.original = (st.st_atime, st.st_mtime)
        self.addCleanup(os.utime, self.alvo, self.original)

    def test_processo_novo_nao_se_acha_velho(self):
        self.assertFalse(api.codigo_desatualizado()["desatualizado"])

    def test_py_mais_novo_que_o_processo_acende_o_aviso(self):
        os.utime(self.alvo, (self.original[0], time.time() + 300))
        saida = api.codigo_desatualizado()
        self.assertTrue(saida["desatualizado"])
        self.assertIn("classificar.py", saida["arquivos"])

    def test_o_aviso_diz_o_que_fazer(self):
        """"Rota não encontrada" não é instrução. "Suba o sistema de novo" é."""
        os.utime(self.alvo, (self.original[0], time.time() + 300))
        aviso = api.codigo_desatualizado()["aviso"]
        self.assertIn("suba o sistema de novo", aviso.lower())
        self.assertIn("versão anterior", aviso)

    def test_o_aviso_traz_as_duas_datas(self):
        """Sem as datas, não dá para conferir se o restart pegou."""
        os.utime(self.alvo, (self.original[0], time.time() + 300))
        saida = api.codigo_desatualizado()
        self.assertRegex(saida["subiu_em"], r"^\d{4}-\d{2}-\d{2}T")
        self.assertRegex(saida["codigo_de"], r"^\d{4}-\d{2}-\d{2}T")

    def test_salvar_durante_a_subida_nao_conta(self):
        """Gravar um .py no mesmo segundo em que o servidor sobe é normal."""
        os.utime(self.alvo, (self.original[0], api._SUBIU_EM + 1))
        self.assertFalse(api.codigo_desatualizado()["desatualizado"])

    def test_a_conta_nao_quebra_se_a_pasta_sumir(self):
        """Uma verificação de saúde não pode derrubar a verificação de saúde."""
        corpo = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        trecho = corpo[corpo.index("def codigo_desatualizado"):]
        trecho = trecho[:trecho.index("\ndef ")]
        self.assertIn("except OSError", trecho)


class TestOndeOAvisoAparece(unittest.TestCase):

    def test_a_saude_carrega_o_estado(self):
        corpo = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        saude = corpo[corpo.index("def route_health"):]
        saude = saude[:saude.index("\ndef ")]
        self.assertIn('"codigo": codigo_desatualizado()', saude)

    def test_a_rota_de_saude_e_publica(self):
        """A faixa precisa aparecer antes de qualquer login dar certo."""
        corpo = (ROOT / "scripts" / "lape" / "api.py").read_text(encoding="utf-8")
        achado = re.search(r'\^/api/health/\?\$",\s*\w+,\s*(None|"\w+")', corpo)
        self.assertIsNotNone(achado)
        self.assertEqual(achado.group(1), "None")

    def test_a_tela_so_acusa_depois_de_confirmar(self):
        """Acusar "versão velha" por um 404 qualquer troca um erro confuso
        por outro: a tela pergunta ao servidor antes de pôr a faixa."""
        corpo = APP[APP.index("async function avisarServidorVelho"):]
        corpo = corpo[:corpo.index("\n}")]
        self.assertIn("/api/health", corpo)
        self.assertIn("if (!c.desatualizado) return;", corpo)

    def test_a_faixa_aparece_uma_vez_so(self):
        corpo = APP[APP.index("let avisouVelho"):]
        self.assertIn("if (avisouVelho) return;", corpo[:200])

    def test_so_o_404_de_rota_dispara(self):
        """Um 404 de registro que não existe não é servidor velho."""
        corpo = APP[APP.index("async function api(path"):]
        corpo = corpo[:corpo.index("\n}")]
        self.assertIn("response.status === 404", corpo)
        self.assertIn("rota n", corpo)

    def test_a_faixa_tem_folha(self):
        self.assertIn(".faixa-velha", TEMA)

    def test_a_faixa_nao_usa_cor_sozinha(self):
        """Faixa âmbar sem texto não informa; o texto é que diz o que houve."""
        corpo = APP[APP.index("const faixa = h("):]
        corpo = corpo[:corpo.index("document.body.insertBefore")]
        self.assertIn("Feche a janela preta", corpo)
        self.assertIn("Subir LAPE", corpo)


if __name__ == "__main__":
    unittest.main()
