#!/usr/bin/env python3
"""
Da a cada estande da planta a sua categoria, lendo a cor com que ele foi
pintado e comparando com a legenda. Escreve data/estandes.json.

Por que isso importa: a planta pinta cada estande com a cor da sua categoria --
agricultura, avicultura, veiculos e motos nauticas, maquinas e equipamentos,
cooperativas, alimentacao e bebidas, galpao do produtor. Essa informacao estava
sendo jogada fora, e ela responde duas perguntas que o projeto vinha
respondendo por estimativa:

  1. ONDE ficam as areas do roteiro que nao tem rotulo proprio. O audio separa
     "maquinas e equipamentos" de "veiculos e motos", mas o mapa escreve os
     dois num rotulo vermelho so. As cores separam: o arco salmao e maquinas, o
     arco azul e veiculos. Antes disso, os dois planos eram ancora 'derivada',
     com raio e azimute chutados.
  2. O QUE tem dentro de cada estande, na hora de povoar a cena.

Dois detalhes que enganam, e os dois custaram uma rodada errada cada:

  - Os preenchimentos sao PONTILHADOS, nao chapados. Amostrar um pixel devolve
    branco em metade das vezes; o que vale e a media da vizinhanca.
  - **Comparar direto com o quadradinho da legenda nao funciona.** A legenda e
    um pontilhado fino e o estande e um hachurado diagonal: densidades
    diferentes para a mesma tinta. Medindo assim, os 19 estandes de maquinas
    caem em 'alimentacao e bebidas', que e a mesma tinta rosa mais cheia.
    Por isso aqui as cores sao AGRUPADAS entre os proprios estandes, que
    compartilham o modo de desenho, e so o grupo e comparado com a legenda.

O que a serie A ensina: os 41 estandes A sao circulos pequenos, com o rotulo
ocupando o miolo. A amostra cai no texto e devolve cinza. Eles ficam como
'sem preenchimento', e a categoria deles vem do roteiro -- estao todos em volta
da Praca de Alimentacao.

Uso:
    python scripts/classificar_estandes.py
    python scripts/classificar_estandes.py --dpi 400 --raio 4
"""

import argparse
import colorsys
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pymupdf

ESCALA = 0.5611  # m/pt

# Caixa dos quadradinhos de cor da legenda, medida na prancha.
LEGENDA_X0, LEGENDA_X1 = 896.0, 917.0

# 'GALPAO DO PRODUTOR' e 'CAFE COLONIAL E COZINHA' dividem o mesmo quadradinho
# laranja -- sao 9 rotulos para 8 cores. Juntar os dois evita que a rotina de
# pareamento invente uma cor que nao existe.
JUNTAR_NA_LEGENDA = {
    "GALPÃO DO PRODUTOR": "GALPÃO DO PRODUTOR / CAFÉ COLONIAL E COZINHA",
    "CAFÉ COLONIAL E COZINHA": "GALPÃO DO PRODUTOR / CAFÉ COLONIAL E COZINHA",
}

# Acima desta distancia em RGB, a cor lida nao e nenhuma da legenda -- estande
# sem preenchimento, ou o ponto caiu numa linha. Fica como 'sem categoria'.
DISTANCIA_MAX = 42.0

# Abaixo desta saturacao a amostra e cinza -- estande sem preenchimento, ou o
# anel caiu no corredor. Sem este corte, o cinza casa com 'EDIFICACOES', que e
# justamente a cor do nada.
SATURACAO_MIN = 5.0

# Familias de matiz, em graus do circulo de cores. Serve para dizer se dois
# preenchimentos sao a MESMA tinta -- o brilho muda com a densidade do
# hachurado, o matiz nao.
FAIXAS_DE_MATIZ = [
    (15.0, 45.0, "laranja"),
    (45.0, 75.0, "amarelo"),
    (75.0, 170.0, "verde"),
    (170.0, 250.0, "azul"),
    (250.0, 295.0, "roxo"),
    (295.0, 345.0, "magenta"),
]


def cor_do_preenchimento(pixels, escuro_max=120):
    """A cor aparente de um preenchimento pontilhado.

    Tem que ser MEDIA com o branco dentro, e nao mediana so dos pixels
    coloridos. Motivo medido: 'Alimentacao e Bebidas' e 'Maquinas e
    Equipamentos' usam a MESMA tinta rosa, e o que as separa e a densidade do
    pontilhado -- uma e mais cheia que a outra. Ficando so com o pixel colorido,
    as duas devolvem a mesma cor e os 40 estandes de maquinas caem em
    alimentacao. A media com o branco preserva a densidade, que e a informacao.

    O que sai fora e so o pixel escuro: traco de contorno e letra do rotulo.
    Esses nao sao preenchimento e puxariam tudo para o cinza.
    """
    p = pixels.astype(float)
    claros = p[p.max(axis=1) > escuro_max]
    if len(claros) < 12:
        return None
    return claros.mean(axis=0)


