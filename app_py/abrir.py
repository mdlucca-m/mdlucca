#!/usr/bin/env python3
"""Abre o ELASE e publica um endereço para os atletas.

    python3 abrir.py            # servidor + o melhor túnel que esta máquina tiver
    python3 abrir.py --rede     # só a rede local (mesmo wi-fi), sem túnel
    python3 abrir.py --porta 8080

Por que este arquivo existe: subir o servidor é fácil, e o que trava é a parte
seguinte — deixar o celular do atleta alcançar essa máquina. Aqui as tentativas
acontecem em ordem, sozinhas, e **cada falha diz o que fazer**, em vez de
devolver uma mensagem de erro em inglês no meio do terminal.

Ordem das tentativas:
  1. `cloudflared` já instalado
  2. baixar `cloudflared` (uma vez, para a pasta ao lado)
  3. `ssh` para o localhost.run — não instala nada, só precisa de ssh

A rede local aparece SEMPRE, antes de qualquer túnel: ela não depende de
internet, não depende de terceiros e é a que funciona no ginásio.
"""

import argparse
import os
import platform
import re
import shutil
import socket
import stat
import subprocess
import sys
import threading
import time
from http.server import ThreadingHTTPServer

import banco
import elase

AQUI = os.path.dirname(os.path.abspath(__file__))


# ── Enfeite de terminal ──────────────────────────────────────────────────────
def caixa(titulo, linhas, marca="="):
    largura = max([len(titulo)] + [len(l) for l in linhas]) + 4
    print("\n" + marca * largura)
    print(f"  {titulo}")
    print(marca * largura)
    for l in linhas:
        print("  " + l)
    print(marca * largura + "\n")


