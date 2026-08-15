#!/usr/bin/env python3
"""As tendas do recinto, nas posicoes medidas da planta.

Ordem do Natan em 15/08: *"preciso colocar as tendas nas posicoes reais"*.

Ate aqui os 134 estandes da planta eram **caixa** de 3,2 m de altura, na
posicao certa. Posicao certa e forma errada: o que cobre estande de feira e
tenda piramidal de lona branca, e de 20 m de camera a diferenca entre caixa e
tenda e a diferenca entre maquete e parque. Este modulo troca a forma **sem
tocar na posicao** -- o `x, y` de cada estande continua vindo de
`data/mapa_agroshow26.json`, medido do desenho e convertido pelo mesmo
`terreno.para_mundo` de sempre, e a orientacao continua saindo do
`orientar_estandes` do gerador, que alinha cada um ao eixo da sua fileira.

## O que a medicao encontrou, e e o motivo de o modulo existir

A planta foi desenhada **na grade de tenda padrao**, e isso nao estava escrito
em lugar nenhum -- sai do histograma das areas cotadas:

    serie A ... 35 dos 41 estandes tem 25,0 m² -> tenda 5x5 exata
    serie C ... 39 dos 93 estandes tem 100,0 m² -> tenda 10x10 exata

As duas modas caem **em cima** das medidas padrao de tenda de feira no Brasil
(3x3, 5x5, 10x10), que a doutrina manda nao errar (§ "Nao aceitar sem saber as
medidas padrao das tendas -- errar isso invalida a planta inteira"). Nao e
coincidencia que se possa ignorar: e a prova de que a familia de tenda e a
leitura certa da planta, e nao uma escolha de gosto.

## A regra

Cada estande recebe a familia de **lado mais proximo** e uma escala em X/Y que
fecha a area cotada exatamente. Z nao escala: o pe-direito e medida de mercado,
nao proporcao. Com o teto de +-30% declarado abaixo, **131 dos 134 estandes**
sao instancia de tres malhas; 3 sobram e recebem malha propria, com o motivo
gravado no objeto.

O teto existe porque escala e emprestimo de forma, e emprestimo tem limite: uma
5x5 esticada para 7,4 m deixa de ser 5x5. Onde estoura, a peca sai propria --
mesmo criterio que o gerador ja usava para as areas fora do modulo.

Confira sem Blender e sem GPU:

    python3 scripts/tendas.py --conferir
"""

import argparse
import json
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO = RAIZ / "data" / "tendas.json"

# A fonte de estande e a MESMA do gerador: data/mapa_agroshow26.json, em pontos
# de PDF, convertida por terreno.para_mundo. Ha uma segunda fonte com as
# coordenadas ja em metros (data/estandes.json, saida do classificar_estandes) e
# as duas concordam -- conferido codigo a codigo, maior desvio 5 mm, mesmas
# areas e mesmas series nos 134. Ler a do gerador mesmo assim, porque contrato e
# geometria que discordam de fonte e defeito que nao aparece na tela.
MAPA = RAIZ / "data" / "mapa_agroshow26.json"

# Medidas padrao de tenda de feira no Brasil. Nao sao escolha: sao o que se
# aluga, e sao as tres que a doutrina nomeia.
FAMILIAS = {"3x3": 3.0, "5x5": 5.0, "10x10": 10.0}

# Ate quanto uma familia pode ser esticada antes de deixar de ser ela mesma.
# 1,30 nao e numero redondo escolhido a esmo -- foi lido do histograma: com ele
# a serie C inteira (min 0,817, max 1,288) cabe, e o que sobra sao exatamente os
# tres estandes de 50 e 55 m², que sao "duas 5x5 emparelhadas" e nao uma 5x5.
TETO_DE_ESCALA = 1.30

# Abaixo disso a escala nao vale a pena gravar: e instancia limpa.
TOLERANCIA_EXATA = 0.02

