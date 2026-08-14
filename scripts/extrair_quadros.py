#!/usr/bin/env python3
"""Extrai quadros de referencia de videos e monta folhas de contato.

Uso interativo (o normal):

    python extrair_quadros.py --pasta "E:/AGROSHOW/footage"

Ele lista os videos da pasta com a duracao de cada um, voce escolhe quais
quer pelos numeros e informa quantos quadros tirar de cada video. Enter
aceita o padrao de 30.

Uso direto, sem perguntas:

    python extrair_quadros.py --videos abertura.mp4 rodeio.mp4 --quadros 40 60

Saida:

    extracao/
      abertura/
        quadros/   q001_00-00-04.jpg ...
        folhas/    contato-01.jpg ...
      rodeio/
        ...
      INDICE.md

Requisitos: ffmpeg e ffprobe no PATH. Pillow e numpy sao opcionais — com
eles as folhas saem com etiqueta de timecode e a opcao --nitidez funciona.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXTENSOES = {
    ".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm",
    ".mts", ".m2ts", ".wmv", ".mpg", ".mpeg",
}

PADRAO_QUADROS = 30
COLUNAS_FOLHA = 6
LINHAS_FOLHA = 5
LARGURA_MINIATURA = 400
JANELA_NITIDEZ = 0.4  # segundos para cada lado, ao procurar o quadro mais nitido


# ---------------------------------------------------------------- utilidades

def checar_ferramentas():
    faltando = [f for f in ("ffmpeg", "ffprobe") if shutil.which(f) is None]
    if faltando:
        sys.exit(
            f"Nao encontrei no PATH: {', '.join(faltando)}.\n"
            "Instale o ffmpeg (https://ffmpeg.org/download.html) e rode de novo."
        )


def duracao(video: Path) -> float:
    saida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
        capture_output=True, text=True,
    )
    try:
        return float(saida.stdout.strip())
    except ValueError:
        return 0.0


def tc(segundos: float) -> str:
    """Timecode com hifens — dois pontos nao sao permitidos em nome de arquivo."""
    s = int(segundos)
    return f"{s // 3600:02d}-{(s % 3600) // 60:02d}-{s % 60:02d}"


def tc_legivel(segundos: float) -> str:
    return tc(segundos).replace("-", ":")


def nome_limpo(texto: str) -> str:
    return "".join(c if c.isalnum() or c in "-_ " else "_" for c in texto).strip()


# ------------------------------------------------------------------- escolha

def listar_videos(pasta: Path) -> list[Path]:
    return sorted(
        (p for p in pasta.iterdir() if p.is_file() and p.suffix.lower() in EXTENSOES),
        key=lambda p: p.name.lower(),
    )


def escolher_videos(pasta: Path) -> list[Path]:
    videos = listar_videos(pasta)
    if not videos:
        sys.exit(f"Nenhum video encontrado em {pasta}")

    print(f"\nVideos em {pasta}:\n")
    duracoes = {}
    for i, v in enumerate(videos, 1):
        d = duracao(v)
        duracoes[v] = d
        print(f"  [{i:2d}]  {tc_legivel(d)}  {v.name}")

    print("\nQuais quer usar? Numeros separados por virgula (ex: 1,3,5),")
    print("intervalos (ex: 2-6), ou 'todos'.")
    resposta = input("> ").strip().lower()

    if resposta in ("todos", "todas", "all", ""):
        return videos

    escolhidos = []
    for parte in resposta.replace(" ", "").split(","):
        if not parte:
            continue
        if "-" in parte:
            try:
                ini, fim = (int(x) for x in parte.split("-", 1))
            except ValueError:
                print(f"  ignorando '{parte}'")
                continue
            escolhidos.extend(range(ini, fim + 1))
        else:
            try:
                escolhidos.append(int(parte))
            except ValueError:
                print(f"  ignorando '{parte}'")

    selecao = []
    for n in escolhidos:
        if 1 <= n <= len(videos) and videos[n - 1] not in selecao:
            selecao.append(videos[n - 1])
        elif not 1 <= n <= len(videos):
            print(f"  numero fora da lista: {n}")

    if not selecao:
        sys.exit("Nenhum video selecionado.")
    return selecao


def perguntar_quantidade(video: Path, dur: float) -> int:
    while True:
        resposta = input(
            f"  Quantos quadros de '{video.name}' ({tc_legivel(dur)})? "
            f"[{PADRAO_QUADROS}] "
        ).strip()
        if not resposta:
            return PADRAO_QUADROS
        try:
            n = int(resposta)
        except ValueError:
            print("    Digite um numero.")
            continue
        if n < 1:
            print("    Precisa ser pelo menos 1.")
            continue
        if n < PADRAO_QUADROS:
            print(f"    Aviso: menos de {PADRAO_QUADROS} quadros cobre pouco do video.")
        return n


# ---------------------------------------------------------------- extracao

def marcas(dur: float, n: int) -> list[float]:
    """Instantes distribuidos pelo video, com folga nas pontas.

    Fade de entrada e de saida costumam ser preto — a margem evita gastar
    quadro com eles.
    """
    margem = min(1.0, dur * 0.02)
    util = max(dur - 2 * margem, 0.0)
    if n == 1 or util == 0:
        return [margem + util / 2]
    return [margem + util * i / (n - 1) for i in range(n)]


def extrair_quadro(video: Path, t: float, destino: Path, qualidade: int):
    """Devolve (deu_certo, mensagem_de_erro_do_ffmpeg)."""
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{t:.3f}",
           "-i", str(video), "-frames:v", "1"]
    if destino.suffix.lower() in (".jpg", ".jpeg"):
        cmd += ["-q:v", str(qualidade)]
    cmd.append(str(destino))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    except OSError as e:
        return False, str(e)
    if destino.exists() and destino.stat().st_size > 0:
        return True, ""
    return False, (r.stderr or "").strip() or "ffmpeg nao gravou o arquivo"


def nitidez(caminho: Path):
    """Variancia do laplaciano. Quanto maior, menos borrado."""
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(caminho) as img:
            img = img.convert("L")
            largura = 512
            altura = max(1, int(img.height * largura / img.width))
            a = np.asarray(img.resize((largura, altura)), dtype=np.float32)
    except Exception:
        return None
    lap = (a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:]
           - 4 * a[1:-1, 1:-1])
    return float(lap.var())


def extrair_mais_nitido(video: Path, t: float, destino: Path, qualidade: int,
                        dur: float) -> bool:
    """Testa tres instantes em volta de t e guarda o menos borrado.

    Footage de drone e de mao entrega muito quadro com motion blur. Como
    a imagem aqui vira referencia visual, borrado nao serve.
    """
    candidatos = [t - JANELA_NITIDEZ, t, t + JANELA_NITIDEZ]
    candidatos = [max(0.0, min(c, max(dur - 0.1, 0.0))) for c in candidatos]

    melhor_valor, erro = None, ""
    with tempfile.TemporaryDirectory() as tmp:
        for i, c in enumerate(candidatos):
            provisorio = Path(tmp) / f"c{i}{destino.suffix}"
            ok, erro = extrair_quadro(video, c, provisorio, qualidade)
            if not ok:
                continue
            valor = nitidez(provisorio)
            if valor is None:  # sem Pillow/numpy — fica com o instante do meio
                return extrair_quadro(video, t, destino, qualidade)
            if melhor_valor is None or valor > melhor_valor:
                melhor_valor = valor
                shutil.copy(provisorio, destino)
    if destino.exists() and destino.stat().st_size > 0:
        return True, ""
    return False, erro


def extrair_do_video(video: Path, quantidade: int, pasta_saida: Path,
                     extensao: str, qualidade: int, usar_nitidez: bool):
    dur = duracao(video)
    if dur <= 0:
        print(f"  ! {video.name}: nao consegui ler a duracao, pulando")
        return []

    pasta_quadros = pasta_saida / "quadros"
    pasta_quadros.mkdir(parents=True, exist_ok=True)

    resultados, falhas, primeiro_erro = [], 0, ""
    instantes = marcas(dur, quantidade)
    for i, t in enumerate(instantes, 1):
        destino = pasta_quadros / f"q{i:03d}_{tc(t)}{extensao}"
        if usar_nitidez:
            ok, erro = extrair_mais_nitido(video, t, destino, qualidade, dur)
        else:
            ok, erro = extrair_quadro(video, t, destino, qualidade)
        if ok:
            resultados.append((destino, t))
        else:
            falhas += 1
            primeiro_erro = primeiro_erro or erro
            if falhas == 3 and not resultados:
                # Tres falhas seguidas logo de cara: nao adianta insistir nas
                # outras dezenas. Mostra o que o ffmpeg reclamou e para.
                break
        print(f"\r  {video.name}: {len(resultados)}/{quantidade} quadros",
              end="", flush=True)
    print()

    if falhas:
        print(f"  ! {falhas} quadro(s) falharam em {video.name}")
        if primeiro_erro:
            print(f"    ffmpeg disse: {primeiro_erro.splitlines()[0]}")
        if not resultados:
            print("    Nenhum quadro saiu. Codec sem suporte, arquivo corrompido")
            print("    ou caminho inacessivel — confira abrindo o video no player.")
    return resultados


# ------------------------------------------------------------ folha de contato

def fonte(tamanho: int):
    from PIL import ImageFont
    for caminho in (
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ):
        if Path(caminho).exists():
            try:
                return ImageFont.truetype(caminho, tamanho)
            except OSError:
                pass
    return ImageFont.load_default()


def folhas_com_pillow(quadros, pasta_folhas: Path, titulo: str) -> int:
    from PIL import Image, ImageDraw

    por_folha = COLUNAS_FOLHA * LINHAS_FOLHA
    gutter, etiqueta, topo = 10, 26, 46
    paginas = 0

    for pagina, inicio in enumerate(range(0, len(quadros), por_folha), 1):
        lote = quadros[inicio:inicio + por_folha]

        with Image.open(lote[0][0]) as amostra:
            proporcao = amostra.height / amostra.width
        larg_min = LARGURA_MINIATURA
        alt_min = int(larg_min * proporcao)

        largura = COLUNAS_FOLHA * larg_min + (COLUNAS_FOLHA + 1) * gutter
        linhas = (len(lote) + COLUNAS_FOLHA - 1) // COLUNAS_FOLHA
        altura = topo + linhas * (alt_min + etiqueta + gutter) + gutter

        folha = Image.new("RGB", (largura, altura), (18, 18, 18))
        desenho = ImageDraw.Draw(folha)
        desenho.text((gutter, 14), f"{titulo}  ·  folha {pagina}",
                     fill=(240, 240, 240), font=fonte(20))

        for i, (caminho, t) in enumerate(lote):
            col, lin = i % COLUNAS_FOLHA, i // COLUNAS_FOLHA
            x = gutter + col * (larg_min + gutter)
            y = topo + lin * (alt_min + etiqueta + gutter)
            with Image.open(caminho) as img:
                folha.paste(img.resize((larg_min, alt_min)), (x, y))
            desenho.text(
                (x + 2, y + alt_min + 5),
                f"{caminho.stem.split('_')[0]}  {tc_legivel(t)}",
                fill=(190, 190, 190), font=fonte(15),
            )

        folha.save(pasta_folhas / f"contato-{pagina:02d}.jpg", quality=88)
        paginas = pagina

    return paginas


def folhas_com_ffmpeg(quadros, pasta_folhas: Path) -> int:
    """Alternativa sem Pillow. Sai sem etiqueta de timecode."""
    por_folha = COLUNAS_FOLHA * LINHAS_FOLHA
    paginas = 0
    for pagina, inicio in enumerate(range(0, len(quadros), por_folha), 1):
        lote = quadros[inicio:inicio + por_folha]
        with tempfile.TemporaryDirectory() as tmp:
            for i, (caminho, _) in enumerate(lote, 1):
                shutil.copy(caminho, Path(tmp) / f"s{i:03d}{caminho.suffix}")
            padrao = str(Path(tmp) / f"s%03d{lote[0][0].suffix}")
            subprocess.run(
                ["ffmpeg", "-nostdin", "-v", "error", "-y",
                 "-i", padrao,
                 "-vf", f"scale={LARGURA_MINIATURA}:-1,"
                        f"tile={COLUNAS_FOLHA}x{LINHAS_FOLHA}:padding=8:margin=8",
                 "-frames:v", "1",
                 str(pasta_folhas / f"contato-{pagina:02d}.jpg")],
                capture_output=True,
            )
        paginas = pagina
    return paginas


def montar_folhas(quadros, pasta_folhas: Path, titulo: str) -> int:
    if not quadros:
        return 0
    pasta_folhas.mkdir(parents=True, exist_ok=True)
    try:
        import PIL  # noqa: F401
    except ImportError:
        return folhas_com_ffmpeg(quadros, pasta_folhas)
    return folhas_com_pillow(quadros, pasta_folhas, titulo)


# -------------------------------------------------------------------- indice

def escrever_indice(saida: Path, relatorio):
    linhas = [
        "# Quadros extraidos",
        "",
        "Gerado por `scripts/extrair_quadros.py`.",
        "",
        "A coluna **Bloco** esta vazia de proposito: preencha com o numero do",
        "bloco de `docs/prompts-higgsfield.md` que cada quadro serve como",
        "referencia. Quadro real vale mais que geracao — onde houver footage",
        "aproveitavel, ele entra no lugar da imagem de IA.",
        "",
    ]
    for video, dur, quadros, paginas, pasta_quadros, pasta_folhas in relatorio:
        linhas += [
            f"## {video.name}",
            "",
            f"Duracao {tc_legivel(dur)} · {len(quadros)} quadros · "
            f"{paginas} folha(s) de contato",
            "",
            f"Quadros: `{pasta_quadros}`",
            f"Folhas:  `{pasta_folhas}`",
            "",
            "| Quadro | Timecode | Bloco |",
            "|---|---|---|",
        ]
        linhas += [f"| `{c.name}` | {tc_legivel(t)} | |" for c, t in quadros]
        linhas.append("")

    (saida / "INDICE.md").write_text("\n".join(linhas), encoding="utf-8")


# ---------------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(
        description="Extrai quadros de referencia de videos e monta folhas de contato.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--pasta", type=Path,
                   help="pasta com os videos, para escolher da lista")
    p.add_argument("--videos", type=Path, nargs="+",
                   help="caminhos dos videos, sem perguntar nada")
    p.add_argument("--quadros", type=int, nargs="+",
                   help="quantidade por video. Um numero vale para todos")
    p.add_argument("--saida", type=Path, default=Path("extracao"),
                   help="pasta de saida (padrao: extracao)")
    p.add_argument("--png", action="store_true",
                   help="salvar em PNG em vez de JPEG")
    p.add_argument("--qualidade", type=int, default=2,
                   help="qualidade JPEG, 2 = melhor, 31 = pior (padrao: 2)")
    p.add_argument("--nitidez", action="store_true",
                   help="testa 3 instantes por quadro e guarda o menos borrado "
                        "(3x mais lento, precisa de Pillow e numpy)")
    p.add_argument("--folhas", type=Path,
                   help="pasta das folhas de contato. Pode ser outro HD "
                        "(ex: D:/AGROSHOW/folhas). Padrao: junto dos quadros")
    p.add_argument("--sem-folhas", action="store_true",
                   help="nao montar as folhas de contato")
    p.add_argument("--sem-pausa", action="store_true",
                   help="nao esperar Enter no final")
    args = p.parse_args()

    checar_ferramentas()

    if args.videos:
        videos = [v for v in args.videos if v.exists()]
        for v in args.videos:
            if not v.exists():
                print(f"  ! nao encontrei: {v}")
        if not videos:
            sys.exit("Nenhum video valido.")
    else:
        pasta = args.pasta
        if pasta is None:
            entrada = input("Pasta com os videos: ").strip().strip('"').strip("'")
            pasta = Path(entrada)
        if not pasta.is_dir():
            sys.exit(f"Pasta nao encontrada: {pasta}")
        videos = escolher_videos(pasta)

    duracoes = {v: duracao(v) for v in videos}

    if args.quadros:
        if len(args.quadros) == 1:
            quantidades = [args.quadros[0]] * len(videos)
        elif len(args.quadros) == len(videos):
            quantidades = args.quadros
        else:
            sys.exit(
                f"--quadros recebeu {len(args.quadros)} valores para "
                f"{len(videos)} videos. Passe um valor so, ou um por video."
            )
    else:
        print(f"\n{len(videos)} video(s) selecionado(s). "
              f"Enter aceita {PADRAO_QUADROS}.\n")
        quantidades = [perguntar_quantidade(v, duracoes[v]) for v in videos]

    extensao = ".png" if args.png else ".jpg"

    # Cria as duas pastas ANTES de extrair. Descobrir que o HD das folhas nao
    # esta montado depois de meia hora de extracao seria a pior hora possivel.
    for rotulo, destino in (("--saida", args.saida), ("--folhas", args.folhas)):
        if destino is None:
            continue
        try:
            destino.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            sys.exit(f"Nao consegui criar {rotulo} em '{destino}': {e}\n"
                     "Confira se o HD esta conectado e se o caminho existe.")

    if args.nitidez:
        try:
            import numpy  # noqa: F401
            from PIL import Image  # noqa: F401
        except ImportError:
            print("\n! --nitidez precisa de Pillow e numpy: pip install pillow numpy")
            print("  Seguindo sem a selecao de nitidez.\n")
            args.nitidez = False

    print(f"\nQuadros em  {args.saida.resolve()}")
    if args.folhas:
        print(f"Folhas em   {args.folhas.resolve()}")
    print()

    relatorio = []
    for video, quantidade in zip(videos, quantidades):
        nome = nome_limpo(video.stem)
        pasta_video = args.saida / nome
        pasta_folhas = (args.folhas / nome) if args.folhas else (pasta_video / "folhas")

        quadros = extrair_do_video(video, quantidade, pasta_video, extensao,
                                   args.qualidade, args.nitidez)
        paginas = 0 if args.sem_folhas else montar_folhas(quadros, pasta_folhas,
                                                          video.name)
        relatorio.append((video, duracoes[video], quadros, paginas,
                          (pasta_video / "quadros").resolve(),
                          pasta_folhas.resolve()))

    escrever_indice(args.saida, relatorio)

    total = sum(len(r[2]) for r in relatorio)
    folhas = sum(r[3] for r in relatorio)
    print(f"\nPronto. {total} quadros, {folhas} folha(s) de contato.")
    print(f"Indice em {(args.saida / 'INDICE.md').resolve()}")


def pausar():
    """Segura a janela aberta.

    Quem roda com dois cliques no Windows perde o console assim que o script
    termina — inclusive quando termina com erro. Sem isso, qualquer falha
    'fecha sozinho' e nao sobra mensagem nenhuma para diagnosticar.
    """
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\nEnter para fechar.")
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    quer_pausa = "--sem-pausa" not in sys.argv
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompido.")
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code)
        if quer_pausa:
            pausar()
        raise SystemExit(1 if e.code not in (0, None) else 0)
    except Exception:
        import traceback
        traceback.print_exc()
        print("\nDeu erro acima. Copie essa mensagem inteira se for pedir ajuda.")
        if quer_pausa:
            pausar()
        raise SystemExit(1)
    if quer_pausa:
        pausar()
