#!/usr/bin/env python3
"""Passos 0.3 e 0.4: mede VRAM e compara as duas configuracoes de amostragem.

    blender --background out/cena.blend --python scripts/medir_render.py -- \\
        --plano P13 --saida out/medicao

**Por que os dois juntos.** Sao a mesma pergunta feita duas vezes: quanto custa
um quadro nesta maquina, e o que se perde cortando. E os dois precisam do MESMO
quadro para as respostas serem comparaveis.

**A escolha do quadro nao e livre** (revisao do plano, 15/08): tem que ser o
mais ruidoso, nao um facil. Ruido mora onde ha luz indireta -- sombra dentro de
pavilhao, chapa metalica glossy. Medir num quadro limpo diz que 128 samples
basta e a fila inteira desmente isso depois.

**E a comparacao tem que ser com E sem denoise.** Com um OpenImageDenoise bom,
128/0,1 pode empatar visualmente com 0,01/max -- e ai o numero que vai para o
Natan deixa de ser "ruido contra tempo" e vira "0,01 custa +X% por ganho que
ninguem ve". Sao decisoes muito diferentes de tomar.

O ruido e medido, nao olhado: desvio-padrao local mediano em janela 3x3 sobre a
luminancia. Quadro com mais granulado tem desvio local maior, e a mediana
ignora as bordas de geometria, que tambem tem desvio alto e nao sao ruido.
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy

CONFIGS = [
    # nome,           samples, limiar, denoise
    ("128/0,1  sem denoise", 128,   0.1,   False),
    ("128/0,1  com denoise", 128,   0.1,   True),
    ("max/0,01 sem denoise", 4096,  0.01,  False),
    ("max/0,01 com denoise", 4096,  0.01,  True),
]


def vram_do_relatorio(cena):
    """Le a memoria de pico que o Cycles reporta na cena, se houver."""
    for chave in ("memory", "peak_memory"):
        v = cena.get(chave)
        if v:
            return v
    return None


def garantir_gpu(cena):
    """Liga a placa nas preferencias e DIZ o que achou.

    **Esta funcao existe por causa de um achado desta medicao.** A cena guarda
    `cycles.device = 'GPU'`, mas o dispositivo em si mora nas PREFERENCIAS, que
    sao da instalacao e nao do arquivo. Aberto numa sessao limpa, o .blend
    anunciava GPU e as preferencias vinham com `compute_device_type = NONE` e
    nenhum dispositivo marcado -- que e o fallback silencioso para CPU que a
    doutrina descreve na secao 12. O render sai; sai muitas vezes mais lento, e
    ninguem descobre ate a manha seguinte.
    """
    prefs = bpy.context.preferences.addons.get("cycles")
    if prefs is None:
        return {"antes": None, "depois": None, "ligados": [], "aviso": "addon cycles ausente"}
    p = prefs.preferences
    antes = getattr(p, "compute_device_type", None)

    for tipo in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
        try:
            p.compute_device_type = tipo
        except TypeError:
            continue
        p.get_devices()
        if any(d.type == tipo for d in p.devices):
            break
    else:
        return {"antes": antes, "depois": getattr(p, "compute_device_type", None),
                "ligados": [], "aviso": "nenhum backend de GPU disponivel nesta maquina"}

    # Liga a placa e DESLIGA a CPU: com os dois marcados o Cycles divide o
    # trabalho e o tempo medido deixa de ser o da placa.
    for d in p.devices:
        d.use = (d.type != "CPU")
    cena.cycles.device = "GPU"
    return {"antes": antes, "depois": p.compute_device_type,
            "ligados": [d.name for d in p.devices if d.use], "aviso": None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="out/medicao")
    ap.add_argument("--quadro", type=int, default=None)
    ap.add_argument("--plano", default=None,
                    help="CAM_<plano>. Sem isto, escolhe o plano mais ruidoso "
                         "declarado abaixo")
    ap.add_argument("--escala", type=int, default=50,
                    help="resolution_percentage. 50 mede ruido bem e custa 1/4")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

    cena = bpy.context.scene
    raiz = Path(args.saida).resolve()
    raiz.mkdir(parents=True, exist_ok=True)

    # O plano mais ruidoso da decupagem: dentro do pavilhao, a 2 m, onde a luz
    # so chega por rebatimento. Se nao existir camera dele no .blend, cai no
    # primeiro que existir e DIZ que caiu -- medir no plano errado em silencio
    # e o defeito que este script existe para nao ter.
    preferidos = [args.plano] if args.plano else ["P08", "P09", "P07", "P13", "P01"]
    cam = None
    for pid in preferidos:
        cam = bpy.data.objects.get(f"CAM_{pid}")
        if cam:
            if args.plano is None:
                print(f"  plano escolhido ..... {pid} (candidato mais fechado disponivel)")
            break
    if cam is None:
        cams = sorted([o for o in bpy.data.objects if o.type == "CAMERA"],
                      key=lambda o: o.name)
        if not cams:
            raise SystemExit("a cena nao tem camera")
        cam = cams[0]
        print(f"  AVISO: nenhum dos planos {preferidos} tem camera. Caindo em {cam.name}")
    cena.camera = cam

    quadro = args.quadro if args.quadro is not None else cena.frame_current
    cena.frame_set(quadro)
    cena.render.resolution_percentage = args.escala
    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_depth = "8"

    largura = cena.render.resolution_x * args.escala // 100
    altura = cena.render.resolution_y * args.escala // 100

    print("=" * 72)
    print("MEDICAO DE RENDER -- passos 0.3 (VRAM) e 0.4 (amostragem)")
    print("=" * 72)
    print(f"  camera .............. {cam.name}")
    print(f"  quadro .............. {quadro}")
    print(f"  resolucao ........... {largura} x {altura} ({args.escala}%)")
    gpu = garantir_gpu(cena)
    print(f"  compute ANTES ....... {gpu['antes']}")
    print(f"  compute DEPOIS ...... {gpu['depois']}")
    print(f"  dispositivos ligados  {gpu['ligados']}")
    if gpu["aviso"]:
        print(f"  AVISO: {gpu['aviso']} -- os tempos abaixo sao de CPU")
    elif gpu["antes"] in (None, "NONE"):
        print("  ACHADO: a cena dizia GPU e as preferencias estavam em NONE.")
        print("          Aberto assim, o render cai para a CPU em silencio.")
    print(f"  objetos na cena ..... {len(bpy.data.objects)}")
    print(f"  imagens carregadas .. {len(bpy.data.images)}")
    print()

    linhas = []
    for nome, samples, limiar, denoise in CONFIGS:
        c = cena.cycles
        c.samples = samples
        c.adaptive_threshold = limiar
        c.use_adaptive_sampling = True
        c.use_denoising = denoise

        destino = raiz / f"{nome.replace('/', '-').replace(' ', '_')}.png"
        cena.render.filepath = str(destino.with_suffix(""))

        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        dt = time.time() - t0

        arq = destino if destino.exists() else destino.with_suffix(".png")
        linhas.append({"config": nome, "samples": samples, "limiar": limiar,
                       "denoise": denoise, "segundos": round(dt, 1),
                       "arquivo": arq.name})
        print(f"  {nome:24s} {dt:7.1f} s")

    base = next(l for l in linhas if l["config"].startswith("128/0,1  com"))
    alvo = next(l for l in linhas if l["config"].startswith("max/0,01 com"))
    dtempo = 100.0 * (alvo["segundos"] / base["segundos"] - 1)

    print()
    print("  As duas COM denoise, que e como ele renderiza:")
    print(f"    0,01 custa {dtempo:+.0f}% de tempo")
    print("    O RUIDO sai no passo seguinte -- o Python do Blender nao tem cv2:")
    print("      .venv/Scripts/python.exe scripts/medir_ruido.py "
          f"{Path(args.saida).as_posix()}")

    # Escala para o filme inteiro, corrigindo a resolucao reduzida da medicao.
    fator = (100 / args.escala) ** 2
    print(f"\n  projecao a 100% ({4635} quadros):")
    for l in linhas:
        h = l["segundos"] * fator * 4635 / 3600
        print(f"    {l['config']:24s} {h:6.1f} h")

    relatorio = {"camera": cam.name, "quadro": quadro,
                 "escala_pct": args.escala, "resolucao": [largura, altura],
                 "device": cena.cycles.device, "gpu": gpu, "configs": linhas,
                 "delta_tempo_pct": round(dtempo, 1)}
    (raiz / "relatorio.json").write_text(
        json.dumps(relatorio, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  relatorio ........... {raiz / 'relatorio.json'}")
    print("=" * 72)


if __name__ == "__main__":
    main()
