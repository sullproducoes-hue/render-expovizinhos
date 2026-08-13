#!/usr/bin/env python3
"""
Extrai metadados, quadros de triagem e quadros densos do footage de drone da
AGROSHOW 2026.

Este script roda NA MAQUINA DE QUEM TEM OS VIDEOS, nao no ambiente remoto: os
arquivos passam de 3 GB cada, o proxy do ambiente bloqueia o dominio do Drive e
nao ha disco nem ffmpeg la. Aqui e onde o material vira algo que cabe no chat.

Precisa de ffmpeg no PATH. ffprobe e exiftool sao opcionais: sem ffprobe a
duracao sai da propria saida do ffmpeg, e o exiftool so ajuda na leitura dos
atomos proprietarios da DJI. No Windows, use a build completa
(winget install Gyan.FFmpeg) -- a enxuta nao tem drawtext e as folhas saem sem
o timecode gravado no quadro.

Ordem recomendada de uso:

    # 1. o mais barato e o de maior retorno: existe telemetria embutida?
    python3 scripts/extrair_quadros.py --metadados ^
        --pasta "E:\Projetos todos\Mapa - agroshow\Brutos Expo"

    # 2. triagem: um contact sheet por video, 10 quadros com timecode
    python3 scripts/extrair_quadros.py --triagem ^
        --pasta "E:\Projetos todos\Mapa - agroshow\Brutos Expo"

    # 3. so nos videos aprovados, quadros densos em resolucao cheia
    python3 scripts/extrair_quadros.py --densa DJI_0960-015.MP4 --intervalo 2 ^
        --pasta "E:\Projetos todos\Mapa - agroshow\Brutos Expo"

Anexe no chat: os .json e .srt do passo 1 (sao KB), os contact sheets do passo
2, e depois as folhas do passo 3 em lotes.
"""

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

EXTENSOES = {".mp4", ".mov", ".mkv", ".m4v"}

# Margem descartada no inicio e no fim de cada video. Decolagem, pouso e o
# corte final quase nunca servem, e gastam duas das dez amostras da triagem.
MARGEM = 0.03

CELULA = (960, 540)      # tamanho de cada quadro dentro do contact sheet
COLUNAS_TRIAGEM = 5      # 5 x 2 = os 10 quadros pedidos, em uma folha so
LOTE_DENSO = 12          # 4 x 3 por folha na passada densa
LARGURA_FOLHA = 4200     # px -- teto de largura da folha montada


def existe(programa):
    return shutil.which(programa) is not None


class SemPrograma:
    """Resultado falso para quando o programa nem existe no PATH."""
    returncode = 127
    stdout = ""
    stderr = "programa ausente"


def rodar(cmd, capturar=True):
    # Programa ausente nao pode derrubar a rodada: sao 186 arquivos, e parar
    # tudo por causa de um ffprobe que nao veio no pacote e desperdicio.
    try:
        return subprocess.run(cmd, capture_output=capturar, text=True,
                              encoding="utf-8", errors="replace")
    except (FileNotFoundError, OSError):
        return SemPrograma()


def tem_drawtext():
    """O ffmpeg desta maquina sabe gravar texto no quadro?

    drawtext depende de libfreetype, que falta em build enxuta. Sem ele a
    triagem ainda sai, mas sem timecode gravado no pixel -- e o timecode e o
    que permite pedir 'o trecho de 01:23 do DJI_0960' depois. Melhor avisar no
    arranque do que descobrir com 186 folhas prontas.
    """
    saida = rodar(["ffmpeg", "-hide_banner", "-filters"])
    return " drawtext " in (saida.stdout or "")


def videos_da_pasta(pasta):
    return sorted(p for p in Path(pasta).iterdir()
                  if p.suffix.lower() in EXTENSOES)


