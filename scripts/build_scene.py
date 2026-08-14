#!/usr/bin/env python3
"""
Gera a cena 3D do Parque de Exposicoes de Dois Vizinhos para a AGROSHOW 2026,
a partir da planta extraida em data/mapa_agroshow26.json.

Constroi terreno, os 134 estandes instanciados, os pavilhoes, a arena e o
caminho de camera seguindo o percurso ditado pelo cliente. Deixa tudo em
colecoes separadas para que a camada permanente (terreno, pavilhoes) sobreviva
a troca da camada do evento (estandes, palco, sinalizacao) no ano seguinte.

Uso:
    blender --background --python scripts/build_scene.py -- --out cena.blend
    blender --background --python scripts/build_scene.py -- --relevo dem.png

Ou com o modulo bpy instalado (pip install bpy):
    python3 scripts/build_scene.py --out cena.blend

Escala: derivada da propria planta. Os 39 estandes da serie C tem 100 m² (lado
de 10 m) e ficam encostados em fileira; a mediana da distancia entre rotulos
consecutivos e 17,82 pt, o que da 0,5611 m/pt. A serie A nao serve para o mesmo
calculo porque nao esta em fileira continua -- ha corredor entre os modulos.
Confira com uma medida real em campo antes de render final.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

# --------------------------------------------------------------------------
# Constantes do projeto

ESCALA = 0.5611          # metros por ponto de PDF (derivada da serie C)
ALTURA_ESTANDE = 3.2     # m -- tenda/estande padrao de feira
ALTURA_PAVILHAO = 7.0    # m -- pavilhao de animais
SEGUNDOS_POR_PONTO = 8.0 # ritmo do percurso -- 16 pontos = ~2min08, como a referencia
FRACAO_PANORAMICA = 0.35 # parte do trecho gasta virando do ponto anterior para o proximo
ALTURA_ALVO = 4.0        # m -- altura do alvo sobre o terreno, na escala de quem anda
SAIDA_ALEM_DO_PORTAL = 60.0   # m -- ponto de fuga do plano final, fora do recinto
AVANCO_FINAL = -5.0      # m -- onde a camera para, medido do plano do portal.
                         # Negativo: ela para logo antes de cruzar, ainda sob o
                         # vao. Passar do plano joga o portal para tras da nuca
                         # e o ultimo quadro vira campo vazio -- e o cliente
                         # quer o portal como ultima imagem na retina
ELEVACAO_SOL = 14.0      # graus acima do horizonte -- fim de tarde, sombra longa
AZIMUTE_SOL = 295.0      # graus, noroeste: o sol se poe por tras do recinto
FORCA_SOL = 2.5          # W/m2 -- sol direto
FORCA_CEU = 0.35         # o ceu entra so como preenchimento; sol forte e ceu
                         # fraco e o que da contraste. Ceu forte lava a cena
FPS = 30
LARGURA_RENDER = 2760    # 2:1, 2x o nativo do painel P2,9 (1379x690)
ALTURA_RENDER = 1380

# Percurso ditado pelo cliente, em rotulos da planta. A ordem e a do audio.
#
# altura: metros acima do terreno naquele ponto. Nao e constante de proposito.
#   O quadro de conferencia anterior voava a 12 m fixos e via telhado de estande;
#   agora o voo sobe nas transicoes (leitura de conjunto) e desce nos pontos de
#   interesse (leitura de detalhe), que e a gramatica de drone da referencia.
# parada: segundos de permanencia no ponto, alem do tempo de deslocamento. Os
#   quatro diferenciais do cliente -- Fazendinha, Rodeio, Cafe Colonial e
#   Mercado do Produtor -- sao os que ganham mais tela, conforme a restricao 5.
# recuo: metros em que a camera para antes do assunto. Quanto maior o assunto,
#   maior o recuo -- a bacia da arena tem 300 m de borda a borda e nao cabe no
#   mesmo recuo de um estande.
PERCURSO = [
    ("00 Estacionamento",       "ESTACIONAMENTO",        5, 70.0, 0.0, 120.0),
    ("01 Portal de Entrada",    "Portal de Entrada",     0, 16.0, 2.5,  45.0),
    ("02 Pavilhao 1",           "PAVILHÃO 1",            0, 26.0, 1.5,  60.0),
    ("03 Alimentacao Coberta",  "Coberta",               0, 24.0, 1.5,  55.0),
    ("04 Pavilhao 2",           "PAVILHÃO 2",            0, 26.0, 1.5,  60.0),
    ("05 Pavilhao 3",           "PAVILHÃO 3",            0, 34.0, 0.0,  70.0),
    ("06 Mercado do Produtor",  "Mercado do Produtor",   0, 20.0, 3.5,  50.0),
    ("07 Cafe Colonial",        "Café Colonial",         0, 20.0, 3.5,  50.0),
    ("08 Bosque",               "Bosque",                2, 22.0, 1.5,  55.0),
    ("09 Alimentacao Aberta",   "Aberta",                0, 22.0, 1.5,  55.0),
    ("10 Recinto de Leiloes",   "RECINTO DE LEILÕES",    0, 28.0, 2.0,  65.0),
    ("11 Pavilhoes de Animais", "PAVILHÃO - GADO LEITE", 0, 45.0, 1.5, 110.0),
    ("12 Pista de Julgamentos", "PISTA DE JULGAMENTOS",  0, 30.0, 1.5,  75.0),
    ("13 Arena de Rodeio",      "ARENA DE RODEIO",       0, 55.0, 3.5, 190.0),
    ("14 Palco",                "PALCO",                 0, 30.0, 3.5, 110.0),
    # O ultimo ponto voa baixo de proposito: a saida e POR DENTRO do vao do
    # portal, na altura de quem passa. A 14 m a camera atravessava o frontao.
    ("15 Saida pelo Portal",    "Portal de Entrada",     0,  3.6, 0.0,  45.0),
]

COLECOES = ["BASE", "EVENTO", "CAMERA", "LUZ"]

# Bacia da arena, em bandas radiais a partir do centro da pista.
# (raio_interno_m, raio_externo_m, z_interno_m, z_externo_m)
# Alturas ESTIMADAS -- confirme com um quadro de drone antes do render final.
PATAMARES = [
    (0.0,    45.0,  0.0,  0.0),   # pista da arena
    (45.0,   62.0,  0.0,  3.5),   # talude para o patamar dos shows
    (62.0,   78.0,  3.5,  3.5),   # area de shows / camarotes
    (78.0,   95.0,  3.5,  7.0),   # talude para o primeiro anel
    (95.0,  125.0,  7.0,  7.0),   # anel de maquinas e veiculos
    (125.0, 150.0,  7.0, 10.0),   # talude para o plato geral
    (150.0, 9999.0, 10.0, 10.0),  # plato do restante do recinto
]


# --------------------------------------------------------------------------
# Utilitarios de cena

def limpar_cena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def criar_colecoes():
    for nome in COLECOES:
        col = bpy.data.collections.new(nome)
        bpy.context.scene.collection.children.link(col)
    return {c.name: c for c in bpy.data.collections}


def para_mundo(x_pt, y_pt, origem):
    """Converte ponto do PDF para metros no mundo.

    O PDF tem origem no canto superior esquerdo com y crescendo para baixo;
    o Blender tem y crescendo para o norte. Dai a inversao de sinal em y.
    """
    return (
        (x_pt - origem[0]) * ESCALA,
        -(y_pt - origem[1]) * ESCALA,
    )


def caixa(nome, largura, profundidade, altura, colecao):
    """Cria uma caixa com a base apoiada em z=0."""
    malha = bpy.data.meshes.new(nome)
    obj = bpy.data.objects.new(nome, malha)
    colecao.objects.link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((largura, profundidade, altura)),
                    verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector((0, 0, altura / 2)), verts=bm.verts)
    bm.to_mesh(malha)
    bm.free()
    return obj


# --------------------------------------------------------------------------
# Materiais

# (nome, cor base RGB, rugosidade, metalico, cor secundaria, escala do ruido em
#  metros, forca do relevo). Cor secundaria None desliga a variacao.
MATERIAIS = {
    "MAT_TERRENO":  ((0.10, 0.19, 0.05), 0.95, 0.0, (0.22, 0.28, 0.09), 14.0, 0.30),
    "MAT_LONA":     ((0.82, 0.81, 0.78), 0.55, 0.0, (0.68, 0.67, 0.63),  1.6, 0.06),
    "MAT_PAVILHAO": ((0.55, 0.56, 0.58), 0.42, 0.6, (0.44, 0.45, 0.48),  0.9, 0.10),
    "MAT_ARENA":    ((0.38, 0.28, 0.18), 0.90, 0.0, (0.28, 0.20, 0.13),  3.0, 0.25),
    "MAT_ASFALTO":  ((0.09, 0.09, 0.10), 0.80, 0.0, (0.14, 0.14, 0.15),  2.2, 0.15),
    "MAT_MADEIRA":  ((0.16, 0.09, 0.05), 0.65, 0.0, (0.24, 0.14, 0.07),  0.4, 0.12),
    "MAT_TELHA":    ((0.14, 0.13, 0.12), 0.50, 0.4, (0.20, 0.19, 0.17),  0.7, 0.10),
    "MAT_CLARO":    ((0.86, 0.85, 0.83), 0.40, 0.0, None,                1.0, 0.00),
    "MAT_PALCO":    ((0.06, 0.06, 0.07), 0.55, 0.0, (0.11, 0.11, 0.12),  1.2, 0.08),
}


def criar_materiais():
    """Materiais procedurais.

    Sao PBR sem arquivo de textura: ruido em escala metrica quebrando cor e
    relevo. Motivo de nao usar biblioteca aqui -- o proxy de egresso bloqueia
    Poly Haven e ambientCG (ver ESTADO.md), e cor chapada le como maquete antes
    de qualquer outra falha. Na lapidacao local, troque por PBR com textura CC0
    ligando os mapas nos mesmos slots.
    """
    feitos = {}
    for nome, (cor, rug, met, cor2, escala, relevo) in MATERIAIS.items():
        mat = bpy.data.materials.new(nome)
        mat.use_nodes = True
        nos = mat.node_tree.nodes
        elos = mat.node_tree.links
        bsdf = nos.get("Principled BSDF")
        if bsdf is None:
            feitos[nome] = mat
            continue
        bsdf.inputs["Base Color"].default_value = (*cor, 1.0)
        bsdf.inputs["Roughness"].default_value = rug
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = met

        if cor2 is None:
            feitos[nome] = mat
            continue

        # Coordenada de objeto/gerada em escala de mundo: o ruido acompanha o
        # tamanho real da peca, entao a grama de 800 m e a lona de 10 m tem
        # granulacao coerente entre si.
        coord = nos.new("ShaderNodeTexCoord")
        mapa = nos.new("ShaderNodeMapping")
        ruido = nos.new("ShaderNodeTexNoise")
        rampa = nos.new("ShaderNodeValToRGB")
        bump = nos.new("ShaderNodeBump")

        mapa.inputs["Scale"].default_value = (1.0 / escala,) * 3
        ruido.inputs["Scale"].default_value = 6.0
        ruido.inputs["Detail"].default_value = 8.0
        ruido.inputs["Roughness"].default_value = 0.6
        rampa.color_ramp.elements[0].color = (*cor, 1.0)
        rampa.color_ramp.elements[1].color = (*cor2, 1.0)
        rampa.color_ramp.elements[0].position = 0.35
        rampa.color_ramp.elements[1].position = 0.68
        bump.inputs["Strength"].default_value = relevo

        elos.new(coord.outputs["Object"], mapa.inputs["Vector"])
        elos.new(mapa.outputs["Vector"], ruido.inputs["Vector"])
        elos.new(ruido.outputs["Fac"], rampa.inputs["Fac"])
        elos.new(rampa.outputs["Color"], bsdf.inputs["Base Color"])
        elos.new(ruido.outputs["Fac"], bump.inputs["Height"])
        elos.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        feitos[nome] = mat
    return feitos


def aplicar(obj, mat):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.clear()
        obj.data.materials.append(mat)


# --------------------------------------------------------------------------
# Construcao

def elevacao(x, y, centro_arena):
    """Altura do terreno em metros, para um ponto do mundo.

    A bacia da arena e modelada por bandas radiais, nao por DEM. Motivo: os
    DEMs globais disponiveis (SRTM, Copernicus, NASADEM, AW3D30) sao todos de
    ~30 m de resolucao. Num recinto de 800 m isso da cerca de 27 amostras de
    ponta a ponta -- descreve o vale, mas nao enxerga patamares de poucos
    metros. E os patamares sao justamente o que o cliente descreve no audio.

    As bandas saem dos proprios dados da planta: agrupando os 93 estandes da
    serie C pela distancia ao centro da arena, aparecem aneis claros em 72-90 m
    e 108-113 m. Cruzando com o audio -- "primeiro anel de cima" (maquinas),
    "segundo patamar descendo" (shows), "embaixo, em frente ao palco" (arena)
    -- sao tres niveis. As 15 anotacoes de "Talude" na planta caem nas faixas
    de transicao, o que confirma o desenho.

    ALTURAS SAO ESTIMADAS. Um quadro de drone ou uma foto lateral da arena
    confirma em minutos. Ajuste PATAMARES antes do render final.
    """
    r = math.hypot(x - centro_arena[0], y - centro_arena[1])
    for r_int, r_ext, z_int, z_ext in PATAMARES:
        if r < r_ext:
            if r <= r_int:
                return z_int
            # Talude: transicao suave entre um patamar e o seguinte.
            t = (r - r_int) / (r_ext - r_int)
            t = t * t * (3.0 - 2.0 * t)   # smoothstep
            return z_int + (z_ext - z_int) * t
    return PATAMARES[-1][3]


def construir_arena(centro_arena, col, mats):
    """Piso de terra da pista, no fundo da bacia."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=45.0, depth=0.4,
                                        location=(centro_arena[0],
                                                  centro_arena[1], 0.1))
    obj = bpy.context.active_object
    obj.name = "PistaArena"
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    aplicar(obj, mats["MAT_ARENA"])
    return obj


