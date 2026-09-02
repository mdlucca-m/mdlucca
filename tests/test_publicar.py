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
import tempfile
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
        for opcao in ("--fixo", "--permanente", "--dominio", "--endereco", "--parar",
                      "--versao"):
            self.assertIn(opcao, pronto.stdout, f"{opcao} nao aparece na ajuda")


def _funcao_do_bash(nome: str) -> str:
    """Recorta uma funcao do publicar.sh para roda-la sozinha.

    Rodar o script inteiro subiria servico e tunel; o que interessa aqui e
    uma funcao so, com as cores e os caminhos trocados por dubles.
    """
    texto = SH.read_text(encoding="utf-8")
    inicio = texto.index(f"{nome}() {{")
    fim = texto.index("\n}\n", inicio) + 3
    return texto[inicio:fim]


def _constante_do_bash(nome: str) -> str:
    """A linha que declara uma constante, para o dublê usar a de verdade.

    Copiar o valor para dentro do teste faria o teste passar com a regra
    errada no script -- que é exatamente o defeito que ele deveria pegar.
    """
    for linha in SH.read_text(encoding="utf-8").splitlines():
        if linha.startswith(f"{nome}="):
            return linha + "\n"
    raise AssertionError(f"constante {nome} sumiu do publicar.sh")


