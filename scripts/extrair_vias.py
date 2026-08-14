#!/usr/bin/env python3
"""
Tira as vias do bitmap da planta e escreve data/vias.json.

Por que do bitmap: o PDF nao tem geometria vetorial (2 retangulos de fundo, e
so) e o DWG tambem nao -- 4883 textos e zero polilinha. Entao a unica fonte do
tracado e o desenho rasterizado, e a leitura tem que ser feita por imagem.

Como funciona, e por que nao e Hough: as vias sao pares de linhas finas e
CURVAS. Hough acha reta -- numa curva ele devolve dezenas de cacos que nao se
fundem, porque o angulo muda a cada caco. A primeira versao deste script fazia
isso e o resultado foi o quadro da prancha mais o contorno dos estandes, com
zero via. Aqui a leitura e por CONTORNO: o traco vira uma tira fechada, a tira
vira uma linha aberta, e a linha e simplificada em polilinha.

O outro erro que custou caro: o tom. As linhas de rua vivem no cinza 230-252,
quase o branco do fundo. Cortando em 215, como se cortava, elas somem e sobra
so o desenho pesado. O limiar aqui e alto de proposito, e quem separa via de
ruido e o comprimento e a espessura, nao o tom.

O resultado NAO e para virar geometria sozinho. Ele sai com a via mais proxima
identificada pelo rotulo do mapa e vai para um print de conferencia
(scripts/print_mapa.py --vias); quem confirma o tracado e o Natan. Traco lido de
bitmap sem conferencia humana e chute com aparencia de dado.

Uso:
    python scripts/extrair_vias.py
    python scripts/extrair_vias.py --dpi 300 --min-comprimento 60
    python scripts/extrair_vias.py --debug        # salva a mascara usada
"""

import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
import pymupdf

ESCALA = 0.5611  # m/pt, a mesma de scripts/terreno.py

# Rotulos de via na planta. A cada segmento detectado, procura-se qual destes
# esta mais perto -- e assim o traco ganha nome sem ninguem digitar coordenada.
ROTULOS_VIA = [
    "PR 473", "AV. VER. DORVALINO TOSI", "AVENIDA JOSÉ MARCANTE",
    "AVENIDA VINICIUS DE MORAIS", "RUA JORGE AMADO", "CARROS DE APLICATIVO",
]

# Faixa de cinza que conta como traco. Medido na area da Av. Ver. Dorvalino
# Tosi: 93,5% da area e fundo (254-255) e as linhas de rua caem entre 230 e 252.
# Por isso o teto e 252 e nao 215 -- em 215 a rua inteira desaparece.
CINZA_MAX = 252

# Um traco de rua e fino. A razao area/perimetro separa traco de mancha: linha
# de 2 px de espessura da razao perto de 1, hachura e texto dao muito mais.
ESPESSURA_MAX = 3.0

# A moldura da prancha e a caixa do carimbo tambem sao linhas longas e finas, e
# entram na deteccao como se fossem rua. O que as denuncia e serem retas
# perfeitamente alinhadas ao eixo: uma rua real, mesmo reta, tem alguns pontos
# de largura na caixa delimitadora. Elas nao sao apagadas -- ficam marcadas.
MOLDURA_ESPESSURA_PT = 2.5
CAIXA_CARIMBO = (900.0, 770.0, 1440.0, 810.0)


def carregar_bitmap(pdf_path, dpi):
    page = pymupdf.open(pdf_path)[0]
    pix = page.get_pixmap(dpi=dpi)
    img = np.frombuffer(pix.samples, dtype=np.uint8)
    img = img.reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    return img, pix.width / page.rect.width, page.rect.width, page.rect.height


def mascara_de_linha(img):
    """Pixels que sao traco de desenho, incluindo o traco claro das ruas."""
    cinza = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    return (cinza <= CINZA_MAX).astype(np.uint8) * 255


def espinha(contorno):
    """De uma tira fechada para a linha aberta que ela desenha.

    O contorno de um traco fino sobe por um lado e volta pelo outro, entao ele
    passa duas vezes pelo mesmo caminho. Cortando no ponto mais distante do
    inicio, sobra uma passada so -- que e a linha de fato.
    """
    pts = contorno.reshape(-1, 2).astype(float)
    if len(pts) < 4:
        return pts
    d = np.hypot(pts[:, 0] - pts[0, 0], pts[:, 1] - pts[0, 1])
    return pts[:int(np.argmax(d)) + 1]


def detectar(img, px_por_pt, min_comprimento_pt):
    mask = mascara_de_linha(img)
    min_px = min_comprimento_pt * px_por_pt

    contornos, _ = cv2.findContours(mask, cv2.RETR_LIST,
                                    cv2.CHAIN_APPROX_NONE)
    achados = []
    for c in contornos:
        perimetro = cv2.arcLength(c, True)
        if perimetro < 2 * min_px:      # ida e volta: o dobro do comprimento
            continue
        area = cv2.contourArea(c)
        # area/(perimetro/2) e a espessura media da tira. Traco de rua da ~1-2
        # px; predio hachurado e mancha de texto dao muito mais e caem fora.
        if perimetro > 0 and (2 * area / perimetro) > ESPESSURA_MAX:
            continue

        linha = espinha(c)
        if len(linha) < 2:
            continue
        simples = cv2.approxPolyDP(linha.astype(np.float32).reshape(-1, 1, 2),
                                   epsilon=1.5 * px_por_pt, closed=False)
        pts = simples.reshape(-1, 2)
        if len(pts) < 2:
            continue
        comp = float(np.sum(np.hypot(np.diff(pts[:, 0]), np.diff(pts[:, 1]))))
        if comp < min_px:
            continue
        achados.append({"pontos": pts, "comprimento": comp})

    achados.sort(key=lambda s: -s["comprimento"])
    return achados, mask