def construir_terreno(dados, col, centro_arena, relevo=None):
    """Terreno da prancha inteira, esculpido na bacia da arena.

    Com --relevo, um heightmap em escala de cinza entra por deslocamento por
    cima da bacia -- util para o entorno (vale, encostas distantes), onde os
    30 m de resolucao bastam. Para o recinto, quem manda e a bacia.
    """
    larg = dados["prancha"]["largura_pt"] * ESCALA * 1.2
    prof = dados["prancha"]["altura_pt"] * ESCALA * 1.2
    div = 400

    bpy.ops.mesh.primitive_grid_add(x_subdivisions=div, y_subdivisions=div,
                                    size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Terreno"
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)

    # Aplica escala na malha e esculpe a bacia vertice a vertice.
    for v in obj.data.vertices:
        v.co.x *= larg
        v.co.y *= prof
        v.co.z = elevacao(v.co.x, v.co.y, centro_arena)

    if relevo and Path(relevo).exists():
        img = bpy.data.images.load(str(relevo))
        tex = bpy.data.textures.new("RelevoTex", type="IMAGE")
        tex.image = img
        mod = obj.modifiers.new("RelevoEntorno", type="DISPLACE")
        mod.texture = tex
        mod.texture_coords = "UV"
        mod.strength = 20.0
        mod.mid_level = 0.5
        print(f"  relevo do entorno: {relevo}")
    else:
        print("  sem heightmap -- so a bacia derivada da planta")
    return obj


