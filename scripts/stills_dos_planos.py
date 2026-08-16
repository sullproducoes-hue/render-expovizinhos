#!/usr/bin/env python3
"""Um quadro de cada um dos 22 planos -- a entrega que ele pediu.

Nao e' animatic: e' UM still por plano, no meio do plano, na resolucao de
entrega e com a configuracao de Cycles dele. Serve para julgar enquadramento e
luz sem gastar as 12,9 h do filme inteiro.

Duas armadilhas do projeto valem aqui, e as duas ja custaram uma rodada:

  * o dispositivo mora nas PREFERENCIAS, nao no .blend -- sem `placa.ligar()`
    depois de abrir, o Cycles cai para CPU em silencio e o still leva 36 s em
    vez de 10 (ESTADO.md, "o que estava errado antes");
  * marcador de timeline VENCE `scene.camera` (armadilha 34) -- aqui isso e' a
    favor: basta pular para o quadro certo que o marcador troca a camera.

Uso:
    blender out/cena.blend --background --python scripts/stills_dos_planos.py
    blender out/cena.blend --background --python scripts/stills_dos_planos.py -- --escala 50
"""

import argparse
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))

RAIZ = Path(__file__).resolve().parent.parent


def _quadro_do_letreiro(cena, marca, prox):
    """Quadro a fotografar: o meio do trecho em que o LETREIRO aparece.

    O meio do plano parece a escolha obvia e deixou de ser em 15/08: desde que
    o letreiro acende so' no trecho em que cabe no quadro, o meio do plano pode
    cair num instante em que ele esta apagado -- e o still sairia sem o
    letreiro, provando o contrario do que se quer provar. Sem letreiro no
    plano, volta a ser o meio.
    """
    nome = (marca.camera.name if marca.camera else marca.name).replace("CAM_", "")
    obj = bpy.data.objects.get(f"Letreiro_{nome}")
    meio = (marca.frame + prox) // 2
    if obj is None:
        cena.frame_set(meio)
        return meio

    acesos = []
    for q in range(marca.frame, prox + 1, 2):
        cena.frame_set(q)
        if not obj.hide_render:
            acesos.append(q)
    alvo = (acesos[len(acesos) // 2] if acesos else meio)
    cena.frame_set(alvo)
    return alvo


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="out/entrega-1508/planos")
    ap.add_argument("--escala", type=int, default=100)
    args = ap.parse_args(argv)

    cena = bpy.context.scene

    try:
        import placa
        placa.ligar()
    except Exception as e:                      # nao renderiza no escuro
        raise SystemExit(f"GPU nao ligou ({e}) -- abortando: still em CPU "
                         f"leva 3x mais e engana a medicao de custo")

    marcas = sorted(cena.timeline_markers, key=lambda m: m.frame)
    if not marcas:
        raise SystemExit("cena sem marcador de plano -- nada a renderizar")

    fim = cena.frame_end
    saida = RAIZ / args.saida
    saida.mkdir(parents=True, exist_ok=True)

    cena.render.resolution_percentage = args.escala
    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_mode = "RGB"
    cena.render.film_transparent = False

    print(f"{len(marcas)} planos  |  "
          f"{cena.render.resolution_x * args.escala // 100}x"
          f"{cena.render.resolution_y * args.escala // 100}  |  "
          f"{cena.cycles.samples} samples")

    for i, m in enumerate(marcas):
        prox = marcas[i + 1].frame if i + 1 < len(marcas) else fim
        meio = _quadro_do_letreiro(cena, m, prox)
        nome = (m.camera.name if m.camera else m.name).replace("CAM_", "")
        alvo = saida / f"{nome}.png"
        cena.render.filepath = str(alvo)
        print(f"  {nome:<6} quadro {meio:>5} de {m.frame}-{prox}", flush=True)
        bpy.ops.render.render(write_still=True)

    print(f"\ngravado em: {saida}")


if __name__ == "__main__":
    main()
