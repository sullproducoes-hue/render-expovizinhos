#!/usr/bin/env python3
"""Folha de provas da textura: 2 enquadramentos x com e sem.

Antes e depois no MESMO quadro, porque textura e das coisas que quem fez sempre
acha que melhorou. Sem o par lado a lado nao ha como saber se o gramado deixou
de ler como feltro ou se so ficou mais escuro.

Os dois enquadramentos respondem perguntas diferentes, e as duas podem falhar
sozinhas:

* **alto** -- a camera de sobrevoo. Aqui o risco e o PADRAO REPETIDO: a grama
  tem 15 m de lado e o terreno tem 808. Se aparecer grade, a escolha da textura
  esta errada, nao a forca.
* **baixo** -- camera a 6 m junto da arena, que e a altura que o Natan mandou
  usar em lugar aberto (4-15 m). Aqui aparecem as tres que importam de perto:
  a onda da telha pegando o sol rasante, a brita da via e o chao batido.

Mede tambem o tempo por quadro com e sem, que e a pendencia aberta no ESTADO.md
("recronometrar depois da textura") -- de graca, ja que os quatro renders rodam.

Uso:
    blender --background out/cena.blend --python scripts/provas_textura.py
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy
from mathutils import Vector

import build_scene as bs
import sol
import terreno

RAIZ = Path(__file__).resolve().parent.parent
LARG, ALT = 1380, 690


def desligar_textura(mats):
    """Devolve os materiais ao estado de cor chapada, guardando o que tirou.

    Nao apaga no: DESLIGA o link e repoe o valor declarado em MATERIAIS. Assim
    o "sem textura" e exatamente a cena de antes desta rodada, e nao uma cena
    onde a textura sumiu junto com outra coisa.

    O terreno e o caso que exige cuidado: a Base Color dele vem da mistura das
    DUAS GRAMAS MEDIDAS, que nao e textura e nao pode cair aqui. Por isso a
    Base Color so e mexida onde ha um MULTIPLY vindo da textura.
    """
    guardado = []
    for nome, mat in mats.items():
        if nome not in bs.MATERIAIS:
            continue
        cor, rug, _met = bs.MATERIAIS[nome]
        nt = mat.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        if not bsdf:
            continue

        for entrada, valor in (("Normal", None),
                               ("Roughness", rug),
                               ("Base Color", (*cor, 1.0))):
            campo = bsdf.inputs.get(entrada)
            if not campo or not campo.links:
                continue
            link = campo.links[0]
            origem = link.from_socket

            # Base Color: so desliga se quem alimenta e o MULTIPLY da textura.
            # Se for o Mix das duas gramas, fica -- aquilo e medida.
            if entrada == "Base Color":
                no = link.from_node
                if not (no.bl_idname == "ShaderNodeMix"
                        and getattr(no, "blend_type", "") == "MULTIPLY"):
                    continue

            guardado.append((nt, origem, campo))
            nt.links.remove(link)
            if valor is not None:
                campo.default_value = valor
    return guardado


def religar_textura(guardado):
    for nt, origem, campo in guardado:
        nt.links.new(origem, campo)


def camera(cena, col, centro, elev, azim, perto):
    """`perto=False` repete a camera das provas de luz (48 m, contra o sol).
    `perto=True` desce para 6 m, a altura que ele mandou usar em area aberta."""
    d = Vector(sol.direcao(elev, azim))
    raio, altura, lente = (55.0, 6.0, 50.0) if perto else (210.0, 48.0, 35.0)
    pos = Vector((centro[0] - d.x * raio, centro[1] - d.y * raio, altura))
    z = terreno.elevacao(centro[0], centro[1], centro)
    alvo = Vector((centro[0], centro[1], z + (3.0 if perto else 8.0)))

    dados = bpy.data.cameras.new("CamTextura")
    dados.lens = lente
    # a 6 m do chao a camera fica dentro do recinto: sem isto o clip_start
    # padrao ja basta, mas o clip_end de 100 m corta o fundo e o quadro
    # parece vazio -- e a armadilha 11 do RETOMAR.md, na outra ponta
    dados.clip_end = 4000.0
    cam = bpy.data.objects.new("CamTextura", dados)
    col.objects.link(cam)
    cam.location = pos
    cam.rotation_euler = (alvo - pos).to_track_quat("-Z", "Y").to_euler()
    cena.camera = cam
    return cam


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="out/textura")
    args = ap.parse_args(argv)

    cena = bpy.context.scene
    luz = json.loads((RAIZ / "data" / "luz.json").read_text(encoding="utf-8"))
    elev, azim, _rot, _medido = bs.alvo_do_sol(luz)

    pista = bpy.data.objects.get("PistaArena")
    centro = (pista.location.x, pista.location.y) if pista else (0.0, 0.0)
    col = bpy.data.collections.get("LUZ") or cena.collection

    cena.render.resolution_x, cena.render.resolution_y = LARG, ALT
    cena.render.image_settings.file_format = "PNG"

    saida = RAIZ / args.saida
    saida.mkdir(parents=True, exist_ok=True)

    mats = {m.name: m for m in bpy.data.materials}
    tempos = {}

    for perto in (False, True):
        rotulo_enq = "baixo" if perto else "alto"
        for o in list(bpy.data.objects):
            if o.type == "CAMERA":
                bpy.data.objects.remove(o, do_unlink=True)
        camera(cena, col, centro, elev, azim, perto)

        for com in (True, False):
            guardado = [] if com else desligar_textura(mats)
            alvo = saida / f"textura_{rotulo_enq}_{'com' if com else 'sem'}.png"
            cena.render.filepath = str(alvo)
            t0 = time.time()
            bpy.ops.render.render(write_still=True)
            dt = time.time() - t0
            tempos[(rotulo_enq, com)] = dt
            if not com:
                religar_textura(guardado)
            print(f"  {alvo.name}  {dt:.1f} s")

    print("\ncusto da textura (1380x690, metade do master em cada eixo):")
    print("enquadramento     sem       com      delta")
    for enq in ("alto", "baixo"):
        s, c = tempos[(enq, False)], tempos[(enq, True)]
        print(f"{enq:15s} {s:6.1f} s  {c:6.1f} s  {(c / s - 1) * 100:+6.1f}%")
    print("\nEm 1380x690 -- o master 2760x1380 custa ~4x isto por quadro.")


if __name__ == "__main__":
    main()
