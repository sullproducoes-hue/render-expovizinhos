#!/usr/bin/env python3
"""Mesas e cadeiras das pracas de alimentacao e do Cafe Colonial.

Pedido literal do cliente: *"mesas, cadeiras, o pessoal com os guichês lá"*
`[00:57]`. Contrato em `data/mobiliario.json`.

**Isto NAO e proxy, e essa e a diferenca que importa.** Gente e gado viraram
proxy porque nao existe modelo CC0 utilizavel; mesa e cadeira o Poly Haven tem
em CC0, com textura e na escala certa. Era o caminho mais barato do projeto e
estava parado -- e continua sendo o unico lugar onde a biblioteca resolve
sozinha, do jeito que ele pediu em *"quero que baixe tudo que tem de material e
formas sem precisar fazer quase nada do zero"*.

A malha vem por `append` do .blend baixado e e COMPARTILHADA: cada mesa e cada
cadeira e uma instancia, nao uma copia.
"""

import json
import math
import random
from pathlib import Path

import bpy

import terreno

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO = RAIZ / "data" / "mobiliario.json"


def _malha_do_blend(slug, res):
    """Traz a malha de dentro do .blend do Poly Haven.

    Pega a malha de MAIS POLIGONOS do arquivo: os .blend deles costumam trazer
    tambem uma camera, uma luz e um plano de estudio, e `objects[0]` pode ser
    qualquer um deles. Pelo numero de poligonos o objeto de verdade ganha
    sempre.
    """
    caminho = RAIZ / "assets" / "modelo" / slug / f"{slug}_{res}.blend"
    if not caminho.exists():
        return None
    antes = set(bpy.data.meshes)
    with bpy.data.libraries.load(str(caminho), link=False) as (de, para):
        para.meshes = list(de.meshes)
    novas = [m for m in bpy.data.meshes if m not in antes]
    if not novas:
        return None
    return max(novas, key=lambda m: len(m.polygons))


def construir(dados, col_pai, centro_arena, solidos=None, bbox=None):
    if not CONTRATO.exists():
        return 0

    cont = json.loads(CONTRATO.read_text(encoding="utf-8"))
    res = cont.get("resolucao", "1k")
    rnd = random.Random(cont["semente"])

    malhas = {}
    for peca in cont["pecas"]:
        m = _malha_do_blend(peca["slug"], res)
        if m is None:
            print(f"  mobiliario: falta {peca['slug']} em assets/modelo/ -- "
                  f"rode `python scripts/assets.py --mobiliario`")
            return 0
        malhas[peca["papel"]] = m

    col = bpy.data.collections.new("MOBILIARIO")
    col_pai.children.link(col)

    def _norm(s):
        import unicodedata
        s = unicodedata.normalize("NFKD", s.lower())
        return "".join(c for c in s if not unicodedata.combining(c))

    def livre_em(zona):
        """Impede movel dentro de predio -- MENOS o predio da propria zona.

        A primeira versao disto perdeu 117 pecas em silencio: a Praca de
        Alimentacao Coberta E um solido construido, entao o teste generico
        rejeitava justamente as cadeiras que estao no lugar certo. Movel de
        praca coberta fica DENTRO da praca coberta.
        """
        z = _norm(zona)
        alheios = [q for n, q, _c in (solidos or [])
                   if not (z in _norm(n) or _norm(n) in z)]

        def livre(x, y):
            return not any(q[0] <= x <= q[2] and q[1] <= y <= q[3]
                           for q in alheios)
        return livre

    postos = 0
    for arr in cont["arranjos"]:
        p = terreno.ponto_da_zona(dados, arr["zona"])
        if p is None:
            print(f"  aviso: zona '{arr['zona']}' nao existe -- "
                  f"{arr['conjuntos']} conjuntos nao foram postos")
            continue
        malha_mesa = malhas[arr["mesa"]]
        livre = livre_em(arr["zona"])
        raio = arr["raio_m"]
        n_cad = arr.get("cadeiras_por_mesa", 0)
        r_cad = arr.get("raio_da_cadeira_m", 0.95)

        for _ in range(arr["conjuntos"]):
            a = rnd.uniform(0, 2 * math.pi)
            r = raio * math.sqrt(rnd.random())
            x, y = p[0] + r * math.cos(a), p[1] + r * math.sin(a)
            if bbox and not (bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]):
                continue
            if not livre(x, y):
                continue          # mesa dentro de OUTRO predio
            z = terreno.elevacao(x, y, centro_arena)
            # giro proprio por conjunto: praca alinhada em grade le como CG
            giro = rnd.uniform(0, 2 * math.pi)

            o = bpy.data.objects.new(f"Mesa_{arr['zona'][:12]}", malha_mesa)
            col.objects.link(o)
            o.location = (x, y, z)
            o.rotation_euler = (0.0, 0.0, giro)
            o["cc0"] = True
            o["pedido_do_cliente"] = cont["o_pedido_dele"]
            postos += 1

            for k in range(n_cad):
                ang = giro + k * (2 * math.pi / n_cad) + rnd.uniform(-0.35, 0.35)
                d = r_cad * rnd.uniform(0.85, 1.2)
                cx, cy = x + d * math.cos(ang), y + d * math.sin(ang)
                if not livre(cx, cy):
                    continue
                c = bpy.data.objects.new("Cadeira", malhas["cadeira"])
                col.objects.link(c)
                c.location = (cx, cy, terreno.elevacao(cx, cy, centro_arena))
                # a cadeira olha para a mesa, com folga: ninguem devolve a
                # cadeira ao lugar depois de levantar
                c.rotation_euler = (0.0, 0.0,
                                    ang + math.pi + rnd.uniform(-0.5, 0.5))
                postos += 1

    print(f"  mobiliario ......... {postos} pecas CC0 em {len(malhas)} malhas "
          f"(mesa e cadeira -- pedido dele em [00:57])")
    return postos
