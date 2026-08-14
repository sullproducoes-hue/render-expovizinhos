#!/usr/bin/env python3
"""Poe a vista de topo da cena por cima do satelite, na mesma escala.

Responde a pergunta do Natan -- "a posicao das coisas esta tudo correto?" --
com imagem, nao com argumento. Sai um lado-a-lado e uma sobreposicao.

A escala vem da barra do Google medida em pixel: 94 px = 50 m.
A ancora e a arena, porque o projeto nao tem georreferenciamento nenhum.

Uso:
    .venv/Scripts/python.exe scripts/sobrepor.py --arena 960 620
"""

import argparse
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
SATELITE = Path(r"E:\Projetos todos\Mapa - agroshow\Localização das coisas"
                r"\Mapa do google aproximado.png")


def ler(caminho):
    dados = np.fromfile(str(caminho), dtype=np.uint8)
    img = cv2.imdecode(dados, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"nao consegui abrir {caminho}")
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--satelite", default=str(SATELITE))
    ap.add_argument("--cena", default="out/topo-cena.png")
    ap.add_argument("--arena", nargs=2, type=int, default=[960, 620],
                    metavar=("PX", "PY"),
                    help="onde esta o centro da arena NO SATELITE, em pixel")
    ap.add_argument("--saida", default="out/comparacao")
    args = ap.parse_args()

    sat = ler(args.satelite)
    cena = ler(RAIZ / args.cena)
    hc, wc = cena.shape[:2]

    # A cena foi renderizada centrada na arena. Recorta o satelite na mesma
    # janela, centrado no ponto da arena, para que os dois fiquem alinhados
    # por construcao -- assim o que sobrar de desencontro e erro de verdade.
    ax, ay = args.arena
    x0, y0 = ax - wc // 2, ay - hc // 2
    recorte = np.zeros_like(cena)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(sat.shape[1], x0 + wc), min(sat.shape[0], y0 + hc)
    recorte[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = sat[sy0:sy1, sx0:sx1]

    saida = RAIZ / args.saida
    saida.mkdir(parents=True, exist_ok=True)

    # 1) lado a lado
    lado = np.hstack([recorte, cena])
    cv2.line(lado, (wc, 0), (wc, hc), (255, 255, 255), 2)
    cv2.imwrite(str(saida / "lado-a-lado.png"), lado)

    # 2) sobreposicao: o verde do terreno vira transparente, para o satelite
    #    aparecer por baixo e so a construcao da cena ficar em cima
    hsv = cv2.cvtColor(cena, cv2.COLOR_BGR2HSV)
    grama = cv2.inRange(hsv, (30, 60, 30), (90, 255, 160))
    constr = cv2.bitwise_not(grama)
    sobre = recorte.copy()
    sobre[constr > 0] = (0.35 * recorte[constr > 0]
                         + 0.65 * cena[constr > 0]).astype(np.uint8)
    # marca o centro da arena nos dois
    cv2.drawMarker(sobre, (wc // 2, hc // 2), (0, 0, 255),
                   cv2.MARKER_CROSS, 40, 2)
    cv2.imwrite(str(saida / "sobreposto.png"), sobre)

    print(f"escala: 94 px = 50 m  ->  {50/94:.5f} m/px")
    print(f"janela: {wc} x {hc} px  =  {wc*50/94:.0f} x {hc*50/94:.0f} m")
    print(f"arena no satelite: ({ax}, {ay})")
    print(f"gravado: {saida/'lado-a-lado.png'}")
    print(f"gravado: {saida/'sobreposto.png'}")


if __name__ == "__main__":
    main()