def centro_da_arena(dados):
    z = [x for x in dados["zonas"] if x["rotulo"] == "ARENA DE RODEIO"][0]
    return para_mundo(z["x"], z["y"], dados["_origem"])


def fcurves_da_acao(obj):
    """Devolve as fcurves da acao do objeto, em qualquer versao do Blender.

    Ate a 4.3 a acao expunha .fcurves direto. Da 4.4 em diante elas vivem em
    layers > strips > channelbags, e o atributo antigo sumiu na 5.0.
    """
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    acao = ad.action
    if hasattr(acao, "fcurves"):
        return list(acao.fcurves)
    curvas = []
    for camada in getattr(acao, "layers", []):
        for faixa in getattr(camada, "strips", []):
            for saco in getattr(faixa, "channelbags", []):
                curvas.extend(saco.fcurves)
    return curvas


def orientar_estandes(postos):
    """Alinha cada estande ao eixo da sua fileira.

    Estandes vizinhos numa fileira compartilham o eixo da fileira, entao a
    direcao ate o vizinho mais proximo serve de referencia. Isso resolve tanto
    as grades ortogonais quanto os arcos concentricos da arena, sem precisar
    tratar os dois casos separadamente.
    """
    for i, (obj, x, y) in enumerate(postos):
        melhor, dist_melhor = None, float("inf")
        for j, (_, x2, y2) in enumerate(postos):
            if i == j:
                continue
            d = (x - x2) ** 2 + (y - y2) ** 2
            if d < dist_melhor:
                dist_melhor, melhor = d, (x2, y2)
        if melhor is None or dist_melhor > 40.0 ** 2:
            continue
        obj.rotation_euler = (0.0, 0.0,
                              math.atan2(melhor[1] - y, melhor[0] - x))


def construir_estandes(dados, col, centro_arena):
    """Instancia os estandes a partir de dois modulos base.

    39 estandes de 100 m² e 35 de 25 m² sao instancias, nao modelagens
    separadas. Os demais recebem caixa propria dimensionada pela area.
    """
    modulos = {}
    for area, lado in ((100.0, 10.0), (25.0, 5.0)):
        base = caixa(f"MODULO_{int(area)}m2", lado, lado, ALTURA_ESTANDE, col)
        base.hide_render = base.hide_viewport = True
        modulos[area] = base

    origem = dados["_origem"]
    contagem = {"instanciado": 0, "proprio": 0}
    postos = []

    for st in dados["estandes"]:
        area = st.get("area_m2")
        if area is None:
            continue
        x, y = para_mundo(st["x"], st["y"], origem)

        if area in modulos:
            obj = bpy.data.objects.new(st["codigo"], modulos[area].data)
            col.objects.link(obj)
            contagem["instanciado"] += 1
        else:
            lado = math.sqrt(area)
            obj = caixa(st["codigo"], lado, lado, ALTURA_ESTANDE, col)
            contagem["proprio"] += 1

        obj.location = (x, y, elevacao(x, y, centro_arena))
        obj["area_m2"] = area
        obj["serie"] = st["serie"]
        postos.append((obj, x, y))

    orientar_estandes(postos)
    return contagem


def construir_pavilhoes(dados, col, centro_arena):
    """Pavilhoes de animais: 5 de 720 m² e 1 de 560 m².

    Proporcao 60 x 12 m assumida para os de 720 -- confira em campo. A ordem
    fisica norte->sul e gado leite, nucleo cara branca, gado corte, ovinos e
    caprinos, pequenos animais, equinos.
    """
    origem = dados["_origem"]
    feitos = 0
    for z in dados["zonas"]:
        if z["categoria"] != "pavilhoes" or "PAVILHÃO -" not in z["rotulo"]:
            continue
        area = 560.0 if "EQUÍNOS" in z["rotulo"] else 720.0
        profundidade = 12.0
        largura = area / profundidade
        x, y = para_mundo(z["x"], z["y"], origem)
        obj = caixa(z["rotulo"], largura, profundidade, ALTURA_PAVILHAO, col)
        obj.location = (x, y, elevacao(x, y, centro_arena))
        obj["area_m2"] = area
        feitos += 1
    return feitos


def bloco(nome, larg, prof, alt, col, mat, x, y, z, yaw=0.0):
    """Caixa posicionada e girada no mundo, base em z."""
    obj = caixa(nome, larg, prof, alt, col)
    obj.location = (x, y, z)
    obj.rotation_euler = (0.0, 0.0, yaw)
    aplicar(obj, mat)
    return obj


