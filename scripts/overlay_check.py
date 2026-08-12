#!/usr/bin/env python3
"""
Confere a cena 3D contra a planta: desenha a projecao em planta de tudo que o
gerador cria por cima do bitmap do PDF oficial.

E a unica forma barata de responder "isso esta no lugar certo?". Render de
camera mostra se o quadro ficou bonito; so a sobreposicao mostra se o galpao
esta 90 m ao lado de onde deveria. Uma primeira versao do percurso posicionou
cinco blocos por estimativa geometrica e errou de 88 a 182 m -- erro que esta
conferencia pega em segundos.

Uso:
    python3 scripts/overlay_check.py
    python3 scripts/overlay_check.py --out docs/conferencia-planta.png --dpi 200
"""

import argparse
import importlib.util
import io
import contextlib
import sys
from pathlib import Path

import bpy
import pymupdf
from PIL import Image, ImageDraw

CAMINHO_GERADOR = Path(__file__).with_name("build_scene.py")

# Cor por natureza do objeto. O terreno fica de fora: cobre a prancha inteira
# e so atrapalharia a leitura.
CORES = {
    "BASE": (255, 140, 0, 200),      # laranja -- permanente
    "EVENTO": (0, 190, 255, 200),    # ciano -- camada do ano
    "PERCURSO": (255, 0, 200, 255),  # magenta -- caminho da camera
    "PARADA": (255, 240, 0, 255),    # amarelo -- onde a camera para
}
IGNORAR = {"Terreno"}


def carregar_gerador():
    spec = importlib.util.spec_from_file_location("build_scene", CAMINHO_GERADOR)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def montar_cena(gerador, dados_json):
    argv = sys.argv
    sys.argv = ["build_scene.py", "--dados", dados_json]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            gerador.main()
    finally:
        sys.argv = argv
    # Sem isto as matrizes de mundo continuam na identidade -- o gerador so
    # mexeu em .location -- e todo objeto cai no centro da prancha. Falso
    # alarme muito convincente: parece que a cena inteira esta fora do lugar.
    bpy.context.view_layer.update()


def fabrica_projecao(gerador, dados, largura_px):
    """Devolve mundo (m) -> pixel do bitmap da prancha."""
    origem = (dados["prancha"]["largura_pt"] / 2, dados["prancha"]["altura_pt"] / 2)
    escala_px = largura_px / dados["prancha"]["largura_pt"]

    def projetar(x, y):
        px = (x / gerador.ESCALA + origem[0]) * escala_px
        py = (origem[1] - y / gerador.ESCALA) * escala_px
        return (px, py)

    return projetar


# Cantos da face de baixo da caixa envolvente, em ordem de contorno. A ordem
# do bound_box do Blender e fixa; estes quatro indices dao o retangulo do chao.
CANTOS_BASE = (0, 3, 7, 4)


def contorno_em_planta(obj, projetar):
    """Pegada do objeto em planta, ja em pixels da prancha.

    Poligono e nao caixa envolvente: com caixa envolvente um pavilhao girado a
    18 graus desenha um retangulo alinhado aos eixos, e a conferencia perde
    justamente o que ela existe para mostrar.
    """
    from mathutils import Vector
    cantos = [obj.matrix_world @ Vector(obj.bound_box[i]) for i in CANTOS_BASE]
    return [projetar(c.x, c.y) for c in cantos]


def desenhar(gerador, dados, pdf, destino, dpi):
    pagina = pymupdf.open(pdf)[0]
    pix = pagina.get_pixmap(dpi=dpi)
    fundo = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    fundo = fundo.convert("RGBA")
    camada = Image.new("RGBA", fundo.size, (0, 0, 0, 0))
    pincel = ImageDraw.Draw(camada)
    projetar = fabrica_projecao(gerador, dados, pix.width)

    contagem = {"BASE": 0, "EVENTO": 0}
    for nome_col in ("BASE", "EVENTO"):
        col = bpy.data.collections.get(nome_col)
        if not col:
            continue
        for obj in col.objects:
            if obj.type != "MESH" or obj.name in IGNORAR or obj.hide_render:
                continue
            pincel.polygon(contorno_em_planta(obj, projetar),
                           outline=CORES[nome_col], width=2)
            contagem[nome_col] += 1

    curva = bpy.data.objects.get("PercursoCamera")
    if curva:
        pontos = []
        for spline in curva.data.splines:
            for bp in spline.bezier_points:
                pontos.append(projetar(bp.co.x, bp.co.y))
        pincel.line(pontos, fill=CORES["PERCURSO"], width=4, joint="curve")

    paradas = 0
    for obj in bpy.data.objects:
        if not obj.name.startswith("PT_"):
            continue
        px, py = projetar(obj.location.x, obj.location.y)
        r = 7
        pincel.ellipse([px - r, py - r, px + r, py + r],
                       outline=CORES["PARADA"], width=3)
        pincel.text((px + 10, py - 6), obj.name[3:], fill=CORES["PARADA"])
        paradas += 1

    Image.alpha_composite(fundo, camada).convert("RGB").save(destino)
    return contagem, paradas


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dados", default="data/mapa_agroshow26.json")
    ap.add_argument("--pdf", default="reference/Mapa_AGROSHOW26.pdf")
    ap.add_argument("--out", default="docs/conferencia-planta.png")
    ap.add_argument("--dpi", type=int, default=200)
    args = ap.parse_args()

    import json
    dados = json.loads(Path(args.dados).read_text(encoding="utf-8"))

    gerador = carregar_gerador()
    montar_cena(gerador, args.dados)
    contagem, paradas = desenhar(gerador, dados, args.pdf, args.out, args.dpi)

    print(f"escrito: {args.out}")
    print(f"  objetos BASE ........ {contagem['BASE']} (laranja)")
    print(f"  objetos EVENTO ...... {contagem['EVENTO']} (ciano)")
    print(f"  paradas da camera ... {paradas} (amarelo)")
    print("  percurso ............ magenta")


if __name__ == "__main__":
    main()