def sondar_por_ffmpeg(video):
    """Duracao e resolucao lidas da saida do proprio ffmpeg.

    Rede de seguranca para instalacao sem ffprobe -- acontece em build enxuto e
    em pacote de editor. Le a linha 'Duration:' e a linha do stream de video.
    """
    saida = rodar(["ffmpeg", "-hide_banner", "-i", str(video)])
    texto = (saida.stderr or "") + (saida.stdout or "")
    duracao, largura, altura, fps = 0.0, None, None, 0.0
    for linha in texto.splitlines():
        linha = linha.strip()
        if linha.startswith("Duration:"):
            relogio = linha.split("Duration:")[1].split(",")[0].strip()
            try:
                h, m, s = relogio.split(":")
                duracao = int(h) * 3600 + int(m) * 60 + float(s)
            except ValueError:
                pass
        if "Video:" in linha:
            for pedaco in linha.split(","):
                pedaco = pedaco.strip()
                if "x" in pedaco and pedaco.split("x")[0].strip().isdigit():
                    try:
                        l, a = pedaco.split()[0].split("x")
                        largura, altura = int(l), int(a)
                    except ValueError:
                        pass
                if pedaco.endswith("fps"):
                    try:
                        fps = float(pedaco.split()[0])
                    except ValueError:
                        pass
    if not duracao or largura is None:
        return None
    return {"duracao": duracao, "largura": largura, "altura": altura,
            "fps": fps, "bruto": {}}


def sondar(video):
    """Duracao, resolucao e fps. Devolve None se nem ffmpeg leu o arquivo."""
    if not existe("ffprobe"):
        return sondar_por_ffmpeg(video)
    saida = rodar([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(video),
    ])
    if saida.returncode != 0:
        return sondar_por_ffmpeg(video)
    dados = json.loads(saida.stdout)
    video_stream = next((s for s in dados.get("streams", [])
                         if s.get("codec_type") == "video"), None)
    if video_stream is None:
        return None
    fps = video_stream.get("r_frame_rate", "0/1")
    num, _, den = fps.partition("/")
    try:
        fps = float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        fps = 0.0
    return {
        "duracao": float(dados.get("format", {}).get("duration", 0.0)),
        "largura": video_stream.get("width"),
        "altura": video_stream.get("height"),
        "fps": fps,
        "bruto": dados,
    }


# --------------------------------------------------------------------------
# 1. Metadados e telemetria

def extrair_metadados(video, destino, seco=False):
    """Despeja tudo que for texto: ffprobe, faixa de legenda e atomos DJI.

    A DJI grava os dados de voo dentro do proprio MP4 -- uma faixa de legenda
    com GPS, altitude relativa e absoluta, distancia focal e exposicao, quadro a
    quadro. Isso pesa alguns KB e responde por medida o que os quadros so
    responderiam por proporcao: a cota de cada patamar e a escala do recinto.
    """
    destino.mkdir(parents=True, exist_ok=True)
    achados = []

    if existe("ffprobe"):
        alvo_json = destino / f"{video.stem}.ffprobe.json"
        cmd = ["ffprobe", "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", "-show_chapters", str(video)]
        if seco:
            print("  " + " ".join(cmd))
        else:
            saida = rodar(cmd)
            if saida.returncode == 0:
                alvo_json.write_text(saida.stdout, encoding="utf-8")
                achados.append(alvo_json.name)
    else:
        # Sem ffprobe, o proprio ffmpeg descreve o arquivo na saida de erro.
        alvo_txt = destino / f"{video.stem}.ffmpeg.txt"
        cmd = ["ffmpeg", "-hide_banner", "-i", str(video)]
        if seco:
            print("  " + " ".join(cmd))
        else:
            saida = rodar(cmd)
            texto = (saida.stderr or "") + (saida.stdout or "")
            if texto.strip():
                alvo_txt.write_text(texto, encoding="utf-8")
                achados.append(alvo_txt.name)

    # Faixa de legenda embutida: e onde mora a telemetria nos DJI recentes.
    alvo_srt = destino / f"{video.stem}.telemetria.srt"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(video),
           "-map", "0:s:0", str(alvo_srt)]
    if seco:
        print("  " + " ".join(cmd))
    else:
        rodar(cmd)
        if alvo_srt.exists() and alvo_srt.stat().st_size > 0:
            achados.append(alvo_srt.name)
        elif alvo_srt.exists():
            alvo_srt.unlink()

    if existe("exiftool"):
        alvo_exif = destino / f"{video.stem}.exiftool.txt"
        cmd = ["exiftool", "-a", "-u", "-g1", str(video)]
        if seco:
            print("  " + " ".join(cmd))
        else:
            saida = rodar(cmd)
            if saida.returncode == 0:
                alvo_exif.write_text(saida.stdout, encoding="utf-8")
                achados.append(alvo_exif.name)

    return achados