def prisma_duas_aguas(nome, larg, prof, alt, col):
    """Frontao em duas aguas, base em z=0. E a silhueta do celeiro."""
    malha = bpy.data.meshes.new(nome)
    obj = bpy.data.objects.new(nome, malha)
    col.objects.link(obj)
    hx, hy = larg / 2.0, prof / 2.0
    verts = [(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0),
             (0, -hy, alt), (0, hy, alt)]
    faces = [(0, 1, 2, 3), (0, 4, 5, 3), (1, 2, 5, 4), (0, 1, 4), (3, 2, 5)]
    malha.from_pydata(verts, [], faces)
    malha.update()
    return obj


def letreiro(nome, texto, tamanho, col, mat, x, y, z, yaw):
    """Texto em relevo, de pe no plano da fachada."""
    curva = bpy.data.curves.new(nome, type="FONT")
    curva.body = texto
    curva.size = tamanho
    curva.align_x = "CENTER"
    curva.align_y = "CENTER"
    curva.extrude = 0.06
    obj = bpy.data.objects.new(nome, curva)
    col.objects.link(obj)
    obj.location = (x, y, z)
    # O texto nasce olhando para -Y local; meia volta em Z poe a leitura na
    # direcao de quem chega, senao a fachada mostra o letreiro espelhado.
    obj.rotation_euler = (math.radians(90.0), 0.0, yaw + math.pi)
    aplicar(obj, mat)
    return obj


def construir_portal(dados, col, centro_arena, mats):
    """Portal de entrada, conceito celeiro, na leitura mais economica.

    A fachada e a da foto em reference/PORTAL-referencia.md: frontao em duas
    aguas com trelica em V invertido, tabuas verticais escuras, tres vaos de
    passagem, letreiro em relevo e alas laterais mais baixas com telha escura.
    O cliente disse que a versao construida sera mais barata -- entao aqui e
    volume e proporcao, sem ornamento que a foto nao mostre.

    E o primeiro e o ultimo plano do video, por isso ele existe como geometria
    desde a base, e nao como caixa generica.
    """
    z = achar_zona(dados, "Portal de Entrada", 0)
    if z is None:
        return None
    x, y = para_mundo(z["x"], z["y"], dados["_origem"])
    solo = elevacao(x, y, centro_arena)

    # A fachada olha para quem chega. O interior do recinto esta na direcao do
    # centro da arena, entao a frente e o sentido oposto.
    para_dentro = math.atan2(centro_arena[1] - y, centro_arena[0] - x)
    yaw = para_dentro + math.pi / 2.0   # eixo longo transversal a passagem
    ex, ey = math.cos(yaw), math.sin(yaw)          # ao longo da fachada
    # Para fora do recinto: e para ca que olham letreiro, janelas e luminarias,
    # porque quem chega vem do estacionamento, nao de dentro.
    fx, fy = -math.cos(para_dentro), -math.sin(para_dentro)

    def posto(desloc_lateral, desloc_frente=0.0):
        return (x + ex * desloc_lateral + fx * desloc_frente,
                y + ey * desloc_lateral + fy * desloc_frente)

    madeira, telha, claro = (mats["MAT_MADEIRA"], mats["MAT_TELHA"],
                             mats["MAT_CLARO"])

    # Quatro pilares abrindo os tres vaos de passagem.
    for d in (-9.0, -3.0, 3.0, 9.0):
        px, py = posto(d)
        bloco("PortalPilar", 1.2, 3.0, 5.0, col, madeira, px, py, solo, yaw)

    # Corpo central: a viga sobre os vaos e a parede de tabuas com o letreiro.
    bloco("PortalViga", 20.0, 3.4, 1.0, col, madeira, x, y, solo + 5.0, yaw)
    bloco("PortalParede", 20.0, 3.0, 2.6, col, madeira, x, y, solo + 6.0, yaw)

    frontao = prisma_duas_aguas("PortalFrontao", 20.0, 3.0, 3.2, col)
    frontao.location = (x, y, solo + 8.6)
    frontao.rotation_euler = (0.0, 0.0, yaw)
    aplicar(frontao, madeira)

    # Trelica em V invertido: as duas barras acompanham as aguas do frontao,
    # entao angulo e comprimento saem da propria geometria dele.
    meia_base, subida = 9.0, 2.9
    inclinacao = math.atan2(subida, meia_base)
    barra = math.hypot(meia_base, subida)
    for lado in (-1.0, 1.0):
        tx, ty = posto(lado * meia_base / 2.0, 0.1)
        t = bloco("PortalTrelica", barra, 0.3, 0.3, col, claro,
                  tx, ty, solo + 8.6 + subida / 2.0, yaw)
        # Girar em torno de +Y leva o topo da barra para -Z, entao o sinal do
        # angulo acompanha o lado: cada barra sobe na direcao do cume.
        t.rotation_euler = (0.0, lado * inclinacao, yaw)

    letreiro("PortalLetreiro1", "PARQUE DE EXPOSIÇÕES", 1.15, col, claro,
             *posto(0.0, 1.6), solo + 7.5, yaw)
    letreiro("PortalLetreiro2", "★★★ DE DOIS VIZINHOS - PR ★★★", 0.62, col,
             claro, *posto(0.0, 1.6), solo + 6.4, yaw)

    # Alas laterais, mais baixas, com beiral curto de telha ondulada escura.
    for lado in (-1.0, 1.0):
        ax, ay = posto(lado * 17.0)
        bloco("PortalAla", 14.0, 6.0, 4.0, col, madeira, ax, ay, solo, yaw)
        bloco("PortalBeiral", 15.0, 7.0, 0.35, col, telha,
              ax, ay, solo + 4.0, yaw)
        # Janelas de guilhotina brancas, duas por ala.
        for d in (-3.5, 3.5):
            jx, jy = posto(lado * 17.0 + d, 3.05)
            bloco("PortalJanela", 1.4, 0.15, 1.8, col, claro,
                  jx, jy, solo + 1.5, yaw)

    # Luminarias de parede em ferro preto, seis na fachada.
    for d in (-15.0, -7.0, -2.0, 2.0, 7.0, 15.0):
        lx, ly = posto(d, 1.7)
        bloco("PortalLuminaria", 0.4, 0.4, 0.5, col, mats["MAT_PALCO"],
              lx, ly, solo + 4.2, yaw)

    return (x, y, solo)


