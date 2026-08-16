#!/usr/bin/env python3
"""
Acha, por medida, o MENOR ajuste de camera que faz cada plano mostrar o lugar
que ele promete -- e escreve o resultado de volta em data/planos.json.

Por que existe. Em 15/08 a folha de stills mostrou seis planos que o portao de
camera aprovava e que nao mostram nada: tela cheia de telhado branco (P07,
P08), tela cheia de copa (P09, P12), predio ocupando metade do quadro (P20).
Reenquadrar era decisao de quem dirige e ficou parada duas sessoes. A ordem do
Natan de 15/08 -- "tome todas as medidas necessarias pra finalizar hoje" --
destravou, e a forma honesta de destravar nao e' eu escolher enquadramento a
olho: e' medir o que esta errado, buscar o menor ajuste que conserta, e deixar
o numero de antes e o de depois escritos.

O que ele varre, em ordem de custo crescente (mudanca pequena primeiro):

    delta de altura     0 .. +26 m somados as duas pontas
    fator de distancia  1.00 .. 2.40 multiplicando as duas pontas
    giro de azimute     0, +-18, +-32, +-50 graus

O primeiro candidato que passa vence. Nao busca o "melhor" quadro -- busca o
quadro que nao esta quebrado com o menor desvio do que ja estava escrito, que
e' a unica coisa que eu posso decidir sem inventar direcao de fotografia.

Criterio de aprovacao, o mesmo do scripts/enquadramento.py:

    perto <= 0.45   nenhuma amostra com quase metade do quadro a menos de 14 m
    ceu   <= 0.80   nao e' um plano de ceu vazio
    alvo  >= 0.55   o que bloqueia a mira e' o proprio assunto, nao outra coisa
    nunca enterrada, nunca dentro de volume fechado

A velocidade NAO e' corrigida aqui: mexer em distancia muda o comprimento do
caminho e portanto a velocidade. Quem reconcilia isso e' o passo seguinte,
--ajustar-duracao, que roda sem Blender.

    blender.exe --background --python scripts/consertar_camera.py -- \
        --blend out/cena-1508c.blend --escrever
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

PERTO_M = 14.0
TETO_PERTO = 0.30
TETO_CEU = 0.80
PISO_ALVO = 0.55

# Apertados na terceira rodada de 15/08: com dominio 0.55 os numeros passavam e
# a folha out/entrega-1508e/contato-22.jpg ainda mostrava telhado branco tomando
# P04, P07 e P08 -- e P08 e' o Cafe Colonial, um dos quatro diferenciais. Quem
# manda e' o quadro, nao o teto: o teto desceu ate o quadro concordar.
#
# Acrescentados em 15/08, depois que a folha out/entrega-1508d/contato-22.jpg
# mostrou que o teto de "perto" nao pega o defeito principal: o telhado de um
# pavilhao a 25 m de distancia enche 70% do quadro e passa verde, porque 25 m
# nao e' perto. O que mede o defeito e' DOMINIO -- quanto do quadro e' UMA
# superficie so.
TETO_DOMINIO = 0.30      # um unico objeto ocupando mais que isso nao e' plano
TETO_VEGETACAO = 0.35    # parede de copa: sao muitos objetos, dominio nao pega
PREFIXO_VEG = ("Arvore", "Arbusto")

DIRECOES = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))]

# Colecoes escondidas durante a medida: os letreiros foram dimensionados para
# as cameras VELHAS e sao justamente o que vai ser refeito depois. Medir contra
# eles seria medir contra o proprio defeito.
ESCONDER = ["LETREIROS", "MARCOS_CAMERA", "CAMERA"]

DELTAS_ALT = [0.0, -4.0, 3.0, 6.0, 9.0, 12.0, 16.0, 20.0, 26.0, 34.0, 44.0]
FATORES_DIST = [1.00, 1.15, 1.30, 1.50, 1.75, 2.00, 2.40, 3.00, 3.80]
GIROS_AZ = [0.0, 18.0, -18.0, 32.0, -32.0, 50.0, -50.0, 75.0, -75.0]

# Modo --sem-renumerar: distancia por SOMA, nao por fator. Num push-in o
# comprimento do caminho e' |dist_ini - dist_fim|; somar o mesmo valor nas
# duas pontas afasta a camera e deixa o comprimento -- e portanto a
# velocidade e a duracao -- exatamente onde estavam. E' o que permite
# consertar enquadramento com o render ja rodando, sem renumerar o filme e
# sem jogar fora o que ja esta no disco.
SOMAS_DIST = [0.0, 8.0, 15.0, 22.0, 30.0, 40.0, 55.0, 70.0, -8.0]
ALT_MINIMA = 5.0   # nunca abaixo da regra dele de "lugar aberto 4-15 m"


def custo(dalt, fdist, gaz, somar=False):
    """Quanto o candidato se afasta do que ja estava escrito."""
    dist = abs(fdist) / 12.0 if somar else (fdist - 1.0) * 3.0
    return abs(dalt) / 8.0 + dist + abs(gaz) / 22.0


def candidatos(somar=False):
    faixa = SOMAS_DIST if somar else FATORES_DIST
    lista = [(d, f, g) for d in DELTAS_ALT for f in faixa for g in GIROS_AZ]
    lista.sort(key=lambda c: custo(*c, somar=somar))
    return lista


def grade(lente_mm, sensor_mm, prop, nx, ny):
    meia_h = math.atan((sensor_mm / 2.0) / lente_mm)
    meia_v = math.atan((sensor_mm / prop / 2.0) / lente_mm)
    dirs = []
    for iy in range(ny):
        fy = (iy / (ny - 1)) * 2 - 1 if ny > 1 else 0.0
        for ix in range(nx):
            fx = (ix / (nx - 1)) * 2 - 1 if nx > 1 else 0.0
            dirs.append(Vector((math.tan(meia_h * fx * 0.92),
                                math.tan(meia_v * fy * 0.92),
                                -1.0)).normalized())
    return dirs


def aplicar(plano, dalt, fdist, gaz, somar=False):
    """Copia do plano com o candidato aplicado.

    `somar=True` trata `fdist` como DESLOCAMENTO em metros, nao como fator.
    """
    novo = json.loads(json.dumps({k: v for k, v in plano.items()
                                  if not k.startswith("_")}))
    c = novo["camera"]
    c["alt_ini_m"] = round(max(ALT_MINIMA, plano["camera"]["alt_ini_m"] + dalt), 2)
    c["alt_fim_m"] = round(max(ALT_MINIMA, plano["camera"]["alt_fim_m"] + dalt), 2)
    if somar:
        c["dist_ini_m"] = round(max(6.0, plano["camera"]["dist_ini_m"] + fdist), 1)
        c["dist_fim_m"] = round(max(6.0, plano["camera"]["dist_fim_m"] + fdist), 1)
    else:
        c["dist_ini_m"] = round(plano["camera"]["dist_ini_m"] * fdist, 1)
        c["dist_fim_m"] = round(plano["camera"]["dist_fim_m"] * fdist, 1)
    c["azimute_deg"] = round((plano["camera"]["azimute_deg"] + gaz) % 360.0, 1)
    novo["_alvo"] = plano["_alvo"]
    novo["_alvo_fim"] = plano["_alvo_fim"]
    return novo


def velocidade_ok(plano_teste, centro):
    """O candidato mantem o plano dentro da faixa cinematografica?

    Sem isto, o modo --sem-renumerar entregaria uma camera bonita e um
    movimento fora de faixa -- que e' o defeito que a decupagem inteira existe
    para nao ter. A duracao NAO pode ser tocada aqui: mexer nela renumera o
    filme e invalida o que ja foi renderizado.
    """
    m = planos_mod.medir(plano_teste, centro)
    lo, hi = planos_mod.FAIXAS[plano_teste["movimento"]]
    return lo <= m["v_pico"] <= hi, m["v_pico"]


def dentro_de_volume(cena, dg, origem):
    impares = 0
    for direcao in DIRECOES:
        n, p = 0, Vector(origem)
        for _ in range(48):
            ok, loc, _, _, _, _ = cena.ray_cast(dg, p, direcao, distance=2000.0)
            if not ok:
                break
            n += 1
            p = loc + direcao * 0.01
        if n % 2 == 1:
            impares += 1
    return impares >= 3


def medir(cena, dg, plano, centro, dirs, n_amostras, checar_volume=True):
    """Devolve (passa, metricas) para um plano ja com o candidato aplicado."""
    pior_perto = 0.0
    pior_ceu = 0.0
    pior_alvo = 1.0
    pior_dominio = 0.0
    pior_veg = 0.0
    falha = None

    for i in range(n_amostras):
        t = i / (n_amostras - 1)
        pos_t, mira_t = planos_mod.amostra(plano, t, centro)
        pos = Vector(pos_t)
        mira = Vector(mira_t)

        # enterrada
        ok, loc, _, _, _, _ = cena.ray_cast(dg, pos, Vector((0, 0, -1)),
                                            distance=800.0)
        if ok and (pos.z - loc.z) < 0.5:
            return False, {"falha": "enterrada", "t": round(t, 2), "nota": 9.9}

        # o assunto esta atras de outra coisa?
        v = mira - pos
        L = v.length
        if L > 1e-6:
            d = v.normalized()
            ok2, loc2, _, _, _, _ = cena.ray_cast(dg, pos + d * 0.05, d,
                                                  distance=L)
            razao = ((loc2 - pos).length / L) if ok2 else 1.0
            pior_alvo = min(pior_alvo, razao)
            if razao < PISO_ALVO:
                falha = falha or ("alvo_ocluso", round(t, 2), round(razao, 2))

        # quadro tomado / ceu vazio
        rot = (mira - pos).to_track_quat("-Z", "Y")
        n_perto = n_ceu = n_veg = 0
        conta = {}
        for dr in dirs:
            mundo = rot @ dr
            # ray_cast devolve (ok, local, normal, indice, OBJETO, matriz):
            # o objeto e' o 5o, nao o 6o. Trocar isso entrega uma Matrix onde
            # se espera um Object e o erro so aparece em tempo de execucao.
            ok3, loc3, _, _, obj3, _ = cena.ray_cast(dg, pos + mundo * 0.05,
                                                     mundo, distance=3000.0)
            if not ok3:
                n_ceu += 1
                continue
            if (loc3 - pos).length < PERTO_M:
                n_perto += 1
            nome = obj3.name if obj3 else "?"
            if nome.startswith(PREFIXO_VEG):
                n_veg += 1
                nome = "_vegetacao"      # copa nao se soma por instancia
            conta[nome] = conta.get(nome, 0) + 1
        n = len(dirs)
        pior_perto = max(pior_perto, n_perto / n)
        pior_ceu = max(pior_ceu, n_ceu / n)
        dom = max((v for k, v in conta.items() if k != "_vegetacao"), default=0) / n
        pior_dominio = max(pior_dominio, dom)
        pior_veg = max(pior_veg, n_veg / n)

        if checar_volume and dentro_de_volume(cena, dg, pos):
            return False, {"falha": "dentro", "t": round(t, 2), "nota": 9.9}

    metricas = {"perto": round(pior_perto, 3), "ceu": round(pior_ceu, 3),
                "alvo": round(pior_alvo, 3), "dominio": round(pior_dominio, 3),
                "vegetacao": round(pior_veg, 3)}
    # "nota" e' o excesso somado sobre os tetos. Serve para o melhor-esforco:
    # quando NENHUM candidato passa, o menos ruim ainda e' melhor que deixar
    # como esta -- e ele sai carimbado como melhor-esforco, nao como aprovado.
    metricas["nota"] = round(
        max(0.0, pior_perto - TETO_PERTO) * 2.0
        + max(0.0, pior_ceu - TETO_CEU) * 1.0
        + max(0.0, PISO_ALVO - pior_alvo) * 2.0
        + max(0.0, pior_dominio - TETO_DOMINIO) * 3.0
        + max(0.0, pior_veg - TETO_VEGETACAO) * 2.0, 4)
    for teto, valor, nome in ((TETO_DOMINIO, pior_dominio, "dominio"),
                              (TETO_VEGETACAO, pior_veg, "vegetacao"),
                              (TETO_PERTO, pior_perto, "perto"),
                              (TETO_CEU, pior_ceu, "ceu")):
        if valor > teto:
            metricas["falha"] = nome
            return False, metricas
    if falha:
        metricas["falha"] = "alvo"
        return False, metricas
    return True, metricas


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--blend", required=True)
    ap.add_argument("--planos-json", dest="planos_json", default="data/planos.json")
    ap.add_argument("--dados", default="data/mapa_agroshow26.json")
    ap.add_argument("--escrever", action="store_true",
                    help="grava o conserto em data/planos.json")
    ap.add_argument("--relatorio", default="out/conserto-camera.json")
    ap.add_argument("--sem-renumerar", action="store_true", dest="sem_renumerar",
                    help="distancia por SOMA e velocidade travada na faixa, para "
                         "a duracao (e portanto a numeracao dos quadros) nao mudar")
    ap.add_argument("--so-planos", default=None,
                    help="lista de planos a tocar, ex: P04,P08,P12")
    ap.add_argument("--intocaveis", default=None,
                    help="planos que NAO podem mudar (ja renderizados), ex: P01,P02")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:]
                         if "--" in sys.argv else sys.argv[1:])

    bpy.ops.wm.open_mainfile(filepath=str(Path(args.blend).resolve()))
    cena = bpy.context.scene
    for nome in ESCONDER:
        col = bpy.data.collections.get(nome)
        if col:
            for o in col.objects:
                o.hide_set(True)
                o.hide_viewport = True
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()

    dados = terreno.carregar_mapa(args.dados)
    pacote = planos_mod.carregar(args.planos_json, dados=dados)
    centro = pacote["centro"]
    prop = cena.render.resolution_x / cena.render.resolution_y

    cands = candidatos(somar=args.sem_renumerar)
    so = set(args.so_planos.split(",")) if args.so_planos else None
    intocaveis = set(args.intocaveis.split(",")) if args.intocaveis else set()
    if args.sem_renumerar:
        print("  modo SEM RENUMERAR: distancia por soma, velocidade travada na faixa")
    if so:
        print(f"  so estes planos: {', '.join(sorted(so))}")
    if intocaveis:
        print(f"  intocaveis (ja renderizados): {', '.join(sorted(intocaveis))}")
    print(f"  {len(cands)} candidatos por plano, do mais barato ao mais caro")
    print(f"{'plano':6} {'d.alt':>6} {'f.dist':>7} {'giro':>6} {'perto':>6} "
          f"{'ceu':>6} {'alvo':>6} {'domin':>6} {'veget':>6}  situacao")
    print("-" * 104)

    doc = json.loads(Path(args.planos_json).read_text(encoding="utf-8"))
    por_id = {p["id"]: p for p in doc["planos"]}
    relatorio = []

    for plano in pacote["planos"]:
        if plano["id"] in intocaveis or (so and plano["id"] not in so):
            continue
        lente = float(plano["lente_mm"])
        rala = grade(lente, 36.0, prop, 5, 3)
        fina = grade(lente, 36.0, prop, 9, 5)

        ok0, m0 = medir(cena, dg, plano, centro, fina, 9)
        if ok0:
            print(f"{plano['id']:6} {'-':>6} {'-':>7} {'-':>6} "
                  f"{m0['perto']:6.2f} {m0['ceu']:6.2f} {m0['alvo']:6.2f} "
                  f"{m0.get('dominio', -1):6.2f} {m0.get('vegetacao', -1):6.2f}"
                  f"  ja passava")
            relatorio.append({"id": plano["id"], "mudou": False, "antes": m0})
            continue

        escolhido = None
        melhor = None       # (nota, dalt, fdist, gaz, metricas, teste)
        for dalt, fdist, gaz in cands:
            if dalt == 0.0 and fdist == 1.0 and gaz == 0.0:
                continue
            teste = aplicar(plano, dalt, fdist, gaz, somar=args.sem_renumerar)
            if args.sem_renumerar:
                vok, _vp = velocidade_ok(teste, centro)
                if not vok:
                    continue
            ok, mr = medir(cena, dg, teste, centro, rala, 5, checar_volume=False)
            if not ok:
                nota = mr.get("nota", 9.9)
                if melhor is None or nota < melhor[0]:
                    melhor = (nota, dalt, fdist, gaz, mr, teste)
                continue
            ok2, m2 = medir(cena, dg, teste, centro, fina, 9)
            if ok2:
                escolhido = (dalt, fdist, gaz, m2, teste)
                break
            nota = m2.get("nota", 9.9)
            if melhor is None or nota < melhor[0]:
                melhor = (nota, dalt, fdist, gaz, m2, teste)

        if escolhido is None and melhor is not None and melhor[0] < m0.get("nota", 9.9):
            _, dalt, fdist, gaz, _mm, teste = melhor
            ok3, m3 = medir(cena, dg, teste, centro, fina, 9)
            m3["melhor_esforco"] = True
            escolhido = (dalt, fdist, gaz, m3, teste)

        if escolhido is None:
            print(f"{plano['id']:6} {'-':>6} {'-':>7} {'-':>6} "
                  f"{m0.get('perto', float('nan')):6.2f} "
                  f"{m0.get('ceu', float('nan')):6.2f} "
                  f"{m0.get('alvo', float('nan')):6.2f}  SEM CONSERTO "
                  f"({m0.get('falha')})")
            relatorio.append({"id": plano["id"], "mudou": False, "antes": m0,
                              "sem_conserto": True})
            continue

        dalt, fdist, gaz, m2, teste = escolhido
        selo = "MELHOR-ESFORCO " if m2.get("melhor_esforco") else ""
        print(f"{plano['id']:6} {dalt:+6.0f} {fdist:7.2f} {gaz:+6.0f} "
              f"{m2['perto']:6.2f} {m2['ceu']:6.2f} {m2['alvo']:6.2f} "
              f"{m2.get('dominio', -1):6.2f} {m2.get('vegetacao', -1):6.2f}  "
              f"{selo}era {m0.get('falha')} "
              f"dom={m0.get('dominio','?')} veg={m0.get('vegetacao','?')}")

        alvo_doc = por_id[plano["id"]]
        antes_cam = dict(alvo_doc["camera"])
        relatorio.append({
            "id": plano["id"], "titulo": plano["titulo"], "mudou": True,
            "delta_alt_m": dalt, "fator_dist": fdist, "giro_az_deg": gaz,
            "antes": m0, "depois": m2,
            "camera_antes": antes_cam, "camera_depois": teste["camera"],
        })
        if args.escrever:
            alvo_doc["camera"] = teste["camera"]
            alvo_doc["camera_antes_1508"] = antes_cam
            alvo_doc["conserto_1508"] = (
                ("MELHOR ESFORCO -- nenhum candidato passou em tudo. " if
                 m2.get("melhor_esforco") else "") +
                f"reenquadrado por medida: altura {dalt:+.0f} m, distancia "
                f"{('%+.0f m' % fdist) if args.sem_renumerar else ('x%.2f' % fdist)}"
                f", azimute {gaz:+.0f} graus. Antes falhava em "
                f"{m0.get('falha')} (dominio={m0.get('dominio')}, "
                f"vegetacao={m0.get('vegetacao')}, perto={m0.get('perto')}, "
                f"alvo={m0.get('alvo')}); depois dominio={m2.get('dominio')}, "
                f"vegetacao={m2.get('vegetacao')}, perto={m2['perto']}, "
                f"alvo={m2['alvo']}.")

    Path(args.relatorio).parent.mkdir(parents=True, exist_ok=True)
    Path(args.relatorio).write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=1), encoding="utf-8")
    print("-" * 76)
    print(f"  relatorio em {args.relatorio}")

    if args.escrever:
        Path(args.planos_json).write_text(
            json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        n = sum(1 for r in relatorio if r.get("mudou"))
        print(f"  {n} plano(s) reescrito(s) em {args.planos_json}")
        print("  ATENCAO: rodar `python scripts/planos.py --conferir` -- mexer "
              "em distancia muda a velocidade.")


if __name__ == "__main__":
    main()
