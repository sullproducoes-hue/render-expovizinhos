#!/usr/bin/env python3
"""Vista de topo da cena NO REFERENCIAL DA PRANCHA, para cair em cima do mapa.

Complemento do `sobrepor_planta.py`: aquele desenha PONTOS (onde a planta diz x
onde o objeto esta), e ponto nao mostra objeto girado. Este desenha a FORMA, que
e onde o "torto" aparece.

Por que nao gira a camera: o `conferir_posicao.py` compensa o norte porque
compara com o satelite, que e norte-acima. A PLANTA nao -- ela e o proprio
referencial de onde as posicoes sairam (`terreno.para_mundo`). Entao a camera
fica sem giro e o pixel cai por construcao.

A prancha tem 1440 x 810 pt, que a 0,5611 m/pt da 808 x 454 m -- exatamente a
extensao do terreno que o gerador declara. A origem do mundo e o centro da
prancha, entao a camera fica em (0, 0).

Uso:
    blender out/cena.blend --background --python scripts/topo_planta.py
"""

import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))

import terreno

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "out" / "conferencia" / "topo-cena.png"


def main():
    dados = json.loads((RAIZ / terreno.MAPA_PADRAO).read_text(encoding="utf-8"))
    larg_pt = dados["prancha"]["largura_pt"]
    alt_pt = dados["prancha"]["altura_pt"]
    larg_m = larg_pt * terreno.ESCALA
    alt_m = alt_pt * terreno.ESCALA

    cena = bpy.context.scene

    # camera ortografica de topo, cobrindo a prancha inteira
    dc = bpy.data.cameras.new("CamTopoPlanta")
    dc.type = "ORTHO"
    dc.ortho_scale = larg_m          # a maior dimensao manda no Blender
    dc.clip_start = 1.0
    dc.clip_end = 6000.0             # a camera fica a 1500 m: o default de 100 m
    cam = bpy.data.objects.new("CamTopoPlanta", dc)   # devolveria quadro vazio
    cena.collection.objects.link(cam)
    cam.location = (0.0, 0.0, 1500.0)
    cam.rotation_euler = (0.0, 0.0, 0.0)   # sem giro: a planta E o referencial
    cena.camera = cam

    # 3600 x 2025 e o mesmo raster do sobrepor_planta.py com --zoom 2.5
    cena.render.resolution_x = 3600
    cena.render.resolution_y = int(round(3600 * alt_pt / larg_pt))
    cena.render.resolution_percentage = 100
    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_mode = "RGBA"
    cena.render.film_transparent = True      # fundo vazado, para sobrepor
    cena.render.filepath = str(SAIDA)

    # chapado de proposito: aqui nao se julga luz, se julga posicao e rumo
    cena.render.engine = "BLENDER_WORKBENCH"
    if hasattr(cena, "display"):
        cena.display.shading.light = "FLAT"
        cena.display.shading.color_type = "MATERIAL"

    print(f"prancha ....... {larg_pt} x {alt_pt} pt")
    print(f"terreno ....... {larg_m:.1f} x {alt_m:.1f} m")
    print(f"raster ........ {cena.render.resolution_x} x {cena.render.resolution_y}")
    print(f"camera ........ ortho {dc.ortho_scale:.1f} m, sem giro, em (0,0,1500)")

    bpy.ops.render.render(write_still=True)
    print(f"gravado: {SAIDA}")


if __name__ == "__main__":
    main()
