#!/usr/bin/env python3
"""
Renderiza o filme plano a plano, a partir de um .blend ja construido por
build_scene.py. Rede de seguranca (Plano B) da proposta de render: o Plano A
e vestir e renderizar no Twinmotion, mas se o portao de sabado 12h nao
segurar a cena por VRAM, o filme sai daqui, sem sair do Blender.

Tres modos:

  Calibracao -- renderiza N quadros de um plano e cronometra. Decide se a
  noite de domingo fecha antes de prometer o cronograma:

      blender --background --python scripts/render_shots.py -- \\
          --blend out/cena.blend --plano P19 --quadros 24 --cronometrar

  Animatic -- rascunho rapido, resolucao e amostras baixas, para aprovacao
  do cliente na sexta. Vai para out/animatic/ por padrao:

      blender --background --python scripts/render_shots.py -- \\
          --blend out/cena.blend --animatic --escala 25

  Final -- render de entrega, retomavel. Pula quadro que ja existe em
  out/final/, entao um Ctrl+C ou uma queda de energia nao custa o que ja
  foi feito. Roda a noite inteira sem baba:

      blender --background --python scripts/render_shots.py -- \\
          --blend out/cena.blend

Sempre le data/planos.json (via scripts/planos.py) para saber a faixa de
quadros e a camera (CAM_<id>) de cada plano -- a mesma fonte que
build_scene.py usou para montar as cameras dentro do .blend.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy

import planos as planos_mod
import terreno


def planos_selecionados(pacote, filtro):
    if not filtro:
        return pacote["planos"]
    pedidos = set(filtro.split(","))
    sel = [p for p in pacote["planos"] if p["id"] in pedidos]
    faltando = pedidos - {p["id"] for p in sel}
    if faltando:
        raise SystemExit(f"plano(s) inexistente(s): {sorted(faltando)}")
    return sel


def quadros_do_plano(plano, limite=None):
    ini, fim = plano["_quadro_ini"], plano["_quadro_fim"]
    if limite:
        fim = min(fim, ini + limite - 1)
    return range(ini, fim + 1)


def renderizar_quadro(cena, quadro, destino):
    cena.frame_set(quadro)
    cena.render.filepath = str(destino / f"{quadro:05d}")
    bpy.ops.render.render(write_still=True)


def aplicar_rascunho(cena, escala):
    """Baixa resolucao e amostras para o animatic. Nao salva de volta no .blend."""
    cena.render.resolution_percentage = escala
    try:
        cena.eevee.taa_render_samples = 16
    except AttributeError:
        pass
    try:
        cena.render.use_motion_blur = False   # motion blur custa caro e nao ajuda a aprovar corte
    except AttributeError:
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--blend", required=True, help=".blend construido por build_scene.py")
    ap.add_argument("--planos-json", dest="planos_json", default="data/planos.json")
    ap.add_argument("--dados", default="data/mapa_agroshow26.json")
    ap.add_argument("--saida", default=None,
                    help="pasta de saida. Padrao: out/final, ou out/animatic com --animatic")
    ap.add_argument("--plano", default=None,
                    help="so estes planos (lista separada por virgula, ex: P13,P14,P15). "
                         "Sem isso, o filme inteiro")
    ap.add_argument("--quadros", type=int, default=None,
                    help="limita a N quadros por plano, a partir do inicio dele")
    ap.add_argument("--animatic", action="store_true",
                    help="rascunho rapido: resolucao reduzida, poucas amostras, sem motion blur")
    ap.add_argument("--escala", type=int, default=25,
                    help="resolution_percentage do animatic (padrao 25%%)")
    ap.add_argument("--cronometrar", action="store_true",
                    help="mede o tempo por quadro e projeta o filme inteiro. "
                         "Use com --plano e --quadros para calibrar antes do render de verdade")
    ap.add_argument("--forcar", action="store_true",
                    help="re-renderiza mesmo quadro ja existente em disco")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])

    if not Path(args.blend).exists():
        raise SystemExit(f"blend nao encontrado: {args.blend} -- rode build_scene.py --out primeiro")

    bpy.ops.wm.open_mainfile(filepath=str(Path(args.blend).resolve()))
    cena = bpy.context.scene

    dados = terreno.carregar_mapa(args.dados)
    pacote = planos_mod.carregar(args.planos_json, dados=dados)
    selecionados = planos_selecionados(pacote, args.plano)

    destino = Path(args.saida) if args.saida else Path("out/animatic" if args.animatic else "out/final")
    destino.mkdir(parents=True, exist_ok=True)

    if args.animatic:
        aplicar_rascunho(cena, args.escala)
        print(f"animatic: resolucao {args.escala}%, amostras baixas, sem motion blur -> {destino}")

    total_planos = len(selecionados)
    total_quadros = pulados = renderizados = 0
    tempos = []

    for i, plano in enumerate(selecionados, 1):
        cam = bpy.data.objects.get(f"CAM_{plano['id']}")
        if cam is None:
            print(f"  [{plano['id']}] SEM CAMERA no .blend -- pulando "
                  f"(rode build_scene.py com esse plano incluido)")
            continue
        cena.camera = cam

        quadros = list(quadros_do_plano(plano, args.quadros))
        titulo = plano["titulo"] or plano.get("nota", "")[:40]
        print(f"[{i}/{total_planos}] {plano['id']} · {titulo!r} · "
              f"{len(quadros)} quadros ({quadros[0]}-{quadros[-1]})")

        for quadro in quadros:
            total_quadros += 1
            arq = destino / f"{quadro:05d}.png"
            if arq.exists() and not args.forcar:
                pulados += 1
                continue

            t0 = time.time()
            renderizar_quadro(cena, quadro, destino)
            dt = time.time() - t0
            tempos.append(dt)
            renderizados += 1

            if args.cronometrar:
                print(f"    quadro {quadro:05d}: {dt:5.1f} s")

    print("\n" + "=" * 58)
    print(f"  quadros no lote ....... {total_quadros}")
    print(f"  ja existiam (pulados) . {pulados}")
    print(f"  renderizados agora .... {renderizados}")

    if tempos:
        media = sum(tempos) / len(tempos)
        print(f"  tempo medio/quadro .... {media:.1f} s")
        if args.cronometrar:
            projetado = media * pacote["total_quadros"]
            print(f"\n  CALIBRACAO -- projecao para o filme inteiro "
                  f"({pacote['total_quadros']} quadros):")
            print(f"    {projetado/3600:.1f} h de render")
            if projetado / 3600 > 11:
                print("    NAO CABE na noite de domingo (~11 h). "
                      "Corte samples, corte vegetacao distante, ou vai de Twinmotion.")
            else:
                print("    cabe na noite de domingo.")
    print("=" * 58)


if __name__ == "__main__":
    main()