# --------------------------------------------------------------------------
# 2 e 3. Quadros e contact sheets

def timecode(segundos):
    m, s = divmod(int(segundos), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def escapar_texto(txt):
    """Escapa o texto para o filtro drawtext do ffmpeg."""
    return txt.replace("\\", "\\\\").replace(":", "\\:").replace("'", "")


def extrair_quadro(video, instante, alvo, largura=None, rotulo=None,
                   seco=False):
    """Um quadro no instante dado. -ss antes do -i faz a busca ser rapida."""
    filtros = []
    if largura:
        filtros.append(f"scale={largura}:-2")
    if rotulo:
        # O rotulo fica gravado no pixel de proposito: e o que me deixa pedir
        # "o trecho de 01:23 do DJI_0960" em vez de descrever o quadro.
        filtros.append(
            "drawtext=text='" + escapar_texto(rotulo) + "'"
            ":x=16:y=h-th-16:fontsize=28:fontcolor=white"
            ":box=1:boxcolor=black@0.55:boxborderw=8"
        )
    def montar(lista):
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{instante:.3f}",
               "-i", str(video), "-frames:v", "1"]
        if lista:
            cmd += ["-vf", ",".join(lista)]
        return cmd + ["-q:v", "2", str(alvo)]

    if seco:
        print("  " + " ".join(montar(filtros)))
        return True
    if rodar(montar(filtros)).returncode == 0:
        return True
    # Sem fonte instalada o drawtext falha -- acontece em ffmpeg de Windows.
    # Melhor o quadro sair sem rotulo do que a triagem parar.
    sem_rotulo = [f for f in filtros if not f.startswith("drawtext")]
    return rodar(montar(sem_rotulo)).returncode == 0


def montar_folha(padrao, inicio, quantidade, alvo, colunas, seco=False):
    """Junta os quadros numa folha unica.

    Uma folha por video em vez de dez arquivos soltos: e o que permite triar
    186 fitas numa conversa so, sem estourar o contexto de quem revisa.

    O tile monta a grade a partir de UMA sequencia de imagens, nao de varias
    entradas separadas -- por isso a entrada e o padrao numerado dos quadros.
    Passar dez arquivos como dez '-i' devolve a primeira celula preenchida e o
    resto preto.
    """
    if quantidade <= 0:
        return False
    linhas = math.ceil(quantidade / colunas)
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-start_number", str(inicio), "-i", str(padrao),
           # Teto de largura: a folha densa com celulas de 1920 passaria de
           # 7.000 px e viraria anexo pesado sem ganho de leitura.
           "-vf", f"tile={colunas}x{linhas}:margin=8:padding=8:color=black,"
                  f"scale='min({LARGURA_FOLHA},iw)':-2",
           "-frames:v", "1", "-q:v", "3", str(alvo)]
    if seco:
        print("  " + " ".join(cmd))
        return True
    return rodar(cmd).returncode == 0


def instantes(duracao, quantidade):
    """Instantes igualmente espacados, fora das margens de decolagem e corte."""
    inicio = duracao * MARGEM
    fim = duracao * (1.0 - MARGEM)
    if quantidade == 1:
        return [(inicio + fim) / 2.0]
    passo = (fim - inicio) / (quantidade - 1)
    return [inicio + passo * i for i in range(quantidade)]


def triagem(video, destino, quantidade, seco=False, pular_prontos=True):
    folha_pronta = destino / f"FOLHA_{video.stem}.jpg"
    if pular_prontos and folha_pronta.exists():
        # O envio sao 186 arquivos e leva horas. Poder rodar o script varias
        # vezes, conforme os videos chegam, sem refazer o que ja saiu, e o que
        # torna a triagem incremental em vez de uma espera unica.
        return {"video": video.name, "duracao": 0.0, "resolucao": "-",
                "fps": 0, "folha": folha_pronta.name, "quadros": quantidade,
                "pulado": True}
    info = sondar(video)
    if info is None:
        print(f"  ! ffprobe nao leu {video.name} -- upload incompleto?")
        return None
    destino.mkdir(parents=True, exist_ok=True)

    quadros = []
    for i, t in enumerate(instantes(info["duracao"], quantidade)):
        alvo = destino / f"{video.stem}_t{i:02d}.jpg"
        rotulo = f"{video.name}  {timecode(t)}"
        if extrair_quadro(video, t, alvo, CELULA[0], rotulo, seco):
            quadros.append(alvo)

    folha = destino / f"FOLHA_{video.stem}.jpg"
    montar_folha(destino / f"{video.stem}_t%02d.jpg", 0, len(quadros) or
                 quantidade, folha, COLUNAS_TRIAGEM, seco)
    return {
        "video": video.name,
        "duracao": info["duracao"],
        "resolucao": f"{info['largura']}x{info['altura']}",
        "fps": round(info["fps"], 2),
        "folha": folha.name,
        "quadros": len(quadros),
    }