def anel(img, x_px, y_px, r_int, r_ext):
    """Pixels num anel em volta do ponto.

    Anel e nao disco porque o rotulo do estande ('C-52', '105,00 m²') fica bem
    no centro dele. Amostrar o centro amostra a letra; o anel cai no
    preenchimento.
    """
    y0, y1 = max(0, y_px - r_ext), y_px + r_ext + 1
    x0, x1 = max(0, x_px - r_ext), x_px + r_ext + 1
    recorte = img[y0:y1, x0:x1]
    if recorte.size == 0:
        return np.empty((0, 3), dtype=np.uint8)
    ys, xs = np.mgrid[y0:y1, x0:x1]
    d = np.hypot(xs - x_px, ys - y_px)
    return recorte[(d >= r_int) & (d <= r_ext)]


def agrupar(amostras, k):
    """Junta as cores lidas em k grupos. Cada grupo e uma categoria da planta."""
    import cv2
    criterio = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.4)
    _, _, centros = cv2.kmeans(amostras.astype(np.float32), k, None,
                               criterio, 25, cv2.KMEANS_PP_CENTERS)
    return sorted(centros, key=lambda c: (-float(c.max() - c.min()), float(c.sum())))


def familia_de_tom(cor):
    """Em que familia de cor o preenchimento cai.

    Familia, e nao categoria, porque a legenda usa a mesma tinta duas vezes em
    densidades diferentes: 'Alimentacao e Bebidas' e 'Maquinas e Equipamentos'
    sao o mesmo rosa; 'Galpao do Produtor' e 'Avicultura' sao o mesmo laranja.
    O tom diz a familia; separar dentro dela exigiria comparar densidade entre
    a legenda e o estande, e as duas sao desenhadas de jeitos diferentes.
    """
    r, g, b = (float(v) / 255.0 for v in cor)
    if max(r, g, b) * 255 - min(r, g, b) * 255 < SATURACAO_MIN:
        return "cinza"
    matiz = colorsys.rgb_to_hsv(r, g, b)[0] * 360.0
    for inicio, fim, nome in FAIXAS_DE_MATIZ:
        if inicio <= matiz < fim:
            return nome
    return "rosa"    # o vermelho corre a volta do circulo, de 345 a 15 graus


def casar_com_legenda(cor, legenda):
    """Categoria do grupo, ou a lista de candidatas quando o tom nao decide.

    Devolve (nome, ambiguo). Onde a familia tem uma categoria so -- azul, roxo,
    amarelo -- o nome e certo. Onde tem duas, sai o par, marcado como ambiguo:
    e mais util dizer 'rosa: alimentacao ou maquinas' do que escolher uma e
    fingir certeza.
    """
    familia = familia_de_tom(cor)
    if familia == "cinza":
        return None, False

    candidatas = [nome for nome, c in legenda.items()
                  if familia_de_tom(c) == familia]
    if not candidatas:
        return f"sem correspondência na legenda (tom {familia})", True
    if len(candidatas) == 1:
        return candidatas[0], False
    return " ou ".join(sorted(candidatas)), True


