#!/usr/bin/env python3
"""Mede o custo em disco de cada arranjo de saida, no MESMO quadro.

    blender --background out/cena.blend --python scripts/medir_compressao.py -- \\
        --plano P11 --saida out/compressao

**Por que existe.** A primeira projecao de disco saiu de UM quadro (o P01) e
deu 199 GB. Amostrados seis planos, a media real foi 63 MB/quadro e **285 GB de
300 GB livres** -- 43% acima, e folga que nao existe. O P01 e o plano mais
aberto do filme, com metade do quadro em ceu liso; ceu comprime quase de graca
e detalhe nao comprime. Medir num plano so e medir o plano, nao o filme.

Aqui os arranjos competem no mesmo quadro fechado, que e o pior caso, e o
numero que sai da para decidir sem chutar.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy

import placa as placa_mod
import saida as saida_mod

# nome do arranjo -> o que muda no contrato
ARRANJOS = {
    "atual  (8 camadas, DWAA)":        {},
    "beauty DWAB":                     {"beauty_codec": "DWAB"},
    "beauty so Combined":              {"beauty_passes": ["Combined"]},
    "beauty so Combined + DWAB":       {"beauty_passes": ["Combined"], "beauty_codec": "DWAB"},
    "beauty Combined+Diff+Gloss":      {"beauty_passes": ["Combined", "DiffDir", "DiffInd",
                                                          "GlossDir", "GlossInd"]},
    "data PIZ no lugar de ZIP":        {"data_codec": "PIZ"},
    "data sem CryptoMaterial":         {"sem_crypto_material": True},
}


def aplicar(contrato, mudanca):
    import copy
    c = copy.deepcopy(contrato)
    if "beauty_codec" in mudanca:
        c["slots"]["beauty"]["codec"] = mudanca["beauty_codec"]
    if "data_codec" in mudanca:
        c["slots"]["data"]["codec"] = mudanca["data_codec"]
    if "beauty_passes" in mudanca:
        c["slots"]["beauty"]["passes"] = mudanca["beauty_passes"]
    if mudanca.get("sem_crypto_material"):
        c["cryptomatte"]["material"] = False
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="out/compressao")
    ap.add_argument("--plano", default="P11")
    ap.add_argument("--quadro", type=int, default=None)
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

    cena = bpy.context.scene
    placa_mod.ligar(cena)

    cam = bpy.data.objects.get(f"CAM_{args.plano}")
    if cam is None:
        raise SystemExit(f"sem CAM_{args.plano} no .blend")
    cena.camera = cam
    if args.quadro is not None:
        cena.frame_set(args.quadro)

    base = saida_mod.carregar()
    raiz = Path(args.saida).resolve()
    linhas = []

    print("=" * 74)
    print(f"CUSTO EM DISCO POR ARRANJO -- {args.plano}, quadro {cena.frame_current}")
    print("=" * 74)

    for nome, mudanca in ARRANJOS.items():
        pasta = raiz / nome.replace(" ", "_").replace("(", "").replace(")", "").replace(",", "")
        contrato = aplicar(base, mudanca)
        nos = saida_mod.montar(cena, pasta, contrato=contrato, verbose=False)
        saida_mod.nomear(nos, cena.frame_current)
        bpy.ops.render.render(write_still=False)

        medidas = {}
        for slot in ("beauty", "data", "preview"):
            d = pasta / contrato["slots"][slot]["pasta"]
            medidas[slot] = sum(a.stat().st_size for a in d.glob("*")) if d.exists() else 0
        total = sum(medidas.values())
        gb = total * 4635 / 1e9
        linhas.append({"arranjo": nome, "bytes": total,
                       "por_slot_mb": {k: round(v / 1e6, 1) for k, v in medidas.items()},
                       "gb_do_filme_neste_plano": round(gb, 1)})
        print(f"  {nome:30s} {total/1e6:6.1f} MB/quadro   -> {gb:5.0f} GB "
              f"(beauty {medidas['beauty']/1e6:.1f} / data {medidas['data']/1e6:.1f})")

    print()
    print("  Lembre: este e UM plano fechado, o pior caso. A media dos seis")
    print("  planos amostrados ficou ~24% abaixo do pior. Compare os arranjos")
    print("  ENTRE SI aqui, e aplique a proporcao a media medida.")

    (raiz / "relatorio.json").write_text(
        json.dumps({"plano": args.plano, "quadro": cena.frame_current,
                    "arranjos": linhas}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    print("=" * 74)


if __name__ == "__main__":
    main()
