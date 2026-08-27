#!/usr/bin/env python3
"""Testes dos scripts de publicacao (PowerShell e bash).

    python3 -m unittest discover -s tests -v

Nao ha PowerShell nesta maquina, entao aqui nao se executa nada: o que se
checa e a classe de defeito que ja mordeu de verdade e que a leitura do
codigo nao pega sozinha.

O caso que originou este arquivo: PowerShell nao distingue maiusculas em
nome de variavel. O parametro `[switch]$Endereco` e a variavel local
`$endereco`, que guardava o endereco do tunel, eram a MESMA variavel --
e atribuir uma string a um switch e erro terminante. O script morria
depois de subir o servico, com uma mensagem sobre conversao de tipo que
nao tinha relacao aparente com nada.
"""
from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PS1 = ROOT / "deploy" / "publicar.ps1"
SH = ROOT / "deploy" / "publicar.sh"

# Parametro que o corpo pode reatribuir, e por que isso e seguro. Qualquer
# outro nome que apareca aqui e colisao: um local roubando o nome de um
# parametro, com o tipo do parametro valendo sobre ele.
REATRIBUICAO_PERMITIDA = {
    "dominio": "string recebendo string: o script normaliza e grava o que foi digitado",
    "fixo": "switch recebendo $true: o modo gravado em disco reativa a si mesmo",
    "permanente": "switch recebendo $true: idem",
}


class TestColisaoDeNomes(unittest.TestCase):
    def parametros(self) -> set[str]:
        bloco = PS1.read_text(encoding="utf-8").split("param(", 1)[1].split("\n)", 1)[0]
        return {n.lower() for n in re.findall(r"\$(\w+)", bloco)}

    def test_o_bloco_de_parametros_foi_lido(self):
        nomes = self.parametros()
        self.assertIn("porta", nomes)
        self.assertIn("endereco", nomes)

    def test_nenhum_local_rouba_o_nome_de_um_parametro(self):
        texto = PS1.read_text(encoding="utf-8")
        corpo = texto.split("\n)", 1)[1]
        atribuidos = {n.lower() for n in re.findall(r"\$(\w+)\s*=[^=]", corpo)}
        invasores = (self.parametros() & atribuidos) - set(REATRIBUICAO_PERMITIDA)
        self.assertEqual(
            invasores, set(),
            "variavel local com o mesmo nome de um parametro (PowerShell nao"
            f" distingue maiusculas): {sorted(invasores)}")


class TestSintaxeDoPowerShell(unittest.TestCase):
    """Não há PowerShell nesta máquina; o que dá para conferir é o que já quebrou.

    `"$dono:"` não é o que parece: o PowerShell lê `$nome:` como variável
    qualificada por unidade (o irmão de `$env:PATH`) e recusa o ARQUIVO
    INTEIRO na leitura -- nem a primeira linha roda. Um dois-pontos depois de
    uma variável dentro de aspas derruba tudo, e a mensagem de erro fala de
    unidade de disco, que não tem relação aparente com nada.
    """

    ESCOPOS = {"env", "script", "global", "local", "using", "private",
               "variable", "function"}

    def test_variavel_seguida_de_dois_pontos_e_delimitada(self):
        texto = PS1.read_text(encoding="utf-8")
        soltas = []
        for numero, linha in enumerate(texto.split("\n"), 1):
            for achado in re.finditer(r"\$([A-Za-z_]\w*):", linha):
                if achado.group(1).lower() not in self.ESCOPOS:
                    soltas.append(f"linha {numero}: {achado.group(0)}")
        self.assertEqual(soltas, [],
                         "variável seguida de ':' dentro de aspas — use ${nome}: "
                         + "; ".join(soltas))


class TestPidVazio(unittest.TestCase):
    """Um .pid vazio nao pode derrubar a subida.

    Ele aparece sempre que uma tentativa anterior morreu antes de o processo
    nascer -- e o script era chamado justo depois disso, na tentativa
    seguinte, que e quando a pessoa mais precisa que ele funcione.
    """

    def test_o_powershell_confere_o_numero_antes_de_matar(self):
        texto = PS1.read_text(encoding="utf-8")
        trecho = texto.split("function Parar-Tudo", 1)[1].split("\n}", 1)[0]
        self.assertIn("-match", trecho, "Parar-Tudo mata sem conferir se ha numero")
        self.assertIn("Stop-Process", trecho)

    def test_o_bash_confere_o_numero_antes_de_matar(self):
        texto = SH.read_text(encoding="utf-8")
        trecho = texto.split("parar() {", 1)[1].split("\n}", 1)[0]
        self.assertIn("[0-9]+", trecho, "parar() mata sem conferir se ha numero")

    def test_nao_se_grava_pid_de_processo_que_nao_nasceu(self):
        texto = PS1.read_text(encoding="utf-8")
        for alvo in ("$api.Id | Out-File", "$procTunel.Id | Out-File"):
            self.assertIn(alvo, texto)
        # cada gravacao vem precedida da conferencia de que ha processo
        self.assertEqual(texto.count("if (-not $procTunel) { Erro"),
                         texto.count("$procTunel.Id | Out-File"))


class TestBash(unittest.TestCase):
    def test_sintaxe(self):
        pronto = subprocess.run(["bash", "-n", str(SH)], capture_output=True, text=True)
        self.assertEqual(pronto.returncode, 0, pronto.stderr)

    def test_parar_aguenta_pid_vazio(self):
        # o teste roda o script de verdade, com dois .pid vazios plantados
        exec_dir = ROOT / ".lape-run"
        exec_dir.mkdir(exist_ok=True)
        criados = []
        try:
            for nome in ("api", "tunel"):
                alvo = exec_dir / f"{nome}.pid"
                alvo.write_text("", encoding="utf-8")
                criados.append(alvo)
            pronto = subprocess.run(["bash", str(SH), "--parar"],
                                    capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(pronto.returncode, 0, pronto.stderr)
            for alvo in criados:
                self.assertFalse(alvo.exists(), "o .pid vazio deveria ter sido apagado")
        finally:
            for alvo in criados:
                alvo.unlink(missing_ok=True)
            if exec_dir.exists() and not any(exec_dir.iterdir()):
                exec_dir.rmdir()

    def test_a_ajuda_cobre_todas_as_opcoes(self):
        pronto = subprocess.run(["bash", str(SH), "--help"],
                                capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        for opcao in ("--fixo", "--permanente", "--dominio", "--endereco", "--parar"):
            self.assertIn(opcao, pronto.stdout, f"{opcao} nao aparece na ajuda")


class TestOsDoisScriptsOferecemOMesmo(unittest.TestCase):
    """O laboratorio e Windows, mas o servidor do futuro sera Linux.

    Duas maneiras de publicar que divergem em silencio viram, mais adiante,
    uma instrucao no README que so funciona num dos dois.
    """

    def test_mesmos_modos(self):
        ps1 = PS1.read_text(encoding="utf-8")
        sh = SH.read_text(encoding="utf-8")
        for ps, bash in [("$Fixo", "--fixo"), ("$Permanente", "--permanente"),
                         ("$Dominio", "--dominio"), ("$Endereco", "--endereco"),
                         ("$Parar", "--parar")]:
            self.assertIn(ps, ps1, f"{ps} sumiu do publicar.ps1")
            self.assertIn(bash, sh, f"{bash} sumiu do publicar.sh")

    def test_os_dois_gravam_o_endereco_no_mesmo_lugar(self):
        # e o que faz `-Endereco` responder depois de uma subida escondida
        self.assertIn("endereco.txt", PS1.read_text(encoding="utf-8"))
        self.assertIn("endereco.txt", SH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
