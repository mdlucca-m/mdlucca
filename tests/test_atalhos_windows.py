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

# Estes dois nao passam pelo publicar.ps1: sobem o servidor direto, SEM
# tunel. Existem porque o tunel e a parte que pode falhar (conta do
# ngrok, antivirus, rede da universidade) -- e quando ela falha, a pessoa
# fica sem o sistema por um motivo que nao tem nada a ver com o sistema.
#
# E porque o caminho a mao tem tres armadilhas que ja pegaram todo mundo:
# a janela abre na pasta errada, o endereco 127.0.0.1:8000 vai parar no
# terminal em vez do navegador, e o PowerShell e o Prompt de Comando tem
# sintaxes diferentes para a mesma coisa.
LOCAIS = {
    "Abrir LAPE.bat": 8000,
    "Ver a demonstracao.bat": 8001,
}
TODOS = list(ATALHOS) + list(LOCAIS)


class TestOsAtalhosExistem(unittest.TestCase):

    def test_os_tres_estao_na_raiz(self):
        for nome in TODOS:
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


class TestOsAtalhosLocais(unittest.TestCase):
    """Os dois que sobem o LAPE sem tunel, para duplo clique."""

    def corpo(self, nome: str) -> str:
        return "\n".join(l for l in (ROOT / nome).read_text(encoding="ascii").splitlines()
                         if not l.strip().lower().startswith("rem"))

    def test_os_dois_existem(self):
        for nome in LOCAIS:
            with self.subTest(arquivo=nome):
                self.assertTrue((ROOT / nome).exists(), nome)

    def test_cada_um_abre_o_navegador_na_sua_porta(self):
        """O endereço ir parar no terminal em vez do navegador foi o que
        mais atrapalhou. Aqui quem digita é o arquivo."""
        for nome, porta in LOCAIS.items():
            with self.subTest(arquivo=nome):
                corpo = self.corpo(nome)
                self.assertIn('start "" http://127.0.0.1:%d' % porta, corpo)

    def test_cada_um_sobe_o_servidor_na_mesma_porta_que_abre(self):
        """Abrir o navegador numa porta e servir noutra daria a mesma tela
        de 'recusou a conexão' que a digitação à mão dava."""
        for nome, porta in LOCAIS.items():
            with self.subTest(arquivo=nome):
                corpo = self.corpo(nome)
                self.assertIn("--port %d" % porta, corpo)

    def test_nenhum_dos_dois_mexe_no_tunel(self):
        """São a saída de emergência para quando o túnel falha: depender
        dele aqui anularia a razão de existirem."""
        for nome in LOCAIS:
            with self.subTest(arquivo=nome):
                corpo = self.corpo(nome)
                for proibido in ("ngrok", "publicar.ps1", "-Fixo", "cloudflare"):
                    self.assertNotIn(proibido, corpo)

    def test_a_demonstracao_nunca_toca_o_banco_de_verdade(self):
        """A linha que SERVE precisa apontar para o banco de demonstração.
        Conferir que o nome aparece em algum lugar não basta: ele aparece
        também no `if not exist`, e trocar só a linha do servidor passaria
        despercebido -- com a massa indo para cima dos dados reais."""
        corpo = self.corpo("Ver a demonstracao.bat")
        servir = next(l for l in corpo.splitlines() if "--port" in l)
        self.assertIn("--db data\\demo.sqlite", servir)
        self.assertNotIn("--forcar", corpo)

    def test_o_login_que_cria_e_o_login_que_a_tela_mostra_sao_o_mesmo(self):
        """Se divergirem, a conta existe e a pessoa não entra nela -- e a
        mensagem na tela diz, com todas as letras, uma credencial que não
        funciona."""
        corpo = self.corpo("Ver a demonstracao.bat")
        criacao = next(l for l in corpo.splitlines() if "--acesso" in l)
        mostrado = next(l for l in corpo.splitlines()
                        if l.strip().startswith("echo") and "senha" in l)
        login = criacao.split("--acesso")[1].split()[1]
        senha = criacao.split("--senha")[1].split()[0]
        self.assertIn(login, mostrado)
        self.assertIn(senha, mostrado)

    def test_a_demonstracao_nao_regenera_a_massa_a_cada_clique(self):
        """Regerar apagaria o que a pessoa acabou de experimentar na tela."""
        corpo = self.corpo("Ver a demonstracao.bat")
        self.assertIn('if not exist "data\\demo.sqlite" (', corpo)

    def test_a_senha_da_demonstracao_nao_e_segredo_de_verdade(self):
        """É um banco de dados inventados que só existe nesta máquina. A
        senha está no arquivo de propósito -- guardá-la em outro lugar
        faria a pessoa não conseguir entrar na própria demonstração.

        E não pode ser a de nenhum outro lugar: se alguém reaproveitar
        aqui a senha do sistema de verdade, ela passa a estar escrita, em
        texto puro, num arquivo versionado."""
        corpo = self.corpo("Ver a demonstracao.bat")
        self.assertIn("demo@lape.local", corpo)
        self.assertIn("demo12345", corpo)
        self.assertIn(".local", corpo)     # domínio que não existe na internet


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
        for nome in TODOS:
            with self.subTest(arquivo=nome):
                texto = (ROOT / nome).read_text(encoding="utf-8")
                self.assertNotRegex(texto, r"\b(rd|ak|cr|tn|ep|as|ed)_[A-Za-z0-9]{12,}")
                self.assertNotIn("add-authtoken", texto)


