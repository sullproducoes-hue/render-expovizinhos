#!/usr/bin/env python3
"""Renderiza so os quadros-guia do Plano A -- os que viram entrada da IA.

Ordem do Natan em 15/08: *"preciso gerar as cenas no flow para posteriormente
animar (...) mas nao posso cometer erros o lugar tem que ser exatamente o lugar
onde sera o agroshow"*.

O que garante o lugar e **o quadro**, nao o prompt: cada clipe de Flow ou
Higgsfield recebe primeiro e ultimo quadro renderizados da cena medida, e a IA
so preenche o meio. Este script produz esses quadros. Quais sao eles sai de
`scripts/cenas_ia.py`, que quebra os 22 planos na grade de duracao da
plataforma.

    blender --background --python scripts/render_guias.py -- \\
        --blend out/cena.blend --plataforma flow

## As tres coisas que este render faz diferente do render do filme

**1. Sai em 16:9, nao em 2:1.** Nem o Flow nem o Higgsfield geram 2:1. Gera-se
em 16:9 e a entrega 2:1 sai cortando a faixa central do resultado. O corte e
seguro por construcao: toda camera da cena mira o alvo por constraint Track To,
entao o assunto esta no centro do quadro -- cortar topo e base simetricamente
nao pode perde-lo. E a largura nao muda: 16:9 e 2:1 tem a mesma horizontal, o
16:9 so tem mais ceu e mais chao.

O `sensor_fit` vai declarado em HORIZONTAL. No AUTO o Blender ajusta o sensor
pela maior dimensao e daria no mesmo hoje -- mas ai a moldura passaria a
depender da resolucao, que e fallback mudo, e a doutrina §12 e explicita.

**2. Sem letreiro.** Modelo generativo destroi tipografia: reescreve letra,
troca acento, inventa palavra. Passar as duas frases literais dele por uma IA
e a maneira mais rapida de perde-las. A colecao LETREIROS sai do quadro e o
texto entra na montagem, por cima do clipe pronto, onde a regra de 8%/4% da
altura continua valendo sobre o master 2760x1380.

**3. PNG, sem EXR e sem passe.** O destino e o upload num site. Cryptomatte,
normal e depth nao servem para nada aqui e custariam 20 MB por quadro.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy

import cenas_ia
import placa as placa_mod
import planos as planos_mod
import terreno

# 16:9 UHD. E generoso de proposito: o guia e barato (dezenas de quadros, nao
# milhares) e sobra de resolucao na entrada nunca atrapalhou modelo nenhum.
LARGURA_GUIA = 3840
ALTURA_GUIA = 2160

# A faixa que vira a entrega, dentro do 16:9.
ALTURA_2_1 = LARGURA_GUIA // 2


def preparar(cena, largura, altura):
    """16:9, sensor horizontal, PNG. E devolve o que foi mexido, para o log."""
    cena.render.resolution_x = largura
    cena.render.resolution_y = altura
    cena.render.resolution_percentage = 100
    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_depth = "8"
    # O PNG e entrega para o olho e para o upload: precisa do AgX assado.
    # (No EXR essa mesma chave tem de ficar DESLIGADA -- ver scripts/saida.py.)
    cena.render.image_settings.color_management = "FOLLOW_SCENE"
    cena.render.film_transparent = False

    for cam in bpy.data.cameras:
        cam.sensor_fit = "HORIZONTAL"

    return f"{largura}x{altura} ({largura/altura:.4f}:1), PNG 8, sensor HORIZONTAL"


def esconder_letreiros(cena):
    """Tira a colecao LETREIROS do render. Devolve quantos objetos sairam."""
    col = bpy.data.collections.get("LETREIROS")
    if col is None:
        return 0
    col.hide_render = True
    col.hide_viewport = True
    n = len(col.all_objects)
    # hide_render na colecao ja basta para o Cycles, mas objeto marcado a mao
    # dentro dela sobreviveria a um relink futuro. Marca os dois.
    for o in col.all_objects:
        o.hide_render = True
    return n


def mapa_de_quadros(lote):
    """quadro absoluto -> (id do plano, lista de clipes que o usam).

    Um quadro de emenda serve a dois clipes e e renderizado UMA vez. E disso
    que sai a economia: 51 quadros para 29 clipes, e nao 58.
    """
    mapa = {}
    for pl in lote["planos"]:
        for c in pl["clipes"]:
            for ponta, quadro in (("ini", c["quadro_ini"]), ("fim", c["quadro_fim"])):
                d = mapa.setdefault(quadro, {"plano": pl["id"], "usos": []})
                d["usos"].append(f"{c['id']}:{ponta}")
    return dict(sorted(mapa.items()))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--blend", required=True)
    ap.add_argument("--plataforma", default="flow", choices=("flow", "higgsfield"))
    ap.add_argument("--planos-json", dest="planos_json", default="data/planos.json")
    ap.add_argument("--dados", default="data/mapa_agroshow26.json")
    ap.add_argument("--saida", default=None,
                    help="pasta de saida. Padrao: out/cenas/<plataforma>/quadros")
    ap.add_argument("--largura", type=int, default=LARGURA_GUIA)
    ap.add_argument("--altura", type=int, default=ALTURA_GUIA)
    ap.add_argument("--forcar", action="store_true",
                    help="re-renderiza quadro que ja existe em disco")
    ap.add_argument("--permitir-cpu", action="store_true")
    ap.add_argument("--com-letreiro", action="store_true",
                    help="NAO esconde os letreiros. So para conferir moldura -- "
                         "quadro com texto nao vai para a IA")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:]
                         if "--" in sys.argv else sys.argv[1:])

    if not Path(args.blend).exists():
        raise SystemExit(f"blend nao encontrado: {args.blend} -- "
                         f"rode build_scene.py --out primeiro")

    bpy.ops.wm.open_mainfile(filepath=str(Path(args.blend).resolve()))
    cena = bpy.context.scene

    # PRIMEIRA coisa depois de abrir: o dispositivo mora nas preferencias, nao
    # no .blend, e sem isto o Cycles cai para a CPU sem avisar (RETOMAR, 23).
    if args.permitir_cpu:
        placa_mod.ligar(cena)
    else:
        placa_mod.exigir(cena)

    dados = terreno.carregar_mapa(args.dados)
    pacote = planos_mod.carregar(args.planos_json, dados=dados)
    contrato = cenas_ia.carregar_contrato()
    lote = cenas_ia.montar(pacote, contrato, args.plataforma)

    # Blender resolve caminho relativo contra a raiz do DRIVE, nao contra o cwd
    # (RETOMAR, 28): --saida out/x ja gravou em C:\out\x. Absoluto, sempre.
    destino = Path(args.saida) if args.saida else Path(
        f"out/cenas/{args.plataforma}/quadros")
    destino = destino.resolve()
    destino.mkdir(parents=True, exist_ok=True)

    print(f"render dos quadros-guia: {preparar(cena, args.largura, args.altura)}")
    faixa = args.largura // 2
    corte = (args.altura - faixa) // 2
    print(f"faixa 2:1 da entrega ..... {args.largura}x{faixa}, "
          f"cortando {corte} px de cada lado")

    if args.com_letreiro:
        print("letreiros: MANTIDOS -- este lote NAO serve para a IA")
    else:
        print(f"letreiros: escondidos ({esconder_letreiros(cena)} objetos) -- "
              f"texto entra na montagem")

    mapa = mapa_de_quadros(lote)
    print(f"plataforma {args.plataforma}: {lote['clipes']} clipes, "
          f"{len(mapa)} quadros-guia\n")

    feitos = pulados = 0
    tempos = []
    for quadro, info in mapa.items():
        cam = bpy.data.objects.get(f"CAM_{info['plano']}")
        if cam is None:
            print(f"  [{quadro:05d}] SEM CAMERA CAM_{info['plano']} no .blend "
                  f"-- pulando")
            continue
        cena.camera = cam

        arq = destino / f"{quadro:05d}.png"
        if arq.exists() and not args.forcar:
            pulados += 1
            continue

        cena.frame_set(quadro)
        cena.render.filepath = str(arq.with_suffix(""))
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        dt = time.time() - t0
        tempos.append(dt)
        feitos += 1
        print(f"  {quadro:05d}.png  {info['plano']:4}  {dt:5.1f} s  "
              f"<- {', '.join(info['usos'])}")

    print("\n" + "=" * 62)
    print(f"  quadros no lote ....... {len(mapa)}")
    print(f"  ja existiam ........... {pulados}")
    print(f"  renderizados agora .... {feitos}")
    if tempos:
        media = sum(tempos) / len(tempos)
        print(f"  tempo medio/quadro .... {media:.1f} s")
        print(f"  o lote inteiro ........ {media * len(mapa) / 60:.1f} min")
        print(f"  o filme todo seria .... "
              f"{media * pacote['total_quadros'] / 3600:.1f} h "
              f"({pacote['total_quadros']} quadros)")
    print(f"  saida ................. {destino}")
    print("=" * 62)


if __name__ == "__main__":
    main()
