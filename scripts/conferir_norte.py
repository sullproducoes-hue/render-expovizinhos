#!/usr/bin/env python3
"""Confere se o +Y do mundo da cena e mesmo o norte verdadeiro.

O risco: `terreno.para_mundo` so inverte o sinal do y do PDF. Nada no projeto
garante que a prancha esta alinhada com o norte. Se estiver girada, TODO o sol
esta errado -- e o Natan, que conhece o parque, ve na hora.

Metodo: a fileira dos 6 pavilhoes de animais e a feicao mais longa e mais
inequivoca do recinto, visivel na planta (rotulos com coordenada) e no satelite
(galpoes brancos alongados). O satelite do Google e sempre norte-acima.

**Direcao de fileira sozinha tem ambiguidade de 180 graus** -- uma reta e igual
girada meia volta. Aqui isso se resolve porque a ordem dos pavilhoes e dado do
projeto (gado leite ao norte, equinos ao sul, ver ESTADO.md), entao o vetor e
direcionado, nao so uma reta.

Roda no venv (cv2 + numpy).

Uso:
    .venv/Scripts/python.exe scripts/conferir_norte.py
    .venv/Scripts/python.exe scripts/conferir_norte.py --recorte 350 620 620 920
"""

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
SATELITE = Path(r"E:\Projetos todos\Mapa - agroshow\Localização das coisas"
                r"\Mapa do google aproximado.png")

# Ordem fisica norte -> sul, dado do projeto (ESTADO.md: "a ordem fisica
# norte->sul e gado leite, nucleo cara branca, gado corte, ovinos e caprinos,
# pequenos animais, equinos"). E o que tira a ambiguidade de 180 graus.
ORDEM_PAVILHOES = [
    "PAVILHÃO - GADO LEITE",
    "PAVILHÃO - NÚCLEO CARA BRANCA",
    "PAVILHÃO - GADO CORTE",
    "PAVILHÃO - OVINOS E CAPRINOS",
    "PAVILHÃO - PEQUENOS ANIMAIS",
    "PAVILHÃO - EQUÍNOS",
]


def azimute(dx, dy):
    """Compasso: 0 = norte (+Y), 90 = leste (+X), horario."""
    return math.degrees(math.atan2(dx, dy)) % 360.0


def _locais():
    d = json.loads((RAIZ / "data" / "locais.json").read_text(encoding="utf-8"))
    return {L["nome"]: (L["x_m"], L["y_m"]) for L in d["locais"]}


def azimute_da_planta():
    """Vetor direcionado do primeiro ao ultimo pavilhao, pela ordem declarada."""
    loc = _locais()
    faltando = [n for n in ORDEM_PAVILHOES if n not in loc]
    if faltando:
        raise SystemExit(f"rotulos ausentes em locais.json: {faltando}")

    pts = np.array([loc[n] for n in ORDEM_PAVILHOES], dtype=float)

    # ajuste por minimos quadrados na fileira inteira, nao so nas pontas:
    # usa os 6 pontos e nao acumula o erro de leitura de dois rotulos.
    centro = pts.mean(axis=0)
    _, _, vt = np.linalg.svd(pts - centro)
    eixo = vt[0]
    # orienta o eixo no sentido primeiro -> ultimo
    if np.dot(pts[-1] - pts[0], eixo) < 0:
        eixo = -eixo

    az = azimute(eixo[0], eixo[1])
    residuo = float(np.abs((pts - centro) @ vt[1]).max())
    return az, residuo, pts


