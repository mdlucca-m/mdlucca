"""Copia de seguranca do banco, movida pelo cadastro.

Um backup por relogio guarda muita copia igual e perde justamente a hora em
que algo aconteceu. Aqui quem manda e o `change_log`: se alguem cadastrou um
artigo, uma submissao, uma pessoa, sai copia. Se ninguem mexeu em nada, nao
sai -- exceto a copia diaria, que existe para haver sempre uma recente
mesmo numa semana parada.

A copia e feita pela API `sqlite3.backup`, e nao copiando o arquivo: copiar
o arquivo enquanto o servico escreve produz um banco que abre e mente. Como
o banco roda em WAL, a copia crua ainda perderia o que esta no `-wal`.

Cada copia fica registrada em `ingest_log` com `source = 'backup'`. E dai
que a conferencia de publicacao sabe dizer se ha copia e de quando.
"""
from __future__ import annotations

import gzip
import os
import shutil
import sqlite3
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from . import config
from .db import Database

# Nunca duas copias coladas: numa tarde de cadastro em massa, uma copia a
# cada registro encheria o disco sem acrescentar seguranca nenhuma.
INTERVALO_MINIMO_MIN = int(os.environ.get("LAPE_BACKUP_INTERVALO_MIN", "30"))
# Mesmo sem mexer em nada, uma copia por dia.
INTERVALO_DIARIO_H = int(os.environ.get("LAPE_BACKUP_DIARIO_H", "24"))
# Quantas mudancas ja justificam uma copia.
MUDANCAS_PARA_COPIAR = int(os.environ.get("LAPE_BACKUP_MUDANCAS", "1"))
# Teto para a copia. `Connection.backup` fica tentando enquanto o banco
# estiver ocupado -- para sempre, se o cadeado nunca soltar. Dentro de um
# servico, uma espera sem fim e uma mina: melhor desistir, avisar e tentar
# de novo na proxima passagem.
TEMPO_MAXIMO_S = int(os.environ.get("LAPE_BACKUP_TIMEOUT_S", "120"))
# Quanto tempo guardar, e quantas copias manter de qualquer jeito.
DIAS_GUARDADOS = int(os.environ.get("LAPE_BACKUP_KEEP", "30"))
MINIMO_GUARDADO = int(os.environ.get("LAPE_BACKUP_KEEP_MIN", "10"))


def pasta(db_path: Path | None = None) -> Path:
    """Onde as copias moram. Ao lado do banco, salvo indicacao em contrario."""
    indicada = os.environ.get("LAPE_BACKUP_DIR")
    if indicada:
        return Path(indicada)
    origem = Path(db_path or config.DB_PATH)
    return origem.parent / "backups"


def ultimo(db: Database) -> dict[str, Any] | None:
    """O registro da copia mais recente, ou None se nunca houve uma.

    `rows_read` guarda a marca: o maior id do `change_log` no momento da
    copia. E por ela que se conta o que veio depois.
    """
    linhas = db.dicts(
        "SELECT run_at, file, message, rows_read AS marca FROM ingest_log"
        " WHERE source = 'backup' AND status = 'ok' ORDER BY id DESC LIMIT 1")
    return linhas[0] if linhas else None


def marca_atual(db: Database) -> int:
    return int(db.scalar("SELECT COALESCE(MAX(id), 0) FROM change_log") or 0)


