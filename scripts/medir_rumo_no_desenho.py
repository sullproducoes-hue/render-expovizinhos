#!/usr/bin/env python3
"""Mede o rumo dos pavilhoes DIRETO no desenho, por caminho independente.

Motivo: na sobreposicao de 15/08 as caixas da cena cruzam os retangulos
desenhados dos pavilhoes de animais. A cena obedece `data/footprints.json`
(rumo 108,4 graus, `rumo_confiavel: true`) -- entao, se ela esta torta, quem
esta errado e' a medida, nao o gerador.

Este script nao usa nada do extrator: recorta a regiao de cada pavilhao no
raster do PDF, acha as retas por Hough e toma o angulo das MAIS LONGAS, que
sao as bordas do retangulo. A hachura interna tambem produz retas, mas curtas
-- e a armadilha 15 do RETOMAR e' exatamente medir a hachura achando que se
mede o predio.

Uso:
    .venv/Scripts/python.exe scripts/medir_rumo_no_desenho.py
"""

import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import terreno

RAIZ = Path(__file__).resolve().parent.parent
PDF = RAIZ / "reference" / "Mapa_AGROSHOW26.pdf"
ZOOM = 6.0          # bem alto: linha fina de planta nao sobrevive a pouco dpi


def main():
    import pymupdf

    fp = json.loads((RAIZ / "data" / "footprints.json").read_text(encoding="utf-8"))
    alvos = [z for z in fp["itens"] if "PAVILHÃO -" in str(z.get("rotulo", ""))]

    pix = pymupdf.open(PDF)[0].get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    cinza = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY if pix.n == 3
                         else cv2.COLOR_RGBA2GRAY)

    print(f"raster {pix.w}x{pix.h} a {ZOOM}x  ({ZOOM} px por pt)\n")
    print(f"{'pavilhao':<32} {'no desenho':>11} {'footprints':>11} {'erro':>8}")

    erros = []
    for z in alvos:
        cx, cy = z["x_pt"] * ZOOM, z["y_pt"] * ZOOM
        # janela generosa: o maior pavilhao tem 55,7 m = 99 pt
        r = int(62 * ZOOM)
        x0, y0 = max(0, int(cx - r)), max(0, int(cy - r))
        x1, y1 = min(pix.w, int(cx + r)), min(pix.h, int(cy + r))
        rec = cinza[y0:y1, x0:x1]
        if rec.size == 0:
            continue

        bordas = cv2.Canny(rec, 40, 130, apertureSize=3)
        linhas = cv2.HoughLinesP(bordas, 1, np.pi / 720, threshold=60,
                                 minLineLength=int(18 * ZOOM), maxLineGap=6)
        if linhas is None:
            print(f"{z['rotulo'][:32]:<32} {'sem retas':>11}")
            continue
        linhas = linhas.reshape(-1, 4)   # armadilha 10: shape muda entre versoes

        # a borda longa do predio e' a reta mais comprida da janela
        comp = np.hypot(linhas[:, 2] - linhas[:, 0], linhas[:, 3] - linhas[:, 1])
        ordem = np.argsort(-comp)
        # angulo em azimute de mapa (0 = norte, cresce para leste); y do raster
        # cresce para BAIXO, dai o sinal invertido
        angs = []
        for i in ordem[:14]:
            dx = linhas[i, 2] - linhas[i, 0]
            dy = -(linhas[i, 3] - linhas[i, 1])
            angs.append((90.0 - np.degrees(np.arctan2(dy, dx))) % 180.0)

        # mediana circular em modulo 180: gira para perto da primeira e mediana
        base = angs[0]
        rel = [((a - base + 90) % 180) - 90 for a in angs]
        medido = (base + float(np.median(rel))) % 180.0

        alvo = float(z.get("rumo_graus", float("nan")))
        erro = ((medido - alvo + 90) % 180) - 90
        erros.append(erro)
        marca = "OK" if abs(erro) < 3 else "DIVERGE"
        print(f"{z['rotulo'][:32]:<32} {medido:>11.1f} {alvo:>11.1f} "
              f"{erro:>+7.1f}  {marca}")

    if erros:
        print(f"\nerro mediano: {float(np.median(erros)):+.1f} graus  "
              f"(n={len(erros)})")
        print("Se o erro for consistente e grande, o rumo de footprints.json "
              "esta errado\ne a cena esta girada junto -- ver armadilha 15.")


if __name__ == "__main__":
    main()