def passada_densa(video, destino, intervalo, largura, seco=False):
    info = sondar(video)
    if info is None:
        print(f"  ! ffprobe nao leu {video.name}")
        return None
    destino.mkdir(parents=True, exist_ok=True)

    total = max(1, int(info["duracao"] * (1.0 - 2 * MARGEM) / intervalo))
    quadros = []
    for i, t in enumerate(instantes(info["duracao"], total)):
        alvo = destino / f"{video.stem}_d{i:04d}.jpg"
        rotulo = f"{video.name}  {timecode(t)}"
        if extrair_quadro(video, t, alvo, largura, rotulo, seco):
            quadros.append(alvo)

    # Folhas em lote, para revisar muito quadro sem abrir um por um.
    folhas = []
    padrao = destino / f"{video.stem}_d%04d.jpg"
    total_quadros = len(quadros) or total
    for i in range(0, total_quadros, LOTE_DENSO):
        lote = min(LOTE_DENSO, total_quadros - i)
        folha = destino / f"FOLHA_{video.stem}_lote{i // LOTE_DENSO:02d}.jpg"
        if montar_folha(padrao, i, lote, folha, 4, seco):
            folhas.append(folha.name)
    return {"video": video.name, "quadros": len(quadros), "folhas": folhas}


# --------------------------------------------------------------------------

PASTA_PADRAO = r"E:\Projetos todos\Mapa - agroshow\Brutos Expo"