def construir_palco_e_camarotes(dados, col, centro_arena, mats):
    """Palco de frente e camarotes dos dois lados. SEM ARQUIBANCADA.

    Restricao 1 do cliente, dita no audio 2 aos 01:16: "nao da pra colocar
    arquibancada... e so a pista da arena e dos lados camarote. E de frente, o
    palco de shows." Se aparecer degrau de arquibancada em volta da pista, a
    entrega e rejeitada -- por isso a estrutura entra aqui, na geometria, e nao
    fica a cargo de quem for lapidar depois.
    """
    origem = dados["_origem"]
    feitos = {"palco": 0, "camarotes": 0}

    def de_costas_para_a_arena(px, py):
        """Yaw com o eixo longo tangente a pista, frente voltada ao centro."""
        return math.atan2(centro_arena[1] - py, centro_arena[0] - px) + math.pi / 2.0

    def na_borda(px, py, raio):
        """Empurra o ponto para um raio fixo, mantendo o azimute.

        O rotulo da planta e ancora de texto, nao implantacao: 'PALCO' cai a
        16 m do centro, dentro da pista. Palco e camarotes ficam na borda --
        a pista precisa estar livre para o rodeio. O azimute do rotulo continua
        mandando de que lado cada um esta.
        """
        dx, dy = px - centro_arena[0], py - centro_arena[1]
        d = math.hypot(dx, dy) or 1.0
        return centro_arena[0] + dx / d * raio, centro_arena[1] + dy / d * raio

    z = achar_zona(dados, "PALCO", 0)
    if z is not None:
        px, py = na_borda(*para_mundo(z["x"], z["y"], origem), 52.0)
        solo = elevacao(px, py, centro_arena)
        yaw = de_costas_para_a_arena(px, py)
        fx = math.cos(yaw - math.pi / 2.0)
        fy = math.sin(yaw - math.pi / 2.0)
        bloco("PalcoPiso", 26.0, 14.0, 1.8, col, mats["MAT_PALCO"],
              px, py, solo, yaw)
        bloco("PalcoFundo", 26.0, 1.0, 11.0, col, mats["MAT_PALCO"],
              px - fx * 6.5, py - fy * 6.5, solo, yaw)
        bloco("PalcoCobertura", 28.0, 16.0, 0.8, col, mats["MAT_PALCO"],
              px, py, solo + 12.0, yaw)
        for lx in (-13.0, 13.0):
            for ly in (-7.0, 7.0):
                cx = px + math.cos(yaw) * lx + fx * ly
                cy = py + math.sin(yaw) * lx + fy * ly
                bloco("PalcoTorre", 0.9, 0.9, 12.0, col, mats["MAT_PALCO"],
                      cx, cy, solo, yaw)
        feitos["palco"] = 1

    for rotulo in ("CAMAROTES - LADO A", "CAMAROTES - LADO B"):
        z = achar_zona(dados, rotulo, 0)
        if z is None:
            continue
        cx, cy = na_borda(*para_mundo(z["x"], z["y"], origem), 58.0)
        solo = elevacao(cx, cy, centro_arena)
        yaw = de_costas_para_a_arena(cx, cy)
        ex, ey = math.cos(yaw), math.sin(yaw)
        nome = rotulo.replace(" ", "_")
        # Fileira de modulos fechados, dois pavimentos, varanda voltada a pista.
        # Nao e degrau em arquibancada: cada modulo e um camarote.
        for i in range(6):
            d = (i - 2.5) * 9.0
            mx, my = cx + ex * d, cy + ey * d
            bloco(f"{nome}_modulo", 8.4, 7.0, 3.2, col, mats["MAT_CLARO"],
                  mx, my, solo, yaw)
            bloco(f"{nome}_superior", 8.4, 7.0, 3.0, col, mats["MAT_CLARO"],
                  mx, my, solo + 3.4, yaw)
            bloco(f"{nome}_cobertura", 9.2, 8.4, 0.4, col, mats["MAT_TELHA"],
                  mx, my, solo + 6.4, yaw)
        feitos["camarotes"] += 1

    return feitos


def achar_zona(dados, rotulo, ocorrencia=0):
    achados = [z for z in dados["zonas"] if z["rotulo"] == rotulo]
    if not achados:
        return None
    achados.sort(key=lambda z: (z["y"], z["x"]))
    return achados[min(ocorrencia, len(achados) - 1)]


def curva_por_pontos(nome, coords, col):
    """Bezier suave passando por uma lista de (x, y, z)."""
    curva = bpy.data.curves.new(nome, type="CURVE")
    curva.dimensions = "3D"
    spline = curva.splines.new("BEZIER")
    spline.bezier_points.add(len(coords) - 1)
    for bp, co in zip(spline.bezier_points, coords):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(nome, curva)
    col.objects.link(obj)
    return obj


def fracoes_do_percurso(coords):
    """Fracao do comprimento acumulado em cada ponto, medida em corda.

    O offset_factor da constraint anda por comprimento de arco, e a corda entre
    os pontos de controle e uma aproximacao boa o bastante dele: o que importa
    aqui e nao acelerar num trecho longo e arrastar num curto.
    """
    dist = [0.0]
    for a, b in zip(coords, coords[1:]):
        dist.append(dist[-1] + math.dist(a, b))
    total = dist[-1] or 1.0
    return [d / total for d in dist]


