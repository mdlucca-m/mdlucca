#!/usr/bin/env python3
"""O banco do laboratorio nao vai para o repositorio publico.

    python3 -m unittest tests.test_banco_protegido -v

O `data/db.sqlite` esta versionado desde o primeiro commit. A copia que
esta la e de 19 artigos e 17 primeiros nomes, sem login e sem senha --
conferidas as dez versoes do historico. O risco nao e ela: e a PROXIMA.
Um `git add -A` na maquina do laboratorio empurraria o banco vivo, com os
hashes de senha de quem tem conta, para um repositorio publico -- e
commit apagado continua no historico.

Tirar o arquivo do Git nao serve, e o primeiro teste desta casa a provar
isso: o commit que o remove faz o `git pull` da maquina do laboratorio
ABORTAR, porque o banco de la esta modificado e o merge quereria apaga-lo.
O "Abrir LAPE" passaria a dizer "nao deu para atualizar agora" em toda
subida, para sempre, e ninguem entenderia por que.

Entao esconde em vez de tirar, e os testes guardam as duas pontas: o git
para de ver o banco, E a atualizacao continua funcionando.
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import banco_protegido as bp  # noqa: E402


def git(raiz, *args, esperar=True):
    r = subprocess.run(["git", *args], cwd=str(raiz), text=True, capture_output=True)
    if esperar and r.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} falhou: {r.stderr}")
    return r


def banco(caminho: Path, *, com_segredo: bool) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if caminho.exists():
        caminho.unlink()
    con = sqlite3.connect(caminho)
    con.execute("CREATE TABLE members (id INTEGER PRIMARY KEY, full_name TEXT,"
                " login TEXT, password_hash TEXT, email TEXT, phone TEXT)")
    if com_segredo:
        con.execute("INSERT INTO members (full_name, login, password_hash)"
                    " VALUES ('Alguem', 'alguem@udesc.br', 'pbkdf2$muito$longo')")
    else:
        con.execute("INSERT INTO members (full_name) VALUES ('Alguem')")
    con.commit()
    con.close()


class BaseDoRepositorio(unittest.TestCase):
    """Um repositorio de verdade, com remoto de verdade.

    Com um repositorio de mentira nao ha `git pull` para conferir -- e e
    o `git pull` que este modulo existe para nao quebrar.
    """

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.casa = Path(tmp.name)
        self.remoto = self.casa / "remoto.git"
        git(self.casa, "init", "-q", "--bare", str(self.remoto))
        git(self.casa, "--git-dir", str(self.remoto), "symbolic-ref",
            "HEAD", "refs/heads/main")

        self.autor = self.casa / "autor"
        git(self.casa, "clone", "-q", str(self.remoto), str(self.autor))
        for chave, valor in (("user.email", "t@t"), ("user.name", "T"),
                             ("commit.gpgsign", "false")):
            git(self.autor, "config", chave, valor)
        git(self.autor, "checkout", "-q", "-b", "main")
        # o repositorio precisa do lape_agent.py no lugar: o gancho o chama
        (self.autor / "scripts").mkdir(parents=True, exist_ok=True)
        (self.autor / "scripts" / "lape_agent.py").write_text(
            "raise SystemExit(0)\n", encoding="utf-8")
        banco(self.autor / "data" / "db.sqlite", com_segredo=False)
        (self.autor / "codigo.py").write_text("x = 1\n", encoding="utf-8")
        git(self.autor, "add", "-A")
        git(self.autor, "commit", "-qm", "inicio")
        git(self.autor, "push", "-q", "-u", "origin", "main")

    def clonar_a_maquina_do_laboratorio(self) -> Path:
        """Um clone com o banco VIVO no lugar -- modificado, nunca comitado."""
        lab = self.casa / "lab"
        git(self.casa, "clone", "-q", str(self.remoto), str(lab))
        for chave, valor in (("user.email", "l@l"), ("user.name", "L")):
            git(lab, "config", chave, valor)
        banco(lab / "data" / "db.sqlite", com_segredo=True)
        return lab

    def commit_de_codigo_no_remoto(self, texto="y = 2\n"):
        (self.autor / "codigo.py").write_text(texto, encoding="utf-8")
        git(self.autor, "commit", "-qam", "mudou o codigo")
        git(self.autor, "push", "-q", "origin", "main")


class TestPorQueNaoDaParaTirarDoGit(BaseDoRepositorio):
    """A alternativa obvia, e a medicao que a descarta.

    Este teste guarda um NAO: "tira o banco do Git" e a primeira ideia de
    qualquer pessoa, inclusive minha, e ela quebra a atualizacao da
    maquina do laboratorio. Sem o teste, alguem tenta de novo em seis
    meses -- e descobre pelo laboratorio parado.
    """

    def test_um_commit_que_remove_o_banco_aborta_o_pull_do_laboratorio(self):
        lab = self.clonar_a_maquina_do_laboratorio()
        # o autor tira o banco do versionamento e empurra
        git(self.autor, "rm", "-q", "--cached", "data/db.sqlite")
        (self.autor / ".gitignore").write_text("data/db.sqlite\n", encoding="utf-8")
        git(self.autor, "add", ".gitignore")
        git(self.autor, "commit", "-qm", "para de versionar o banco")
        git(self.autor, "push", "-q", "origin", "main")

        r = git(lab, "pull", "--ff-only", esperar=False)
        self.assertNotEqual(r.returncode, 0,
                            "o pull deveria abortar -- se passou, reveja a decisão")
        self.assertIn("db.sqlite", r.stdout + r.stderr)
        # e o banco vivo continua la, intacto: o pull aborta, nao apaga
        self.assertTrue(bp.tem_dados_de_pessoas(lab / "data" / "db.sqlite"))


class TestAsDuasTravas(BaseDoRepositorio):

    def test_liga_as_duas_e_diz_o_que_fez(self):
        lab = self.clonar_a_maquina_do_laboratorio()
        feito = bp.proteger(lab)
        self.assertEqual(feito["skip_worktree"], "ligado")
        self.assertEqual(feito["gancho"], "instalado")
        self.assertTrue((lab / ".git" / "hooks" / "pre-commit").exists())

    def test_rodar_duas_vezes_nao_faz_nada_diferente(self):
        """O lancador roda isto em TODA subida."""
        lab = self.clonar_a_maquina_do_laboratorio()
        bp.proteger(lab)
        feito = bp.proteger(lab)
        self.assertEqual(feito["skip_worktree"], "ja estava")
        self.assertEqual(feito["gancho"], "ja estava")

    def test_o_git_para_de_ver_o_banco_vivo(self):
        lab = self.clonar_a_maquina_do_laboratorio()
        self.assertIn("db.sqlite", git(lab, "status", "--short").stdout)
        bp.proteger(lab)
        self.assertNotIn("db.sqlite", git(lab, "status", "--short").stdout)

    def test_git_add_tudo_nao_pega_mais_o_banco(self):
        """É o comando que causaria o vazamento, e o que todo mundo digita."""
        lab = self.clonar_a_maquina_do_laboratorio()
        bp.proteger(lab)
        (lab / "codigo.py").write_text("z = 3\n", encoding="utf-8")
        git(lab, "add", "-A")
        em_fila = git(lab, "diff", "--cached", "--name-only").stdout.split()
        self.assertIn("codigo.py", em_fila)
        self.assertNotIn("data/db.sqlite", em_fila)

    def test_a_atualizacao_continua_funcionando(self):
        """A outra ponta -- e a que a alternativa descartada quebrava."""
        lab = self.clonar_a_maquina_do_laboratorio()
        bp.proteger(lab)
        self.commit_de_codigo_no_remoto("y = 2\n")
        r = git(lab, "pull", "--ff-only", esperar=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((lab / "codigo.py").read_text(encoding="utf-8"), "y = 2\n")
        # e o banco vivo nao foi tocado
        self.assertTrue(bp.tem_dados_de_pessoas(lab / "data" / "db.sqlite"))

    def test_nao_atropela_um_gancho_de_outra_pessoa(self):
        lab = self.clonar_a_maquina_do_laboratorio()
        alvo = lab / ".git" / "hooks" / "pre-commit"
        alvo.write_text("#!/bin/sh\necho gancho de outra pessoa\n", encoding="utf-8")
        feito = bp.proteger(lab)
        self.assertIn("nao foi trocado", feito["gancho"])
        self.assertIn("outra pessoa", alvo.read_text(encoding="utf-8"))
        # a primeira trava vale mesmo sem a segunda
        self.assertEqual(feito["skip_worktree"], "ligado")

    def test_pasta_que_nao_e_repositorio_nao_estoura(self):
        fora = self.casa / "fora"
        fora.mkdir()
        feito = bp.proteger(fora)
        self.assertIn("repositorio", feito["porque"])


class TestOGanchoDePreCommit(BaseDoRepositorio):
    """A trava para quando a primeira for desfeita.

    `git add -f`, um clone novo, uma ferramenta grafica que mexe no index
    -- todas passam por cima do skip-worktree. O gancho olha o que esta
    EM FILA, que e o que iria para o historico.
    """

    def test_recusa_o_banco_com_login_e_senha(self):
        lab = self.clonar_a_maquina_do_laboratorio()
        git(lab, "add", "-f", "data/db.sqlite")
        codigo, recado = bp.conferir_o_que_vai_no_commit(lab)
        self.assertEqual(codigo, 1)
        self.assertIn("login", recado)
        self.assertIn("password_hash", recado)
        self.assertIn("git restore --staged", recado)

    def test_deixa_passar_o_banco_sem_ninguem_dentro(self):
        """Um banco de exemplo, sem pessoa nenhuma, nao e vazamento."""
        lab = self.clonar_a_maquina_do_laboratorio()
        banco(lab / "data" / "db.sqlite", com_segredo=False)
        git(lab, "add", "-f", "data/db.sqlite")
        codigo, recado = bp.conferir_o_que_vai_no_commit(lab)
        self.assertEqual(codigo, 0)
        self.assertEqual(recado, "")

    def test_commit_que_nao_mexe_no_banco_passa_reto(self):
        lab = self.clonar_a_maquina_do_laboratorio()
        (lab / "codigo.py").write_text("z = 3\n", encoding="utf-8")
        git(lab, "add", "codigo.py")
        self.assertEqual(bp.conferir_o_que_vai_no_commit(lab)[0], 0)

    def test_confere_o_que_esta_em_fila_e_nao_o_que_esta_em_disco(self):
        """São coisas diferentes, e o historico recebe o que esta em fila."""
        lab = self.clonar_a_maquina_do_laboratorio()
        git(lab, "add", "-f", "data/db.sqlite")
        # depois do `add`, o arquivo em disco fica limpo -- mas a fila nao
        banco(lab / "data" / "db.sqlite", com_segredo=False)
        self.assertEqual(bp.conferir_o_que_vai_no_commit(lab)[0], 1)

    def test_o_gancho_instalado_barra_o_commit_de_verdade(self):
        """Fim a fim: o gancho no lugar, rodado pelo proprio git.

        Testar so a funcao deixaria passar um gancho que nao executa --
        caminho errado, sem permissao, shebang quebrado.
        """
        lab = self.clonar_a_maquina_do_laboratorio()
        # o lape_agent.py do clone precisa ser o de verdade para o gancho
        # ter o que chamar
        (lab / "scripts" / "lape_agent.py").write_text(
            "import sys\n"
            "from pathlib import Path\n"
            f"sys.path.insert(0, {str(ROOT / 'scripts')!r})\n"
            "from lape import banco_protegido as bp\n"
            "codigo, recado = bp.conferir_o_que_vai_no_commit(\n"
            "    Path(__file__).resolve().parents[1])\n"
            "print(recado)\n"
            "raise SystemExit(codigo)\n", encoding="utf-8")
        # a fila vem ANTES de proteger: com skip-worktree ligado o proprio
        # `git add -f` ja e recusado (ver o teste a seguir), e aqui o que
        # se quer exercitar e o gancho
        git(lab, "add", "-f", "data/db.sqlite")
        bp.proteger(lab)
        r = git(lab, "commit", "-m", "levando o banco sem querer", esperar=False)
        self.assertNotEqual(r.returncode, 0, "o gancho deveria ter barrado")
        self.assertIn("RECUSADO", r.stdout + r.stderr)

    def test_com_a_trava_ligada_nem_o_add_forcado_passa(self):
        """Achado ao escrever os testes, e melhor do que eu esperava.

        Com skip-worktree ligado, o `git add -f` recusa com a mensagem de
        sparse-checkout em vez de colocar o arquivo na fila. Fica escrito
        porque e comportamento do git que este modulo passou a depender:
        se uma versao futura afrouxar isso, o gancho e quem segura.
        """
        lab = self.clonar_a_maquina_do_laboratorio()
        bp.proteger(lab)
        r = git(lab, "add", "-f", "data/db.sqlite", esperar=False)
        em_fila = git(lab, "diff", "--cached", "--name-only").stdout.split()
        self.assertNotIn("data/db.sqlite", em_fila,
                         f"o add -f colocou o banco na fila (saida: {r.stderr})")

    def test_o_recado_ensina_a_sair_da_frente_e_a_resolver(self):
        """Escape hatch documentado e melhor do que um descoberto com raiva.

        E o recado tem de ensinar as DUAS coisas: como tirar o banco da
        fila agora, e como nunca mais precisar disto. Um "recusado" seco
        faz a pessoa procurar como desligar a trava.
        """
        lab = self.clonar_a_maquina_do_laboratorio()
        git(lab, "add", "-f", "data/db.sqlite")
        _, recado = bp.conferir_o_que_vai_no_commit(lab)
        self.assertIn("--no-verify", recado)
        self.assertIn("lape_agent.py proteger", recado)


class TestOQueContaComoSegredo(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.casa = Path(tmp.name)

    def test_login_senha_email_e_telefone_contam(self):
        self.assertEqual(
            bp.CAMPOS_DE_SEGREDO, ("login", "password_hash", "email", "phone"))

    def test_cada_campo_sozinho_ja_barra(self):
        for campo in bp.CAMPOS_DE_SEGREDO:
            with self.subTest(campo=campo):
                caminho = self.casa / f"{campo}.sqlite"
                con = sqlite3.connect(caminho)
                con.execute("CREATE TABLE members (id INTEGER PRIMARY KEY,"
                            " login TEXT, password_hash TEXT, email TEXT,"
                            " phone TEXT)")
                con.execute(f"INSERT INTO members ({campo}) VALUES ('x')")
                con.commit()
                con.close()
                self.assertTrue(bp.tem_dados_de_pessoas(caminho))

    def test_campo_vazio_nao_e_segredo(self):
        """String vazia nao e dado -- e coluna que ninguem preencheu."""
        caminho = self.casa / "vazio.sqlite"
        con = sqlite3.connect(caminho)
        con.execute("CREATE TABLE members (id INTEGER PRIMARY KEY, login TEXT)")
        con.execute("INSERT INTO members (login) VALUES ('')")
        con.execute("INSERT INTO members (login) VALUES (NULL)")
        con.commit()
        con.close()
        self.assertEqual(bp.tem_dados_de_pessoas(caminho), [])

    def test_arquivo_que_nao_existe_ou_nao_e_sqlite(self):
        self.assertEqual(bp.tem_dados_de_pessoas(self.casa / "nao-existe"), [])
        qualquer = self.casa / "qualquer.sqlite"
        qualquer.write_bytes(b"isto nao e um banco")
        self.assertEqual(bp.tem_dados_de_pessoas(qualquer), [])
        # e nao cria arquivo ao perguntar: abrir sqlite para escrita criaria
        self.assertFalse((self.casa / "nao-existe").exists())

    def test_banco_sem_a_tabela_de_pessoas(self):
        caminho = self.casa / "outro.sqlite"
        con = sqlite3.connect(caminho)
        con.execute("CREATE TABLE articles (id INTEGER PRIMARY KEY)")
        con.commit()
        con.close()
        self.assertEqual(bp.tem_dados_de_pessoas(caminho), [])


class TestAQueEstaNoGitHoje(unittest.TestCase):
    """A copia publicada, conferida -- e nao suposta.

    Este teste e o que autoriza a frase "o que esta no Git nao tem login
    nem senha". Sem ele a frase e memoria minha, e memoria envelhece.
    """

    def test_o_banco_versionado_nao_tem_dado_de_pessoa(self):
        achados = bp.tem_dados_de_pessoas(ROOT / bp.BANCO_NO_GIT)
        self.assertEqual(achados, [],
                         f"o banco versionado passou a ter {achados}")

    def test_o_lancador_liga_a_trava_antes_de_atualizar(self):
        """Depois do pull, uma subida inteira rodaria sem a trava."""
        for nome in ("Abrir LAPE.bat", "Subir LAPE.bat"):
            with self.subTest(arquivo=nome):
                texto = (ROOT / nome).read_text(encoding="utf-8",
                                                errors="replace")
                self.assertIn("lape_agent.py proteger", texto)
                self.assertLess(texto.index("lape_agent.py proteger"),
                                texto.index("git pull --ff-only"))


if __name__ == "__main__":
    unittest.main()
