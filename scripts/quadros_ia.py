#!/usr/bin/env python3
"""
Quadros-chave da cena 3D, um por ponta de plano -- a placa de entrada do
Plano A (IA geradora de video a partir de imagem).

Ordem do Natan, 15/08/2026: *"Levante as melhores imagens para criar com IA,
para usar essas imagens reais e colocar tipo uma exposicao nesse lugar,
primeiro os quadros e depois crio os videos."*

O que este script NAO faz, de proposito:

  - nao renderiza o filme (4.635 quadros, 12,9 h). "Primeiro os quadros" e
    conjunto de imagens para aprovacao, nao a fila de entrega;
  - nao grava EXR nem passe nenhum. Placa de referencia nao precisa de
    cryptomatte, e disco e o recurso apertado deste projeto;
  - nao gera nada com IA. Isso e passo dele.

Renderiza o PRIMEIRO e o ULTIMO quadro de cada plano, na resolucao de
entrega (2760x1380), com a configuracao de render que ele ditou. Primeiro e
ultimo porque e o par que as ferramentas de imagem-para-video pedem
(start frame / end frame), e porque num plano com movimento o quadro inicial
sozinho nao mostra o que o plano entrega.

    "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" \\
        --background --python scripts/quadros_ia.py -- \\
        --blend out/cena.blend --saida out/quadros-ia

Saida: out/quadros-ia/<Pxx>_<slug>/3d/ini.png e fim.png

Armadilha 34 (D029): marcador de timeline vence `scene.camera`. Aqui os
quadros pedidos estao SEMPRE dentro da faixa do proprio plano, entao o
marcador aponta para a mesma camera -- mas os marcadores sao limpos na
sessao assim mesmo, para o script nao depender disso.
"""

import argparse
import re
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy

import placa as placa_mod
import planos as planos_mod
import terreno


def slug(texto):
    if not texto:
        return "sem-titulo"
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-").lower()
    return t[:44] or "sem-titulo"


def nome_da_pasta(plano):
    titulo = plano.get("titulo") or plano.get("nota") or ""
    return f"{plano['id']}_{slug(titulo)}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--blend", required=True)
    ap.add_argument("--planos-json", dest="planos_json", default="data/planos.json")
    ap.add_argument("--dados", default="data/mapa_agroshow26.json")
    ap.add_argument("--saida", default="out/quadros-ia")
    ap.add_argument("--plano", default=None, help="so estes planos, separados por virgula")
    ap.add_argument("--escala", type=int, default=100, help="resolution_percentage")
    ap.add_argument("--pontas", default="ini,fim",
                    help="quais quadros de cada plano: ini, fim, meio (lista por virgula)")
    ap.add_argument("--forcar", action="store_true")
    ap.add_argument("--permitir-cpu", action="store_true")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])

    if not Path(args.blend).exists():
        raise SystemExit(f"blend nao encontrado: {args.blend}")

    bpy.ops.wm.open_mainfile(filepath=str(Path(args.blend).resolve()))
    cena = bpy.context.scene

    if args.permitir_cpu:
        placa_mod.ligar(cena)
    else:
        placa_mod.exigir(cena)

    # D029 / armadilha 34: marcador vence scene.camera. Some com eles na sessao;
    # o .blend em disco nao muda porque nada e salvo aqui.
    cena.timeline_markers.clear()

    cena.render.resolution_percentage = args.escala
    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_mode = "RGB"
    cena.render.film_transparent = False

    dados = terreno.carregar_mapa(args.dados)
    pacote = planos_mod.carregar(args.planos_json, dados=dados)
    planos = pacote["planos"]
    if args.plano:
        pedidos = set(args.plano.split(","))
        planos = [p for p in planos if p["id"] in pedidos]
        faltando = pedidos - {p["id"] for p in planos}
        if faltando:
            raise SystemExit(f"plano(s) inexistente(s): {sorted(faltando)}")

    pontas = [p.strip() for p in args.pontas.split(",") if p.strip()]
    # Absoluto de proposito: `render.filepath` relativo e resolvido contra o CWD
    # do PROCESSO do Blender, que no Windows nao e a pasta de onde o comando
    # saiu -- a primeira rodada gravou tudo em C:\out\.
    raiz = Path(args.saida).resolve()
    raiz.mkdir(parents=True, exist_ok=True)

    feitos = pulados = 0
    tempos = []
    for i, plano in enumerate(planos, 1):
        cam = bpy.data.objects.get(f"CAM_{plano['id']}")
        if cam is None:
            print(f"  [{plano['id']}] SEM CAMERA no .blend -- pulando")
            continue
        cena.camera = cam
        destino = raiz / nome_da_pasta(plano) / "3d"
        destino.mkdir(parents=True, exist_ok=True)

        ini, fim = plano["_quadro_ini"], plano["_quadro_fim"]
        alvo = {"ini": ini, "fim": fim, "meio": (ini + fim) // 2}
        titulo = plano.get("titulo") or plano.get("nota", "")[:40]
        print(f"[{i}/{len(planos)}] {plano['id']} · {titulo!r} · quadros {ini}-{fim}")

        for ponta in pontas:
            quadro = alvo[ponta]
            arq = destino / f"{ponta}.png"
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
            print(f"    {ponta} (quadro {quadro:05d}): {dt:5.1f} s -> {arq}")

    print("\n" + "=" * 58)
    print(f"  renderizados .......... {feitos}")
    print(f"  ja existiam ........... {pulados}")
    if tempos:
        print(f"  tempo medio/quadro .... {sum(tempos)/len(tempos):.1f} s")
    print("=" * 58)


if __name__ == "__main__":
    main()
