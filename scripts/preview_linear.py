#!/usr/bin/env python3
"""Faz uma versao OLHAVEL dos quadros lineares, com grade de coordenadas.

    .venv/Scripts/python.exe scripts/preview_linear.py --video "1 (16)"
    .venv/Scripts/python.exe scripts/preview_linear.py --todos

Os PNG de `extracao/linear/` sao 16 bits LINEARES: abertos direto, aparecem
quase pretos, porque o olho espera gama. Este script NAO existe para medir --
existe para eu **escolher o recorte** e depois declarar a caixa em pixel do
quadro original. A conta de medicao continua acontecendo no linear.

A grade e o ponto: sem ela eu chutaria coordenada, e chute em caixa de amostra
e como chutar cor. Cada linha vem rotulada com o pixel do quadro ORIGINAL
(3840x2160), nao com o pixel da miniatura.
"""

import argparse
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
LINEAR = Path(r"E:\Projetos todos\Mapa - agroshow\Brutos Expo"
              r"\agroshow extrator somente\extracao\linear")
PASSO = 240  # px do quadro original entre linhas da grade


def linear_para_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def preview(png, destino, escala=0.25):
    bruto = cv2.imdecode(np.fromfile(str(png), dtype=np.uint8),
                         cv2.IMREAD_UNCHANGED)
    if bruto is None:
        return None
    lin = bruto.astype(np.float64) / 65535.0
    vis = (linear_para_srgb(lin) * 255).astype(np.uint8)
    h, w = vis.shape[:2]
    vis = cv2.resize(vis, (int(w * escala), int(h * escala)))

    for x in range(0, w, PASSO):
        xs = int(x * escala)
        cv2.line(vis, (xs, 0), (xs, vis.shape[0]), (0, 255, 255), 1)
        cv2.putText(vis, str(x), (xs + 3, 16), cv2.FONT_HERSHEY_SIMPLEX,
                    0.42, (0, 255, 255), 1)
    for y in range(0, h, PASSO):
        ys = int(y * escala)
        cv2.line(vis, (0, ys), (vis.shape[1], ys), (0, 255, 255), 1)
        cv2.putText(vis, str(y), (3, ys + 16), cv2.FONT_HERSHEY_SIMPLEX,
                    0.42, (0, 255, 255), 1)

    destino.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(destino), vis, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return destino


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--escala", type=float, default=0.25)
    ap.add_argument("--saida", default="out/linear-preview")
    args = ap.parse_args()

    pastas = (sorted(LINEAR.iterdir()) if args.todos
              else [LINEAR / args.video])
    n = 0
    for p in pastas:
        if not p.is_dir():
            continue
        for png in sorted(p.glob("*.png")):
            d = RAIZ / args.saida / p.name / (png.stem + ".jpg")
            if preview(png, d, args.escala):
                n += 1
                print(f"  {d.relative_to(RAIZ)}")
    print(f"\n{n} previews. A grade e em pixel do quadro ORIGINAL.")


if __name__ == "__main__":
    main()
