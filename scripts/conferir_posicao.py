#!/usr/bin/env python3
"""Vista de topo da cena, na escala e na orientacao do satelite, para sobrepor.

O Natan perguntou se a posicao das coisas esta certa, e mandou conferir isso
ANTES do sol -- que e a ordem certa: iluminar uma cena onde as coisas estao no
lugar errado e trabalho jogado fora.

Metodo: render ortografico de cima, com a camera girada para compensar o norte
do mapa, na mesma metros-por-pixel medida na barra de escala do Google
(94 px = 50 m -> 0,53191 m/px). Sai um PNG que se poe por cima do satelite.

Nao ha georreferenciamento no projeto, entao a ancora e a arena: os dois lados
sao centrados nela. Qualquer desencontro que sobrar e erro de escala, de rumo
ou de posicao -- que e exatamente o que se quer ver.

Uso:
    blender --background --python scripts/conferir_posicao.py -- --arena-px 960 620
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy

import terreno

RAIZ = Path(__file__).resolve().parent.parent

# Barra de escala do Google medida em pixel: 94 px = 50 m.
M_POR_PX = 50.0 / 94.0


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", default="out/cena.blend")
    ap.add_argument("--largura", type=int, default=1920)
    ap.add_argument("--altura", type=int, default=1080)
    ap.add_argument("--saida", default="out/topo-cena.png")
    args = ap.parse_args(argv)

    luz = json.loads((RAIZ / "data" / "luz.json").read_text(encoding="utf-8"))
    norte = luz["norte_do_mapa_graus"]

    bpy.ops.wm.open_mainfile(filepath=str(RAIZ / args.blend))
    cena = bpy.context.scene

    pista = bpy.data.objects.get("PistaArena")
    centro = (pista.location.x, pista.location.y) if pista else (0.0, 0.0)

    for o in list(bpy.data.objects):
        if o.type == "CAMERA":
            bpy.data.objects.remove(o, do_unlink=True)

    dados = bpy.data.cameras.new("CamTopo")
    dados.type = "ORTHO"
    dados.ortho_scale = args.largura * M_POR_PX      # metros cobertos na largura
    # o clip_end default e 100 m e a camera esta a 1200 m: sem isto o quadro
    # sai vazio e parece que a cena nao existe
    dados.clip_start = 1.0
    dados.clip_end = 5000.0
    cam = bpy.data.objects.new("CamTopo", dados)
    cena.collection.objects.link(cam)
    cam.location = (centro[0], centro[1], 1200.0)

    # Olhando para baixo. O giro em Z compensa o norte do mapa: o satelite e
    # sempre norte-acima, e o +Y da cena esta girado 8,6 graus em relacao ao
    # norte verdadeiro. Sem isto a sobreposicao acusaria um erro que e so de
    # referencial.
    cam.rotation_euler = (0.0, 0.0, math.radians(-norte))
    cena.camera = cam

    cena.render.resolution_x = args.largura
    cena.render.resolution_y = args.altura
    cena.render.resolution_percentage = 100
    cena.render.image_settings.file_format = "PNG"
    cena.render.filepath = str(RAIZ / args.saida)

    # Rapido e chapado: aqui nao se julga luz, se julga posicao.
    cena.render.engine = "BLENDER_WORKBENCH"
    if hasattr(cena, "display"):
        cena.display.shading.light = "FLAT"
        cena.display.shading.color_type = "MATERIAL"
        cena.display.shading.show_xray = False

    print(f"topo ortografico: {dados.ortho_scale:.1f} m de largura, "
          f"{M_POR_PX:.5f} m/px")
    print(f"centrado na arena ({centro[0]:.1f}, {centro[1]:.1f})")
    print(f"camera girada {-norte:+.1f} graus para ficar norte-acima")

    bpy.ops.render.render(write_still=True)
    print(f"gravado: {cena.render.filepath}")


if __name__ == "__main__":
    main()