class TestAtualizacaoSozinha(unittest.TestCase):
    """O `git pull` que ninguem precisa lembrar de rodar.

    Atualizar sozinho e conveniencia, e conveniencia nao pode custar o ar do
    laboratorio. Entao cada teste aqui e uma maneira de a atualizacao dar
    errado -- e a checagem de que o servico subiria assim mesmo.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.origem = self.base / "origem"
        self.copia = self.base / "copia"
        self.git("init", "--initial-branch=main", str(self.origem), cwd=self.base)
        (self.origem / "a.txt").write_text("primeira versao\n", encoding="utf-8")
        self.git("add", "-A", cwd=self.origem)
        self.commit("primeiro", cwd=self.origem)
        self.git("clone", str(self.origem), str(self.copia), cwd=self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args, cwd):
        return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                              text=True, check=True)

    def commit(self, mensagem, cwd):
        return self.git("-c", "user.email=teste@lape", "-c", "user.name=Teste",
                        "commit", "-m", mensagem, cwd=cwd)

    def relatorio_versionado(self):
        """docs/ rastreado nos dois lados -- como está no repositório real."""
        (self.origem / "docs").mkdir(exist_ok=True)
        (self.origem / "docs" / "index.html").write_text("relatório\n", encoding="utf-8")
        self.git("add", "-A", cwd=self.origem)
        self.commit("relatório inicial", cwd=self.origem)
        self.git("pull", cwd=self.copia)

    def novidade_no_servidor(self, texto="segunda versao\n"):
        (self.origem / "a.txt").write_text(texto, encoding="utf-8")
        self.git("add", "-A", cwd=self.origem)
        self.commit("segundo", cwd=self.origem)

    def rodar(self, raiz=None, ambiente=""):
        raiz = raiz or self.copia
        exec_dir = self.base / "run"
        exec_dir.mkdir(exist_ok=True)
        script = (
            "set -u\n"
            "azul(){ printf '%s\\n' \"$*\"; }\n"
            "verde(){ printf '%s\\n' \"$*\"; }\n"
            "aviso(){ printf '! %s\\n' \"$*\"; }\n"
            f'RAIZ="{raiz}"\n'
            f'EXEC="{exec_dir}"\n'
            f"{ambiente}\n"
            + _constante_do_bash("GERADOS")
            + _funcao_do_bash("atualizar_codigo")
            + "\natualizar_codigo\n"
        )
        return subprocess.run(["bash", "-c", script], capture_output=True, text=True)

    def conteudo(self):
        return (self.copia / "a.txt").read_text(encoding="utf-8")

    def test_puxa_o_que_esta_no_servidor(self):
        self.novidade_no_servidor()
        pronto = self.rodar()
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertIn("atualizado", pronto.stdout.lower())
        self.assertEqual(self.conteudo(), "segunda versao\n")

    def test_sem_novidade_nao_finge_que_houve(self):
        pronto = self.rodar()
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertIn("já estava atualizado", pronto.stdout)

    def test_alteracao_local_nao_e_atropelada(self):
        # o dia em que alguem editar um arquivo na maquina do laboratorio,
        # o script nao pode apagar o trabalho para subir a versao do servidor
        self.novidade_no_servidor()
        (self.copia / "a.txt").write_text("mexido a mao\n", encoding="utf-8")
        pronto = self.rodar()
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertIn("não vou sobrescrever", pronto.stdout)
        self.assertEqual(self.conteudo(), "mexido a mao\n")

    def test_lixo_solto_na_raiz_nao_desliga_a_atualizacao(self):
        """Arquivo nao rastreado nao e trabalho a proteger.

        Aconteceu na maquina do laboratorio: comandos de PowerShell digitados
        num prompt de cmd deixaram arquivos vazios chamados "powershell" e
        "Set-ExecutionPolicy" na raiz do repositorio. A partir dali toda
        subida dizia "ha alteracoes locais no codigo: nao vou sobrescrever" --
        e nao havia alteracao nenhuma no codigo. A maquina parou de se
        atualizar em silencio, e ninguem tinha como ligar uma coisa a outra.
        """
        self.novidade_no_servidor()
        for lixo in ("powershell", "Set-ExecutionPolicy", "Subir LAPE.bat"):
            (self.copia / lixo).write_text("", encoding="utf-8")
        pronto = self.rodar()
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertNotIn("não vou sobrescrever", pronto.stdout)
        self.assertEqual(self.conteudo(), "segunda versao\n")
        # e o lixo continua onde estava: o script nao apaga nada de ninguem
        self.assertTrue((self.copia / "powershell").exists())

    def test_arquivo_rastreado_e_lixo_solto_juntos_ainda_travam(self):
        # ignorar o nao rastreado nao pode fazer o script atropelar edicao
        # de verdade que esteja no mesmo diretorio
        self.novidade_no_servidor()
        (self.copia / "a.txt").write_text("mexido a mao\n", encoding="utf-8")
        (self.copia / "powershell").write_text("", encoding="utf-8")
        pronto = self.rodar()
        self.assertIn("não vou sobrescrever", pronto.stdout)
        self.assertEqual(self.conteudo(), "mexido a mao\n")

    def test_o_banco_vivo_nao_conta_como_alteracao_local(self):
        """O banco muda a cada cadastro. Se contasse, nunca haveria atualização.

        Foi o defeito que quase matou esta funcionalidade no nascimento:
        `data/db.sqlite` é versionado, e na máquina do laboratório está
        modificado o tempo todo -- a atualização automática ficaria
        permanentemente desligada, em silêncio, exatamente onde precisa
        funcionar.
        """
        (self.origem / "data").mkdir()
        (self.origem / "data" / "db.sqlite").write_text("banco\n", encoding="utf-8")
        self.git("add", "-A", cwd=self.origem)
        self.commit("banco", cwd=self.origem)
        self.git("pull", "--ff-only", cwd=self.copia)
        self.novidade_no_servidor()
        # o laboratório cadastrou alguma coisa: o banco local mudou
        (self.copia / "data" / "db.sqlite").write_text("banco com cadastro novo\n",
                                                       encoding="utf-8")
        pronto = self.rodar()
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertIn("atualizado", pronto.stdout.lower())
        self.assertEqual(self.conteudo(), "segunda versao\n")          # código veio
        self.assertEqual((self.copia / "data" / "db.sqlite").read_text(encoding="utf-8"),
                         "banco com cadastro novo\n")                  # banco intacto

    def test_o_relatorio_gerado_nao_conta_como_alteracao_local(self):
        # o defeito que este teste guarda: docs/index.html e docs/index.json
        # são reescritos pelo PRÓPRIO sistema a cada subida. Contá-los como
        # "alteração local" desligava a atualização para sempre justamente
        # na máquina do laboratório -- e foi o que aconteceu
        self.relatorio_versionado()
        self.novidade_no_servidor()
        (self.copia / "docs" / "index.html").write_text("relatório de hoje\n",
                                                        encoding="utf-8")
        pronto = self.rodar()
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertNotIn("alterações locais", pronto.stdout)
        self.assertEqual(self.conteudo(), "segunda versao\n")

    def test_o_relatorio_travando_o_pull_e_refeito(self):
        # quando a mudança do servidor toca docs/, o git recusa por causa
        # do relatório local. Restaurá-lo é seguro: a próxima subida o
        # reescreve. O banco em data/ nunca entra nessa restauração
        self.relatorio_versionado()
        (self.origem / "docs" / "index.html").write_text("relatório novo\n",
                                                         encoding="utf-8")
        (self.origem / "a.txt").write_text("segunda versao\n", encoding="utf-8")
        self.git("add", "-A", cwd=self.origem)
        self.commit("mexe no relatório também", cwd=self.origem)
        (self.copia / "docs" / "index.html").write_text("gerado agora\n", encoding="utf-8")
        pronto = self.rodar()
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertEqual(self.conteudo(), "segunda versao\n")

    def test_o_banco_nunca_e_restaurado_para_destravar(self):
        # restaurar data/ -- ou a raiz inteira, que dá no mesmo -- apagaria
        # os cadastros do laboratório. O script pode desistir da
        # atualização; do banco, nunca. Só linhas que EXECUTAM contam:
        # avisar contra o comando perigoso é o oposto de fazê-lo.
        for arquivo in (PS1, SH):
            texto = arquivo.read_text(encoding="utf-8")
            executadas = [
                linha.strip() for linha in texto.splitlines()
                if "checkout --" in linha
                and not linha.strip().startswith(("#", "//"))
                and "echo" not in linha and "Write-Host" not in linha
            ]
            with self.subTest(arquivo=arquivo.name):
                self.assertTrue(executadas, "o destravamento sumiu do script")
                for linha in executadas:
                    self.assertIn("checkout -- docs", linha,
                                  f"restauração perigosa: {linha}")

    def test_em_outro_ramo_nao_mexe(self):
        self.git("checkout", "-b", "experimento", cwd=self.copia)
        self.novidade_no_servidor()
        pronto = self.rodar()
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertIn("experimento", pronto.stdout)
        self.assertEqual(self.conteudo(), "primeira versao\n")

    def test_pasta_sem_git_passa_batido(self):
        solta = self.base / "sem-git"
        solta.mkdir()
        pronto = self.rodar(raiz=solta)
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertEqual(pronto.stdout.strip(), "")

    def test_dispensa_pedida_e_respeitada(self):
        self.novidade_no_servidor()
        pronto = self.rodar(ambiente="SEM_ATUALIZAR=1")
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertIn("dispensada", pronto.stdout)
        self.assertEqual(self.conteudo(), "primeira versao\n")

    def test_servidor_inalcancavel_nao_derruba_a_subida(self):
        # sem internet o pull falha; o servico tem de subir do mesmo jeito
        self.git("remote", "set-url", "origin",
                 str(self.base / "nao-existe"), cwd=self.copia)
        pronto = self.rodar()
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertIn("seguindo com o código atual", pronto.stdout)

    def test_os_dois_scripts_tem_as_mesmas_travas(self):
        ps1 = PS1.read_text(encoding="utf-8")
        sh = SH.read_text(encoding="utf-8")
        for trecho in ("--ff-only", "status --porcelain", "rev-parse --abbrev-ref HEAD"):
            self.assertIn(trecho, ps1, f"trava ausente no publicar.ps1: {trecho}")
            self.assertIn(trecho, sh, f"trava ausente no publicar.sh: {trecho}")


class TestRelatorioDeVersao(unittest.TestCase):
    """`--versao` responde "atualizou?" sem ninguem precisar ler git.

    A resposta util nao e o commit: e o numero de mudancas esperando e o
    motivo de nao terem entrado. Sem o motivo, quem esta no laboratorio
    so sabe que nao atualizou -- que e onde a conversa ja estava.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.origem = self.base / "origem"
        self.copia = self.base / "copia"
        self.git("init", "--initial-branch=main", str(self.origem), cwd=self.base)
        (self.origem / "a.txt").write_text("um\n", encoding="utf-8")
        self.git("add", "-A", cwd=self.origem)
        self.commit("primeiro", cwd=self.origem)
        self.git("clone", str(self.origem), str(self.copia), cwd=self.base)

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args, cwd):
        return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                              text=True, check=True)

    def commit(self, mensagem, cwd):
        return self.git("-c", "user.email=teste@lape", "-c", "user.name=Teste",
                        "commit", "-m", mensagem, cwd=cwd)

    def novidade_no_servidor(self):
        (self.origem / "a.txt").write_text("dois\n", encoding="utf-8")
        self.git("add", "-A", cwd=self.origem)
        self.commit("segundo", cwd=self.origem)

    def rodar(self):
        script = (
            "set -u\n"
            "azul(){ printf '%s\\n' \"$*\"; }\n"
            "verde(){ printf '%s\\n' \"$*\"; }\n"
            "aviso(){ printf '! %s\\n' \"$*\"; }\n"
            f'RAIZ="{self.copia}"\n'
            + _constante_do_bash("GERADOS")
            + _funcao_do_bash("mostrar_versao")
            + "\nmostrar_versao\n"
        )
        return subprocess.run(["bash", "-c", script], capture_output=True, text=True)

    def test_em_dia_diz_que_esta_em_dia(self):
        pronto = self.rodar()
        self.assertEqual(pronto.returncode, 0, pronto.stderr)
        self.assertIn("versão mais nova", pronto.stdout)

    def test_atrasada_diz_quantas_esperam(self):
        self.novidade_no_servidor()
        pronto = self.rodar()
        self.assertIn("1 mudança(s) esperando", pronto.stdout)

    def test_diz_que_o_ramo_e_o_impedimento(self):
        self.novidade_no_servidor()
        self.git("checkout", "-b", "experimento", cwd=self.copia)
        self.git("branch", "--set-upstream-to=origin/main", cwd=self.copia)
        self.assertIn("ramo", self.rodar().stdout)

    def test_diz_que_a_alteracao_local_e_o_impedimento(self):
        self.novidade_no_servidor()
        (self.copia / "a.txt").write_text("mexido a mao\n", encoding="utf-8")
        saida = self.rodar().stdout
        self.assertIn("alteração local", saida)
        self.assertIn("a.txt", saida, "nao mostrou qual arquivo esta segurando")

    def test_nada_impede_manda_rodar_de_novo(self):
        self.novidade_no_servidor()
        saida = self.rodar().stdout
        self.assertIn("nada impede", saida)
        self.assertIn("publicar.sh", saida)


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
                         ("$Parar", "--parar"), ("$Versao", "--versao")]:
            self.assertIn(ps, ps1, f"{ps} sumiu do publicar.ps1")
            self.assertIn(bash, sh, f"{bash} sumiu do publicar.sh")

    def test_os_dois_gravam_o_endereco_no_mesmo_lugar(self):
        # e o que faz `-Endereco` responder depois de uma subida escondida
        self.assertIn("endereco.txt", PS1.read_text(encoding="utf-8"))
        self.assertIn("endereco.txt", SH.read_text(encoding="utf-8"))


