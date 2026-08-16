#!/usr/bin/env python3
"""Antes e depois do rumo dos pavilhoes, desenhado sobre a planta.

Nao reconstroi a cena: desenha o retangulo medido de cada pavilhao nos dois
rumos -- o antigo, espelhado (108,4), e o corrigido (71,6) -- em cima do proprio
desenho do cliente. Quem estiver certo encosta no retangulo desenhado.

Uso:
    .venv/Scripts/python.exe scripts/prova_rumo.py
"""

import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import terreno

RAIZ = Path(__file__).resolve().parent.parent
PDF = RAIZ / "reference" / "Mapa_AGROSHOW26.pdf"
ZOOM = 4.0

VERMELHO = (40, 40, 235)    # o rumo antigo, espelhado
VERDE = (60, 165, 60)       # o rumo corrigido


def retangulo(cx_px, cy_px, larg_px, prof_px, rumo_graus):
    """Cantos de um retangulo centrado, com o lado longo no azimute dado."""
    a = math.radians(rumo_graus)
    ux, uy = math.sin(a), -math.cos(a)          # y do raster cresce p/ baixo
    vx, vy = -uy, ux
    hl, hp = larg_px / 2.0, prof_px / 2.0
    return np.array([[cx_px + ux * hl + vx * hp, cy_px + uy * hl + vy * hp],
                     [cx_px + ux * hl - vx * hp, cy_px + uy * hl - vy * hp],
                     [cx_px - ux * hl - vx * hp, cy_px - uy * hl - vy * hp],
                     [cx_px - ux * hl + vx * hp, cy_px - uy * hl + vy * hp]],
                    dtype=np.int32)


def main():
    import pymupdf

    novo = json.loads((RAIZ / "data" / "footprints.json").read_text(encoding="utf-8"))
    velho_p = RAIZ / "data" / "footprints-v2-rumo-espelhado-1508.json"
    velho = json.loads(velho_p.read_text(encoding="utf-8")) if velho_p.exists() else None

    vmap = {}
    if velho:
        for z in velho["itens"]:
            vmap.setdefault(str(z.get("rotulo")), z)

    pix = pymupdf.open(PDF)[0].get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR if pix.n == 3 else cv2.COLOR_RGBA2BGR)

    por_m = ZOOM / terreno.ESCALA      # pixels por metro
    alvos = [z for z in novo["itens"] if "PAVILHÃO -" in str(z.get("rotulo", ""))]

    for z in alvos:
        cx, cy = z["x_pt"] * ZOOM, z["y_pt"] * ZOOM
        lp, pp = z["largura_m"] * por_m, z["profundidade_m"] * por_m
        v = vmap.get(str(z["rotulo"]))
        if v:
            cv2.polylines(img, [retangulo(cx, cy, lp, pp, v["rumo_graus"])],
                          True, VERMELHO, 3, cv2.LINE_AA)
        cv2.polylines(img, [retangulo(cx, cy, lp, pp, z["rumo_graus"])],
                      True, VERDE, 3, cv2.LINE_AA)

    # recorte na regiao dos pavilhoes
    xs = [z["x_pt"] * ZOOM for z in alvos]
    ys = [z["y_pt"] * ZOOM for z in alvos]
    m = 70 * por_m
    x0, y0 = max(0, int(min(xs) - m)), max(0, int(min(ys) - m))
    x1, y1 = min(pix.w, int(max(xs) + m)), min(pix.h, int(max(ys) + m))
    rec = img[y0:y1, x0:x1]

    faixa = np.full((120, rec.shape[1], 3), 255, np.uint8)
    cv2.line(faixa, (30, 40), (100, 40), VERMELHO, 4)
    cv2.putText(faixa, "antes: 108,4 (espelhado)", (115, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.line(faixa, (30, 90), (100, 90), VERDE, 4)
    cv2.putText(faixa, "agora: 71,6 (corrigido)", (115, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)

    saida = RAIZ / "out" / "conferencia" / "prova-rumo-pavilhoes.png"
    saida.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(saida), np.vstack([faixa, rec]))
    print(f"{len(alvos)} pavilhoes desenhados nos dois rumos")
    print(f"gravado: {saida}")


if __name__ == "__main__":
    main()
