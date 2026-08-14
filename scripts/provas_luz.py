#!/usr/bin/env python3
"""Renderiza a folha de provas da luz: 2 HDRIs x 2 enquadramentos.

Nao cruza tres eixos. A regua de cor e fixada e declarada (nao muda a cena,
muda como se olha para ela), e o horizonte e decisao tecnica -- entao sobram
HDRI x enquadramento, que sao os dois que mudam o filme.

Os dois enquadramentos existem porque a 10 graus de elevacao **contraluz e sol
nas costas sao dois filmes diferentes**: escolher HDRI olhando so um deles e
escolher errado.

Provas em 1380x690 -- o nativo do painel P2,9, metade do master em cada eixo,
~1/4 do tempo por quadro.

Uso:
    blender --background --python scripts/provas_luz.py -- --energia 2.0
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy
from mathutils import Vector

import build_scene as bs
import sol
import terreno

RAIZ = Path(__file__).resolve().parent.parent

# 1380x690: nativo do painel. O master continua 2760x1380 -- aqui e prova.
LARG, ALT = 1380, 690


def camera_de_prova(cena, col, centro, elev, azim, contra_o_sol):
    """Camera sobre a bacia, alta o bastante para ver talude e estruturas.

    `contra_o_sol=True` poe a camera do lado oposto ao sol olhando para ele:
    e o enquadramento onde o ceu, o haze e a silhueta aparecem, e onde um
    HDRI ruim denuncia. `False` poe o sol nas costas, que e onde a cor do
    material e a sombra longa aparecem.
    """
    d = Vector(sol.direcao(elev, azim))
    raio, altura = 210.0, 48.0
    lado = 1.0 if contra_o_sol else -1.0
    pos = Vector((centro[0] - d.x * raio * lado,
                  centro[1] - d.y * raio * lado,
                  altura))
    alvo = Vector((centro[0], centro[1],
                   terreno.elevacao(centro[0], centro[1], centro) + 8.0))

    dados = bpy.data.cameras.new("CamProva")
    dados.lens = 35.0
    cam = bpy.data.objects.new("CamProva", dados)
    col.objects.link(cam)
    cam.location = pos
    cam.rotation_euler = (alvo - pos).to_track_quat("-Z", "Y").to_euler()
    cena.camera = cam
    return cam


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", default="out/cena.blend")
    ap.add_argument("--energia", type=float,
                    help="sobrepoe a energia da SUN do luz.json")
    ap.add_argument("--saida", default="out/luz")
    args = ap.parse_args(argv)

    luz = json.loads((RAIZ / "data" / "luz.json").read_text(encoding="utf-8"))
    if args.energia is not None:
        luz["sol"]["energia"] = args.energia

    bpy.ops.wm.open_mainfile(filepath=str(RAIZ / args.blend))
    cena = bpy.context.scene
    dados_mapa = None

    # centro da arena: a cena ja tem a pista construida la
    pista = bpy.data.objects.get("PistaArena")
    centro = (pista.location.x, pista.location.y) if pista else (0.0, 0.0)

    col = bpy.data.collections.get("LUZ") or cena.collection
    for o in list(col.objects):
        if o.type in {"LIGHT", "CAMERA"}:
            bpy.data.objects.remove(o, do_unlink=True)

    cena.render.resolution_x, cena.render.resolution_y = LARG, ALT
    cena.render.image_settings.file_format = "PNG"
    bs.configurar_cor(cena, luz)

    saida = RAIZ / args.saida
    saida.mkdir(parents=True, exist_ok=True)

    candidatos = [Path(c["arquivo"]).stem for c in luz["hdri"]["candidatos"]]
    feitos = []

    for slug in candidatos:
        luz_var = json.loads(json.dumps(luz))
        luz_var["hdri"]["escolhido"] = slug
        elev, azim, rot, medido = bs.alvo_do_sol(luz_var)

        # limpa o sol anterior
        for o in list(bpy.data.objects):
            if o.type == "LIGHT":
                bpy.data.objects.remove(o, do_unlink=True)

        bs.construir_luz(col, luz_var, elev, azim, medido)
        bs.construir_ceu(cena, luz_var, rot)

        curto = slug.replace("_puresky_4k", "").replace("_4k", "")
        dif = abs(elev - medido["elevacao_deg"]) if medido else None
        print(f"\n{curto}: ceu girado {rot:.1f}, SUN a {elev:.1f} graus, "
              f"sol do HDRI a {medido['elevacao_deg']:.1f} "
              f"(diferenca {dif:.1f})")

        for contra in (True, False):
            for o in list(bpy.data.objects):
                if o.type == "CAMERA":
                    bpy.data.objects.remove(o, do_unlink=True)
            camera_de_prova(cena, col, centro, elev, azim, contra)

            rotulo = "contra" if contra else "costas"
            alvo = saida / f"luz_{curto}_{rotulo}.png"
            cena.render.filepath = str(alvo)
            bpy.ops.render.render(write_still=True)
            feitos.append(alvo.name)
            print(f"  {alvo.name}")

    print(f"\n{len(feitos)} provas em {saida}")
    for f in feitos:
        print(f"  {f}")


if __name__ == "__main__":
    main()