class TestAsTresArmadilhasConhecidas(unittest.TestCase):

    def ler(self, nome: str) -> str:
        return (ROOT / nome).read_text(encoding="utf-8")

    def test_todos_entram_na_pasta_do_proprio_arquivo(self):
        """A janela abre em C:\\Users\\seu-nome, e não na pasta do sistema."""
        for nome in TODOS:
            with self.subTest(arquivo=nome):
                self.assertIn('cd /d "%~dp0"', self.ler(nome))

    def test_quem_chama_o_powershell_libera_a_politica_de_execucao(self):
        """Só os que chamam o publicar.ps1. Os atalhos locais sobem o
        python direto: não há script de PowerShell, e portanto não há
        política a liberar -- exigir a linha deles seria exigir uma
        defesa contra um risco que eles não correm."""
        for nome in ATALHOS:
            with self.subTest(arquivo=nome):
                self.assertIn("-ExecutionPolicy Bypass", self.ler(nome))
        for nome in LOCAIS:
            with self.subTest(arquivo=nome, local=True):
                # sem os `rem`: o comentario EXPLICA a diferenca entre o
                # PowerShell e o Prompt, e citar a palavra num comentario
                # nao e o mesmo que chamar o programa
                corpo = "\n".join(l for l in self.ler(nome).splitlines()
                                  if not l.strip().lower().startswith("rem"))
                self.assertNotIn("powershell", corpo.lower())

    def test_todos_conferem_estar_na_pasta_certa(self):
        """Copiar o arquivo para a área de trabalho, em vez de criar atalho.

        Cada um confere o que ELE precisa: os do túnel precisam da pasta
        `deploy`, os locais precisam do `scripts`. Exigir o mesmo arquivo
        dos dois faria o atalho local reclamar de uma pasta que ele nem
        usa."""
        for nome in ATALHOS:
            with self.subTest(arquivo=nome):
                texto = self.ler(nome)
                self.assertIn('if not exist "deploy\\publicar.ps1"', texto)
                self.assertIn("criar atalho", texto.lower())
        for nome in LOCAIS:
            with self.subTest(arquivo=nome, local=True):
                self.assertIn('if not exist "scripts\\lape_agent.py"', self.ler(nome))

    def test_a_janela_nao_fecha_sozinha_no_fim(self):
        """Sem `pause` NO FIM, o resultado some antes de ser lido.

        Procurar a palavra em qualquer lugar do arquivo nao serve: ha um
        `pause` dentro do bloco que avisa "este arquivo nao esta na pasta
        certa", e ele passava o teste mesmo com o do fim removido.
        """
        for nome in TODOS:
            with self.subTest(arquivo=nome):
                linhas = [l.strip() for l in self.ler(nome).splitlines() if l.strip()]
                self.assertEqual(linhas[-1].lower(), "pause",
                                 "%s não pausa na última linha" % nome)


class TestOFormatoDoArquivo(unittest.TestCase):
    """Um .bat malformado não dá erro: executa a primeira linha e para."""

    def test_a_quebra_de_linha_e_a_do_windows(self):
        for nome in TODOS:
            with self.subTest(arquivo=nome):
                bruto = (ROOT / nome).read_bytes()
                self.assertIn(b"\r\n", bruto, "%s está com quebra de Unix" % nome)
                soltos = re.findall(rb"(?<!\r)\n", bruto)
                self.assertEqual(soltos, [], "%s mistura quebras" % nome)

    def test_nao_ha_acento(self):
        """O cmd.exe não roda em UTF-8: acento vira caractere quebrado, e o
        texto que existe para orientar passa a atrapalhar."""
        for nome in TODOS:
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
