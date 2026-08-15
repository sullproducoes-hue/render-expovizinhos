#!/usr/bin/env python3
"""
Extrai, em resolucao nativa, os quadros do footage listados em
`data/quadros-ia.json` -- a familia `real` das placas de entrada da IA.

Roda no venv (nao precisa de bpy). Decode na GPU quando da, com rebaixamento
silencioso para CPU: e a ordem permanente da casa.

    .venv/Scripts/python.exe scripts/quadros_reais.py
    .venv/Scripts/python.exe scripts/quadros_reais.py --plano P19,P20
    .venv/Scripts/python.exe scripts/quadros_reais.py --contato   # so as folhas

Saida: out/quadros-ia/<Pxx>_<slug>/real/<n>_<video>_<tc>.jpg
       out/quadros-ia/<Pxx>_<slug>/CONTATO.jpg   (3d + real lado a lado)

Duas travas que ja custaram uma rodada cada neste projeto:

  - `-ss` ANTES de `-i` e busca por keyframe, rapida e imprecisa; depois de
    `-i` e exata e lenta. Aqui vale a exata: o timecode veio de uma folha de
    contato e um segundo de erro troca o assunto do quadro.
  - tres arquivos do acervo sao HLG bt2020 (os IMG_91xx de iPhone). Sem
    tonemap explicito o quadro sai lavado -- e este e justamente o material
    do parque VAZIO, que e o melhor para a IA vestir. A cadeia de conversao
    entra so neles, detectada por ffprobe, nunca por nome de arquivo.
"""

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "data" / "quadros-ia.json"

TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,"
           "zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


def slug(texto):
    if not texto:
        return "sem-titulo"
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower()
    return t[:44] or "sem-titulo"


def pasta_do_local(local):
    return f"{local['plano']}_{slug(local['local'])}"


def eh_hdr(video):
    """HLG/PQ bt2020 -> precisa de tonemap. Lido do arquivo, nao do nome."""
    try:
        saida = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=color_transfer,color_primaries",
             "-of", "json", str(video)],
            capture_output=True, text=True, timeout=60).stdout
        fluxo = json.loads(saida)["streams"][0]
    except Exception:
        return False
    trc = (fluxo.get("color_transfer") or "").lower()
    prim = (fluxo.get("color_primaries") or "").lower()
    return trc in ("arib-std-b67", "smpte2084") or prim == "bt2020"


def duracao(video):
    try:
        s = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", str(video)],
                           capture_output=True, text=True, timeout=60).stdout.strip()
        return float(s)
    except Exception:
        return None


