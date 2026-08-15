#!/usr/bin/env python3
"""Extrai quadros LINEARES de 16 bits do footage, para medir cor e tirar textura.

    .venv/Scripts/python.exe scripts/extrair_linear.py --listar
    .venv/Scripts/python.exe scripts/extrair_linear.py --video "1 (16)" --instantes 21 66 110
    .venv/Scripts/python.exe scripts/extrair_linear.py --todos --por-video 4

**Esta e a SEGUNDA extracao, e ela existe separada de proposito.** A primeira,
em `extracao/<video>/`, e JPEG em sRGB e serve para o olho escolher quadro. Ela
NAO serve para medir, e o motivo e sutil o bastante para ter que estar escrito:

O metodo de medicao do projeto divide a amostra por uma ancora conhecida do
MESMO quadro para derrubar o iluminante. Divisao so vale em espaco LINEAR. Num
JPEG sRGB, com a gama embutida, a conta continua rodando e continua devolvendo
numero -- numero errado, e consistente, e por isso `texturas.py --conferir` nao
acusa nada. Erro que passa no teste e o pior tipo que existe.

**A cadeia sai do ffprobe, nao de habito.** Os 17 videos de 13/08 sao bt709 SDR,
10 bits, 4:2:0 -- conferido, e esta em `data/footage-quinta.json`. O material
ANTIGO do AgroShow tem HLG bt2020 no meio (os IMG_91xx de iPhone), e a triagem
de 14/08 precisou de tonemap por causa disso. Aplicar a cadeia de HLG neste
material aqui destruiria a cor **em silencio**: a imagem sai, so sai errada.
Por isso o script LE o ffprobe de cada arquivo e monta a cadeia a partir dele,
e recusa o que nao souber tratar.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FOOTAGE = Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo"
               r"\agroshow extrator somente")
CONTRATO = RAIZ / "data" / "footage-quinta.json"

# transferencia do ffprobe -> nome do zscale. O `unknown` do ffprobe em material
# de camera quase sempre e bt709; assumir isso e razoavel e fica DITO no log,
# nunca calado.
TRANSFERENCIA = {
    "bt709": "bt709", "unknown": "bt709", "": "bt709",
    "bt470bg": "bt470bg", "smpte170m": "smpte170m",
    "iec61966-2-1": "iec61966-2-1", "srgb": "iec61966-2-1",
    "arib-std-b67": "arib-std-b67",     # HLG
    "smpte2084": "smpte2084",           # PQ
}
HDR = {"arib-std-b67", "smpte2084"}


def sondar(video):
    saida = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries",
         "stream=width,height,pix_fmt,color_transfer,color_primaries,color_space"
         ":format=duration",
         "-of", "json", str(video)],
        capture_output=True, text=True).stdout
    d = json.loads(saida)
    s = d["streams"][0]
    return {"largura": s.get("width"), "altura": s.get("height"),
            "pix_fmt": s.get("pix_fmt"),
            "trc": (s.get("color_transfer") or "unknown"),
            "primaries": (s.get("color_primaries") or "unknown"),
            "matrix": (s.get("color_space") or "unknown"),
            "duracao_s": float(d["format"]["duration"])}


def cadeia(info):
    """Monta o filtro zscale a partir do que o arquivo DIZ que e."""
    trc = TRANSFERENCIA.get(info["trc"])
    if trc is None:
        raise SystemExit(
            f"transferencia desconhecida: {info['trc']!r}. Nao vou inventar "
            "uma cadeia de cor -- acrescente o caso em TRANSFERENCIA depois de "
            "conferir o que ela e.")
    prim = info["primaries"] if info["primaries"] not in ("unknown", "") else "bt709"
    mtx = info["matrix"] if info["matrix"] not in ("unknown", "") else "bt709"
    # `npl=100` so tem sentido em HDR (nits de pico); em SDR ele e ruido no
    # comando. Fica so onde vale.
    npl = ":npl=100" if info["trc"] in HDR else ""
    return (f"zscale=t={trc}:m={mtx}:p={prim}:r=full,"
            f"zscale=t=linear{npl},format=gbrp16le")


def extrair(video, instantes, destino, verbose=True):
    info = sondar(video)
    filtro = cadeia(info)
    destino.mkdir(parents=True, exist_ok=True)
    if verbose:
        print(f"  {video.name}: {info['largura']}x{info['altura']} "
              f"{info['pix_fmt']} trc={info['trc']} -> linear 16 bits")
        if info["trc"] in HDR:
            print("    (material HDR: a cadeia inclui o npl. NAO e o caso dos 17 de 13/08)")

    feitos = []
    for t in instantes:
        alvo = destino / f"{video.stem}__{int(t):04d}s.png"
        if alvo.exists():
            feitos.append(alvo)
            continue
        r = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{t}", "-i", str(video),
             "-frames:v", "1", "-vf", filtro,
             "-pix_fmt", "rgb48le", str(alvo)],
            capture_output=True, text=True)
        if alvo.exists():
            feitos.append(alvo)
        elif verbose:
            print(f"    FALHOU em {t}s: {r.stderr.strip()[:160]}")
    return info, feitos


def instantes_do_contrato(vid_id, n, duracao):
    """Instantes bem distribuidos, com folga nas pontas."""
    return [round(duracao * (0.1 + 0.8 * i / max(n - 1, 1)), 1) for i in range(n)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video", default=None, help='ex: "1 (16)"')
    ap.add_argument("--instantes", type=float, nargs="*", default=None,
                    help="segundos. Sem isto, distribui --por-video ao longo do clipe")
    ap.add_argument("--por-video", type=int, default=4)
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--saida", default=None,
                    help="padrao: <footage>/extracao/linear")
    args = ap.parse_args()

    contrato = json.loads(CONTRATO.read_text(encoding="utf-8"))
    raiz_saida = Path(args.saida) if args.saida else FOOTAGE / "extracao" / "linear"

    if args.listar:
        print(f"{'video':10s} {'dur':>6s}  o que mostra")
        for v in contrato["videos"]:
            print(f"  {v['id']:8s} {v['duracao_s']:4d}s  {v['mostra'][:78]}")
        return

    alvos = [v for v in contrato["videos"]
             if args.todos or v["id"] == args.video]
    if not alvos:
        raise SystemExit(f"nao achei {args.video!r} no contrato. Use --listar.")

    print("=" * 74)
    print("EXTRACAO LINEAR 16 BITS -- para MEDIR, nao para olhar")
    print("=" * 74)
    total = 0
    for v in alvos:
        arq = FOOTAGE / f"{v['id']}.mp4"
        if not arq.exists():
            print(f"  AUSENTE: {arq}")
            continue
        info = sondar(arq)
        ts = (args.instantes if args.instantes
              else instantes_do_contrato(v["id"], args.por_video, info["duracao_s"]))
        _, feitos = extrair(arq, ts, raiz_saida / v["id"])
        total += len(feitos)
        print(f"    {len(feitos)} quadro(s) em {raiz_saida / v['id']}")

    print(f"\n  {total} quadros lineares. MEDIR SO AQUI.")
    print("=" * 74)


if __name__ == "__main__":
    main()