class TestOsArquivosDeTeste(unittest.TestCase):
    """Nome de arquivo de teste é chave: repetir um apaga o outro.

    Aconteceu ao escrever um teste novo de extração: já havia um
    `test_extracao.py` (formatos de exportação), e o arquivo novo o
    substituiu inteiro. Nada acusou — a suíte seguiu verde, com 24 testes
    a menos.
    """

    def test_todo_teste_tem_a_sua_classe_e_nenhuma_se_repete(self):
        import ast
        from collections import defaultdict

        onde = defaultdict(list)
        for arquivo in sorted((ROOT / "tests").glob("test_*.py")):
            arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
            for no in arvore.body:
                if isinstance(no, ast.ClassDef):
                    onde[no.name].append(arquivo.name)
        # classes de teste com o mesmo nome em arquivos diferentes não são
        # erro, mas tornam o relatório ambíguo -- e escondem perda como a
        # que motivou este teste
        repetidas = {nome: arqs for nome, arqs in onde.items() if len(arqs) > 1}
        self.assertEqual(repetidas, {}, f"classe de teste repetida: {repetidas}")

    # Dívida conhecida, e declarada aqui de propósito: enquanto o nome
    # estiver nesta lista, o módulo não tem teste nenhum. A lista existe
    # para que a dívida seja visível e para que um módulo NOVO não entre
    # sem teste — não para dar a entender que está tudo coberto.
    SEM_TESTE_AINDA = {
        "config",             # só caminhos e constantes lidos do ambiente
        "ingest_citations",   # falta: bate no OpenAlex/Crossref, precisa de dublê
    }

    def test_todo_modulo_novo_chega_com_teste(self):
        modulos = {caminho.stem for caminho in (ROOT / "scripts" / "lape").glob("*.py")
                   if caminho.stem != "__init__"}
        texto = "\n".join(arquivo.read_text(encoding="utf-8")
                          for arquivo in (ROOT / "tests").glob("test_*.py"))
        sem_teste = sorted(m for m in modulos
                           if m not in texto and m not in self.SEM_TESTE_AINDA)
        self.assertEqual(sem_teste, [], f"módulo sem nenhum teste: {sem_teste}")

    def test_a_lista_de_divida_nao_guarda_nome_que_ja_tem_teste(self):
        # dívida quitada tem de sair da lista, senão ela vira decoração
        texto = "\n".join(arquivo.read_text(encoding="utf-8")
                          for arquivo in (ROOT / "tests").glob("test_*.py"))
        for nome in self.SEM_TESTE_AINDA:
            with self.subTest(modulo=nome):
                self.assertNotIn(f"lape import {nome}", texto)


