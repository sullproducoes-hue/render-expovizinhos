#!/usr/bin/env python3
"""Folha de prova da concha: dois quadros, um de frente e um de topo.

    blender --background out/cena.blend --python scripts/prova_concha.py

Existe porque `nada entra em contrato sem folha de prova` -- a regra que as
tres caixas de amostra erradas desta sessao ensinaram. Geometria nova que
ninguem olhou e geometria que pode estar deitada, torta ou dentro do chao, e
nenhuma dessas tres da erro na tela.

Roda `placa.ligar()` primeiro: a GPU nao mora no `.blend` (armadilha 23).
"""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import placa  # noqa: E402

SAIDA = RAIZ / "out" / "concha"


def alvo():
    o = bpy.data.objects.get("ConchaPalco")
    if o is None:
        raise SystemExit("ConchaPalco nao esta na cena")
    pontos = [f for p in o.children
              for f in (p.matrix_world @ Vector(c) for c in p.bound_box)]
    mn = Vector((min(p.x for p in pontos), min(p.y for p in pontos),
                 min(p.z for p in pontos)))
    mx = Vector((max(p.x for p in pontos), max(p.y for p in pontos),
                 max(p.z for p in pontos)))
    return o, (mn + mx) / 2.0, mx - mn


def por_camera(nome, centro, olho):
    cam = bpy.data.cameras.new(nome)
    cam.lens = 35.0
    ob = bpy.data.objects.new(nome, cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = olho
    d = (centro - Vector(olho))
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def main():
    placa.ligar()
    o, centro, tam = alvo()
    print(f"ConchaPalco em ({o.location.x:.1f}, {o.location.y:.1f}, "
          f"{o.location.z:.1f})  caixa {tam.x:.1f} x {tam.y:.1f} x {tam.z:.1f} m")

    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.render.resolution_percentage = 100
    sc.cycles.samples = 64
    SAIDA.mkdir(parents=True, exist_ok=True)

    # ARMADILHA: os 22 planos do filme estao presos a MARCADORES de timeline, e
    # marcador de camera VENCE `scene.camera` na hora do render. Sem limpar, as
    # duas provas saem identicas -- e saem com a camera de um plano qualquer,
    # sem erro nenhum na tela. Foi o que aconteceu na primeira tentativa.
    n = len(sc.timeline_markers)
    sc.timeline_markers.clear()
    print(f"  {n} marcadores de camera removidos desta sessao (o .blend em disco nao muda)")

    vistas = {
        "frente": Vector((centro.x - 6, centro.y - 46, centro.z + 9)),
        "topo": Vector((centro.x + 2, centro.y - 18, centro.z + 52)),
    }
    for nome, olho in vistas.items():
        sc.camera = por_camera(f"prova_{nome}", centro, olho)
        sc.render.filepath = str(SAIDA / nome)
        bpy.ops.render.render(write_still=True)
        print(f"  {nome}: {SAIDA / (nome + '.png')}")


if __name__ == "__main__":
    main()
