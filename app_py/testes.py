#!/usr/bin/env python3
"""Testes do ELASE.   python3 testes.py

Cada teste diz o que está protegendo. O que me interessa aqui não é cobertura:
é impedir que volte um erro que já aconteceu — carga contada duas vezes, Z
calculado sobre uma base que inclui o próprio ponto, gerador sobrescrevendo
treino que o preparador ajustou à mão.
"""

import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date, timedelta
from http.server import ThreadingHTTPServer

import banco
import analise
import sistema
import elase


def dia(n):
    """n dias a partir de hoje, negativo para trás."""
    return (date.today() + timedelta(days=n)).isoformat()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        # segunda-feira desta semana, para as contas de semana baterem
        banco.criar(self.db, banco.segunda_desta_semana())

    def tearDown(self):
        for suf in ("", "-wal", "-shm"):
            try:
                os.unlink(self.db + suf)
            except OSError:
                pass

    def con(self):
        return banco.conectar(self.db)

    def atleta(self, con, nome="Atleta Teste"):
        return elase.criar_atleta(con, {"nome": nome, "posicao": "Central",
                                        "estatura": 198, "massa": 92})["id"]


class TestBanco(Base):
    def test_esquema_cria_e_semeia(self):
        with self.con() as con:
            self.assertIsNotNone(banco.config(con))
            self.assertEqual(len(banco.blocos(con)), 8)
            n = con.execute("SELECT COUNT(*) c FROM exercicios").fetchone()["c"]
            self.assertGreater(n, 15)

    def test_criar_e_idempotente(self):
        banco.criar(self.db)
        banco.criar(self.db)
        with self.con() as con:
            self.assertEqual(len(banco.blocos(con)), 8,
                             "rodar criar() de novo não pode duplicar os blocos")

    def test_nao_existe_coluna_de_dinheiro(self):
        """Regra do projeto: nenhum dado financeiro do atleta, em lugar nenhum."""
        with self.con() as con:
            tabelas = [r["name"] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            proibidas = ("salario", "salário", "renda", "valor_pago", "remuneracao")
            for t in tabelas:
                for col in con.execute(f"PRAGMA table_info({t})").fetchall():
                    self.assertNotIn(col["name"].lower(), proibidas,
                                     f"coluna financeira em {t}")

    def test_chave_estrangeira_ligada(self):
        """Sem isto, uma série aponta para sessão inexistente e ninguém reclama."""
        import sqlite3
        with self.con() as con:
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("INSERT INTO series (sessao_id,exercicio,numero)"
                            " VALUES (9999,0,1)")

    def test_um_dia_uma_sessao_de_equipe(self):
        import sqlite3
        with self.con() as con:
            elase.salvar_prescricao(con, {"data": dia(1), "tipo": "Força",
                "exercicios": [{"nome": "Agachamento", "grupo": "Força",
                                "series": 5, "reps": "5"}]})
            with self.assertRaises(sqlite3.IntegrityError):
                elase.salvar_prescricao(con, {"data": dia(1), "tipo": "Força",
                    "exercicios": [{"nome": "Supino", "grupo": "Força",
                                    "series": 5, "reps": "5"}]})

    def test_plano_sessao(self):
        exs = [{"series": 5, "reps": "3", "pausa": 180, "grupo": "Força"},
               {"series": 4, "reps": "5", "pausa": 120, "grupo": "Pliometria"}]
        p = banco.plano_sessao(exs, "Força")
        self.assertEqual(p["series"], 9)
        self.assertEqual(p["contatos"], 20, "só o pliométrico conta contato")
        # 5*(180+12) + 4*(120+20) = 960 + 560 = 1520 s = 25,33 min → 25
        self.assertEqual(p["dur"], 25)
        self.assertEqual(p["ua"], 25 * 7)

    def test_primeiro_numero(self):
        self.assertEqual(banco._primeiro_numero("8 cada lado"), 8)
        self.assertEqual(banco._primeiro_numero("máximo"), 0)
        self.assertEqual(banco._primeiro_numero(3), 3)


class TestAnalise(Base):
    def test_desvio_amostral(self):
        self.assertAlmostEqual(analise.desvio([2, 4, 4, 4, 5, 5, 7, 9]), 2.1380899, places=5)
        self.assertEqual(analise.desvio([5]), 0.0, "um ponto não tem desvio")

    def test_quartis_exige_cinco_pontos(self):
        self.assertIsNone(analise.quartis([1, 2, 3, 4]))
        q = analise.quartis([1, 2, 3, 4, 5])
        self.assertEqual(q["mediana"], 3)
        self.assertEqual(q["q1"], 2)
        self.assertEqual(q["q3"], 4)

    def test_spearman_conhecido(self):
        """r = 1 − 6Σd²/(n(n²−1)).
        d = [0,-1,1,-1,1,-1,1] → Σd² = 6 → r = 1 − 36/336 = 0,892857…"""
        a = [1, 2, 3, 4, 5, 6, 7]
        b = [1, 3, 2, 5, 4, 7, 6]
        r = analise.spearman(a, b)
        self.assertAlmostEqual(r["r"], 1 - 6 * 6 / (7 * (49 - 1)), places=9)
        self.assertAlmostEqual(r["r"], 0.8928571, places=6)
        self.assertTrue(r["forte"])

    def test_spearman_recusa_poucos_pares(self):
        self.assertIsNone(analise.spearman([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]),
                          "cinco pares não dão conclusão — tem de devolver None")

    def test_postos_com_empate(self):
        self.assertEqual(analise.postos([10, 20, 20, 30]), [1.0, 2.5, 2.5, 4.0])

    def test_z_movel_nao_inclui_o_proprio_ponto(self):
        """A base é a janela ANTERIOR. Incluir o ponto encolhe o desvio e
        esconde justamente o desvio que se quer ver."""
        datas = [dia(-i) for i in range(9, -1, -1)]
        vals = [10, 10, 11, 9, 10, 11, 9, 10, 10, 20]
        z = analise.z_movel(datas, vals, 30)
        base = vals[:-1]
        esperado = (vals[-1] - analise.media(base)) / analise.desvio(base)
        self.assertAlmostEqual(z[-1], esperado, places=9)
        com_ponto = (vals[-1] - analise.media(vals)) / analise.desvio(vals)
        self.assertGreater(abs(z[-1]), abs(com_ponto),
                           "o Z sem o próprio ponto tem de ser MAIOR")

    def test_z_movel_exige_base_minima(self):
        datas = [dia(-i) for i in range(4, -1, -1)]
        self.assertIsNone(analise.z_movel(datas, [1, 2, 3, 4, 5], 30)[2],
                          "menos de 5 pontos de base não é base")

    def test_acwr_e_monotonia(self):
        with self.con() as con:
            aid = self.atleta(con)
            # 28 dias de 100 UA/dia: aguda 700, crônica 700 → ACWR 1,0
            for i in range(28):
                con.execute("INSERT INTO sessoes (atleta_id,data,carga_ua,check_out)"
                            " VALUES (?,?,?,'x')", (aid, dia(-i), 100))
            c = analise.carga(con, aid)
            self.assertAlmostEqual(c["acwr"], 1.0, places=6)
            self.assertEqual(c["semanal"], 700)
            # Carga idêntica todo dia: desvio zero, monotonia indefinida.
            # Devolver 0 aqui seria a pior resposta — lê-se como "ótima
            # variação" quando é justamente o caso máximo.
            self.assertIsNone(c["monotonia"])
            self.assertTrue(c["monotonia_indefinida"])
            self.assertIsNone(c["strain"])
            p = analise.prontidao(con, aid)
            self.assertTrue(any("idêntica" in t for t, _ in p["bandeiras"]),
                            "e isso tem de virar bandeira, não passar batido")

    def test_acwr_zero_sem_cronica(self):
        with self.con() as con:
            aid = self.atleta(con)
            c = analise.carga(con, aid)
            self.assertEqual(c["acwr"], 0, "sem sessão, ACWR é 0 e não divisão por zero")

    def test_zona_acwr_respeita_historico(self):
        self.assertEqual(analise.zona_acwr(1.9, 10)["t"], "Histórico curto")
        self.assertEqual(analise.zona_acwr(1.9, 30)["t"], "Risco elevado")
        self.assertEqual(analise.zona_acwr(1.0, 30)["t"], "Zona ideal")

    def test_tmd_e_z_por_subescala(self):
        with self.con() as con:
            aid = self.atleta(con)
            # 8 coletas calmas e uma nona com Fadiga no teto
            for i in range(9):
                d = dia(-(9 - i))
                for sub, itens in banco.BRUMS_ITENS:
                    for it in itens:
                        # A base precisa variar ENTRE coletas. Variar dentro da
                        # coleta não serve: a subescala é a SOMA dos 4 itens, e
                        # uma alternância interna deixa a soma constante — base
                        # sem desvio, e aí não existe Z para testar.
                        v = 1 + (i % 2)
                        if i == 8 and sub == "Fadiga":
                            v = 4
                        con.execute("INSERT INTO brums (atleta_id,data,momento,item,subescala,valor)"
                                    " VALUES (?,?,'pre',?,?,?)", (aid, d, it, sub, v))
            zs = {x["subescala"]: x for x in analise.z_hoje(con, aid)}
            self.assertIsNotNone(zs["Fadiga"]["z"])
            self.assertGreater(zs["Fadiga"]["z"], 2,
                               "Fadiga de 4 para 16 tem de estourar o Z")
            self.assertEqual(zs["Fadiga"]["ruim"], zs["Fadiga"]["z"])
            self.assertEqual(zs["Vigor"]["ruim"], -(zs["Vigor"]["z"] or 0),
                             "no Vigor o alerta é para BAIXO")

    def test_prontidao_ignora_componente_ausente(self):
        """Quem não respondeu a BRUMS não é quem está com o humor péssimo."""
        with self.con() as con:
            aid = self.atleta(con)
            p = analise.prontidao(con, aid)
            self.assertNotIn("humor", p["componentes"])
            self.assertIsNotNone(p["valor"])
            self.assertLessEqual(p["valor"], 100)


class TestSistema(Base):
    def blocos(self):
        with self.con() as con:
            return banco.blocos(con)

    def test_ciclo_nao_tem_teto(self):
        self.assertEqual(sistema.posicao_no_ciclo(8, 8), 8)
        self.assertEqual(sistema.ciclo_de(8, 8), 1)
        self.assertEqual(sistema.posicao_no_ciclo(9, 8), 1)
        self.assertEqual(sistema.ciclo_de(9, 8), 2)
        self.assertEqual(sistema.ciclo_de(100, 8), 13)
        self.assertEqual(sistema.posicao_no_ciclo(100, 8), 4)

    def test_reteste_fecha_cada_ciclo(self):
        self.assertTrue(sistema.e_semana_reteste(8, 8))
        self.assertTrue(sistema.e_semana_reteste(16, 8))
        self.assertFalse(sistema.e_semana_reteste(9, 8))

    def test_gera_tres_por_semana(self):
        bl = self.blocos()
        s, _ = sistema.gerar(bl, banco.segunda_desta_semana(), 1, 4)
        self.assertEqual(len(s), 12)

    def test_nao_sobrescreve(self):
        bl = self.blocos()
        inicio = banco.segunda_desta_semana()
        ocupada = banco.mais_dias(inicio, 0)
        s, pulados = sistema.gerar(bl, inicio, 1, 1, [ocupada])
        self.assertEqual(len(s), 2)
        self.assertIn(ocupada, pulados)

    def test_contatos_dentro_do_alvo(self):
        """O bloco define os contatos da semana. Repartir por sessão em vez de
        por exercício estourava o alvo em 40% — foi um erro real."""
        bl = self.blocos()
        inicio = banco.segunda_desta_semana()
        s, _ = sistema.gerar(bl, inicio, 1, 16)
        for r in sistema.resumo(s, bl, inicio):
            fora = abs(r["contatos"] - r["alvo_contatos"])
            self.assertLessEqual(fora, 10,
                f"semana {r['semana']}: {r['contatos']} contatos contra alvo "
                f"{r['alvo_contatos']}")

    def test_descarga_descarrega(self):
        bl = self.blocos()
        inicio = banco.segunda_desta_semana()
        s, _ = sistema.gerar(bl, inicio, 3, 5)
        por = {r["semana"]: r for r in sistema.resumo(s, bl, inicio)}
        self.assertLess(por[4]["ua"], por[3]["ua"] * 0.75)
        self.assertGreater(por[5]["ua"], por[4]["ua"])

    def test_intensidade_sobe_e_recua(self):
        bl = self.blocos()
        inicio = banco.segunda_desta_semana()
        s, _ = sistema.gerar(bl, inicio, 1, 8)
        pct = {}
        for x in s:
            if x["objetivo"] != "Força máxima":
                continue
            ag = next((e for e in x["exercicios"]
                       if e["nome"] == "Agachamento" and e["pct_rm"]), None)
            if ag:
                pct[banco.semana_de(x["data"], inicio)] = ag["pct_rm"]
        self.assertLess(pct[1], pct[3], "sobe dentro do bloco de acumulação")
        self.assertLess(pct[4], pct[3], "recua na descarga")
        self.assertLess(pct[5], pct[7], "sobe de novo na transmutação")

    def test_reteste_mede_e_nao_treina(self):
        bl = self.blocos()
        s, _ = sistema.gerar(bl, banco.segunda_desta_semana(), 8, 8)
        ret = [x for x in s if "RETESTE" in x["notas"]]
        self.assertEqual(len(ret), 1)
        self.assertIn("1RM", ret[0]["objetivo"])
        # O que tem de ser baixo é o volume de TRABALHO. Mobilidade antes de um
        # 1RM é preparação, e contá-la aqui mediria a coisa errada — aquecer
        # antes de testar é correto, não volume extra.
        trabalho = sum(e["series"] for e in ret[0]["exercicios"]
                       if e["grupo"] not in banco.SEM_CARGA)
        self.assertLessEqual(trabalho, 12, "o reteste mede, não treina")
        self.assertTrue(any(e["grupo"] == "Mobilidade" for e in ret[0]["exercicios"]),
                        "mas ele PRECISA abrir com mobilidade: medir sem preparar "
                        "mede o aquecimento, não a força")


class TestMobilidadeEducativo(Base):
    """Mobilidade articular e educativos de LPO dentro das sessões geradas."""

    def blocos(self):
        with self.con() as con:
            return banco.blocos(con)

    def test_toda_sessao_abre_com_mobilidade(self):
        bl = self.blocos()
        s, _ = sistema.gerar(bl, banco.segunda_desta_semana(), 1, 8)
        for x in s:
            primeiro = x["exercicios"][0]
            self.assertEqual(primeiro["grupo"], "Mobilidade",
                             f"{x['data']} começa com {primeiro['nome']}")

    def test_as_tres_articulacoes_em_toda_sessao(self):
        """Tornozelo, quadril e ombro. Se uma some, some para a temporada
        inteira — e é justamente a que vai cobrar."""
        chaves = {
            "tornozelo": ("tornozelo", "panturrilha", "agachamento profundo"),
            "quadril": ("quadril", "psoas", "cossaco", "airplane"),
            "ombro": ("ombro", "bastão", "parede com elástico", "torácica",
                      "cross-body", "y-t-w"),
        }
        bl = self.blocos()
        s, _ = sistema.gerar(bl, banco.segunda_desta_semana(), 1, 4)
        for x in s:
            mob = " ".join(e["nome"].lower() for e in x["exercicios"]
                           if e["grupo"] == "Mobilidade")
            for junta, palavras in chaves.items():
                self.assertTrue(any(w in mob for w in palavras),
                                f"{x['notas'][:40]}: falta {junta} em «{mob}»")

    def test_educativos_de_lpo_presentes_e_antes_da_barra(self):
        bl = self.blocos()
        s, _ = sistema.gerar(bl, banco.segunda_desta_semana(), 1, 1)
        sessao_a = next(x for x in s if x["objetivo"] == "Força máxima")
        grupos = [e["grupo"] for e in sessao_a["exercicios"]]
        self.assertIn("Educativo", grupos)
        # todo educativo vem ANTES do primeiro LPO com carga
        i_edu = max(i for i, g in enumerate(grupos) if g == "Educativo")
        i_lpo = min(i for i, g in enumerate(grupos) if g == "LPO")
        self.assertLess(i_edu, i_lpo,
                        "educativo depois da barra pesada não ensina nada")

    def test_volume_de_educativo_cai_com_a_intensidade(self):
        """Na acumulação o educativo é treino; na realização é rampa."""
        self.assertEqual(sistema.quantos_educativos(1), 4)
        self.assertEqual(sistema.quantos_educativos(3), 4)
        self.assertGreater(sistema.quantos_educativos(1),
                           sistema.quantos_educativos(8))
        self.assertGreaterEqual(sistema.quantos_educativos(8), 1,
                                "nunca chega a zero: a técnica se perde")

    def test_mobilidade_nao_conta_como_contato(self):
        """Contato pliométrico é impacto. Alongamento não é."""
        exs = [{"series": 3, "reps": "30 s", "grupo": "Mobilidade", "pausa": 30},
               {"series": 4, "reps": "5", "grupo": "Pliometria", "pausa": 120}]
        p = banco.plano_sessao(exs, "Potência")
        self.assertEqual(p["contatos"], 20)

    def test_permanencia_em_segundos_nao_vira_repeticao(self):
        """"30 s" é meio minuto, não 30 repetições de 4 segundos."""
        self.assertEqual(banco._segundos_de_trabalho("30 s"), 30)
        self.assertEqual(banco._segundos_de_trabalho("30 s cada lado"), 30)
        self.assertEqual(banco._segundos_de_trabalho("8 cada lado"), 32)
        self.assertEqual(banco._segundos_de_trabalho("3"), 12)
        um = banco.plano_sessao(
            [{"series": 2, "reps": "30 s", "grupo": "Mobilidade", "pausa": 30}], "Força")
        # 2 * (30 pausa + 30 trabalho) = 120 s = 2 min
        self.assertEqual(um["dur"], 2)

    def test_tempo_de_preparacao_vem_separado(self):
        bl = self.blocos()
        s, _ = sistema.gerar(bl, banco.segunda_desta_semana(), 1, 1)
        for x in s:
            p = banco.plano_sessao(x["exercicios"], x["tipo"])
            self.assertGreater(p["dur_prep"], 0, "há preparação na sessão")
            self.assertLess(p["dur_prep"], p["dur"],
                            "mas ela não é a sessão inteira")


class TestVideos(Base):
    def test_todo_exercicio_tem_link_que_funciona(self):
        """Busca, e não vídeo cravado: não consigo assistir a um vídeo para
        conferir se mostra o movimento certo, e demonstração errada num app de
        treino é risco de lesão."""
        with self.con() as con:
            for e in banco.dics(con.execute("SELECT nome FROM exercicios").fetchall()):
                u = banco.busca_video(e["nome"])
                self.assertTrue(u.startswith("https://www.youtube.com/results?"))
                self.assertNotIn(" ", u, "o endereço tem de estar codificado")

    def test_exercicios_de_mobilidade_e_educativo_tem_dica(self):
        """Um nome sozinho não ensina: "90/90 de quadril" não diz o que fazer."""
        with self.con() as con:
            sem = [e["nome"] for e in con.execute(
                "SELECT nome FROM exercicios WHERE grupo IN ('Mobilidade','Educativo')"
                " AND (dica IS NULL OR dica='')").fetchall()]
        self.assertEqual(sem, [], f"sem dica técnica: {sem}")

    def test_migracao_de_banco_antigo(self):
        """Banco criado antes tinha CHECK na coluna grupo, e SQLite não altera
        CHECK: 'Mobilidade' seria recusada para sempre."""
        import sqlite3
        velho = self.db + ".velho"
        c = sqlite3.connect(velho)
        c.executescript("""
            CREATE TABLE exercicios (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              nome TEXT NOT NULL UNIQUE,
              grupo TEXT NOT NULL CHECK (grupo IN
                ('Força','Potência','LPO','Pliometria','Técnico-Tático','Recuperação')),
              ref1rm TEXT);
            INSERT INTO exercicios (nome,grupo) VALUES ('Invenção do treinador','Força');
        """)
        c.commit()
        c.close()
        try:
            banco.criar(velho)
            with banco.conectar(velho) as con:
                cols = {x["name"] for x in con.execute("PRAGMA table_info(exercicios)")}
                self.assertIn("video_url", cols)
                self.assertIn("dica", cols)
                n = con.execute("SELECT COUNT(*) x FROM exercicios"
                                " WHERE grupo='Mobilidade'").fetchone()["x"]
                self.assertGreater(n, 5, "os exercícios novos entraram")
                sobrou = con.execute("SELECT 1 FROM exercicios"
                                     " WHERE nome='Invenção do treinador'").fetchone()
                self.assertIsNotNone(sobrou, "o que ELE criou não pode sumir")
        finally:
            for suf in ("", "-wal", "-shm"):
                try:
                    os.unlink(velho + suf)
                except OSError:
                    pass


class TestAPI(Base):
    """Sobe o servidor de verdade e conversa com ele por HTTP."""

    def setUp(self):
        super().setUp()
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), elase.Handler)
        self.srv.caminho_db = self.db
        self.porta = self.srv.server_address[1]
        self.t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.t.start()
        with self.con() as con:
            self.pin = banco.config(con)["pin_treinador"]

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        super().tearDown()

    def pedir(self, rota, dados=None, metodo=None, pin=None):
        url = f"http://127.0.0.1:{self.porta}{rota}"
        corpo = json.dumps(dados).encode() if dados is not None else None
        req = urllib.request.Request(url, data=corpo,
                                     method=metodo or ("POST" if dados is not None else "GET"))
        req.add_header("Content-Type", "application/json")
        if pin:
            req.add_header("X-Pin", pin)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_estado(self):
        cod, d = self.pedir("/api/estado")
        self.assertEqual(cod, 200)
        self.assertEqual(len(d["blocos"]), 8)
        self.assertEqual(d["semana"], 1)

    def test_pagina_inicial_serve(self):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.porta}/") as r:
            html = r.read().decode()
        self.assertIn("ELASE", html)
        self.assertIn("app.js", html)

    def test_cadastro_liberado_entra_ativo(self):
        cod, d = self.pedir("/api/cadastro", {"nome": "João Pedro", "posicao": "Oposto",
                                              "estatura": 197, "massa": 90})
        self.assertEqual(cod, 200)
        self.assertEqual(d["status"], "Ativo")
        self.assertTrue(d["liberado"])

    def test_cadastro_com_aprovacao_fica_pendente(self):
        self.pedir("/api/config", {"cadastro_liberado": 0}, pin=self.pin)
        cod, d = self.pedir("/api/cadastro", {"nome": "Maria Clara"})
        self.assertEqual(d["status"], "Pendente")

    def test_cadastro_exige_nome(self):
        cod, d = self.pedir("/api/cadastro", {"posicao": "Central"})
        self.assertEqual(cod, 400)
        self.assertIn("nome", d["erro"])

    def test_posicao_invalida_e_recusada_em_portugues(self):
        cod, d = self.pedir("/api/cadastro", {"nome": "X", "posicao": "Goleiro"})
        self.assertEqual(cod, 400)
        self.assertIn("Posição desconhecida", d["erro"])

    def test_area_do_treinador_exige_pin(self):
        cod, d = self.pedir("/api/sistema/gerar", {"de": 1, "ate": 1})
        self.assertEqual(cod, 403)
        cod, d = self.pedir("/api/sistema/gerar", {"de": 1, "ate": 1}, pin="errado")
        self.assertEqual(cod, 403)
        cod, d = self.pedir("/api/sistema/gerar", {"de": 1, "ate": 1}, pin=self.pin)
        self.assertEqual(cod, 200)

    def test_ciclo_completo_do_atleta(self):
        """Cadastro → prescrição → check-in → séries → check-out → análise.
        É o caminho inteiro; se ele passa, o sistema faz o que promete."""
        _, a = self.pedir("/api/cadastro", {"nome": "Vitor Hugo", "posicao": "Central",
                                            "estatura": 200, "massa": 95})
        aid = a["id"]
        _, g = self.pedir("/api/sistema/gerar", {"de": 1, "ate": 1}, pin=self.pin)
        self.assertEqual(g["criadas"], 3)

        _, ps = self.pedir(f"/api/prescricoes?de={banco.segunda_desta_semana()}"
                           f"&ate={banco.mais_dias(banco.segunda_desta_semana(), 6)}")
        pid = ps[0]["id"]
        n_exs = len(ps[0]["exercicios"])
        self.assertGreater(n_exs, 4)

        _, s = self.pedir("/api/sessao/abrir", {
            "atleta_id": aid, "prescricao_id": pid,
            "wellness": {"sono_qual": 4, "sono_horas": 8, "estresse": 2, "dor": 1, "kss": 3},
            "brums": {i: 1 for sub, itens in banco.BRUMS_ITENS for i in itens}})
        sid = s["sessao_id"]

        # duas séries feitas, uma digitada e NÃO concluída
        self.pedir("/api/sessao/serie", {"sessao_id": sid, "exercicio": 1, "numero": 1,
                                         "carga": 100, "reps": 3, "feita": True})
        self.pedir("/api/sessao/serie", {"sessao_id": sid, "exercicio": 1, "numero": 2,
                                         "carga": 100, "reps": 3, "feita": True})
        self.pedir("/api/sessao/serie", {"sessao_id": sid, "exercicio": 1, "numero": 3,
                                         "carga": 100, "reps": 3, "feita": False})

        cod, f = self.pedir("/api/sessao/fechar", {"sessao_id": sid, "pse": 7})
        self.assertEqual(cod, 200)
        self.assertEqual(f["tonelagem"], 600,
                         "série não concluída não entra na tonelagem")
        self.assertEqual(f["carga_ua"], f["dur_min"] * 7)

        cod, an = self.pedir(f"/api/analise?atleta={aid}")
        self.assertEqual(cod, 200)
        self.assertEqual(an["carga"]["n"], 1)
        self.assertGreater(an["prontidao"], 0)
        self.assertIn("sono", an["componentes"])

    def test_nao_fecha_duas_vezes(self):
        _, a = self.pedir("/api/cadastro", {"nome": "Dois Checkouts"})
        self.pedir("/api/sistema/gerar", {"de": 1, "ate": 1}, pin=self.pin)
        _, ps = self.pedir(f"/api/prescricoes?de={banco.segunda_desta_semana()}"
                           f"&ate={banco.mais_dias(banco.segunda_desta_semana(), 6)}")
        _, s = self.pedir("/api/sessao/abrir",
                          {"atleta_id": a["id"], "prescricao_id": ps[0]["id"]})
        self.pedir("/api/sessao/fechar", {"sessao_id": s["sessao_id"], "pse": 6})
        cod, d = self.pedir("/api/sessao/fechar", {"sessao_id": s["sessao_id"], "pse": 9})
        self.assertEqual(cod, 400)
        self.assertIn("já foi encerrada", d["erro"])

    def test_brums_recusa_item_desconhecido(self):
        _, a = self.pedir("/api/cadastro", {"nome": "Item Errado"})
        cod, d = self.pedir("/api/brums", {"atleta_id": a["id"],
                                           "respostas": {"Felizardo": 2}})
        self.assertEqual(cod, 400)
        self.assertIn("desconhecido", d["erro"])

    def test_gerar_duas_vezes_nao_duplica(self):
        _, g1 = self.pedir("/api/sistema/gerar", {"de": 1, "ate": 4}, pin=self.pin)
        _, g2 = self.pedir("/api/sistema/gerar", {"de": 1, "ate": 4}, pin=self.pin)
        self.assertEqual(g1["criadas"], 12)
        self.assertEqual(g2["criadas"], 0)
        self.assertEqual(g2["pulados"], 12)

    def test_sql_so_leitura(self):
        for ruim in ["DELETE FROM atletas",
                     "UPDATE atletas SET nome='x'",
                     "DROP TABLE sessoes",
                     "INSERT INTO atletas (nome,apelido) VALUES ('a','a')",
                     "PRAGMA table_info(atletas)"]:
            cod, d = self.pedir("/api/sql", {"sql": ruim}, pin=self.pin)
            self.assertEqual(cod, 400, f"deveria recusar: {ruim}")
        cod, d = self.pedir("/api/sql", {"sql": "SELECT COUNT(*) AS n FROM atletas"},
                            pin=self.pin)
        self.assertEqual(cod, 200)
        self.assertEqual(d["colunas"], ["n"])

    def test_sql_erro_volta_explicado(self):
        cod, d = self.pedir("/api/sql", {"sql": "SELECT * FROM tabela_que_nao_existe"},
                            pin=self.pin)
        self.assertEqual(cod, 400)
        self.assertIn("SQL:", d["erro"])

    def _subir(self, nome, arquivo, dados, pin=None):
        import urllib.parse
        url = f"http://127.0.0.1:{self.porta}/api/exercicio/video-arquivo"
        req = urllib.request.Request(url, data=dados, method="POST")
        req.add_header("X-Exercicio", urllib.parse.quote(nome))
        req.add_header("X-Arquivo", urllib.parse.quote(arquivo))
        if pin:
            req.add_header("X-Pin", pin)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_video_proprio_sobe_e_fica_servido(self):
        """O vídeo do próprio clube vale mais que qualquer link: o atleta
        reconhece o companheiro, a sala e a correção do preparador."""
        cod, d = self._subir("Agachamento cossaco", "treino.mp4", b"\x00" * 2048,
                             pin=self.pin)
        self.assertEqual(cod, 200, d)
        self.assertTrue(d["video_url"].startswith("/videos/"))
        self.assertEqual(d["bytes"], 2048)
        # ficou gravado no exercício
        with self.con() as con:
            u = con.execute("SELECT video_url FROM exercicios WHERE nome=?",
                            ("Agachamento cossaco",)).fetchone()["video_url"]
        self.assertEqual(u, d["video_url"])
        # e é servido pelo app, com o tipo certo
        with urllib.request.urlopen(
                f"http://127.0.0.1:{self.porta}{d['video_url']}") as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers["Content-Type"], "video/mp4")
            self.assertIn("max-age", r.headers.get("Cache-Control", ""))
            self.assertEqual(len(r.read()), 2048)
        os.unlink(os.path.join(elase.VIDEOS, os.path.basename(d["video_url"])))

    def test_video_exige_pin(self):
        cod, d = self._subir("Agachamento cossaco", "x.mp4", b"\x00" * 10)
        self.assertEqual(cod, 403)

    def test_video_recusa_formato_estranho(self):
        cod, d = self._subir("Agachamento cossaco", "planilha.xlsx", b"\x00" * 10,
                             pin=self.pin)
        self.assertEqual(cod, 400)
        self.assertIn("MP4", d["erro"])

    def test_video_recusa_exercicio_inexistente(self):
        cod, d = self._subir("Cambalhota olímpica", "x.mp4", b"\x00" * 10,
                             pin=self.pin)
        self.assertEqual(cod, 400)
        self.assertIn("biblioteca", d["erro"])

    def test_video_recusa_arquivo_vazio(self):
        cod, d = self._subir("Agachamento cossaco", "x.mp4", b"", pin=self.pin)
        self.assertEqual(cod, 400)

    def test_nome_de_arquivo_nao_escapa_da_pasta(self):
        """Nome de exercício vira nome de arquivo. Sem isto, um nome com barra
        escreveria fora da pasta de vídeos."""
        for entrada, proibido in [("../../etc/passwd", "/"),
                                  ("a\\b", "\\"),
                                  ("Rotação torácica (open book)", "ç")]:
            saida = elase._nome_de_arquivo(entrada)
            self.assertNotIn(proibido, saida)
            self.assertNotIn("..", saida)
        self.assertEqual(elase._nome_de_arquivo("Y-T-W no banco inclinado"),
                         "y-t-w-no-banco-inclinado")

    def test_rota_desconhecida(self):
        cod, d = self.pedir("/api/nao-existe")
        self.assertEqual(cod, 404)

    def test_json_invalido_nao_derruba(self):
        url = f"http://127.0.0.1:{self.porta}/api/cadastro"
        req = urllib.request.Request(url, data=b"{isto nao e json", method="POST")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as r:
                cod = r.status
        except urllib.error.HTTPError as e:
            cod, d = e.code, json.loads(e.read())
            self.assertIn("JSON", d["erro"])
        self.assertEqual(cod, 400)


if __name__ == "__main__":
    unittest.main(verbosity=2)
