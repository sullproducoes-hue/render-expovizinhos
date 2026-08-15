#!/usr/bin/env python3
"""Desenha o que eu ENTENDI da marca dele, para ele conferir antes de eu aplicar.

Ordem dele em 15/08: *"antes de fazer quero ver a imagem sobreposta para
conferir as posicoes"*. Entao esta imagem e' o portao: o que estiver errado aqui
se conserta antes de virar geometria, nao depois de 22 renders.

Mostra, sobre a planta:
  - o portal de HOJE (X cinza) e o que ele marcou (alvo laranja), ligados;
  - o tracado da estrada de asfalto lido do rabisco, com os vertices;
  - a distancia entre os dois portais, em metros.

Uso:
    .venv/Scripts/python.exe scripts/conferir_correcao.py
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
CORRECAO = RAIZ / "data" / "correcao-posicao-1508.json"
SAIDA = RAIZ / "out" / "conferencia" / "correcao-para-conferir.png"

LARANJA = (0, 140, 255)
CINZA = (120, 120, 120)
AZUL = (230, 140, 0)
PRETO = (20, 20, 20)


def main():
    import pymupdf

    corr = json.loads(CORRECAO.read_text(encoding="utf-8"))
    dados = terreno.carregar_mapa(RAIZ / terreno.MAPA_PADRAO)
    origem = dados["_origem"]

    zoom = 2.5
    pix = pymupdf.open(PDF)[0].get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR if pix.n == 3 else cv2.COLOR_RGBA2BGR)
    kx = pix.w / dados["prancha"]["largura_pt"]
    ky = pix.h / dados["prancha"]["altura_pt"]

    def px(mx, my):
        return (int(round((mx / terreno.ESCALA + origem[0]) * kx)),
                int(round((-my / terreno.ESCALA + origem[1]) * ky)))

    tela = img.copy()

    # ---- estrada -------------------------------------------------------
    est = corr.get("estrada_asfalto")
    if est:
        pts = [px(x, y) for x, y in est["pontos_m"]]
        for i in range(len(pts) - 1):
            cv2.line(tela, pts[i], pts[i + 1], AZUL, 9, cv2.LINE_AA)
        for p in pts:
            cv2.circle(tela, p, 6, (255, 255, 255), -1)
            cv2.circle(tela, p, 6, PRETO, 2)
        meio = pts[len(pts) // 2]
        cv2.putText(tela, f"estrada de asfalto  {est['comprimento_m']:.0f} m  "
                          f"({est['largura_m']:.0f} m de largura)",
                    (meio[0] - 300, meio[1] - 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (255, 255, 255), 7, cv2.LINE_AA)
        cv2.putText(tela, f"estrada de asfalto  {est['comprimento_m']:.0f} m  "
                          f"({est['largura_m']:.0f} m de largura)",
                    (meio[0] - 300, meio[1] - 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, AZUL, 2, cv2.LINE_AA)

    # ---- portal --------------------------------------------------------
    por = corr.get("portal")
    if por:
        novo = px(*por["novo_m"])
        cv2.line(tela, px(*por["antigo_m"]), novo, (0, 0, 0), 3, cv2.LINE_AA)
        # onde esta hoje
        cv2.drawMarker(tela, px(*por["antigo_m"]), CINZA, cv2.MARKER_TILTED_CROSS,
                       46, 5)
        cv2.putText(tela, "portal HOJE", (px(*por["antigo_m"])[0] + 26,
                                          px(*por["antigo_m"])[1] + 46),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 6, cv2.LINE_AA)
        cv2.putText(tela, "portal HOJE", (px(*por["antigo_m"])[0] + 26,
                                          px(*por["antigo_m"])[1] + 46),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, CINZA, 2, cv2.LINE_AA)
        # onde ele marcou
        for r in (54, 40):
            cv2.circle(tela, novo, r, LARANJA, 5, cv2.LINE_AA)
        cv2.drawMarker(tela, novo, LARANJA, cv2.MARKER_CROSS, 40, 5)
        cv2.putText(tela, f"portal QUE VOCE MARCOU  ({por['desvio_m']:.0f} m "
                          f"do de hoje)", (novo[0] + 62, novo[1] - 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 7, cv2.LINE_AA)
        cv2.putText(tela, f"portal QUE VOCE MARCOU  ({por['desvio_m']:.0f} m "
                          f"do de hoje)", (novo[0] + 62, novo[1] - 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, LARANJA, 2, cv2.LINE_AA)

    # ---- cabecalho -----------------------------------------------------
    cv2.rectangle(tela, (20, 20), (1500, 150), (255, 255, 255), -1)
    cv2.rectangle(tela, (20, 20), (1500, 150), PRETO, 3)
    cv2.putText(tela, "O QUE EU ENTENDI DA SUA MARCA -- confere antes de eu "
                      "construir", (44, 78), cv2.FONT_HERSHEY_SIMPLEX, 1.05,
                PRETO, 2, cv2.LINE_AA)
    cv2.putText(tela, f"lido do print por casamento de imagem, erro de "
                      f"alinhamento {corr['alinhamento']['erro_medio_de_reprojecao']:.1f}",
                (44, 122), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (90, 90, 90), 2,
                cv2.LINE_AA)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(SAIDA), tela)
    print(f"portal hoje ...... {por['antigo_m']} m")
    print(f"portal marcado ... {por['novo_m']} m   ({por['desvio_m']} m de desvio)")
    print(f"estrada .......... {est['vertices']} vertices, "
          f"{est['comprimento_m']} m")
    print(f"gravado: {SAIDA}")


if __name__ == "__main__":
    main()
