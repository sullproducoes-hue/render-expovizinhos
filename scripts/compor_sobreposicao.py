#!/usr/bin/env python3
"""Junta o topo da cena com o mapa oficial, pixel a pixel.

Entra: `out/conferencia/topo-cena.png` (do topo_planta.py, fundo vazado) e o
`reference/Mapa_AGROSHOW26.pdf` rasterizado na mesma janela.

Sai tres imagens, porque cada uma responde uma pergunta diferente:
  sobreposto.png   -- a cena por cima da planta, semitransparente: mostra o
                      DESENCONTRO (o que esta torto e o que esta fora do lugar)
  lado-a-lado.png  -- para conferir forma sem o ruido da mistura
  contorno.png     -- so a borda da cena sobre a planta limpa, para ler rumo

Uso:
    .venv/Scripts/python.exe scripts/compor_sobreposicao.py
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import terreno

RAIZ = Path(__file__).resolve().parent.parent
PDF = RAIZ / "reference" / "Mapa_AGROSHOW26.pdf"
DIR = RAIZ / "out" / "conferencia"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alfa", type=float, default=0.55,
                    help="peso da cena na mistura")
    args = ap.parse_args()

    import pymupdf

    cena = cv2.imread(str(DIR / "topo-cena.png"), cv2.IMREAD_UNCHANGED)
    if cena is None:
        raise SystemExit("rode antes: blender out/cena.blend --background "
                         "--python scripts/topo_planta.py")
    h, w = cena.shape[:2]

    dados = json.loads((RAIZ / terreno.MAPA_PADRAO).read_text(encoding="utf-8"))
    zoom = w / dados["prancha"]["largura_pt"]

    doc = pymupdf.open(PDF)
    pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    mapa = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    mapa = cv2.cvtColor(mapa, cv2.COLOR_RGB2BGR if pix.n == 3 else cv2.COLOR_RGBA2BGR)
    mapa = mapa[:h, :w] if mapa.shape[:2] != (h, w) else mapa

    rgb = cena[:, :, :3]
    alfa = (cena[:, :, 3:4].astype(np.float32) / 255.0) * args.alfa

    sobre = (mapa.astype(np.float32) * (1 - alfa) + rgb.astype(np.float32) * alfa)
    sobre = sobre.astype(np.uint8)
    cv2.imwrite(str(DIR / "sobreposto.png"), sobre)

    # contorno: so a silhueta da cena, para ler rumo sem tapar o desenho
    mascara = (cena[:, :, 3] > 8).astype(np.uint8) * 255
    bordas = cv2.Canny(mascara, 50, 150)
    bordas = cv2.dilate(bordas, np.ones((2, 2), np.uint8))
    cont = mapa.copy()
    cont[bordas > 0] = (40, 40, 235)
    cv2.imwrite(str(DIR / "contorno.png"), cont)

    # lado a lado, reduzido para caber no olho
    esc = 0.5
    m2 = cv2.resize(mapa, None, fx=esc, fy=esc, interpolation=cv2.INTER_AREA)
    fundo = np.full_like(rgb, 255)
    a3 = cena[:, :, 3:4].astype(np.float32) / 255.0
    chapado = (fundo * (1 - a3) + rgb * a3).astype(np.uint8)
    c2 = cv2.resize(chapado, None, fx=esc, fy=esc, interpolation=cv2.INTER_AREA)
    lado = np.hstack([m2, c2])
    cv2.line(lado, (m2.shape[1], 0), (m2.shape[1], m2.shape[0]), (0, 0, 0), 3)
    cv2.imwrite(str(DIR / "lado-a-lado.png"), lado)

    cobertura = float((cena[:, :, 3] > 8).mean())
    print(f"janela ...... {w} x {h} px   ({zoom:.3f} px/pt)")
    print(f"cena cobre .. {cobertura*100:.1f}% do quadro")
    for n in ("sobreposto.png", "contorno.png", "lado-a-lado.png"):
        print(f"gravado: {DIR / n}")


if __name__ == "__main__":
    main()