def azimute_do_satelite(caminho, recorte, debug=None):
    """Direcao da FILEIRA no satelite, pelos centroides dos telhados.

    A primeira versao disto media a orientacao das BORDAS por Hough, e estava
    errada: na planta eu meco a fileira (a reta que liga os centros dos 6
    pavilhoes) e no satelite estava medindo o eixo longo de cada galpao. As duas
    direcoes nao sao a mesma -- no recinto real os galpoes ficam mais ou menos
    atravessados na fileira, entao comparar uma com a outra da desvio inventado.

    Agora o metodo e o mesmo dos dois lados: acha os centroides e ajusta uma
    reta por SVD. De brinde, mede o eixo longo de cada telhado com minAreaRect,
    que serve para conferir a orientacao dos pavilhoes na cena.

    Devolve o azimute da fileira **modulo 180** -- a imagem nao sabe qual ponta
    e o gado leite. Quem resolve o sentido e a planta.
    """
    # cv2.imread nao abre caminho com acento no Windows (usa a API ANSI).
    # Ler os bytes e decodificar resolve, e o caminho tem "Localizacao".
    dados = np.fromfile(str(caminho), dtype=np.uint8)
    img = cv2.imdecode(dados, cv2.IMREAD_COLOR) if dados.size else None
    if img is None:
        raise SystemExit(f"nao consegui abrir {caminho}")
    x0, y0, x1, y1 = recorte
    corte = img[y0:y1, x0:x1]

    # Telhado metalico claro: luminosidade alta e saturacao baixa. Isso separa
    # o galpao da grama, da arvore e da terra sem depender de limiar de cinza,
    # que pegaria tambem o saibro claro das vias.
    hsv = cv2.cvtColor(corte, cv2.COLOR_BGR2HSV)
    mascara = cv2.inRange(hsv, (0, 0, 150), (180, 60, 255))
    nucleo = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, nucleo)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, nucleo)

    n, rotulado, stats, _ = cv2.connectedComponentsWithStats(mascara, 8)
    if n < 2:
        raise SystemExit("a mascara nao pegou telhado nenhum -- ajuste o --recorte")

    # Os galpoes ficam encostados e a morfologia funde os 6 numa mancha so.
    # Isso nao atrapalha: a mancha fundida e alongada NA DIRECAO DA FILEIRA,
    # entao o eixo principal dela e exatamente o que se quer -- e nao depende
    # de separar galpao por galpao, que foi onde a versao anterior quebrou.
    maior = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    ys, xs = np.nonzero(rotulado == maior)
    if len(xs) < 500:
        raise SystemExit(f"mancha pequena demais ({len(xs)} px) -- ajuste o --recorte")

    # pixel tem +y para baixo; o satelite e norte-acima, entao norte = -y
    pts = np.column_stack([xs.astype(float), -ys.astype(float)])
    centro = pts.mean(axis=0)
    _, sing, vt = np.linalg.svd(pts - centro, full_matrices=False)
    fileira = azimute(vt[0][0], vt[0][1]) % 180.0

    # alongamento: 1 = fita fina (fileira nitida), 0 = mancha redonda (sem direcao)
    forca = float(1.0 - sing[1] / sing[0]) if sing[0] > 0 else 0.0

    if debug:
        vis = corte.copy()
        vis[rotulado == maior] = (0, 0, 255)
        cx_, cy_ = centro[0], -centro[1]
        d = vt[0] * (sing[0] / math.sqrt(len(xs))) * 2.0
        cv2.line(vis, (int(cx_ - d[0]), int(cy_ + d[1])),
                 (int(cx_ + d[0]), int(cy_ - d[1])), (0, 255, 0), 2)
        cv2.imwrite(str(debug), vis)

    return fileira, forca, int(len(xs))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--satelite", default=str(SATELITE))
    ap.add_argument("--recorte", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"),
                    default=[330, 620, 640, 940],
                    help="regiao dos galpoes no satelite")
    ap.add_argument("--debug", help="grava o recorte com as linhas achadas")
    args = ap.parse_args()

    az_planta, residuo, pts = azimute_da_planta()
    print("PLANTA -- fileira dos 6 pavilhoes de animais")
    for nome, (x, y) in zip(ORDEM_PAVILHOES, pts):
        print(f"  {nome:34s} x={x:8.1f}  y={y:8.1f}")
    print(f"  azimute do vetor (norte->sul): {az_planta:.1f} graus")
    print(f"  residuo maximo fora da reta:   {residuo:.1f} m")
    print(f"  (RUMO_PAVILHOES no build_scene.py = 341.0)\n")

    az_sat, forca, n = azimute_do_satelite(args.satelite, args.recorte,
                                           args.debug)
    print("SATELITE -- eixo da mancha dos telhados (norte-acima)")
    print(f"  {n} pixels de telhado, alongamento {forca:.2f}")
    print(f"  fileira: {az_sat:.1f} graus (modulo 180)\n")

    # a planta so pode ser comparada modulo 180: a imagem nao sabe o sentido
    desvio = (az_planta - az_sat) % 180.0
    if desvio > 90.0:
        desvio -= 180.0

    print(f"DESVIO: {desvio:+.1f} graus")
    if forca < 0.45:
        print("  INCONCLUSIVO -- a mancha nao e alongada o bastante.")
        print("  Ajuste o --recorte para pegar so os galpoes.")
    elif abs(desvio) <= 3.0:
        print("  Dentro da incerteza de leitura. +Y = norte, segue.")
    elif abs(desvio) <= 10.0:
        print("  Corrigir com norte_do_mapa_graus e mostrar antes/depois.")
    else:
        print("  PARAR E PERGUNTAR antes de renderizar. Acima de 10 graus a")
        print("  hipotese provavel nao e erro de leitura: e a planta usar")
        print("  norte de projeto em vez de norte verdadeiro.")


if __name__ == "__main__":
    main()