def ler_legenda(img, f, locais):
    """Cor de cada categoria, tirada do proprio quadradinho da legenda."""
    cores = {}
    for r in locais["descartados"]:
        if r.get("motivo") != "legenda":
            continue
        nome = JUNTAR_NA_LEGENDA.get(r["texto_no_mapa"], r["texto_no_mapa"])
        if nome in cores:
            continue
        y = int(r["y_pt"] * f)
        faixa = img[y - int(3 * f):y + int(3 * f),
                    int(LEGENDA_X0 * f):int(LEGENDA_X1 * f)]
        cor = cor_do_preenchimento(faixa.reshape(-1, 3))
        if cor is not None:
            cores[nome] = cor
    return cores


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdf", default="reference/Mapa_AGROSHOW26.pdf")
    ap.add_argument("--mapa", default="data/mapa_agroshow26.json")
    ap.add_argument("--locais", default="data/locais.json")
    ap.add_argument("-o", "--out", default="data/estandes.json")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--grupos", type=int, default=7,
                    help="quantos grupos de cor procurar entre os estandes")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")

    page = pymupdf.open(args.pdf)[0]
    pix = page.get_pixmap(dpi=args.dpi)
    img = np.frombuffer(pix.samples, dtype=np.uint8)
    img = img.reshape(pix.height, pix.width, pix.n)[:, :, :3]
    f = pix.width / page.rect.width
    larg_pt, alt_pt = page.rect.width, page.rect.height

    locais = json.loads(Path(args.locais).read_text(encoding="utf-8"))
    mapa = json.loads(Path(args.mapa).read_text(encoding="utf-8"))

    cores = ler_legenda(img, f, locais)
    print(f"cores lidas da legenda: {len(cores)}")
    for nome, c in cores.items():
        print(f"  {nome[:46]:48s} rgb({c[0]:.0f}, {c[1]:.0f}, {c[2]:.0f})")

    # 1. Le a cor de cada estande.
    amostras, lidos = [], []
    for st in mapa["estandes"]:
        # O anel se dimensiona pelo proprio estande. Raio fixo nao serve: um
        # estande de 25 m² tem 8,9 pt de lado, e um anel de 8 pt sai dele e vai
        # amostrar o branco do corredor -- foi assim que 38 estandes viraram
        # 'EDIFICACOES', que e so a cor cinza do fundo.
        lado_pt = (st.get("area_m2") or 25.0) ** 0.5 / ESCALA
        r_int = max(2, int(0.15 * lado_pt * f))
        r_ext = max(r_int + 2, int(0.32 * lado_pt * f))
        cor = cor_do_preenchimento(
            anel(img, int(st["x"] * f), int(st["y"] * f), r_int, r_ext))
        lidos.append((st, cor))
        if cor is not None:
            amostras.append(cor)

    # 2. Agrupa as cores entre si, e so entao compara o grupo com a legenda.
    grupos = agrupar(np.array(amostras), args.grupos)
    casados = [casar_com_legenda(c, cores) for c in grupos]
    print(f"\ngrupos de cor achados entre os estandes: {len(grupos)}")
    for c, (nome, amb) in zip(grupos, casados):
        marca = "   [ambíguo]" if amb else ""
        print(f"  rgb({c[0]:3.0f},{c[1]:3.0f},{c[2]:3.0f})  "
              f"{familia_de_tom(c):8s} -> {nome}{marca}")

    saida, contagem = [], Counter()
    for st, cor in lidos:
        categoria, ambiguo = None, False
        if cor is not None:
            i = int(np.argmin([np.linalg.norm(cor - g) for g in grupos]))
            categoria, ambiguo = casados[i]

        contagem[categoria or "sem preenchimento"] += 1
        saida.append({
            "codigo": st["codigo"],
            "serie": st["serie"],
            "area_m2": st.get("area_m2"),
            "categoria": categoria,
            "categoria_ambigua": ambiguo,
            "cor_lida": [int(v) for v in cor] if cor is not None else None,
            "x_m": round((st["x"] - larg_pt / 2) * ESCALA, 2),
            "y_m": round(-(st["y"] - alt_pt / 2) * ESCALA, 2),
        })

    # Centroide por categoria: e daqui que saem as posicoes das areas do
    # roteiro que nao tem rotulo proprio na planta.
    centroides = {}
    for nome in cores:
        do_grupo = [e for e in saida if e["categoria"] == nome]
        if not do_grupo:
            continue
        centroides[nome] = {
            "estandes": len(do_grupo),
            "x_m": round(sum(e["x_m"] for e in do_grupo) / len(do_grupo), 2),
            "y_m": round(sum(e["y_m"] for e in do_grupo) / len(do_grupo), 2),
            "area_total_m2": round(
                sum(e["area_m2"] or 0 for e in do_grupo), 1),
        }

    dados = {
        "fonte": Path(args.pdf).name,
        "como_ler": (
            "categoria vem da cor com que a planta pintou o estande, comparada "
            "com o quadradinho da legenda. centroides da a posicao media de "
            "cada categoria -- e o que localiza 'Maquinas e Equipamentos' e "
            "'Veiculos e Motos Nauticas', que dividem um rotulo vermelho so."
        ),
        "resumo": dict(contagem),
        "centroides": centroides,
        "estandes": saida,
    }
    Path(args.out).write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                              "utf-8")

    print(f"\nestandes classificados: {len(saida)}")
    for nome, n in contagem.most_common():
        print(f"  {nome[:46]:48s} {n:3d}")
    print("\ncentroides (posicao media de cada categoria):")
    for nome, c in sorted(centroides.items()):
        print(f"  {nome[:46]:48s} ({c['x_m']:8.1f}, {c['y_m']:8.1f}) m  "
              f"{c['estandes']:3d} estandes  {c['area_total_m2']:8.0f} m²")
    print(f"\nescrito: {args.out}")


if __name__ == "__main__":
    main()
