#!/usr/bin/env python3
"""Quanto a vegetacao custa por quadro, medido -- nao estimado.

Ordem do Natan em 14/08: *"medir o custo da vegetacao antes de escolher o teto
de horas"*. Entao aqui nao ha regra de bolso: renderiza-se o MESMO quadro duas
vezes, com e sem as arvores, na resolucao de master e com a configuracao de
render dele (128 samples, OptiX, denoise). A diferenca e o custo.

O quadro e o da CAMERA ATIVA da cena -- hoje a do P01. Para medir o pior caso,
que e o sobrevoo alto com mais copa no campo de visao, ative a camera do P11
antes de rodar.

Uso:
    blender --background out/cena.blend --python scripts/cronometrar_vegetacao.py
"""

import sys
import time
from pathlib import Path

import bpy

RAIZ = Path(__file__).resolve().parent.parent
LARG, ALT = 2760, 1380


def arvores():
    return [o for o in bpy.data.objects if o.name.startswith("Arvore_")]


def renderizar(saida):
    c = bpy.context.scene
    c.render.resolution_x, c.render.resolution_y = LARG, ALT
    c.render.resolution_percentage = 100
    c.render.filepath = str(saida)
    c.render.image_settings.file_format = "PNG"
    t = time.perf_counter()
    bpy.ops.render.render(write_still=True)
    return time.perf_counter() - t


def main():
    cena = bpy.context.scene
    arv = arvores()
    verts_arv = sum(len(o.data.vertices) for o in arv) if arv else 0
    malhas = {o.data.name for o in arv}
    print(f"arvores: {len(arv)} objetos, {len(malhas)} malha(s) compartilhada(s)")
    print(f"  vertices SE cada uma tivesse malha propria: {verts_arv:,}")
    print(f"  vertices de verdade em memoria: "
          f"{sum(len(bpy.data.meshes[m].vertices) for m in malhas):,}")

    cam = cena.camera
    print(f"camera: {cam.name if cam else 'NENHUMA'}   "
          f"{cena.cycles.samples} samples   {cena.cycles.device}")
    if cam is None:
        raise SystemExit("cena sem camera ativa")

    saida = RAIZ / "out" / "cronometro"
    com = renderizar(saida / "com-arvores.png")
    print(f"\ncom arvores ..... {com:6.1f} s/quadro")

    for o in arv:
        o.hide_render = True
    sem = renderizar(saida / "sem-arvores.png")
    print(f"sem arvores ..... {sem:6.1f} s/quadro")

    custo = com - sem
    print(f"\ncusto da vegetacao: {custo:+.1f} s/quadro "
          f"({custo / max(sem, 1e-6) * 100:+.0f}%)")

    quadros = 4635
    print(f"\nno filme inteiro ({quadros} quadros, 154 s a 30 fps):")
    print(f"  sem vegetacao ... {sem * quadros / 3600:5.1f} h")
    print(f"  com vegetacao ... {com * quadros / 3600:5.1f} h")
    print(f"  a vegetacao custa {custo * quadros / 3600:+.1f} h")
    print("\nAtencao: numero de cena CRUA, sem textura e sem gente. "
          "Recronometrar depois da textura -- ver ESTADO.md.")


if __name__ == "__main__":
    main()