def construir_percurso(dados, col, centro_arena):
    """Curva do voo, curva do olhar e a camera entre as duas.

    Duas curvas em vez de uma: a camera anda pela de cima, com altura propria em
    cada ponto, e olha para um alvo que corre pela de baixo, na altura de quem
    caminha. Assim a inclinacao deixa de ser um numero fixo -- ela cai sozinha
    quando o voo sobe e levanta quando o voo desce, que era o defeito do quadro
    de conferencia anterior (12 m fixos e 18 graus, enquadrando telhado de
    estande).
    """
    origem = dados["_origem"]
    pontos, ausentes = [], []

    for nome, rotulo, ocorrencia, altura, parada, recuo in PERCURSO:
        z = achar_zona(dados, rotulo, ocorrencia)
        if z is None:
            ausentes.append((nome, rotulo))
            continue
        x, y = para_mundo(z["x"], z["y"], origem)
        pontos.append((nome, x, y, altura, parada, recuo))

    # A curva do voo nao passa por cima dos assuntos: cada ponto de controle
    # recua alguns metros no sentido de quem chega. Passar por cima entrega o
    # assunto em nadir bem no quadro em que ele deveria estar mais legivel; com
    # o recuo, a camera para curta e enquadra a fachada em tres quartos.
    voo = []
    for i, (_, x, y, h, _, recuo) in enumerate(pontos):
        ax, ay = pontos[i - 1][1:3] if i else pontos[min(1, len(pontos) - 1)][1:3]
        dx, dy = x - ax, y - ay
        if i == 0:
            dx, dy = -dx, -dy      # no primeiro ponto, recua para tras da chegada
        d = math.hypot(dx, dy) or 1.0
        rx, ry = x - dx / d * recuo, y - dy / d * recuo
        voo.append((rx, ry, elevacao(rx, ry, centro_arena) + h))

    olhar = [(x, y, elevacao(x, y, centro_arena) + ALTURA_ALVO)
             for _, x, y, _, _, _ in pontos]

    # Um ponto a mais nas duas curvas, alem do portal e para fora do recinto. E
    # o que faz o video terminar saindo pelo portao -- restricao 6 do cliente --
    # e evita que camera e alvo se encontrem no ultimo quadro, o que giraria o
    # enquadramento sobre si mesmo.
    if len(olhar) >= 2:
        ax, ay, az = olhar[-1]
        bx, by, _ = olhar[-2]
        d = math.dist((ax, ay), (bx, by)) or 1.0
        ux, uy = (ax - bx) / d, (ay - by) / d
        fuga = (ax + ux * SAIDA_ALEM_DO_PORTAL,
                ay + uy * SAIDA_ALEM_DO_PORTAL)
        olhar.append((*fuga, az))
        voo.append((ax + ux * AVANCO_FINAL, ay + uy * AVANCO_FINAL,
                    voo[-1][2]))

    curva_voo = curva_por_pontos("PercursoCamera", voo, col)
    curva_olhar = curva_por_pontos("PercursoAlvo", olhar, col)

    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 35.0
    cam = bpy.data.objects.new("Camera", cam_data)
    col.objects.link(cam)

    alvo = bpy.data.objects.new("AlvoCamera", None)
    alvo.empty_display_type = "SPHERE"
    alvo.empty_display_size = 6.0
    col.objects.link(alvo)

    seg_cam = cam.constraints.new("FOLLOW_PATH")
    seg_cam.target = curva_voo
    seg_cam.use_fixed_location = True
    seg_alvo = alvo.constraints.new("FOLLOW_PATH")
    seg_alvo.target = curva_olhar
    seg_alvo.use_fixed_location = True

    mirar = cam.constraints.new("TRACK_TO")
    mirar.target = alvo
    mirar.track_axis = "TRACK_NEGATIVE_Z"
    mirar.up_axis = "UP_Y"

    # Tempo e olhar.
    #
    # A camera nao para em cima do ponto -- parar sobre o assunto so rende
    # quadro em nadir. O que segura o assunto na tela e o alvo: ele fica travado
    # no ponto que esta chegando durante toda a aproximacao, e so vira para o
    # proximo depois que a camera passou. A permanencia de cada ponto alonga o
    # trecho de aproximacao dele, entao os quatro diferenciais ganham tela sem
    # que o voo trave (restricao 5 do cliente).
    frac_voo = fracoes_do_percurso(voo)
    frac_olhar = fracoes_do_percurso(olhar)

    cena = bpy.context.scene
    chaves_cam, chaves_alvo, chegada = [], [], []
    t = 1.0
    chaves_cam.append((1, frac_voo[0]))
    chaves_alvo.append((1, frac_olhar[1]))
    chegada.append(1)

    for i in range(1, len(pontos)):
        duracao = (SEGUNDOS_POR_PONTO + pontos[i][4]) * FPS
        t += duracao
        quadro = round(t)
        chegada.append(quadro)
        chaves_cam.append((quadro, frac_voo[i]))
        # Segura o assunto ate a chegada...
        chaves_alvo.append((quadro, frac_olhar[i]))
        # ...e vira para o proximo no comeco do trecho seguinte.
        if i + 1 < len(frac_olhar):
            proxima = (SEGUNDOS_POR_PONTO + (pontos[i + 1][4]
                                             if i + 1 < len(pontos) else 0.0)) * FPS
            chaves_alvo.append((round(t + proxima * FRACAO_PANORAMICA),
                                frac_olhar[i + 1]))

    # Trecho final: a camera atravessa o portal enquanto o alvo ja esta fora.
    # Meio trecho basta -- e uma passagem, nao mais um ponto do roteiro.
    fim = round(t + SEGUNDOS_POR_PONTO * FPS * 0.5)
    chaves_cam.append((fim, 1.0))
    chaves_alvo.append((fim, 1.0))

    cena.frame_start = 1
    cena.frame_end = max(chaves_cam[-1][0], chaves_alvo[-1][0])

    for quadro, f in chaves_cam:
        seg_cam.offset_factor = f
        seg_cam.keyframe_insert("offset_factor", frame=quadro)
    for quadro, f in chaves_alvo:
        seg_alvo.offset_factor = f
        seg_alvo.keyframe_insert("offset_factor", frame=quadro)

    for obj in (cam, alvo):
        for fc in fcurves_da_acao(obj):
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"

    cena.camera = cam

    # Marcadores nomeados, para localizar cada ponto do roteiro na viewport, e
    # marcadores de timeline, para achar o quadro de cada ponto no render.
    for (nome, x, y, altura, _, _), co, quadro in zip(pontos, voo, chegada):
        m = bpy.data.objects.new(f"PT_{nome}", None)
        m.empty_display_type = "PLAIN_AXES"
        m.empty_display_size = 8.0
        m.location = co
        col.objects.link(m)
        cena.timeline_markers.new(nome, frame=quadro)

    return pontos, ausentes, chegada


def configurar_render(cena, perfil="previa", exigir_gpu=True):
    cena.render.resolution_x = LARGURA_RENDER
    cena.render.resolution_y = ALTURA_RENDER
    cena.render.resolution_percentage = 100
    cena.render.fps = 30
    cena.render.image_settings.file_format = "PNG"
    cena.render.film_transparent = False

    if perfil == "final":
        configurar_cycles_final(cena, exigir_gpu)
        return

    # Previa: motor rapido para navegar e conferir enquadramento.
    try:
        cena.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        cena.render.engine = "CYCLES"


MENSAGEM_SEM_GPU = """
ERRO: nenhuma GPU encontrada para o render final.

O cliente pediu Cycles com GPU NVIDIA -- render em CPU nao e uma alternativa
silenciosa aceitavel aqui, sao 4.591 quadros e a fila nao fecha em CPU. Antes
de tentar de novo:

  1. Confira o driver NVIDIA (Painel da NVIDIA ou `nvidia-smi` no terminal).
  2. No Blender: Edit > Preferences > System > Cycles Render Devices.
     Escolha OptiX (ou CUDA) e marque a caixa da placa. Isso fica salvo nas
     preferencias do Blender, nao no arquivo da cena -- confirme antes de
     cada maquina nova.
  3. Rode de novo.

Se quiser mesmo assim renderizar em CPU (por exemplo, so para conferir a cena
neste ambiente sem GPU), passe --permitir-cpu explicitamente.
""".strip()


