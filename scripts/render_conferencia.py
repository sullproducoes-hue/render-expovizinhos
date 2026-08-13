#!/usr/bin/env python3
"""
Renderiza quadros de conferencia da cena gerada por scripts/build_scene.py.

Nao e render de entrega: e o teste barato que responde "a camera esta vendo o
que deveria ver?" antes de gastar horas de fila. Roda em Cycles CPU, resolucao
reduzida e amostragem baixa com denoise, porque o ambiente remoto nao tem GPU.

Uso:
    python3 scripts/render_conferencia.py cena.blend --quadros 1,241,3600 \
        --saida docs --escala 35 --amostras 48

Sem --quadros, usa os marcadores de timeline que o gerador deixou na cena --
um por ponto do roteiro -- e renderiza os que forem pedidos por nome em
--pontos, ou o primeiro e o ultimo se nada for pedido.
"""

import argparse
import sys
from pathlib import Path

import bpy


def preparar_render(cena, escala, amostras):
    cena.render.engine = "CYCLES"
    cena.cycles.device = "CPU"
    cena.cycles.samples = amostras
    cena.cycles.use_denoising = True
    # Caminhos curtos: conferencia de enquadramento nao precisa de bounce longo,
    # e cada bounce a mais custa minutos por quadro na CPU.
    cena.cycles.max_bounces = 4
    cena.cycles.diffuse_bounces = 2
    cena.cycles.glossy_bounces = 2
    cena.cycles.transmission_bounces = 2
    cena.render.resolution_percentage = escala
    cena.render.image_settings.file_format = "PNG"


def resolver_quadros(cena, args):
    if args.quadros:
        return [int(q) for q in args.quadros.split(",") if q.strip()]
    marcadores = sorted(cena.timeline_markers, key=lambda m: m.frame)
    if args.pontos:
        alvos = [p.strip().lower() for p in args.pontos.split(",")]
        return [m.frame for m in marcadores
                if any(a in m.name.lower() for a in alvos)]
    if marcadores:
        return [marcadores[0].frame, marcadores[-1].frame]
    return [cena.frame_start, cena.frame_end]


def nome_do_quadro(cena, quadro):
    for m in cena.timeline_markers:
        if m.frame == quadro:
            return m.name.replace(" ", "-").lower()
    return f"quadro-{quadro}"


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("blend", help="arquivo .blend gerado por build_scene.py")
    ap.add_argument("--quadros", default=None, help="lista separada por virgula")
    ap.add_argument("--pontos", default=None,
                    help="filtra os marcadores do roteiro por trecho do nome")
    ap.add_argument("--saida", default="docs")
    ap.add_argument("--prefixo", default="conferencia")
    ap.add_argument("--escala", type=int, default=35,
                    help="porcentagem da resolucao de entrega")
    ap.add_argument("--amostras", type=int, default=48)
    args = ap.parse_args(argv)

    bpy.ops.wm.open_mainfile(filepath=str(Path(args.blend).resolve()))
    cena = bpy.context.scene
    preparar_render(cena, args.escala, args.amostras)

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)

    for quadro in resolver_quadros(cena, args):
        cena.frame_set(quadro)
        destino = saida / f"{args.prefixo}-{nome_do_quadro(cena, quadro)}.png"
        cena.render.filepath = str(destino.resolve())
        print(f"renderizando quadro {quadro} -> {destino}")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