def _agora_do_banco() -> datetime:
    """O relogio do SQLite e UTC; o do Python, local.

    Comparar os dois direto foi o defeito: a oeste de Greenwich a copia
    recem-feita parecia estar tres horas no futuro, a idade dela dava
    negativa, e nenhuma copia seguinte jamais seria considerada devida.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _quando(texto: str | None) -> datetime | None:
    if not texto:
        return None
    try:
        return datetime.fromisoformat(str(texto))
    except ValueError:
        return None


def mudancas_desde(db: Database, marca: int | None) -> int:
    """Quantos registros entraram no `change_log` depois daquela marca.

    Conta-se por id, e nao por horario: o `change_log` grava segundos
    inteiros, e um cadastro feito no mesmo segundo da copia jamais seria
    contado -- ficaria fora dela e fora da proxima decisao, para sempre.
    """
    return int(db.scalar("SELECT COUNT(*) FROM change_log WHERE id > ?",
                         (int(marca or 0),)) or 0)


def pendente(db: Database, agora: datetime | None = None) -> str | None:
    """Por que copiar agora -- ou None, quando nao ha motivo.

    A ordem importa: o intervalo minimo vem antes de tudo, senao um dia de
    cadastro intenso viraria dezenas de copias iguais.
    """
    agora = agora or _agora_do_banco()
    anterior = ultimo(db)
    if anterior is None:
        return "primeira copia"

    feito_em = _quando(anterior["run_at"])
    if feito_em is None:
        return "primeira copia"          # registro ilegivel: trata como inexistente
    idade = agora - feito_em
    if idade < timedelta(minutes=INTERVALO_MINIMO_MIN):
        return None

    novas = mudancas_desde(db, anterior["marca"])
    if novas >= MUDANCAS_PARA_COPIAR:
        return f"{novas} cadastro(s) desde a ultima copia"
    if idade >= timedelta(hours=INTERVALO_DIARIO_H):
        return "copia diaria"
    return None


def fazer(db: Database, motivo: str = "manual", db_path: Path | None = None) -> dict[str, Any]:
    """Copia o banco e registra a copia. Devolve o que foi escrito."""
    # Fechar a transacao aberta antes de copiar, por dois motivos. O
    # primeiro e correcao: o que ainda nao foi gravado nao entraria na copia.
    # O segundo e que `Connection.backup` fica esperando o cadeado de
    # escrita -- copiar a partir da propria conexao que segura esse cadeado
    # trava para sempre, sem erro e sem mensagem.
    db.conn.commit()

    destino = pasta(db_path)
    destino.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo = destino / f"db_{carimbo}.sqlite.gz"

    # o intermediario existe porque `backup` escreve um .sqlite, e o que se
    # guarda e o .gz -- um banco do LAPE comprime para menos de um decimo
    with tempfile.TemporaryDirectory() as temporario:
        cru = Path(temporario) / "db.sqlite"
        alvo = sqlite3.connect(cru)
        prazo = time.monotonic() + TEMPO_MAXIMO_S

        def andamento(_status: int, _restantes: int, _total: int) -> None:
            # chamado a cada passo, inclusive nos que voltam "ocupado": e por
            # aqui que a espera ganha fim
            if time.monotonic() > prazo:
                raise TimeoutError(
                    f"a copia passou de {TEMPO_MAXIMO_S}s esperando o banco liberar")

        try:
            db.conn.backup(alvo, progress=andamento, sleep=0.05)
        finally:
            alvo.close()
        with open(cru, "rb") as entrada, gzip.open(arquivo, "wb", compresslevel=6) as saida:
            shutil.copyfileobj(entrada, saida)

    tamanho = arquivo.stat().st_size
    apagadas = limpar(destino)
    db.log_ingest("backup", target="db.sqlite", file=arquivo.name,
                  rows_read=marca_atual(db), rows_written=tamanho, message=motivo)
    db.conn.commit()
    return {"arquivo": str(arquivo), "bytes": tamanho, "motivo": motivo,
            "apagadas": apagadas}


def copias(db_path: Path | None = None) -> list[Path]:
    destino = pasta(db_path)
    if not destino.exists():
        return []
    return sorted(destino.glob("db_*.sqlite.gz"), reverse=True)


def limpar(destino: Path | None = None, dias: int = DIAS_GUARDADOS,
           minimo: int = MINIMO_GUARDADO) -> int:
    """Apaga copia velha, mas nunca fica abaixo do minimo.

    O minimo importa: um laboratorio que passa um mes sem cadastrar nada nao
    pode acordar sem copia nenhuma so porque as que tinha envelheceram.
    """
    destino = Path(destino) if destino else pasta()
    if not destino.exists():
        return 0
    todas = sorted(destino.glob("db_*.sqlite.gz"), reverse=True)
    limite = datetime.now() - timedelta(days=dias)
    apagadas = 0
    for arquivo in todas[minimo:]:
        if datetime.fromtimestamp(arquivo.stat().st_mtime) < limite:
            arquivo.unlink(missing_ok=True)
            apagadas += 1
    return apagadas


def rodar(db: Database, forcar: bool = False,
          db_path: Path | None = None) -> dict[str, Any] | None:
    """Copia se houver motivo. Devolve None quando nao havia."""
    motivo = "pedido manual" if forcar else pendente(db)
    if motivo is None:
        return None
    return fazer(db, motivo, db_path)


def restaurar(arquivo: Path, destino: Path) -> dict[str, Any]:
    """Descompacta uma copia e confere que ela abre antes de entregar.

    Nao sobrescreve o banco em uso de proposito. Trocar o arquivo debaixo de
    um servico que esta escrevendo e como trocar o pneu com o carro andando:
    o destino e outro caminho, e quem decide a troca -- com o servico
    parado -- e uma pessoa.
    """
    arquivo, destino = Path(arquivo), Path(destino)
    if not arquivo.exists():
        raise FileNotFoundError(f"copia nao encontrada: {arquivo}")
    destino.parent.mkdir(parents=True, exist_ok=True)
    abrir = gzip.open if arquivo.suffix == ".gz" else open
    with abrir(arquivo, "rb") as entrada, open(destino, "wb") as saida:
        shutil.copyfileobj(entrada, saida)

    # copia que nao abre nao e copia: conferir aqui evita descobrir isso no
    # dia em que ela for a unica coisa que restou
    conferencia = sqlite3.connect(destino)
    try:
        try:
            integro = conferencia.execute("PRAGMA integrity_check").fetchone()[0]
        except sqlite3.DatabaseError as exc:
            # arquivo que nem e banco: o sqlite so reclama na primeira leitura
            raise ValueError(f"a copia nao e um banco valido: {exc}") from exc
        contagem = {}
        for tabela in ("articles", "members", "projects", "submissions", "events"):
            try:
                contagem[tabela] = conferencia.execute(
                    f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            except sqlite3.Error:
                contagem[tabela] = None
    finally:
        conferencia.close()
    if integro != "ok":
        raise ValueError(f"a copia esta corrompida: {integro}")
    return {"destino": str(destino), "integridade": integro, "conteudo": contagem}


def resumo(db: Database, db_path: Path | None = None) -> dict[str, Any]:
    anterior = ultimo(db)
    guardadas = copias(db_path)
    return {
        "pasta": str(pasta(db_path)),
        "copias": len(guardadas),
        "ultima": anterior["run_at"] if anterior else None,
        "motivo_da_ultima": anterior["message"] if anterior else None,
        "bytes_guardados": sum(a.stat().st_size for a in guardadas),
        "pendente": pendente(db),
    }
