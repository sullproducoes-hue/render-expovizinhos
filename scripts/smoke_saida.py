#!/usr/bin/env python3
"""Renderiza UM quadro com a arvore de saida de verdade e mede o que sai.

Roda dentro do Blender:

    blender --background out/cena.blend --python scripts/smoke_saida.py -- \\
        --saida out/smoke --quadro 1

Depois `scripts/conferir_matte.py` abre o EXR e extrai um matte. Os dois
juntos sao o passo 0.2: **nao se renderiza 4.635 quadros com Cryptomatte
quebrado.** O custo de descobrir isso agora e um quadro; de descobrir depois,
a fila inteira.

O que ele mede, e por que cada numero importa:

- **tamanho de cada slot**, em disco de verdade. A projecao de 70 GB do plano
  antigo assumia DWAA em tudo; o slot de dado e lossless e nao comprime igual.
  A conta do filme so vale medida.
- **tempo do quadro**, para saber quanto a arvore nova custa sobre o render.
- **as camadas gravadas**, para ninguem descobrir passe faltando no dia 3.
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy

import saida as saida_mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="out/smoke")
    ap.add_argument("--quadro", type=int, default=1)
    ap.add_argument("--escala", type=int, default=100,
                    help="resolution_percentage. 100 = medida real de disco")
    ap.add_argument("--camera", default=None, help="ex: CAM_P01")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

    cena = bpy.context.scene
    raiz = Path(args.saida).resolve()
    raiz.mkdir(parents=True, exist_ok=True)

    if args.camera:
        cam = bpy.data.objects.get(args.camera)
        if cam is None:
            raise SystemExit(f"camera {args.camera} nao existe no .blend")
        cena.camera = cam
    if cena.camera is None:
        cams = [o for o in bpy.data.objects if o.type == "CAMERA"]
        if not cams:
            raise SystemExit("a cena nao tem camera nenhuma")
        cena.camera = sorted(cams, key=lambda o: o.name)[0]

    cena.render.resolution_percentage = args.escala
    largura = cena.render.resolution_x * args.escala // 100
    altura = cena.render.resolution_y * args.escala // 100

    print("=" * 66)
    print("SMOKE TEST DA SAIDA -- passo 0.2")
    print("=" * 66)
    print(f"  camera .............. {cena.camera.name}")
    print(f"  resolucao ........... {largura} x {altura} ({args.escala}%)")
    print(f"  motor ............... {cena.render.engine} / {cena.cycles.device}")
    print(f"  samples ............. {cena.cycles.samples} (limiar "
          f"{cena.cycles.adaptive_threshold})")
    print(f"  denoise ............. {cena.cycles.use_denoising}")
    print("  arvore do compositor:")

    nos = saida_mod.montar(cena, raiz)
    saida_mod.nomear(nos, args.quadro)

    cena.frame_set(args.quadro)
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0

    contrato = saida_mod.carregar()
    print("\n  saiu em disco:")
    medidas = {}
    for nome in ("beauty", "data", "preview"):
        pasta = raiz / contrato["slots"][nome]["pasta"]
        arqs = sorted(pasta.glob("*")) if pasta.exists() else []
        total = sum(a.stat().st_size for a in arqs)
        medidas[nome] = {"bytes": total,
                         "arquivos": [a.name for a in arqs]}
        alvo = arqs[0].name if arqs else "NADA GRAVADO"
        print(f"    {nome:8s} {total/1e6:8.2f} MB   {alvo}")

    quadros = 4635
    print(f"\n  tempo do quadro ..... {dt:.1f} s")

    # A projecao so vale se o quadro medido tiver a resolucao de entrega. A
    # 25% de escala o arquivo tem 1/16 dos pixels, e multiplicar por 4.635 da
    # um numero 16x otimista -- que e exatamente o tipo de conta que faz o
    # disco acabar no meio da noite. Aqui a conta e corrigida e o aviso e dito.
    fator = (100 / args.escala) ** 2
    if args.escala != 100:
        print(f"  AVISO: medido a {args.escala}% -- projecao corrigida por "
              f"{fator:.0f}x. Numero de verdade so a 100%.")

    print(f"\n  PROJECAO PARA O FILME ({quadros} quadros, {'medido' if args.escala == 100 else 'extrapolado'}):")
    soma = 0
    for nome, m in medidas.items():
        gb = m["bytes"] * quadros * fator / 1e9
        soma += gb
        print(f"    {nome:8s} {gb:8.1f} GB")
    print(f"    {'TOTAL':8s} {soma:8.1f} GB     (F: tem 299 GB livres)")
    if soma > 280:
        print("    NAO CABE no F:. Cortar crypto para os planos que precisam,")
        print("    ou baixar levels, ou gravar o data so onde ha isolamento.")
    else:
        print("    cabe no F:.")

    relatorio = {
        "quando": "smoke 0.2",
        "resolucao": [largura, altura],
        "escala_pct": args.escala,
        "camera": cena.camera.name,
        "quadro": args.quadro,
        "segundos_do_quadro": round(dt, 2),
        "quadros_do_filme": quadros,
        "medido_na_resolucao_de_entrega": args.escala == 100,
        "por_slot": {n: {"bytes_do_quadro": m["bytes"],
                         "gb_do_filme": round(m["bytes"] * quadros * fator / 1e9, 1),
                         "arquivos": m["arquivos"]}
                     for n, m in medidas.items()},
        "gb_total_do_filme": round(soma, 1),
    }
    (raiz / "relatorio.json").write_text(
        json.dumps(relatorio, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  relatorio ........... {raiz / 'relatorio.json'}")
    print("=" * 66)


if __name__ == "__main__":
    main()