# Os dois pontos declarados em data/pecas-avulsas.json, medidos de tenda de
# aluguel: 5x5 tem pe 2,6 e cume 3,9; 10x10 tem pe 3,0 e cume 5,2. O resto e
# interpolacao linear entre eles, e extrapolacao segurada nas pontas.
_PE_5, _CUME_5 = 2.6, 3.9
_PE_10, _CUME_10 = 3.0, 5.2


def perfil(lado):
    """Pe-direito e altura de cume de uma tenda de `lado` metros.

    Devolve os dois numeros mais a flecha (cume - pe), que e o que faz a agua
    ter caimento. Segura o pe entre 2,3 e 3,4 m: fora disso deixa de ser tenda
    de feira e vira estrutura, que e outra peca.
    """
    t = (lado - 5.0) / 5.0
    pe = _PE_5 + t * (_PE_10 - _PE_5)
    cume = _CUME_5 + t * (_CUME_10 - _CUME_5)
    pe = min(max(pe, 2.3), 3.4)
    return round(pe, 3), round(max(cume, pe + 0.7), 3)


def familia_de(area_m2):
    """(nome da familia, lado da familia, lado cotado, escala) para uma area.

    O lado cotado e a raiz da area: a planta cota AREA em texto e desenha o
    estande como quadrado, entao raiz da area e a leitura fiel do que esta la.
    Nao e assuncao nova -- e a mesma que o gerador ja fazia com as caixas.
    """
    lado = math.sqrt(area_m2)
    nome, lado_fam = min(FAMILIAS.items(), key=lambda kv: abs(lado - kv[1]))
    return nome, lado_fam, lado, lado / lado_fam


def carregar_estandes(caminho=None):
    """Os 134 estandes da planta, da mesma fonte que o gerador usa."""
    p = Path(caminho) if caminho else MAPA
    return json.loads(p.read_text(encoding="utf-8"))["estandes"]


def classificar(estandes, teto=TETO_DE_ESCALA):
    """Cada estande -> familia, escala e modo (instancia ou malha propria).

    Pura: nao importa bpy, roda em qualquer Python. E o que o --conferir mede.
    """
    itens, censo = [], {}
    for st in estandes:
        area = st.get("area_m2")
        if area is None:
            continue
        nome, lado_fam, lado, escala = familia_de(area)

        if escala > teto or escala < 1.0 / teto:
            modo, motivo = "proprio", (
                f"escala {escala:.3f} fora do teto de {teto:.2f} -- "
                f"{area:.0f} m² nao e uma {nome} esticada, e um conjunto de "
                f"modulos. Sai com malha propria de lado {lado:.2f} m")
        elif abs(escala - 1.0) <= TOLERANCIA_EXATA:
            modo, motivo = "instancia_exata", "area cotada bate com a familia"
        else:
            modo, motivo = "instancia_escalada", (
                f"instancia da {nome} com escala {escala:.3f} em X/Y para "
                f"fechar os {area:.2f} m² cotados; Z nao escala")

        # A altura que o objeto VAI TER na cena, nao a que ele teria se fosse
        # malha propria: instancia herda a malha da familia, e Z nao escala.
        # Reportar o perfil do lado cotado aqui daria 5,95 m para uma tenda que
        # sai da cena com 5,20 -- numero certo sobre a peca errada.
        pe, cume = perfil(lado if modo == "proprio" else lado_fam)
        itens.append({
            "codigo": st["codigo"], "serie": st.get("serie"),
            "area_m2": area, "lado_m": round(lado, 3),
            "familia": nome, "escala": round(escala, 4),
            "modo": modo, "pe_direito_m": pe, "altura_total_m": cume,
            "motivo": motivo,
        })
        chave = f"{nome}/{modo}"
        censo[chave] = censo.get(chave, 0) + 1
    return itens, censo


