#!/usr/bin/env python3
"""Confere se a sombra no chao vem de onde o sol esta no ceu do fundo.

Este e o teste que separa render de CG, e o teste obvio NAO serve: montar um
mastro e medir o azimute da sombra so valida a SUN contra ela mesma, porque o
disco do HDRI esta estourado e macio de proposito (evs_cap 12) e nao joga
sombra. O desalinhamento que este teste existe para pegar passaria batido.

Entao o quadro tem que conter as DUAS coisas ao mesmo tempo:
  (a) a sombra do mastro no chao
  (b) o disco solar do HDRI no ceu

Camera baixa, horizonte na moldura, olhando na direcao do sol. Se estiver
casado, a sombra vem na direcao da camera e o sol esta no alto do quadro. Se o
sinal da rotacao estiver trocado, o sol aparece atras e a sombra foge -- e se
descobre em tres segundos, nao depois de 39 horas de render.

Uso:
    blender --background --python scripts/conferir_sol.py
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy
from mathutils import Vector

import build_scene as bs
import sol

RAIZ = Path(__file__).resolve().parent.parent


def main():
    luz = json.loads((RAIZ / "data" / "luz.json").read_text(encoding="utf-8"))
    elev, azim, rot, medido = bs.alvo_do_sol(luz)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bs.garantir_addon_cycles()
    cena = bpy.context.scene

    col = bpy.data.collections.new("TESTE")
    cena.collection.children.link(col)

    # chao grande e um mastro de 10 m na origem
    bpy.ops.mesh.primitive_plane_add(size=400.0, location=(0, 0, 0))
    chao = bpy.context.active_object
    mat = bpy.data.materials.new("MAT_CHAO")
    mat.use_nodes = True
    b = mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.35, 0.35, 0.33, 1.0)
    b.inputs["Roughness"].default_value = 0.9
    chao.data.materials.append(mat)

    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.35, depth=10.0,
                                        location=(0, 0, 5.0))
    bpy.context.active_object.data.materials.append(mat)

    bs.construir_luz(col, luz, elev, azim, medido)
    bs.construir_ceu(cena, luz, rot)
    bs.configurar_cor(cena, luz)

    # Camera baixa, OLHANDO NA DIRECAO DO SOL: e o unico jeito de ter o disco
    # solar e a sombra no mesmo quadro.
    d = Vector(sol.direcao(elev, azim))
    cam_dados = bpy.data.cameras.new("CamTeste")
    cam_dados.lens = 24.0
    cam = bpy.data.objects.new("CamTeste", cam_dados)
    col.objects.link(cam)
    # atras do mastro, no lado oposto ao sol, a 3 m de altura
    cam.location = (-d.x * 42.0, -d.y * 42.0, 3.0)
    alvo = Vector((0.0, 0.0, 6.0))
    cam.rotation_euler = (alvo - cam.location).to_track_quat("-Z", "Y").to_euler()
    cena.camera = cam

    bs.configurar_render(cena, "cycles")
    cena.render.resolution_x, cena.render.resolution_y = 480, 240
    cena.cycles.samples = 32
    cena.render.filepath = str(RAIZ / "out" / "conferir-sol.png")
    cena.render.image_settings.file_format = "PNG"

    print(f"\nCONFERINDO O CASAMENTO SOL x CEU")
    print(f"  elevacao {elev:.1f}  azimute na cena {azim:.1f}")
    print(f"  ceu girado {rot:.1f} graus")
    print(f"  camera em ({cam.location.x:.0f}, {cam.location.y:.0f}) "
          f"olhando para o sol")
    print(f"  ESPERADO: disco solar no alto do quadro, sombra do mastro "
          f"vindo NA DIRECAO da camera.")

    bpy.ops.render.render(write_still=True)
    print(f"gravado: {cena.render.filepath}")

    # Segundo quadro com a exposicao no chao. O HDRI escolhido tem o disco
    # solar estourado e macio de proposito (evs_cap 12), entao na exposicao de
    # trabalho ele nao aparece como disco -- vira ceu claro. Puxando a
    # exposicao para baixo, so a regiao do sol sobra, e da para conferir se ela
    # esta do mesmo lado da sombra. Isto e instrumento de medida, nao look.
    cena.view_settings.exposure = -6.0
    cena.render.filepath = str(RAIZ / "out" / "conferir-sol-escuro.png")
    bpy.ops.render.render(write_still=True)
    print(f"gravado: {cena.render.filepath}  (exposure -6, so para achar o sol)")


if __name__ == "__main__":
    main()
