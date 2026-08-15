#!/usr/bin/env python3
"""
Portao de camera: acusa plano cuja camera nasce ou morre DENTRO de geometria.

Nasceu de um defeito real, achado em 15/08 na folha de quadros-chave: de 22
planos, quatro davam quadro preto ou chapado (P08 fim, P09 ini, P12 fim, P19
fim) e um enchia a tela com a parede da concha (P20). Sao 4.635 quadros de
render que sairiam errados sem ninguem ver antes.

O conferidor de `planos.py` mede VELOCIDADE e nao ve isso: um plano pode estar
dentro da faixa cinematografica e mesmo assim ter a camera enterrada num
predio. Sao duas checagens diferentes e as duas precisam existir.

Tres testes, do mais barato ao mais caro:

  1. a camera esta ABAIXO do terreno naquele ponto (raycast para baixo);
  2. a camera esta DENTRO de um objeto fechado -- raio para fora, contagem de
     cruzamentos impar;
  3. o primeiro objeto na direcao da mira esta a menos de `--folga` metros.

    "C:\\...\\blender.exe" --background --python scripts/conferir_camera.py -- \\
        --blend out/cena.blend
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy
from mathutils import Vector

import planos as planos_mod
import terreno

DIRECOES = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))]


def cruzamentos(cena, dg, origem, direcao, limite=2000.0):
    """Quantas vezes um raio a partir de `origem` atravessa geometria."""
    n = 0
    p = origem.copy()
    for _ in range(64):
        ok, loc, _, _, _, _ = cena.ray_cast(dg, p, direcao, distance=limite)
        if not ok:
            break
        n += 1
        p = loc + direcao * 0.01
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--blend", required=True)
    ap.add_argument("--planos-json", dest="planos_json", default="data/planos.json")
    ap.add_argument("--dados", default="data/mapa_agroshow26.json")
    ap.add_argument("--folga", type=float, default=8.0,
                    help="metros minimos entre a camera e a primeira superficie na mira")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])

    bpy.ops.wm.open_mainfile(filepath=str(Path(args.blend).resolve()))
    cena = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()

    dados = terreno.carregar_mapa(args.dados)
    pacote = planos_mod.carregar(args.planos_json, dados=dados)

    problemas = []
    print(f"{'plano':6} {'ponta':5} {'z_cam':>8} {'z_solo':>8} {'dentro':>7} {'mira_m':>8}")
    for plano in pacote["planos"]:
        cam = bpy.data.objects.get(f"CAM_{plano['id']}")
        if cam is None:
            problemas.append(f"{plano['id']}: sem camera no .blend")
            continue
        for ponta, quadro in (("ini", plano["_quadro_ini"]), ("fim", plano["_quadro_fim"])):
            cena.frame_set(quadro)
            bpy.context.view_layer.update()   # armadilha 18: matrix_world sem update mente
            pos = cam.matrix_world.translation.copy()
            mira = (cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))).normalized()

            ok, loc, _, _, _, _ = cena.ray_cast(dg, pos, Vector((0, 0, -1)), distance=500.0)
            z_solo = loc.z if ok else float("nan")
            enterrada = bool(ok) and (pos.z - z_solo) < 0.5

            impares = sum(1 for d in DIRECOES if cruzamentos(cena, dg, pos, d) % 2 == 1)
            dentro = impares >= 3   # 3 de 4 direcoes concordando

            ok2, loc2, _, _, _, _ = cena.ray_cast(dg, pos, mira, distance=2000.0)
            dist_mira = (loc2 - pos).length if ok2 else float("inf")

            marca = ""
            if enterrada:
                marca += " ENTERRADA"
                problemas.append(f"{plano['id']} {ponta}: camera abaixo do solo "
                                 f"(z {pos.z:.1f} contra solo {z_solo:.1f})")
            if dentro:
                marca += " DENTRO"
                problemas.append(f"{plano['id']} {ponta}: camera dentro de geometria fechada")
            if dist_mira < args.folga:
                marca += " COLADA"
                problemas.append(f"{plano['id']} {ponta}: superficie a {dist_mira:.1f} m na mira "
                                 f"(folga minima {args.folga:.1f} m)")
            print(f"{plano['id']:6} {ponta:5} {pos.z:8.1f} {z_solo:8.1f} "
                  f"{'sim' if dentro else 'nao':>7} {dist_mira:8.1f}{marca}")

    print("\n" + "=" * 58)
    if problemas:
        print(f"  {len(problemas)} PROBLEMA(S):")
        for p in problemas:
            print(f"    - {p}")
        print("=" * 58)
        raise SystemExit(1)
    print("  nenhum plano com camera enterrada, dentro ou colada.")
    print("=" * 58)


if __name__ == "__main__":
    main()