def resumo(itens):
    """Os numeros que o --conferir imprime e que o contrato guarda."""
    total = len(itens)
    instanciados = sum(1 for i in itens if i["modo"].startswith("instancia"))
    por_familia = {}
    for i in itens:
        d = por_familia.setdefault(i["familia"], {"quantos": 0, "escala_min": 9.9,
                                                  "escala_max": 0.0})
        d["quantos"] += 1
        d["escala_min"] = round(min(d["escala_min"], i["escala"]), 4)
        d["escala_max"] = round(max(d["escala_max"], i["escala"]), 4)
    return {
        "estandes": total,
        "instanciados": instanciados,
        "malha_propria": total - instanciados,
        "malhas_no_arquivo": len(por_familia) + (total - instanciados),
        "por_familia": por_familia,
        "altura_maxima_m": round(max(i["altura_total_m"] for i in itens), 2),
    }


# --------------------------------------------------------------------------
# Geometria -- daqui para baixo o bpy entra, e so aqui

def _malha_de_tenda(nome, lado, col, mats, barriga=True):
    """Tenda piramidal: quatro pes de tubo e lona de quatro aguas.

    Mesma familia de geometria de `avulsas.tenda_piramidal`, com duas coisas a
    mais que a pendencia 12b do RETOMAR pedia: a **barriga do pano**, que e o
    que faz a lona nao ler como placa rigida de perto, e o beiral caido entre
    os cantos. Custa 16 triangulos de telhado em vez de 4, e as 131 instancias
    dividem a mesma malha -- entao o custo em memoria e uma vez, nao 131.
    """
    import bmesh
    import bpy
    from mathutils import Matrix, Vector

    pe, cume = perfil(lado)
    h = lado / 2.0
    bm = bmesh.new()

    for sx in (-1, 1):
        for sy in (-1, 1):
            ini = len(bm.faces)
            bmesh.ops.create_cone(
                bm, cap_ends=True, cap_tris=False, segments=6,
                radius1=0.055, radius2=0.055, depth=pe,
                matrix=Matrix.Translation(Vector((sx * h, sy * h, pe / 2))))
            bm.faces.ensure_lookup_table()
            for f in bm.faces[ini:]:
                f.material_index = 1

    ini = len(bm.faces)
    beiral = h * 1.06                      # a lona passa do pe, como na real
    cantos = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    v = [bm.verts.new((sx * beiral, sy * beiral, pe)) for sx, sy in cantos]
    topo = bm.verts.new((0.0, 0.0, cume))

    # Flecha do pano. 3,5% do vao no beiral e 2% na agua e o que se ve numa
    # tenda esticada de verdade: o beiral cede mais que o meio da agua, porque
    # o meio esta puxado pelo mastro.
    sag_beiral = (0.035 * lado) if barriga else 0.0
    sag_agua = (0.020 * lado) if barriga else 0.0

    for i in range(4):
        a, b = v[i], v[(i + 1) % 4]
        if barriga:
            meio = bm.verts.new(((a.co.x + b.co.x) / 2.0,
                                 (a.co.y + b.co.y) / 2.0,
                                 pe - sag_beiral))
            centro = bm.verts.new(((a.co.x + b.co.x) / 3.0,
                                   (a.co.y + b.co.y) / 3.0,
                                   (pe * 2 + cume) / 3.0 - sag_agua))
            # winding preservado do original (a, b, topo): visto de cima os
            # cantos estao em sentido anti-horario, entao a normal sai para
            # fora e para cima. Trocar a ordem aqui vira lona de dentro para
            # fora, e isso nao aparece no viewport solido -- so no render.
            bm.faces.new((a, meio, centro))
            bm.faces.new((meio, b, centro))
            bm.faces.new((b, topo, centro))
            bm.faces.new((topo, a, centro))
        else:
            bm.faces.new((a, b, topo))

    bm.faces.ensure_lookup_table()
    for f in bm.faces[ini:]:
        f.material_index = 0

    malha = bpy.data.meshes.new(nome)
    bm.to_mesh(malha)
    bm.free()
    for m in mats:
        malha.materials.append(m)
    obj = bpy.data.objects.new(nome, malha)
    col.objects.link(obj)
    return obj