def escolher_dispositivo(exigir_gpu=True):
    """Liga a GPU quando houver. Quando exigir_gpu, PARA em vez de cair para
    CPU -- decisao do cliente foi Cycles com GPU NVIDIA, e um render de dias
    rodando na CPU por engano e pior do que o script recusar a sair.

    A ordem de preferencia e OptiX, depois CUDA, depois os outros backends.
    get_devices_for_type() e a API atual para listar os dispositivos de um
    backend; cai para get_devices() + prefs.devices nas versoes que ainda
    usam a API antiga.
    """
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except KeyError:
        if exigir_gpu:
            raise RuntimeError("addon Cycles indisponivel neste Blender.\n" +
                               MENSAGEM_SEM_GPU)
        return "CPU", "addon cycles indisponivel"

    for tipo in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            prefs.compute_device_type = tipo
        except TypeError:
            continue

        obter_por_tipo = getattr(prefs, "get_devices_for_type", None)
        if obter_por_tipo:
            try:
                dispositivos = list(obter_por_tipo(tipo))
            except TypeError:
                dispositivos = list(obter_por_tipo())
        else:
            try:
                prefs.get_devices()
            except Exception:
                pass
            dispositivos = list(getattr(prefs, "devices", []))

        gpus = [d for d in dispositivos if d.type == tipo]
        if gpus:
            # So a GPU liga -- deixar a CPU tambem marcada nao acelera Cycles
            # o bastante para compensar a confusao de saber o que rodou onde.
            for d in dispositivos:
                d.use = d in gpus
            return "GPU", f"{tipo}: " + ", ".join(d.name for d in gpus)

    if exigir_gpu:
        raise RuntimeError(MENSAGEM_SEM_GPU)
    return "CPU", "nenhuma GPU visivel neste ambiente"


def configurar_cycles_final(cena, exigir_gpu=True):
    """Cycles para a entrega, com o maximo de realismo que a cena comporta.

    Decisao do cliente: o render final e em Cycles, na maquina dele, com GPU
    NVIDIA. Aqui ficam os numeros; a fila roda la.

    exigir_gpu=True (padrao) faz o script PARAR se nao achar GPU, em vez de
    seguir em CPU calado -- e o comportamento pedido pelo cliente. Only passe
    --permitir-cpu quando for so conferir a cena num ambiente sem GPU.

    Os passes nao sao luxo. Sem cryptomatte nao ha mascara para compor placa,
    totem e letreiro -- e o texto e o que vende o video, entao ele e composto,
    nunca gerado. Sem vetor de movimento e profundidade, todo ajuste de motion
    blur ou de atmosfera vira re-render em vez de composicao.
    """
    cena.render.engine = "CYCLES"
    modo, detalhe = escolher_dispositivo(exigir_gpu)
    cena.cycles.device = modo

    # Amostragem adaptativa: gasta amostra onde o ruido esta, nao no ceu limpo.
    cena.cycles.use_adaptive_sampling = True
    cena.cycles.adaptive_threshold = 0.01
    cena.cycles.samples = 512
    cena.cycles.adaptive_min_samples = 64
    cena.cycles.use_denoising = True
    for denoiser in ("OPTIX", "OPENIMAGEDENOISE"):
        try:
            cena.cycles.denoiser = denoiser
            break
        except TypeError:
            continue

    cena.cycles.max_bounces = 12
    cena.cycles.diffuse_bounces = 4
    cena.cycles.glossy_bounces = 4
    cena.cycles.transmission_bounces = 8
    cena.cycles.transparent_max_bounces = 8
    cena.cycles.caustics_reflective = False
    cena.cycles.caustics_refractive = False
    # Dados persistentes entre quadros: a cena e grande e o setup se repete.
    # A propriedade mudou de lugar entre versoes.
    for alvo in (cena.render, cena.cycles):
        if hasattr(alvo, "use_persistent_data"):
            alvo.use_persistent_data = True
            break

    # Movimento perfeito e falso: obturador de 180 graus e o padrao de cinema.
    cena.render.use_motion_blur = True
    cena.render.motion_blur_shutter = 0.5

    # EXR com os passes. Ate a 4.x o formato multicamada era um item proprio do
    # enum; na 5.0 ele sumiu da lista porque as camadas passaram a sair juntas
    # no OPEN_EXR. Tentar os dois deixa o arquivo abrir nas duas versoes.
    imagem = cena.render.image_settings
    for formato in ("OPEN_EXR_MULTILAYER", "OPEN_EXR"):
        try:
            imagem.file_format = formato
            break
        except TypeError:
            continue
    imagem.color_depth = "16"
    imagem.exr_codec = "DWAA"

    camada = cena.view_layers[0]
    camada.use_pass_combined = True
    camada.use_pass_z = True
    camada.use_pass_vector = True
    camada.use_pass_normal = True
    camada.use_pass_cryptomatte_object = True
    camada.use_pass_cryptomatte_material = True

    print(f"  render final: Cycles em {modo} ({detalhe})")
    print("  512 amostras adaptativas, denoise, motion blur 180 graus")
    print("  saida EXR multicamada com z, vetor, normal e cryptomatte")
    if modo == "CPU":
        # So chega aqui com --permitir-cpu -- sem essa flag, a falta de GPU
        # ja teria parado o script antes deste ponto.
        print("  AVISO: --permitir-cpu estava ligado, entao seguiu em CPU. "
              "Em CPU esta fila nao fecha -- use isto so para conferir a "
              "cena, nunca para o render final.")


def construir_ceu(cena, hdri=None):
    """Ceu de fim de tarde: Nishita quando nao ha HDRI, HDRI quando ha.

    O ceu chapado anterior nao iluminava nada -- sem gradiente de horizonte, o
    render inteiro dependia do sol e as sombras fechavam em preto. O Sky Texture
    em modo Nishita e ceu fisico: da o espalhamento atmosferico e o horizonte
    quente da hora dourada sem baixar arquivo, o que importa aqui porque o proxy
    bloqueia Poly Haven (ver ESTADO.md).

    A elevacao e o azimute do ceu sao os mesmos do sol em construir_luz -- ceu e
    sombra em desacordo e o primeiro sinal de maquete.
    """
    mundo = bpy.data.worlds.new("Mundo")
    cena.world = mundo
    mundo.use_nodes = True
    nos = mundo.node_tree.nodes
    elos = mundo.node_tree.links
    fundo = nos.get("Background")
    if fundo is None:
        return mundo

    if hdri and Path(hdri).exists():
        ambiente = nos.new("ShaderNodeTexEnvironment")
        ambiente.image = bpy.data.images.load(str(hdri))
        elos.new(ambiente.outputs["Color"], fundo.inputs["Color"])
        fundo.inputs["Strength"].default_value = 1.0
        print(f"  ceu: HDRI {hdri}")
        return mundo

    ceu = nos.new("ShaderNodeTexSky")
    # O ceu fisico do Nishita virou MULTIPLE_SCATTERING na 5.0; o nome antigo
    # ainda responde nas versoes anteriores.
    for tipo in ("MULTIPLE_SCATTERING", "NISHITA"):
        try:
            ceu.sky_type = tipo
            break
        except TypeError:
            continue
    ceu.sun_elevation = math.radians(ELEVACAO_SOL)
    ceu.sun_rotation = math.radians(AZIMUTE_SOL)
    ceu.sun_disc = False         # o sol direto quem faz e a luz SUN, nao o ceu
    ceu.altitude = 500.0         # Dois Vizinhos esta a ~510 m
    ceu.air_density = 1.1
    # Aerossol: poeira de recinto no fim de tarde. A propriedade mudou de nome
    # entre versoes (dust_density -> aerosol_density).
    for atributo in ("aerosol_density", "dust_density"):
        if hasattr(ceu, atributo):
            setattr(ceu, atributo, 2.2)
            break
    elos.new(ceu.outputs["Color"], fundo.inputs["Color"])
    fundo.inputs["Strength"].default_value = FORCA_CEU
    print("  ceu: Nishita procedural (sem HDRI)")
    return mundo