def perguntar(args):
    """Modo de duplo clique: pergunta o essencial e segue.

    Quem tem os videos nao precisa decorar linha de comando para entregar os
    quadros. As respostas caem nos mesmos campos que as opcoes de linha.
    """
    print("=" * 62)
    print("  TRIAGEM DO FOOTAGE DE DRONE -- AGROSHOW 2026")
    print("=" * 62)
    print()
    print(f"Pasta dos videos [{PASTA_PADRAO}]:")
    resposta = input("> ").strip().strip('"')
    args.pasta = resposta or PASTA_PADRAO

    print()
    print("O que fazer?")
    print("  1) Metadados e telemetria  -- rapido, e o de maior retorno")
    print("  2) Triagem, 10 quadros por video")
    print("  3) Os dois  (recomendado)")
    escolha = input("> [3] ").strip() or "3"
    args.metadados = escolha in ("1", "3")
    args.triagem = escolha in ("2", "3")

    # A saida vai para junto dos videos, e nao para a pasta de onde o script
    # foi aberto -- senao o resultado se perde na pasta de downloads.
    args.saida = str(Path(args.pasta) / "_triagem")
    print(f"\nSaida: {args.saida}\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pasta", default=".", help="pasta com os videos")
    ap.add_argument("--saida", default="triagem", help="pasta de saida")
    ap.add_argument("--metadados", action="store_true",
                    help="despeja ffprobe, telemetria embutida e atomos DJI")
    ap.add_argument("--triagem", action="store_true",
                    help="um contact sheet por video")
    ap.add_argument("--quadros", type=int, default=10,
                    help="quadros por video na triagem (padrao 10)")
    ap.add_argument("--densa", default=None,
                    help="nome do video aprovado para a passada densa")
    ap.add_argument("--intervalo", type=float, default=2.0,
                    help="segundos entre quadros na passada densa")
    ap.add_argument("--largura", type=int, default=1920,
                    help="largura dos quadros da passada densa")
    ap.add_argument("--refazer", action="store_true",
                    help="refaz folhas ja geradas (padrao: pula)")
    ap.add_argument("--dry-run", action="store_true",
                    help="imprime os comandos sem executar")
    args = ap.parse_args()

    # Duplo clique no Windows nao passa argumento nenhum: sem isto a janela
    # abre, imprime uma linha de ajuda e fecha antes de alguem ler.
    interativo = len(sys.argv) == 1
    if interativo:
        perguntar(args)

    if not existe("ffmpeg"):
        print("ERRO: ffmpeg nao esta no PATH.")
        print("  Windows: winget install Gyan.FFmpeg")
        print("  macOS:   brew install ffmpeg")
        print("  Linux:   sudo apt install ffmpeg")
        return 1
    if not existe("ffprobe"):
        print("aviso: ffprobe ausente -- duracao e resolucao saem do ffmpeg")
    if (args.triagem or args.densa) and not tem_drawtext():
        print("aviso: este ffmpeg nao tem drawtext (falta libfreetype).")
        print("       As folhas saem sem timecode gravado no quadro.")
        print("       Windows: winget install Gyan.FFmpeg (build completa)")
    print()

    pasta = Path(args.pasta)
    if not pasta.is_dir():
        print(f"ERRO: pasta nao encontrada: {pasta}")
        return 1
    saida = Path(args.saida)

    if not (args.metadados or args.triagem or args.densa):
        print("Escolha ao menos um modo: --metadados, --triagem ou --densa")
        return 1

    if args.densa:
        video = pasta / args.densa
        if not video.exists():
            print(f"ERRO: video nao encontrado: {video}")
            return 1
        print(f"passada densa em {video.name}, um quadro a cada "
              f"{args.intervalo:g} s")
        r = passada_densa(video, saida / video.stem, args.intervalo,
                          args.largura, args.dry_run)
        if r:
            print(f"  {r['quadros']} quadros em {len(r['folhas'])} folhas")
            print(f"\nAnexe no chat as folhas de {saida / video.stem}, "
                  "em lotes.")
        return 0

    videos = videos_da_pasta(pasta)
    if not videos:
        print(f"Nenhum video em {pasta}")
        return 1
    print(f"{len(videos)} videos em {pasta}\n")

    if args.metadados:
        print("metadados e telemetria:")
        com_telemetria = []
        for v in videos:
            achados = extrair_metadados(v, saida / "metadados", args.dry_run)
            tem_srt = any(a.endswith(".srt") for a in achados)
            if tem_srt:
                com_telemetria.append(v.name)
            marca = "TELEMETRIA" if tem_srt else "-"
            print(f"  {v.name:<32} {marca}")
        print(f"\n  {len(com_telemetria)} de {len(videos)} com telemetria "
              "embutida")
        if com_telemetria:
            print("  Anexe os .srt no chat: sao KB e resolvem as cotas dos "
                  "patamares por medida.")
        else:
            print("  Sem telemetria embutida. Anexe os .ffprobe.json mesmo "
                  "assim -- resolucao, fps e codec ja orientam a triagem.")

    if args.triagem:
        print(f"\ntriagem, {args.quadros} quadros por video:")
        fichas = []
        for v in videos:
            ficha = triagem(v, saida / v.stem, args.quadros, args.dry_run,
                            pular_prontos=not args.refazer)
            if ficha:
                fichas.append(ficha)
                if ficha.get("pulado"):
                    print(f"  {ficha['video']:<32} {'ja pronto':>10}")
                else:
                    print(f"  {ficha['video']:<32} {ficha['resolucao']:>10}  "
                          f"{ficha['duracao']:6.1f}s  -> {ficha['folha']}")
        indice = saida / "triagem.json"
        if not args.dry_run:
            indice.write_text(json.dumps(fichas, indent=2, ensure_ascii=False),
                              encoding="utf-8")
        print(f"\n  {len(fichas)} folhas em {saida}")
        print("  Anexe no chat todas as FOLHA_*.jpg e o triagem.json.")

    return 0


if __name__ == "__main__":
    codigo = main()
    if len(sys.argv) == 1:
        # Janela de duplo clique fecha sozinha; sem a pausa ninguem le o
        # resultado nem o aviso de erro.
        try:
            input("\nPronto. Enter para fechar.")
        except EOFError:
            pass
    sys.exit(codigo)