def _materiais():
    """0 lona, 1 tubo galvanizado. Pe de tenda e tubo de andaime, nao trelica
    de palco: MAT_GRADIL, nao MAT_TRELICA."""
    import bpy
    m = {x.name: x for x in bpy.data.materials}
    return [x for x in (m.get("MAT_LONA"), m.get("MAT_GRADIL")) if x is not None]


def cobertura_de_lona(nome, largura, profundidade, col, mats=None, vao_max=17.0):
    """Cobertura de lona em naves de duas aguas, no lugar da laje chapada.

    A Praca de Alimentacao Coberta tem 145,5 x 33,6 m e o contrato de
    `estimativas.json` ja a declara **MAT_LONA** -- ou seja, o arquivo sempre
    disse que aquilo e pano. O gerador, porem, a construia como caixa de 0,3 m
    de espessura sobre pilares: uma laje. Laje de lona nao existe.

    Cobre o retangulo com naves de duas aguas de no maximo `vao_max` de vao,
    que e a largura em que essas tendas sao alugadas. 33,6 m viram duas naves
    de 16,8 m; 145,5 m e o comprimento que elas correm.

    Devolve o objeto com a base do beiral em z=0, para o chamador so posicionar.
    """
    import bmesh
    import bpy

    mats = _materiais() if mats is None else mats
    naves = max(1, int(math.ceil(profundidade / vao_max)))
    vao = profundidade / naves
    flecha = vao * 0.18                    # caimento da agua, ~10 graus
    bm = bmesh.new()

    meia = largura / 2.0
    for n in range(naves):
        y0 = -profundidade / 2.0 + n * vao
        y1 = y0 + vao
        ym = (y0 + y1) / 2.0
        for y_beiral in (y0, y1):
            # Cada agua e um quadrilatero, do beiral (z=0) ate a cumeeira.
            #
            # A ordem dos vertices e escolhida para a normal sair PARA CIMA por
            # construcao, e nao por `recalc_face_normals` depois. O motivo e que
            # cada agua e uma ilha solta -- nao compartilha aresta com a
            # vizinha --, e o recalc trabalha por casca conectada: com ilhas
            # soltas ele orienta cada uma por conta, e metade do telhado podia
            # sair virada para baixo. Telhado virado nao da erro: da agua preta
            # no render, e so aparece no quadro final.
            #
            # A conta: para o quadrilatero (A, B, C, D) com A e B no beiral, a
            # componente z da normal sai proporcional a (ym - y_beiral). Com o
            # beiral em y0 (abaixo da cumeeira) essa diferenca e positiva e a
            # ordem direta serve; com o beiral em y1 ela e negativa, e a ordem
            # tem que inverter.
            sobe = ym > y_beiral
            a = bm.verts.new((-meia, y_beiral, 0.0))
            b = bm.verts.new((meia, y_beiral, 0.0))
            c = bm.verts.new((meia, ym, flecha))
            d = bm.verts.new((-meia, ym, flecha))
            f = bm.faces.new((a, b, c, d) if sobe else (d, c, b, a))
            f.material_index = 0

    bm.faces.ensure_lookup_table()
    malha = bpy.data.meshes.new(nome)
    bm.to_mesh(malha)
    bm.free()
    for m in mats:
        malha.materials.append(m)
    obj = bpy.data.objects.new(nome, malha)
    col.objects.link(obj)
    obj["naves"] = naves
    obj["vao_m"] = round(vao, 2)
    return obj