def construir_luz(col):
    """Sol em golden hour, coerente com o LOOK LOCK das imagens de apoio."""
    dados_sol = bpy.data.lights.new("Sol", type="SUN")
    dados_sol.energy = FORCA_SOL
    dados_sol.angle = math.radians(0.526)
    sol = bpy.data.objects.new("Sol", dados_sol)
    # A rotacao sai da mesma elevacao e do mesmo azimute do ceu: o eixo -Z do
    # SUN aponta para a cena, entao inclinar 90 - elevacao deixa o raio na
    # altura certa, e girar em Z coloca no azimute.
    sol.rotation_euler = (math.radians(90.0 - ELEVACAO_SOL), 0.0,
                          math.radians(AZIMUTE_SOL + 90.0))
    col.objects.link(sol)
    return sol


# --------------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dados", default="data/mapa_agroshow26.json")
    ap.add_argument("--relevo", default=None,
                    help="heightmap em escala de cinza para deslocar o terreno")
    ap.add_argument("--perfil", choices=("previa", "final"), default="previa",
                    help="previa: motor rapido para navegar. "
                         "final: Cycles com passes, para a entrega")
    ap.add_argument("--permitir-cpu", action="store_true",
                    help="no --perfil final, nao para se faltar GPU -- "
                         "renderiza em CPU mesmo assim. Use so para conferir "
                         "a cena num ambiente sem GPU, nunca para a entrega")
    ap.add_argument("--hdri", default=None,
                    help="HDRI de ceu; sem ele, ceu Nishita procedural")
    ap.add_argument("--out", default=None, help="salva um .blend no caminho")
    args = ap.parse_args(argv)

    dados = json.loads(Path(args.dados).read_text(encoding="utf-8"))
    # Origem no centro da prancha, para a cena nascer centrada no mundo.
    dados["_origem"] = (dados["prancha"]["largura_pt"] / 2,
                        dados["prancha"]["altura_pt"] / 2)

    limpar_cena()
    cols = criar_colecoes()
    centro = centro_da_arena(dados)
    mats = criar_materiais()

    print("construindo terreno...")
    terreno = construir_terreno(dados, cols["BASE"], centro, args.relevo)
    aplicar(terreno, mats["MAT_TERRENO"])
    construir_arena(centro, cols["BASE"], mats)

    print("construindo pavilhoes...")
    n_pav = construir_pavilhoes(dados, cols["BASE"], centro)
    for o in cols["BASE"].objects:
        if "PAVILHÃO" in o.name:
            aplicar(o, mats["MAT_PAVILHAO"])

    print("construindo estandes...")
    cont = construir_estandes(dados, cols["EVENTO"], centro)
    for o in cols["EVENTO"].objects:
        aplicar(o, mats["MAT_LONA"])

    print("construindo portal, palco e camarotes...")
    portal = construir_portal(dados, cols["EVENTO"], centro, mats)
    arena = construir_palco_e_camarotes(dados, cols["EVENTO"], centro, mats)

    print("construindo percurso...")
    pontos, ausentes, chegada = construir_percurso(dados, cols["CAMERA"], centro)

    construir_luz(cols["LUZ"])
    construir_ceu(bpy.context.scene, args.hdri)
    configurar_render(bpy.context.scene, args.perfil,
                      exigir_gpu=not args.permitir_cpu)

    larg_m = dados["prancha"]["largura_pt"] * ESCALA
    prof_m = dados["prancha"]["altura_pt"] * ESCALA

    print("\n" + "=" * 58)
    print(f"  escala .............. {ESCALA} m/pt")
    print(f"  extensao do terreno . {larg_m:.0f} x {prof_m:.0f} m")
    print(f"  pavilhoes ........... {n_pav}")
    print(f"  estandes ............ {cont['instanciado']} instanciados "
          f"+ {cont['proprio']} proprios")
    print(f"  portal .............. {'modelado' if portal else 'AUSENTE'}")
    print(f"  palco / camarotes ... {arena['palco']} palco, "
          f"{arena['camarotes']} lados de camarote (sem arquibancada)")
    print(f"  pontos do percurso .. {len(pontos)} de {len(PERCURSO)}")
    print(f"  render .............. {LARGURA_RENDER}x{ALTURA_RENDER} "
          f"({LARGURA_RENDER/ALTURA_RENDER:.0f}:1)")
    print(f"  animacao ............ {bpy.context.scene.frame_end} quadros "
          f"({bpy.context.scene.frame_end/FPS:.0f} s a {FPS} fps)")
    print(f"  patamares ........... arena 0 m -> shows {PATAMARES[2][2]} m "
          f"-> anel {PATAMARES[4][2]} m -> plato {PATAMARES[6][2]} m")
    print("-" * 58)
    print("  ponto                       quadro    tempo   altura")
    for (nome, _, _, altura, parada, _), quadro in zip(pontos, chegada):
        marca = f"{quadro/FPS:5.1f}s"
        extra = f"  +{parada:.1f}s parado" if parada else ""
        print(f"  {nome:<26} {quadro:>6}   {marca}   {altura:>4.0f} m{extra}")
    if ausentes:
        print("  AUSENTES no percurso:")
        for nome, rotulo in ausentes:
            print(f"     {nome} -> rotulo {rotulo!r} nao encontrado")
    print("=" * 58)

    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.out).resolve()))
        print(f"\nsalvo: {args.out}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as erro:
        # Falta de GPU no --perfil final chega aqui: mensagem limpa e sai,
        # em vez de traceback gigante ou, pior, salvar a cena calado em CPU.
        print(f"\n{erro}\n")
        sys.exit(1)
