#!/usr/bin/env python3
"""Liga a placa nas preferencias do Cycles. Fonte unica, dentro do Blender.

**Por que este arquivo existe, e nao e detalhe.** A cena guarda
`cycles.device = "GPU"`; o DISPOSITIVO, nao. Ele mora nas *preferencias*, que
sao da instalacao do Blender e nao do arquivo `.blend`. Entao:

- `build_scene.py` ligava a placa e construia a cena rapido;
- `render_shots.py` abria o `.blend` numa sessao NOVA, onde as preferencias
  voltavam a `compute_device_type = NONE`, e renderizava **na CPU**;
- e o `.blend` continuava anunciando "GPU" na tela o tempo todo.

Medido em 15/08 no P08: **47 s por quadro na CPU contra ~11,6 s na GPU** --
60 h de filme contra 14,9 h. O `RETOMAR.md` declarava 36-38 s/quadro como se
fosse GPU; era CPU. E o fallback e silencioso: nao ha aviso nenhum.

Por isso a funcao virou modulo proprio: quem renderiza CHAMA, sempre, e no
comeco. Doutrina secao 12: *"nao descobrir estouro de VRAM tarde"* -- vale
igual para descobrir a CPU tarde.

**O nome do arquivo e `placa.py` e nao `gpu.py` de proposito:** o Blender ja
traz um modulo embutido chamado `gpu` (a API de desenho), e ele ja esta em
`sys.modules` quando o script roda. `import gpu` devolve o do Blender mesmo com
`scripts/` na frente do `sys.path`, e o erro que aparece e um
`AttributeError` em funcao que existe -- diagnostico que leva a lugar nenhum.
"""

import bpy


def ligar(cena=None, verbose=True):
    """Liga a melhor GPU disponivel e devolve o que aconteceu.

    Desliga a CPU de proposito: com CPU e GPU marcadas o Cycles divide o
    trabalho entre as duas, e numa RTX 4060 contra um Xeon de 28 threads o
    resultado nao e a soma -- e a CPU segurando os ultimos tiles enquanto a
    placa espera. Para medir tempo de GPU, tem que ser so a GPU.
    """
    addon = bpy.context.preferences.addons.get("cycles")
    if addon is None:
        if verbose:
            print("  AVISO: addon cycles indisponivel -- render vai para a CPU")
        return {"tipo": None, "antes": None, "placas": [],
                "aviso": "addon cycles ausente"}

    prefs = addon.preferences
    antes = getattr(prefs, "compute_device_type", None)

    for tipo in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
        try:
            prefs.compute_device_type = tipo
        except TypeError:
            continue          # backend que esta build nao tem
        prefs.get_devices()
        placas = [d for d in prefs.devices if d.type == tipo]
        if not placas:
            continue
        for d in prefs.devices:
            d.use = (d.type == tipo)
        if cena is not None:
            cena.cycles.device = "GPU"
        if verbose:
            print(f"  gpu ................. {tipo}: "
                  f"{', '.join(dict.fromkeys(d.name for d in placas))}")
            if antes in (None, "NONE"):
                print("  (as preferencias estavam em NONE -- sem esta chamada o "
                      "render sairia na CPU, 4x mais lento, sem avisar)")
        return {"tipo": tipo, "antes": antes,
                "placas": [d.name for d in placas], "aviso": None}

    if verbose:
        print("  AVISO: nenhuma GPU encontrada -- render vai para a CPU")
    return {"tipo": None, "antes": antes, "placas": [],
            "aviso": "nenhum backend de GPU nesta maquina"}


def exigir(cena=None):
    """Como `ligar`, mas ABORTA se cair na CPU.

    Para a fila de render: 4.635 quadros na CPU sao 60 h, e o certo e o
    programa parar e dizer, nao entregar na segunda-feira.
    """
    r = ligar(cena)
    if r["tipo"] is None:
        raise SystemExit(
            "ABORTADO: nenhuma GPU habilitada. Na CPU esta fila leva ~60 h "
            "em vez de ~15 h. Se for de proposito, rode com --permitir-cpu.")
    return r