def extrair(video, tc, destino, hdr):
    filtros = TONEMAP if hdr else None
    # Busca em dois tempos: o `-ss` grosso ANTES de `-i` cai no keyframe mais
    # proximo (instantaneo), o `-ss` fino DEPOIS de `-i` anda os ultimos
    # segundos quadro a quadro (exato). So o `-ss` depois, sozinho, decodifica
    # o arquivo inteiro desde o comeco: em 4K deu ~1 min por quadro.
    grosso = max(0.0, tc - 3.0)
    fino = tc - grosso
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-hwaccel", "cuda", "-ss", f"{grosso:.3f}", "-i", str(video),
           "-ss", f"{fino:.3f}", "-frames:v", "1"]
    if filtros:
        cmd += ["-vf", filtros]
    else:
        # Os `_stabilized` sairam do estabilizador em YUV full range, e o mjpeg
        # recusa: "Non full-range YUV is non-standard". `yuvj420p` e o JPEG
        # full-range de sempre e aceita os dois lados sem converter cor.
        cmd += ["-pix_fmt", "yuvj420p"]
    cmd += ["-q:v", "2", str(destino)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not destino.exists():
        # rebaixa para CPU: a placa recusa alguns perfis, e o quadro importa
        # mais que a velocidade.
        cmd = [c for c in cmd if c not in ("-hwaccel", "cuda")]
        r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not destino.exists():
        return False, (r.stderr or "").strip()[:200]
    return True, ""


def folha_de_contato(pasta, titulo, largura=2400):
    """Junta o 3d e os reais do local numa folha, para olhar de uma vez."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    imagens = []
    for sub, rotulo in (("3d", "3D"), ("real", "REAL")):
        d = pasta / sub
        if not d.is_dir():
            continue
        for arq in sorted(d.iterdir()):
            if arq.suffix.lower() not in (".png", ".jpg", ".jpeg"):
                continue
            img = cv2.imread(str(arq))
            if img is None:
                continue
            imagens.append((f"{rotulo} · {arq.stem}", img))
    if not imagens:
        return None

    cols = 2
    cel_w = largura // cols
    cel_h = int(cel_w * 9 / 16)
    linhas = (len(imagens) + cols - 1) // cols
    folha = np.full((linhas * (cel_h + 34), largura, 3), 24, np.uint8)
    for i, (rotulo, img) in enumerate(imagens):
        h, w = img.shape[:2]
        esc = min(cel_w / w, cel_h / h)
        peq = cv2.resize(img, (int(w * esc), int(h * esc)), interpolation=cv2.INTER_AREA)
        y0 = (i // cols) * (cel_h + 34) + 34
        x0 = (i % cols) * cel_w + (cel_w - peq.shape[1]) // 2
        folha[y0:y0 + peq.shape[0], x0:x0 + peq.shape[1]] = peq
        cv2.putText(folha, rotulo[:70], ((i % cols) * cel_w + 8, y0 - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (235, 235, 235), 1, cv2.LINE_AA)
    cv2.putText(folha, titulo[:90], (8, 22), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (120, 220, 255), 2, cv2.LINE_AA)
    saida = pasta / "CONTATO.jpg"
    cv2.imwrite(str(saida), folha, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return saida


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalogo", default=str(CATALOGO))
    ap.add_argument("--saida", default=None, help="padrao: o campo raizes.saida do catalogo")
    ap.add_argument("--plano", default=None, help="so estes planos, separados por virgula")
    ap.add_argument("--forcar", action="store_true")
    ap.add_argument("--contato", action="store_true", help="so refaz as folhas de contato")
    args = ap.parse_args()

    cat = json.loads(Path(args.catalogo).read_text(encoding="utf-8"))
    raizes = cat["raizes"]
    destino_raiz = Path(args.saida) if args.saida else (RAIZ / raizes["saida"])
    destino_raiz.mkdir(parents=True, exist_ok=True)

    locais = cat["locais"]
    if args.plano:
        pedidos = set(args.plano.split(","))
        locais = [l for l in locais if l["plano"] in pedidos]

    cache_hdr = {}
    feitos = pulados = falhos = 0
    sem_real = []

    for local in locais:
        pasta = destino_raiz / pasta_do_local(local)
        pasta.mkdir(parents=True, exist_ok=True)
        if not local["reais"]:
            sem_real.append(f"{local['plano']} {local['local']}")

        if not args.contato:
            (pasta / "real").mkdir(exist_ok=True)
            for i, item in enumerate(local["reais"], 1):
                base = Path(raizes[item["raiz"]])
                if item["raiz"] == "foto_portal":
                    origem = base
                    alvo = pasta / "real" / f"{i}_foto-portal{origem.suffix.lower()}"
                    if alvo.exists() and not args.forcar:
                        pulados += 1
                        continue
                    if not origem.exists():
                        print(f"  [{local['plano']}] AUSENTE: {origem}")
                        falhos += 1
                        continue
                    alvo.write_bytes(origem.read_bytes())
                    feitos += 1
                    print(f"  [{local['plano']}] foto -> {alvo.name}")
                    continue

                origem = base / item["video"]
                tc = float(item["tc"])
                alvo = pasta / "real" / f"{i}_{slug(Path(item['video']).stem)}_{tc:06.2f}s.jpg"
                if alvo.exists() and not args.forcar:
                    pulados += 1
                    continue
                if not origem.exists():
                    print(f"  [{local['plano']}] AUSENTE: {origem}")
                    falhos += 1
                    continue
                # Portao: o timecode do catalogo veio de uma folha de contato e
                # nada garante que caiba no arquivo. Quatro entradas da primeira
                # rodada pediam segundo 12 num clipe de 7 s, e o ffmpeg falhava
                # com uma mensagem que nao dizia isso.
                dur = duracao(origem)
                if dur and tc > dur - 0.1:
                    print(f"  [{local['plano']}] TC FORA DO ARQUIVO: {item['video']} "
                          f"pede {tc}s e o clipe tem {dur:.1f}s -- corrija data/quadros-ia.json")
                    falhos += 1
                    continue
                if origem not in cache_hdr:
                    cache_hdr[origem] = eh_hdr(origem)
                ok, erro = extrair(origem, tc, alvo, cache_hdr[origem])
                if ok:
                    feitos += 1
                    marca = " [HDR->bt709]" if cache_hdr[origem] else ""
                    print(f"  [{local['plano']}] {item['video']} @{tc}s{marca} -> {alvo.name}")
                else:
                    falhos += 1
                    print(f"  [{local['plano']}] FALHOU {item['video']} @{tc}s: {erro}")

        folha = folha_de_contato(pasta, f"{local['plano']} · {local['local']}")
        if folha:
            print(f"  [{local['plano']}] folha -> {folha.name}")

    print("\n" + "=" * 58)
    print(f"  quadros extraidos ..... {feitos}")
    print(f"  ja existiam ........... {pulados}")
    print(f"  falharam .............. {falhos}")
    if sem_real:
        print(f"  locais SEM quadro real: {len(sem_real)}")
        for s in sem_real:
            print(f"    - {s}")
    print("=" * 58)


if __name__ == "__main__":
    main()