def construir(dados, col, centro_arena, terreno_mod, dentro, bbox=None):
    """Instancia as tendas nas posicoes medidas. Substitui as caixas.

    Recebe `terreno_mod` e `dentro` de fora para nao duplicar a leitura de
    escala nem a regra do corte por plano -- as duas moram no gerador e sao
    fonte unica.
    """
    import bpy

    mats = _materiais()
    est = dados["estandes"]
    itens, _ = classificar(est)
    por_codigo = {i["codigo"]: i for i in itens}

    bases = {}
    for nome, lado in FAMILIAS.items():
        b = _malha_de_tenda(f"TENDA_{nome}", lado, col, mats)
        b.hide_render = b.hide_viewport = True
        bases[nome] = b

    origem = dados["_origem"]
    cont = {"instanciado": 0, "proprio": 0, "fora_do_corte": 0}
    postos = []

    for st in est:
        it = por_codigo.get(st["codigo"])
        if it is None:
            continue
        x, y = terreno_mod.para_mundo(st["x"], st["y"], origem)
        if not dentro(bbox, x, y):
            cont["fora_do_corte"] += 1
            continue

        if it["modo"] == "proprio":
            obj = _malha_de_tenda(st["codigo"], it["lado_m"], col, mats)
            cont["proprio"] += 1
        else:
            obj = bpy.data.objects.new(st["codigo"], bases[it["familia"]].data)
            col.objects.link(obj)
            if it["modo"] == "instancia_escalada":
                obj.scale = (it["escala"], it["escala"], 1.0)
            cont["instanciado"] += 1

        obj.location = (x, y, terreno_mod.elevacao(x, y, centro_arena))
        obj["material"] = "MAT_LONA"
        obj["area_m2"] = it["area_m2"]
        obj["serie"] = it["serie"]
        obj["familia_de_tenda"] = it["familia"]
        obj["altura_total_m"] = it["altura_total_m"]
        obj["posicao_medida"] = True
        obj["procedencia"] = (
            f"posicao medida do desenho (data/estandes.json); forma = tenda "
            f"{it['familia']} padrao. {it['motivo']}")
        postos.append((obj, x, y))

    return cont, postos


# --------------------------------------------------------------------------

def escrever_contrato(itens, censo):
    dados = {
        "_leia": ("As tendas do recinto. A POSICAO de cada uma vem medida de "
                  "data/estandes.json e nao se toca aqui; o que este arquivo "
                  "decide e a FORMA. Confira com: python3 scripts/tendas.py --conferir"),
        "ordem_dele_15_08": "'preciso colocar as tendas nas posicoes reais'.",
        "o_que_mudou": ("os 134 estandes eram caixa de 3,2 m na posicao certa. "
                        "Passam a ser tenda piramidal de lona, na mesma posicao "
                        "e com a mesma orientacao de fileira."),
        "fonte_da_posicao": (
            "data/mapa_agroshow26.json, em pontos de PDF, convertida por "
            "terreno.para_mundo -- a mesma fonte que o gerador usa. A segunda "
            "fonte (data/estandes.json, ja em metros) concorda: mesmos 134 "
            "codigos, mesmas areas, mesmas series, maior desvio 5 mm."),
        "a_prova_de_que_a_familia_e_a_leitura_certa": (
            "35 dos 41 estandes da serie A tem 25,00 m² e 39 dos 93 da serie C "
            "tem 100,00 m². As duas modas caem EM CIMA das medidas padrao de "
            "tenda de feira (5x5 e 10x10). A planta foi desenhada na grade de "
            "tenda, e isso nao estava escrito em lugar nenhum -- sai do "
            "histograma das areas cotadas."),
        "familias_m": FAMILIAS,
        "teto_de_escala": TETO_DE_ESCALA,
        "por_que_o_teto": (
            "escala e emprestimo de forma e emprestimo tem limite. Com 1,30 a "
            "serie C inteira cabe (min 0,817, max 1,288) e o que sobra sao os "
            "tres estandes de 50 e 55 m², que sao duas 5x5 emparelhadas e nao "
            "uma 5x5 esticada. Esses saem com malha propria."),
        "z_nao_escala": (
            "pe-direito e medida de mercado, nao proporcao: uma tenda maior "
            "tem mais chao, nao mais pe. A escala vai so em X/Y. Consequencia "
            "declarada: nas instancias escaladas o caimento da agua muda "
            "(23,8 graus na 10x10 exata, 18,9 graus na maior delas)."),
        "altura_e_a_da_familia_nas_instancias": (
            "instancia herda a malha da familia e Z nao escala, entao a maior "
            "tenda instanciada (12,88 m de lado) sai com os 5,20 m de cume da "
            "10x10, nao com os 5,95 que o lado dela pediria. O `altura_total_m` "
            "de cada item ja e a altura QUE VAI PARA A CENA -- so as tres de "
            "malha propria usam o perfil do proprio lado."),
        "perfil_de_altura": {
            "fonte": "os dois pontos medidos em data/pecas-avulsas.json",
            "5x5": {"pe_direito_m": _PE_5, "altura_total_m": _CUME_5},
            "10x10": {"pe_direito_m": _PE_10, "altura_total_m": _CUME_10},
            "entre_eles": "interpolacao linear; pe segurado entre 2,3 e 3,4 m",
        },
        "barriga_do_pano": (
            "pendencia 12b do RETOMAR. A lona ganha flecha de 3,5% do vao no "
            "beiral e 2% na agua -- e o que tira a leitura de placa rigida de "
            "perto, que era o defeito apontado. Custa 16 triangulos de telhado "
            "em vez de 4, uma vez so: as instancias dividem a malha."),
        "o_que_isto_NAO_muda": [
            "a posicao de nenhum estande -- x_m/y_m continuam os medidos",
            "a orientacao -- continua saindo do orientar_estandes do gerador",
            "a area cotada -- a escala existe justamente para fecha-la",
        ],
        "resumo": resumo(itens),
        "censo_por_familia_e_modo": censo,
        "itens": itens,
    }
    CONTRATO.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    return dados


