"""Prova de fogo do caminho de render: Cycles roda, OptiX esta ativo, a VRAM
aguenta e o caminho de saida existe.

Existe porque D009 registrou que o render ja veio na CPU sem ninguem saber. Aqui
o dispositivo nao e' assumido: ele e' IMPRESSO, e o script aborta se o Cycles
cair para CPU.

Armadilha 34: marcador de timeline vence `scene.camera`. Os marcadores sao
apagados na sessao antes de renderizar; a cena em disco nao muda.

Uso:
  blender --background out/cena-revisar.blend --python scripts/prova_cycles.py -- \
      --saida "F:/heroi/_prova/prova.png" --largura 960 --altura 540 --samples 64
"""

import sys
import argparse
from pathlib import Path

import bpy


def argumentos():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--saida", required=True)
    p.add_argument("--largura", type=int, default=960)
    p.add_argument("--altura", type=int, default=540)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--camera", default=None, help="nome do objeto camera")
    return p.parse_args(argv)


def ligar_gpu():
    """Liga OPTIX e DESLIGA a CPU. Devolve a lista do que ficou ativo.

    `get_devices()` precisa ser chamado antes de `devices` ter conteudo -- sem
    ele a lista vem vazia e o laco abaixo nao liga nada, silenciosamente.
    """
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    try:
        prefs.get_devices()
    except Exception:
        pass

    ativos = []
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
        if d.use:
            ativos.append(f"{d.name} [{d.type}]")
    return ativos


def main():
    a = argumentos()
    cena = bpy.context.scene

    # Armadilha 34 -- marcador vence scene.camera. Limpa na sessao, nao em disco.
    n_marcadores = len(cena.timeline_markers)
    cena.timeline_markers.clear()

    if a.camera:
        obj = bpy.data.objects.get(a.camera)
        if obj is None:
            print(f"ERRO: camera '{a.camera}' nao existe na cena")
            sys.exit(2)
        cena.camera = obj
    if cena.camera is None:
        cams = [o for o in bpy.data.objects if o.type == "CAMERA"]
        if not cams:
            print("ERRO: a cena nao tem nenhuma camera")
            sys.exit(2)
        cena.camera = sorted(cams, key=lambda o: o.name)[0]

    cena.render.engine = "CYCLES"
    ativos = ligar_gpu()
    cena.cycles.device = "GPU"

    cena.cycles.use_adaptive_sampling = True
    cena.cycles.adaptive_min_samples = 10
    cena.cycles.samples = a.samples
    cena.cycles.use_denoising = True
    cena.cycles.denoiser = "OPTIX"
    cena.render.use_persistent_data = True

    cena.render.resolution_x = a.largura
    cena.render.resolution_y = a.altura
    cena.render.resolution_percentage = 100
    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_depth = "8"

    saida = Path(a.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    cena.render.filepath = str(saida)

    print("=" * 60)
    print(f"blender          {bpy.app.version_string}")
    print(f"engine           {cena.render.engine}")
    print(f"cycles.device    {cena.cycles.device}")
    print(f"dispositivos     {ativos or 'NENHUM -- vai cair na CPU'}")
    print(f"denoise          {cena.cycles.denoiser}")
    print(f"samples          min {cena.cycles.adaptive_min_samples} / max {cena.cycles.samples}")
    print(f"resolucao        {a.largura}x{a.altura}")
    print(f"camera           {cena.camera.name}")
    print(f"marcadores       {n_marcadores} apagados na sessao")
    print(f"saida            {saida}")
    print("=" * 60)

    if not ativos:
        print("ABORTA: nenhum dispositivo OPTIX ativo -- o render cairia na CPU (D009)")
        sys.exit(3)

    bpy.ops.render.render(write_still=True)

    if not saida.exists():
        print(f"ABORTA: render terminou mas '{saida}' nao existe")
        sys.exit(4)
    print(f"OK  {saida}  {saida.stat().st_size} bytes")


if __name__ == "__main__":
    main()