def nomear(segmentos, locais, px_por_pt):
    """Da a cada traco o nome do rotulo de via mais proximo.

    Mede do rotulo ate o ponto mais proximo da polilinha, nao ate o meio dela:
    o nome da rua fica escrito ao lado de um trecho da rua, e nao no meio do
    seu comprimento total.
    """
    rotulos = [lo for lo in locais if lo["nome"] in ROTULOS_VIA]
    for s in segmentos:
        pts = s["pontos"] / px_por_pt
        melhor, dmin = None, float("inf")
        for r in rotulos:
            d = float(np.min(np.hypot(pts[:, 0] - r["x_pt"],
                                      pts[:, 1] - r["y_pt"])))
            if d < dmin:
                dmin, melhor = d, r
        s["rotulo_mais_proximo"] = melhor["nome"] if melhor else None
        s["distancia_ao_rotulo_pt"] = round(dmin, 1)
    return segmentos


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", default="reference/Mapa_AGROSHOW26.pdf")
    ap.add_argument("--locais", default="data/locais.json")
    ap.add_argument("-o", "--out", default="data/vias.json")
    ap.add_argument("--dpi", type=int, default=250)
    ap.add_argument("--min-comprimento", type=float, default=45.0,
                    help="comprimento minimo do segmento, em pontos de PDF "
                         "(45 pt ~ 25 m: acima de qualquer contorno de estande)")
    ap.add_argument("--debug", action="store_true",
                    help="salva a mascara de linha usada na deteccao")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    img, px_por_pt, larg_pt, alt_pt = carregar_bitmap(args.pdf, args.dpi)
    segmentos, mask = detectar(img, px_por_pt, args.min_comprimento)

    locais = json.loads(Path(args.locais).read_text(encoding="utf-8"))["locais"]
    segmentos = nomear(segmentos, locais, px_por_pt)
    segmentos.sort(key=lambda s: -s["comprimento"])

    saida = []
    for i, s in enumerate(segmentos, 1):
        pts_pt = [(round(float(x) / px_por_pt, 2), round(float(y) / px_por_pt, 2))
                  for x, y in s["pontos"]]
        pts_m = [(round((x - larg_pt / 2) * ESCALA, 2),
                  round(-(y - alt_pt / 2) * ESCALA, 2)) for x, y in pts_pt]

        xs = [p[0] for p in pts_pt]
        ys = [p[1] for p in pts_pt]
        larg_caixa, alt_caixa = max(xs) - min(xs), max(ys) - min(ys)
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        descarte = None
        if min(larg_caixa, alt_caixa) < MOLDURA_ESPESSURA_PT:
            descarte = "moldura da prancha"
        elif (CAIXA_CARIMBO[0] <= cx <= CAIXA_CARIMBO[2]
              and CAIXA_CARIMBO[1] <= cy <= CAIXA_CARIMBO[3]):
            descarte = "caixa do carimbo"

        saida.append({
            "id": f"V{i:02d}",
            "e_via": descarte is None,
            "descarte": descarte,
            "rotulo_mais_proximo": s["rotulo_mais_proximo"],
            "distancia_ao_rotulo_pt": s["distancia_ao_rotulo_pt"],
            "comprimento_m": round(s["comprimento"] / px_por_pt * ESCALA, 1),
            "vertices": len(pts_pt),
            "pontos_pt": pts_pt,
            "pontos_m": pts_m,
            "conferido_pelo_natan": False,
        })

    dados = {
        "fonte": Path(args.pdf).name,
        "metodo": (f"Hough probabilistico sobre mascara de linha fina, "
                   f"{args.dpi} dpi, segmento minimo {args.min_comprimento} pt"),
        "aviso": (
            "TRACADO LIDO DE BITMAP, NAO CONFERIDO. Nem o PDF nem o DWG tem "
            "vetor, entao isto e leitura de imagem e pode estar errado. Nada "
            "daqui vira geometria antes de 'conferido_pelo_natan': true."
        ),
        "escala_m_por_pt": ESCALA,
        "resumo": {"tracos": len(saida), "vias": sum(1 for s in saida if s["e_via"])},
        "vias": saida,
    }
    Path(args.out).write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                              "utf-8")

    vias = [s for s in saida if s["e_via"]]
    print(f"tracos detectados: {len(saida)}  |  vias: {len(vias)}  |  "
          f"moldura/carimbo: {len(saida) - len(vias)}")
    for s in vias:
        print(f"  {s['id']}  {s['comprimento_m']:6.1f} m  "
              f"{s['vertices']:3d} pts  "
              f"perto de: {s['rotulo_mais_proximo']} "
              f"({s['distancia_ao_rotulo_pt']} pt)")
    print(f"\nescrito: {args.out}")

    if args.debug:
        cv2.imwrite("out/mascara_vias.png", mask)
        print("mascara: out/mascara_vias.png")


if __name__ == "__main__":
    main()
