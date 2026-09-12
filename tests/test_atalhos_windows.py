#!/usr/bin/env python3
"""Os arquivos de duplo clique da maquina do laboratorio.

    python3 -m unittest tests.test_atalhos_windows -v

Existem porque as tres coisas que dao errado ao fazer isso a mao sao
sempre as mesmas, e todas ja aconteceram nesta maquina: a janela abre em
C:\\Users\\seu-nome e nao na pasta do sistema; o PowerShell recusa o script
por politica de execucao; e um valor copiado do painel de alguma conta vai
parar no prompt como se fosse comando.

O modo de errar proprio DESTES arquivos e diferente e pior: passar o modo
do tunel a mao. A tarefa agendada guarda os argumentos com que foi
registrada, entao um `-Fixo` escrito aqui que discorde do modo gravado
faria o computador subir, toda manha, num endereco diferente do que o
laboratorio inteiro tem salvo -- e o link morreria em silencio, de noite,
sem ninguem ter mexido em nada.

Por isso o `.bat` nao escolhe modo: quem escolhe e o publicar.ps1, lendo
o que ja esta gravado.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ATALHOS = {
    "Subir LAPE.bat": "",
    "Subir sozinho ao ligar.bat": "-AoLigar",
    "Nao subir sozinho.bat": "-NaoAoLigar",
}


class TestOsAtalhosExistem(unittest.TestCase):

    def test_os_tres_estao_na_raiz(self):
        for nome in ATALHOS:
            with self.subTest(arquivo=nome):
                self.assertTrue((ROOT / nome).exists(), nome)

    def test_cada_um_chama_a_sua_opcao(self):
        for nome, opcao in ATALHOS.items():
            if not opcao:
                continue
            with self.subTest(arquivo=nome):
                texto = (ROOT / nome).read_text(encoding="utf-8")
                linha = next(l for l in texto.splitlines()
                             if l.strip().startswith("powershell "))
                self.assertIn(opcao, linha)


class TestOQueCadaAtalhoNaoPodeFazer(unittest.TestCase):

    def corpo(self, nome: str) -> str:
        """O arquivo sem os comentarios: `rem` explica, nao executa."""
        return "\n".join(l for l in (ROOT / nome).read_text(encoding="utf-8").splitlines()
                         if not l.strip().lower().startswith("rem"))

    def test_o_atalho_de_agendar_nao_escolhe_o_modo_do_tunel(self):
        """Escolher aqui é o jeito de a tarefa subir num endereço diferente
        do que o laboratório tem salvo, de manhã, sem ninguém ter mexido."""
        for nome in ("Subir sozinho ao ligar.bat", "Nao subir sozinho.bat"):
            with self.subTest(arquivo=nome):
                corpo = self.corpo(nome)
                for modo in ("-Fixo", "-Permanente", "-Sorteado", "-Dominio"):
                    self.assertNotIn(modo, corpo,
                                     "%s escolhe o modo do túnel" % nome)

    def test_nenhum_atalho_carrega_segredo(self):
        """Authtoken em arquivo versionado é authtoken publicado."""
        for nome in ATALHOS:
            with self.subTest(arquivo=nome):
                texto = (ROOT / nome).read_text(encoding="utf-8")
                self.assertNotRegex(texto, r"\b(rd|ak|cr|tn|ep|as|ed)_[A-Za-z0-9]{12,}")
                self.assertNotIn("add-authtoken", texto)


class TestAsTresArmadilhasConhecidas(unittest.TestCase):

    def ler(self, nome: str) -> str:
        return (ROOT / nome).read_text(encoding="utf-8")

    def test_todos_entram_na_pasta_do_proprio_arquivo(self):
        """A janela abre em C:\\Users\\seu-nome, e não na pasta do sistema."""
        for nome in ATALHOS:
            with self.subTest(arquivo=nome):
                self.assertIn('cd /d "%~dp0"', self.ler(nome))

    def test_todos_liberam_a_politica_de_execucao(self):
        for nome in ATALHOS:
            with self.subTest(arquivo=nome):
                self.assertIn("-ExecutionPolicy Bypass", self.ler(nome))

    def test_todos_conferem_estar_na_pasta_certa(self):
        """Copiar o arquivo para a área de trabalho, em vez de criar atalho."""
        for nome in ATALHOS:
            with self.subTest(arquivo=nome):
                texto = self.ler(nome)
                self.assertIn('if not exist "deploy\\publicar.ps1"', texto)
                self.assertIn("criar atalho", texto.lower())

    def test_a_janela_nao_fecha_sozinha_no_fim(self):
        """Sem `pause` NO FIM, o resultado some antes de ser lido.

        Procurar a palavra em qualquer lugar do arquivo nao serve: ha um
        `pause` dentro do bloco que avisa "este arquivo nao esta na pasta
        certa", e ele passava o teste mesmo com o do fim removido.
        """
        for nome in ATALHOS:
            with self.subTest(arquivo=nome):
                linhas = [l.strip() for l in self.ler(nome).splitlines() if l.strip()]
                self.assertEqual(linhas[-1].lower(), "pause",
                                 "%s não pausa na última linha" % nome)


class TestOFormatoDoArquivo(unittest.TestCase):
    """Um .bat malformado não dá erro: executa a primeira linha e para."""

    def test_a_quebra_de_linha_e_a_do_windows(self):
        for nome in ATALHOS:
            with self.subTest(arquivo=nome):
                bruto = (ROOT / nome).read_bytes()
                self.assertIn(b"\r\n", bruto, "%s está com quebra de Unix" % nome)
                soltos = re.findall(rb"(?<!\r)\n", bruto)
                self.assertEqual(soltos, [], "%s mistura quebras" % nome)

    def test_nao_ha_acento(self):
        """O cmd.exe não roda em UTF-8: acento vira caractere quebrado, e o
        texto que existe para orientar passa a atrapalhar."""
        for nome in ATALHOS:
            with self.subTest(arquivo=nome):
                bruto = (ROOT / nome).read_bytes()
                self.assertEqual(bruto.decode("ascii", errors="ignore").encode("ascii"),
                                 bruto, "%s tem byte fora do ASCII" % nome)

    def test_a_opcao_existe_no_script_que_ele_chama(self):
        """Um `.bat` que chama opção inexistente falha só na mão de quem usa."""
        script = (ROOT / "deploy" / "publicar.ps1").read_text(encoding="utf-8")
        declaradas = set(re.findall(r"\[switch\]\$(\w+)", script))
        for opcao in ("AoLigar", "NaoAoLigar"):
            with self.subTest(opcao=opcao):
                self.assertIn(opcao, declaradas)


if __name__ == "__main__":
    unittest.main()