class TestSubirComOWindows(unittest.TestCase):
    """`-AoLigar` num computador de universidade.

    Tres defeitos moravam aqui, e os dois primeiros so apareceram quando
    alguem sem direito de administrador tentou usar a opcao:

      1. o comentario prometia "nao pede administrador" e o codigo pedia:
         sem `-Principal`, o Windows le a tarefa como sendo para qualquer
         usuario, e devolve "Acesso negado";
      2. dentro de uma funcao, `$MyInvocation.MyCommand.Path` e o da
         FUNCAO e vem vazio -- a tarefa saia registrada com `-File ""`;
      3. desligar tirava a tarefa e deixava o atalho de inicializacao, e o
         sistema continuava subindo sozinho sem nada para desligar.
    """

    def ps1(self):
        return PS1.read_text(encoding="utf-8")

    def agendar(self):
        texto = self.ps1()
        return texto[texto.index("function Agendar"):texto.index("\nif ($AoLigar)")]

    def test_a_tarefa_declara_para_quem_e(self):
        corpo = self.agendar()
        self.assertIn("New-ScheduledTaskPrincipal", corpo)
        self.assertIn("-Principal $quem", corpo)
        self.assertIn("-RunLevel Limited", corpo)
        self.assertIn("-AtLogOn -User $eu", corpo)

    def test_o_caminho_do_script_nao_vem_de_dentro_da_funcao(self):
        corpo = self.agendar()
        self.assertIn("$script = $PSCommandPath", corpo)
        self.assertNotIn("$MyInvocation.MyCommand.Path", corpo)

    def test_ha_plano_b_para_quem_nao_e_administrador(self):
        # num computador de universidade, quase ninguem e
        corpo = self.agendar()
        self.assertIn("catch {", corpo)
        self.assertIn("Caminho-Inicializar", corpo)
        self.assertIn("Startup", self.ps1())

    def test_desligar_desliga_os_dois_caminhos(self):
        texto = self.ps1()
        corpo = texto[texto.index("if ($NaoAoLigar)"):]
        corpo = corpo[:corpo.index("exit 0")]
        self.assertIn("Unregister-ScheduledTask", corpo)
        self.assertIn("Remove-Item (Caminho-Inicializar)", corpo)

    def test_a_dica_some_pelos_dois_caminhos(self):
        # olhar so a tarefa fazia a dica reaparecer todo dia para quem
        # tinha caido no plano B
        texto = self.ps1()
        corpo = texto[texto.index("Para subir sozinho toda vez") - 400:]
        corpo = corpo[:corpo.index("Para subir sozinho toda vez") + 80]
        self.assertIn("Get-ScheduledTask", corpo)
        self.assertIn("Test-Path (Caminho-Inicializar)", corpo)

if __name__ == "__main__":
    unittest.main(verbosity=2)
