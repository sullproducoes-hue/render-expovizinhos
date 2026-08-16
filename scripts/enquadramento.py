#!/usr/bin/env python3
"""
Mede o ENQUADRAMENTO de cada plano ao longo do movimento inteiro, nao so nas
pontas.

Por que existe. O `conferir_camera.py` testa o quadro inicial e o final de cada
plano: camera enterrada, camera dentro de geometria fechada, superficie colada
na mira. Ele passou verde em planos cujo still mostra tela cheia de telhado
branco (P07, P08), tela cheia de copa (P09, P12) e predio ocupando metade do
quadro (P20). Os tres portoes de letreiro tambem nao pegam isso -- eles medem
se a letra CABE, nao se o plano MOSTRA alguma coisa.

O que este modulo mede, com raycast numa grade que cobre o frustum:

  perto     fracao dos raios que batem em superficie a menos de `perto_m`.
            E' o "quadro tomado por telhado ou copa". Acima de ~0.45 o plano
            nao mostra o lugar, mostra um obstaculo.
  ceu       fracao dos raios que nao batem em nada. Acima de ~0.75 o plano e'
            ceu vazio.
  alvo      o raio da camera ate o ponto de mira chega la? Se bate antes de
            90% da distancia, o assunto do plano esta atras de alguma coisa.
  enterrada camera abaixo do terreno.
  dentro    camera dentro de volume fechado (3 de 4 direcoes com cruzamento
            impar).

Roda dentro do Blender, sobre um .blend ja construido:

    blender.exe --background --python scripts/enquadramento.py -- \
        --blend out/cena.blend --json out/enquadramento.json
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy
from mathutils import Vector

import planos as planos_mod
import terreno

DIRECOES = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))]

# Grade de raios pelo frustum. Impar nos dois eixos para haver raio central.
GRADE_X = 9
GRADE_Y = 5

# Teto de cada defeito. Sao os numeros que separam os stills que leem dos que
# nao leem, medidos na folha out/_quebrados.jpg de 15/08.
TETO_PERTO = 0.45
TETO_CEU = 0.80
PERTO_M = 14.0


def grade_do_frustum(lente_mm, sensor_mm, prop):
    """Direcoes no espaco da camera para uma grade que cobre o quadro.

    prop = largura/altura. O sensor do Blender e' AUTO: o lado maior recebe
    `sensor_mm`. Em 16:9 o lado maior e' a horizontal.
    """
    meia_h = math.atan((sensor_mm / 2.0) / lente_mm)
    meia_v = math.atan((sensor_mm / prop / 2.0) / lente_mm)
    dirs = []
    for iy in range(GRADE_Y):
        fy = (iy / (GRADE_Y - 1)) * 2 - 1          # -1 .. 1
        for ix in range(GRADE_X):
            fx = (ix / (GRADE_X - 1)) * 2 - 1
            # 0.92 encolhe a grade para nao medir exatamente a borda do quadro
            d = Vector((math.tan(meia_h * fx * 0.92),
                        math.tan(meia_v * fy * 0.92),
                        -1.0))
            dirs.append(d.normalized())
    return dirs


def dentro_de_volume(cena, dg, origem):
    impares = 0
    for direcao in DIRECOES:
        n, p = 0, origem.copy()
        for _ in range(48):
            ok, loc, _, _, _, _ = cena.ray_cast(dg, p, direcao, distance=2000.0)
            if not ok:
                break
            n += 1
            p = loc + direcao * 0.01
        if n % 2 == 1:
            impares += 1
    return impares >= 3


def medir_instante(cena, dg, cam, dirs):
    """Mede um quadro ja posicionado. Devolve o dicionario de metricas."""
    m = cam.matrix_world
    pos = m.translation.copy()
    rot = m.to_quaternion()

    n_perto = n_ceu = 0
    d_min = float("inf")
    for d in dirs:
        mundo = (rot @ d).normalized()
        ok, loc, _, _, _, _ = cena.ray_cast(dg, pos + mundo * 0.05, mundo,
                                            distance=3000.0)
        if not ok:
            n_ceu += 1
            continue
        dist = (loc - pos).length
        d_min = min(d_min, dist)
        if dist < PERTO_M:
            n_perto += 1

    total = len(dirs)
    ok_solo, loc_solo, _, _, _, _ = cena.ray_cast(
        dg, pos, Vector((0, 0, -1)), distance=800.0)
    z_solo = loc_solo.z if ok_solo else float("nan")

    return {
        "x": round(pos.x, 2), "y": round(pos.y, 2), "z": round(pos.z, 2),
        "perto": round(n_perto / total, 3),
        "ceu": round(n_ceu / total, 3),
        "d_min": round(d_min, 2) if d_min < float("inf") else None,
        "enterrada": bool(ok_solo) and (pos.z - z_solo) < 0.5,
        "dentro": dentro_de_volume(cena, dg, pos),
    }


def alvo_livre(cena, dg, cam, alvo_obj):
    """O ponto de mira esta visivel da camera?"""
    pos = cam.matrix_world.translation.copy()
    destino = alvo_obj.matrix_world.translation.copy()
    v = destino - pos
    L = v.length
    if L < 1e-6:
        return True, 0.0
    d = v.normalized()
    ok, loc, _, _, _, _ = cena.ray_cast(dg, pos + d * 0.05, d, distance=L)
    if not ok:
        return True, 1.0
    # Razao, nao distancia absoluta. Quando o alvo E' um predio, o raio bate na
    # fachada dele a ~0.85 do caminho, e isso e' o plano funcionando. So conta
    # como oclusao quando algo bloqueia bem antes -- arvore, talude, telhado de
    # outro predio. O piso de 0.55 separa os dois casos na medida de 15/08.
    return ((loc - pos).length / L) > 0.55, (loc - pos).length / L


def medir_plano(cena, dg, plano, amostras=9):
    cam = bpy.data.objects.get(f"CAM_{plano['id']}")
    alvo = bpy.data.objects.get(f"MIRA_{plano['id']}")
    if cam is None:
        return None

    prop = cena.render.resolution_x / cena.render.resolution_y
    dirs = grade_do_frustum(cam.data.lens, cam.data.sensor_width, prop)

    q0, q1 = plano["_quadro_ini"], plano["_quadro_fim"]
    linhas = []
    for i in range(amostras):
        q = int(round(q0 + (q1 - q0) * i / (amostras - 1)))
        cena.frame_set(q)
        bpy.context.view_layer.update()
        dgq = bpy.context.evaluated_depsgraph_get()
        cam_av = cam.evaluated_get(dgq)      # armadilha 44: constraint
        reg = medir_instante(cena, dgq, cam_av, dirs)
        reg["quadro"] = q
        if alvo is not None:
            livre, dist = alvo_livre(cena, dgq, cam_av, alvo.evaluated_get(dgq))
            reg["alvo_livre"] = livre
            reg["alvo_razao"] = round(dist, 3)
        linhas.append(reg)

    pior_perto = max(l["perto"] for l in linhas)
    pior_ceu = max(l["ceu"] for l in linhas)
    n_ocluso = sum(0 if l.get("alvo_livre", True) else 1 for l in linhas)
    return {
        "id": plano["id"],
        "titulo": plano["titulo"],
        "amostras": linhas,
        "pior_perto": pior_perto,
        "media_perto": round(sum(l["perto"] for l in linhas) / len(linhas), 3),
        "pior_ceu": pior_ceu,
        "n_ocluso": n_ocluso,
        "n_enterrada": sum(1 for l in linhas if l["enterrada"]),
        "n_dentro": sum(1 for l in linhas if l["dentro"]),
        "reprova": (pior_perto > TETO_PERTO or pior_ceu > TETO_CEU
                    or n_ocluso > 0
                    or any(l["enterrada"] or l["dentro"] for l in linhas)),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--blend", required=True)
    ap.add_argument("--planos-json", dest="planos_json", default="data/planos.json")
    ap.add_argument("--dados", default="data/mapa_agroshow26.json")
    ap.add_argument("--json", dest="saida", default=None)
    ap.add_argument("--amostras", type=int, default=9)
    ap.add_argument("--so-avisa", action="store_true")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:]
                         if "--" in sys.argv else sys.argv[1:])

    bpy.ops.wm.open_mainfile(filepath=str(Path(args.blend).resolve()))
    cena = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()

    dados = terreno.carregar_mapa(args.dados)
    pacote = planos_mod.carregar(args.planos_json, dados=dados)

    print(f"{'plano':6} {'perto':>7} {'medio':>7} {'ceu':>6} {'ocl':>4} "
          f"{'ent':>4} {'dtr':>4}  titulo")
    print("-" * 78)
    relatorio, reprovados = [], []
    for plano in pacote["planos"]:
        r = medir_plano(cena, dg, plano, args.amostras)
        if r is None:
            print(f"{plano['id']:6}  sem camera no .blend")
            continue
        relatorio.append(r)
        marca = "  REPROVA" if r["reprova"] else ""
        print(f"{r['id']:6} {r['pior_perto']:7.2f} {r['media_perto']:7.2f} "
              f"{r['pior_ceu']:6.2f} {r['n_ocluso']:4} {r['n_enterrada']:4} "
              f"{r['n_dentro']:4}  {r['titulo'][:28]}{marca}")
        if r["reprova"]:
            reprovados.append(r["id"])

    print("-" * 78)
    print(f"  tetos: perto>{TETO_PERTO} (a menos de {PERTO_M:.0f} m), "
          f"ceu>{TETO_CEU}, alvo ocluso, enterrada, dentro")
    if args.saida:
        Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
        Path(args.saida).write_text(
            json.dumps(relatorio, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  gravado em {args.saida}")

    if reprovados:
        print(f"  {len(reprovados)} REPROVADO(S): {', '.join(reprovados)}")
        if not args.so_avisa:
            raise SystemExit(1)
    else:
        print("  todos os 22 planos mostram o lugar que prometem.")


if __name__ == "__main__":
    main()
