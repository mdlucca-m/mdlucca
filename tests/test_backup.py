#!/usr/bin/env python3
"""Testes da copia de seguranca guiada pelo cadastro.

    python3 -m unittest discover -s tests -v

Um backup so vale pelo dia em que for usado. Por isso o que se checa aqui
nao e "o arquivo apareceu", e sim: ele abre, tem o que tinha no banco, e
existe justamente quando alguem cadastrou algo.
"""
from __future__ import annotations

import gzip
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lape import backup, hooks, ingest_excel, preflight  # noqa: E402
from lape.db import Database  # noqa: E402


class BancoTemporario(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.caminho = Path(self.tmp.name) / "db.sqlite"
        self.db = Database(self.caminho)
        self.db.migrate()
        ingest_excel.ingest_members(self.db, [{"full_name": "Marina Cardoso"}])
        # o intervalo minimo existe para a producao, nao para o teste
        self.intervalo = backup.INTERVALO_MINIMO_MIN
        self.teto = backup.TEMPO_MAXIMO_S
        backup.INTERVALO_MINIMO_MIN = 0

    def tearDown(self):
        backup.INTERVALO_MINIMO_MIN = self.intervalo
        backup.TEMPO_MAXIMO_S = self.teto
        self.db.close()
        self.tmp.cleanup()

    def pasta(self) -> Path:
        return self.caminho.parent / "backups"


class TestQuandoCopiar(BancoTemporario):
    def test_sem_copia_nenhuma_a_primeira_e_devida(self):
        self.assertEqual(backup.pendente(self.db), "primeira copia")

    def test_depois_de_copiar_nada_mais_e_devido(self):
        backup.fazer(self.db, "teste", self.caminho)
        self.assertIsNone(backup.pendente(self.db))

    def test_um_cadastro_torna_a_copia_devida(self):
        backup.fazer(self.db, "teste", self.caminho)
        hooks.emit(self.db, "integrante.cadastrado", entity="members", detail="alguém")
        self.db.conn.commit()
        motivo = backup.pendente(self.db)
        self.assertIsNotNone(motivo)
        self.assertIn("cadastro", motivo)

    def test_o_intervalo_minimo_segura_a_enxurrada(self):
        # numa tarde de cadastro em massa, uma copia por registro so encheria
        # o disco -- o intervalo e o que impede isso
        backup.INTERVALO_MINIMO_MIN = 30
        backup.fazer(self.db, "teste", self.caminho)
        for i in range(20):
            hooks.emit(self.db, "artigo.cadastrado", entity="articles", detail=str(i))
        self.db.conn.commit()
        self.assertIsNone(backup.pendente(self.db))

    def test_um_dia_parado_ainda_rende_uma_copia(self):
        backup.INTERVALO_MINIMO_MIN = 30
        backup.fazer(self.db, "teste", self.caminho)
        ontem = (datetime.now() - timedelta(days=2)).isoformat(sep=" ", timespec="seconds")
        self.db.execute("UPDATE ingest_log SET run_at = ? WHERE source = 'backup'", (ontem,))
        self.db.conn.commit()
        self.assertEqual(backup.pendente(self.db), "copia diaria")

    def test_rodar_sem_motivo_nao_copia(self):
        backup.fazer(self.db, "teste", self.caminho)
        self.assertIsNone(backup.rodar(self.db, db_path=self.caminho))

    def test_forcar_copia_de_qualquer_jeito(self):
        backup.fazer(self.db, "teste", self.caminho)
        feito = backup.rodar(self.db, forcar=True, db_path=self.caminho)
        self.assertIsNotNone(feito)
        self.assertEqual(feito["motivo"], "pedido manual")


class TestACopiaServe(BancoTemporario):
    def test_a_copia_abre_e_tem_o_que_o_banco_tinha(self):
        ingest_excel.ingest_articles(self.db, [
            {"title": "Ansiedade em atletas", "authors": "Cardoso", "status": "Publicado"},
        ])
        feito = backup.fazer(self.db, "teste", self.caminho)
        destino = Path(self.tmp.name) / "restaurado.sqlite"
        conferido = backup.restaurar(Path(feito["arquivo"]), destino)
        self.assertEqual(conferido["integridade"], "ok")
        self.assertEqual(conferido["conteudo"]["articles"], 1)
        self.assertEqual(conferido["conteudo"]["members"], 1)

    def test_a_copia_carrega_o_que_foi_cadastrado_depois_da_anterior(self):
        backup.fazer(self.db, "primeira", self.caminho)
        ingest_excel.ingest_articles(self.db, [
            {"title": "Sono e desempenho", "authors": "Cardoso"}])
        feito = backup.fazer(self.db, "segunda", self.caminho)
        destino = Path(self.tmp.name) / "segunda.sqlite"
        conferido = backup.restaurar(Path(feito["arquivo"]), destino)
        self.assertEqual(conferido["conteudo"]["articles"], 1)

    def test_restaurar_nao_toca_no_banco_em_uso(self):
        feito = backup.fazer(self.db, "teste", self.caminho)
        antes = self.caminho.stat().st_mtime
        backup.restaurar(Path(feito["arquivo"]), Path(self.tmp.name) / "outro.sqlite")
        self.assertEqual(self.caminho.stat().st_mtime, antes)

    def test_copia_corrompida_e_recusada(self):
        # descobrir que a copia nao presta no dia de usar seria tarde demais
        ruim = self.pasta()
        ruim.mkdir(parents=True, exist_ok=True)
        arquivo = ruim / "db_00000000_000000.sqlite.gz"
        with gzip.open(arquivo, "wb") as saida:
            saida.write(b"isto nao e um banco")
        with self.assertRaises(ValueError):
            backup.restaurar(arquivo, Path(self.tmp.name) / "nao-vai.sqlite")

    def test_copiar_com_gravacao_pendente_nao_trava(self):
        """Regressao de um travamento, nao de uma falha.

        `Connection.backup` fica tentando enquanto o cadeado de escrita
        estiver preso. Copiando a partir da propria conexao que segura esse
        cadeado, a espera e por alguem que nunca vem. O conserto foi fechar
        a transacao antes de copiar; o teto de tempo e o que garante que,
        se isso voltar a acontecer, o resultado seja uma falha e nao uma
        suite pendurada.
        """
        backup.TEMPO_MAXIMO_S = 5
        self.db.execute("INSERT INTO change_log (event) VALUES ('sem commit')")
        feito = backup.fazer(self.db, "teste", self.caminho)
        self.assertTrue(Path(feito["arquivo"]).exists())

        # e o que estava pendente entrou na copia
        destino = Path(self.tmp.name) / "conferir.sqlite"
        backup.restaurar(Path(feito["arquivo"]), destino)
        conferencia = sqlite3.connect(destino)
        try:
            quantas = conferencia.execute("SELECT COUNT(*) FROM change_log").fetchone()[0]
        finally:
            conferencia.close()
        self.assertEqual(quantas, 1, "a gravacao pendente ficou de fora da copia")

    def test_a_copia_desiste_em_vez_de_esperar_para_sempre(self):
        # dentro de um servico, esperar sem fim e uma mina: melhor desistir,
        # avisar e tentar de novo na proxima passagem
        backup.TEMPO_MAXIMO_S = -1
        with self.assertRaises(TimeoutError):
            backup.fazer(self.db, "teste", self.caminho)
        self.assertEqual(backup.copias(self.caminho), [],
                         "desistir nao pode deixar arquivo pela metade")

    def test_a_copia_fica_registrada_para_a_conferencia(self):
        backup.fazer(self.db, "teste", self.caminho)
        registro = backup.ultimo(self.db)
        self.assertIsNotNone(registro)
        self.assertEqual(registro["message"], "teste")


class TestRotacao(BancoTemporario):
    def envelhecer(self, arquivo: Path, dias: int) -> None:
        import os

        quando = (datetime.now() - timedelta(days=dias)).timestamp()
        os.utime(arquivo, (quando, quando))

    def test_copia_velha_e_apagada(self):
        for i in range(15):
            (self.pasta()).mkdir(parents=True, exist_ok=True)
            arquivo = self.pasta() / f"db_2020010{i % 10}_00000{i}.sqlite.gz"
            arquivo.write_bytes(b"x")
            self.envelhecer(arquivo, 90)
        apagadas = backup.limpar(self.pasta(), dias=30, minimo=10)
        self.assertEqual(apagadas, 5)
        self.assertEqual(len(backup.copias(self.caminho)), 10)

    def test_nunca_fica_sem_copia_nenhuma(self):
        # um laboratorio que passa dois meses sem cadastrar nada nao pode
        # acordar sem copia so porque as que tinha envelheceram
        self.pasta().mkdir(parents=True, exist_ok=True)
        for i in range(3):
            arquivo = self.pasta() / f"db_20200101_00000{i}.sqlite.gz"
            arquivo.write_bytes(b"x")
            self.envelhecer(arquivo, 400)
        self.assertEqual(backup.limpar(self.pasta(), dias=30, minimo=10), 0)
        self.assertEqual(len(backup.copias(self.caminho)), 3)


class TestConferenciaAvisaDaCopia(BancoTemporario):
    def test_o_aviso_some_depois_da_primeira_copia(self):
        titulos = {a["titulo"] for a in preflight.conferir(self.db)}
        self.assertIn("Nenhum backup registrado", titulos)

        backup.fazer(self.db, "teste", self.caminho)
        achados = preflight.conferir(self.db)
        titulos = {a["titulo"] for a in achados}
        self.assertFalse(any(t == "Nenhum backup registrado" for t in titulos))
        copia = next(a for a in achados if a["titulo"].startswith("Último backup"))
        self.assertEqual(copia["nivel"], "ok")


if __name__ == "__main__":
    unittest.main(verbosity=2)