def ip_local():
    """O IP desta máquina na rede local.

    O truque do socket UDP não envia pacote nenhum: só pergunta ao sistema qual
    interface ele usaria para sair. É o jeito que funciona com várias placas de
    rede, onde `hostname -I` devolve três endereços e você não sabe qual é."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


# ── cloudflared ──────────────────────────────────────────────────────────────
def nome_do_binario():
    """Qual arquivo do cloudflared serve para este computador."""
    so = platform.system().lower()
    arq = platform.machine().lower()
    x64 = arq in ("x86_64", "amd64")
    arm = arq in ("arm64", "aarch64")
    if so == "linux":
        return "cloudflared-linux-" + ("amd64" if x64 else "arm64" if arm else "386")
    if so == "darwin":
        return "cloudflared-darwin-" + ("amd64" if x64 else "arm64")
    if so == "windows":
        return "cloudflared-windows-" + ("amd64" if x64 else "386") + ".exe"
    return None


def achar_cloudflared():
    """No PATH, ou já baixado aqui do lado."""
    achado = shutil.which("cloudflared")
    if achado:
        return achado
    local = os.path.join(AQUI, "cloudflared.exe" if os.name == "nt" else "cloudflared")
    return local if os.path.isfile(local) else None


def baixar_cloudflared():
    """Baixa o cloudflared uma vez, para a pasta do app.

    Devolve o caminho, ou None com o motivo impresso. Não levanta exceção: se o
    download falhar, ainda há o caminho do ssh e o da rede local."""
    import urllib.request

    binario = nome_do_binario()
    if not binario:
        print("  · não sei qual versão do cloudflared serve para "
              f"{platform.system()}/{platform.machine()}")
        return None
    url = ("https://github.com/cloudflare/cloudflared/releases/latest/download/" + binario)
    destino = os.path.join(AQUI, "cloudflared.exe" if os.name == "nt" else "cloudflared")
    print(f"  · baixando cloudflared ({binario})…")
    try:
        with urllib.request.urlopen(url, timeout=60) as r, open(destino, "wb") as f:
            shutil.copyfileobj(r, f)
    except Exception as e:
        print(f"  · o download não foi: {e}")
        return None
    if os.name != "nt":
        os.chmod(destino, os.stat(destino).st_mode | stat.S_IEXEC)
    print("  · baixado.")
    return destino


PADRAO_CF = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
PADRAO_LR = re.compile(r"https://[a-z0-9-]+\.lhr\.life|https://[a-z0-9.-]+\.localhost\.run")


def tentar_cloudflared(porta, caminho, achou):
    proc = subprocess.Popen(
        [caminho, "tunnel", "--url", f"http://localhost:{porta}", "--no-autoupdate"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    return _vigiar(proc, PADRAO_CF, achou, "cloudflared")


def tentar_ssh(porta, achou):
    """localhost.run pelo ssh: não instala nada. Windows 10+, macOS e Linux já
    têm ssh. A chave do servidor é aceita automaticamente porque o serviço é
    público e anônimo — não há segredo trafegando na autenticação."""
    if not shutil.which("ssh"):
        print("  · esta máquina não tem ssh")
        return None
    proc = subprocess.Popen(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null"
         if os.name != "nt" else "NUL", "-o", "ServerAliveInterval=30",
         "-R", f"80:localhost:{porta}", "nokey@localhost.run"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    return _vigiar(proc, PADRAO_LR, achou, "localhost.run")


# Erros que NÃO adianta esperar: quando aparece um destes, o túnel já morreu.
# Sem isto o programa fica 45 s parado olhando para uma falha que ele já leu no
# primeiro segundo — e quem está esperando acha que travou.
FATAIS = re.compile(
    r"not in allowlist|failed with status \d|connection refused|no such host|"
    r"permission denied|could not resolve|network is unreachable|"
    r"failed to request quick tunnel|remote port forwarding failed", re.I)


def _vigiar(proc, padrao, achou, nome, espera=45):
    """Lê a saída do túnel até aparecer um endereço. Guarda as últimas linhas
    para poder MOSTRAR o motivo quando não aparece — um túnel que falha calado
    é a pior parte deste trabalho."""
    ultimas = []
    morreu = threading.Event()

    def ler():
        for linha in proc.stdout:
            ultimas.append(linha.rstrip())
            del ultimas[:-12]
            m = padrao.search(linha)
            if m and not achou["url"]:
                achou["url"] = m.group(0)
                achou["via"] = nome
                return
            if FATAIS.search(linha):
                morreu.set()
                return

    t = threading.Thread(target=ler, daemon=True)
    t.start()
    limite = time.time() + espera
    while time.time() < limite and not achou["url"] and not morreu.is_set():
        if proc.poll() is not None:
            break
        time.sleep(0.3)
    if achou["url"]:
        return proc
    proc.terminate()
    print(f"  · {nome} não abriu" + ("." if morreu.is_set() else f" em {espera}s."))
    for l in ultimas[-6:]:
        if l.strip():
            print("      " + l)
    return None


def main():
    p = argparse.ArgumentParser(description="Abre o ELASE e publica o endereço")
    p.add_argument("--porta", type=int, default=8000)
    p.add_argument("--rede", action="store_true",
                   help="só a rede local, sem tentar túnel")
    p.add_argument("--db", default=banco.CAMINHO)
    args = p.parse_args()

    banco.criar(args.db)
    srv = ThreadingHTTPServer(("0.0.0.0", args.porta), elase.Handler)
    srv.caminho_db = args.db
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    with banco.conectar(args.db) as con:
        cfg = banco.config(con)
        n = con.execute("SELECT COUNT(*) c FROM atletas WHERE status='Ativo'").fetchone()["c"]

    ip = ip_local()
    caixa(f"ELASE · {cfg['equipe']} · {cfg['categoria']}", [
        f"elenco: {n} atleta(s) ativo(s)",
        f"macrociclo desde {cfg['macro_inicio']}",
        f"PIN do preparador: {cfg['pin_treinador']}",
        "",
        "NESTE COMPUTADOR:",
        f"   http://localhost:{args.porta}",
        "",
        "NA REDE LOCAL (mesmo wi-fi) — funciona sem internet:",
        f"   http://{ip}:{args.porta}" if ip else "   (não achei o IP desta máquina)",
    ])

    proc = None
    if not args.rede:
        print("  Procurando um endereço público para os atletas de fora da rede…\n")
        achou = {"url": None, "via": None}
        cf = achar_cloudflared()
        if cf:
            print(f"  · usando o cloudflared de {cf}")
        else:
            cf = baixar_cloudflared()
        # uma tentativa por binário, e só uma: com a detecção de erro fatal,
        # repetir o mesmo cloudflared contra a mesma rede dá o mesmo resultado
        # e só faz quem está esperando ver a falha duas vezes
        if cf:
            proc = tentar_cloudflared(args.porta, cf, achou)
        if not proc and not achou["url"]:
            print("  · tentando pelo ssh (localhost.run), que não instala nada")
            proc = tentar_ssh(args.porta, achou)

        if achou["url"]:
            caixa("ENDEREÇO PÚBLICO — MANDE ESTE PARA OS ATLETAS", [
                achou["url"],
                "",
                f"(via {achou['via']}; vale enquanto este programa estiver aberto)",
                "",
                "Cadastro direto:",
                achou["url"] + "/#cadastro",
            ], "#")
        else:
            caixa("NÃO CONSEGUI ABRIR O TÚNEL", [
                "Isso quase sempre é uma destas três coisas:",
                "",
                "1. A rede bloqueia (wi-fi de clube e de empresa costumam).",
                "   Teste no 4G do celular, compartilhando a internet.",
                "2. Antivírus ou firewall barrou o cloudflared.",
                "   Libere, ou use a rede local abaixo.",
                "3. Sem internet de saída nesta máquina.",
                "",
                "A REDE LOCAL ACIMA CONTINUA FUNCIONANDO e é o suficiente",
                "para cadastrar o elenco inteiro no ginásio. Não precisa de",
                "túnel nenhum — basta o atleta estar no mesmo wi-fi.",
            ], "!")

    print("  Ctrl+C para parar.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  Parando…")
        if proc:
            proc.terminate()
        srv.shutdown()
        print("  Parado.\n")


if __name__ == "__main__":
    main()