def _cruz(u, v):
    return (u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def conferir_normais(largura=145.5, profundidade=33.6, vao_max=17.0):
    """Prova, em aritmetica pura, que toda agua sai com a normal para cima.

    Isto existe porque **telhado virado nao da erro**: o arquivo salva, o objeto
    aparece no viewport solido, e o defeito so surge como agua preta no render.
    Foi por isso que a cobertura deixou de depender de `recalc_face_normals` --
    cada agua e uma ilha solta, e o recalc trabalha por casca conectada.

    A conta e a mesma que o bmesh faria, com os mesmos vertices na mesma ordem,
    sem precisar de Blender: normal = (B-A) x (D-A), e o que se exige e z > 0.
    """
    problemas = []

    naves = max(1, int(math.ceil(profundidade / vao_max)))
    vao = profundidade / naves
    flecha = vao * 0.18
    meia = largura / 2.0
    for n in range(naves):
        y0 = -profundidade / 2.0 + n * vao
        y1 = y0 + vao
        ym = (y0 + y1) / 2.0
        for yb in (y0, y1):
            sobe = ym > yb
            A = (-meia, yb, 0.0)
            B = (meia, yb, 0.0)
            C = (meia, ym, flecha)
            D = (-meia, ym, flecha)
            q = (A, B, C, D) if sobe else (D, C, B, A)
            if _cruz(_sub(q[1], q[0]), _sub(q[3], q[0]))[2] <= 0:
                problemas.append(f"cobertura: agua da nave {n} com beiral em "
                                 f"y={yb:.2f} sai com a normal para BAIXO")

    for lado in FAMILIAS.values():
        pe, cume = perfil(lado)
        h, beiral = lado / 2.0, lado / 2.0 * 1.06
        sag_b, sag_a = 0.035 * lado, 0.020 * lado
        v = [(sx * beiral, sy * beiral, pe)
             for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        topo = (0.0, 0.0, cume)
        for i in range(4):
            a, b = v[i], v[(i + 1) % 4]
            meio = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, pe - sag_b)
            centro = ((a[0] + b[0]) / 3, (a[1] + b[1]) / 3,
                      (pe * 2 + cume) / 3 - sag_a)
            # A referencia e a face original de `avulsas.tenda_piramidal`, que
            # esta em producao e sabidamente certa: a barriga so pode subdividir
            # aquela face, nunca virar o pano do avesso.
            ref = _cruz(_sub(b, a), _sub(topo, a))
            for tri in ((a, meio, centro), (meio, b, centro),
                        (b, topo, centro), (topo, a, centro)):
                nrm = _cruz(_sub(tri[1], tri[0]), _sub(tri[2], tri[0]))
                if sum(x * y for x, y in zip(nrm, ref)) <= 0:
                    problemas.append(
                        f"tenda {lado:.0f}x{lado:.0f}: face da barriga na agua "
                        f"{i} aponta ao contrario da face original")
    return problemas


def conferir(itens, censo):
    """Imprime o censo e devolve a lista de problemas. Sem bpy, sem GPU."""
    r = resumo(itens)
    print("=" * 62)
    print("  TENDAS -- forma nova, posicao intocada")
    print("=" * 62)
    print(f"  estandes ............. {r['estandes']}")
    print(f"  instanciados ......... {r['instanciados']}")
    print(f"  malha propria ........ {r['malha_propria']}")
    print(f"  malhas no arquivo .... {r['malhas_no_arquivo']} "
          f"(3 familias + as proprias)")
    print(f"  altura maxima ........ {r['altura_maxima_m']} m "
          f"(a caixa antiga tinha 3,2)")
    print()
    for nome in FAMILIAS:
        d = r["por_familia"].get(nome)
        if not d:
            continue
        print(f"  {nome:>6} .... {d['quantos']:3} estandes, "
              f"escala {d['escala_min']:.3f} a {d['escala_max']:.3f}")
    print()
    for chave in sorted(censo):
        print(f"    {chave:<28} {censo[chave]}")

    problemas = []
    for i in itens:
        if i["modo"] != "proprio" and not (1.0 / TETO_DE_ESCALA <= i["escala"]
                                           <= TETO_DE_ESCALA):
            problemas.append(f"{i['codigo']}: instancia com escala "
                             f"{i['escala']:.3f}, fora do teto")
        pe, cume = i["pe_direito_m"], i["altura_total_m"]
        if not 2.3 <= pe <= 3.4:
            problemas.append(f"{i['codigo']}: pe-direito {pe} m fora da faixa")
        if cume <= pe:
            problemas.append(f"{i['codigo']}: cume {cume} nao passa do pe {pe}")

    normais = conferir_normais()
    problemas += normais
    print()
    for nome, lado in FAMILIAS.items():
        pe, cume = perfil(lado)
        graus = math.degrees(math.atan2(cume - pe, lado / 2.0))
        print(f"  {nome:>6} .... pe {pe:.2f} m · cume {cume:.2f} m · "
              f"caimento {graus:.1f} graus")
    print(f"  normais ... {'todas para cima' if not normais else 'INVERTIDAS'} "
          f"(20 faces conferidas em aritmetica, sem Blender)")

    print()
    if problemas:
        print(f"  {len(problemas)} PROBLEMA(S):")
        for p in problemas:
            print(f"    - {p}")
    else:
        print("  sem problema: toda instancia dentro do teto, "
              "todo pe-direito na faixa.")
    print("=" * 62)
    return problemas


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--conferir", action="store_true",
                    help="mede a classificacao e falha se algo sair da regra")
    ap.add_argument("--escrever", action="store_true",
                    help="regrava data/tendas.json")
    args = ap.parse_args()

    est = carregar_estandes()
    itens, censo = classificar(est)

    if args.escrever:
        escrever_contrato(itens, censo)
        print(f"gravado: {CONTRATO.relative_to(RAIZ)}  ({len(itens)} estandes)")
    if args.conferir or not args.escrever:
        if conferir(itens, censo):
            sys.exit(1)


if __name__ == "__main__":
    main()
