#!/usr/bin/env python3
"""
Gera a cena 3D do Parque de Exposicoes de Dois Vizinhos para a AGROSHOW 2026,
a partir da planta extraida em data/mapa_agroshow26.json.

Constroi terreno, os 134 estandes instanciados, os pavilhoes, a arena, o portal,
o palco, os camarotes e o caminho de camera seguindo o percurso ditado pelo
cliente. Deixa tudo em colecoes separadas para que a camada permanente
(terreno, pavilhoes) sobreviva a troca da camada do evento (estandes, palco,
sinalizacao) no ano seguinte.

Uso:
    blender --background --python scripts/build_scene.py -- --out cena.blend

Ou com o modulo bpy instalado (pip install bpy):
    python3 scripts/build_scene.py --out cena.blend
    python3 scripts/build_scene.py --conferencia docs/   # quadros de checagem

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
RAIO_PISTA = 26.0        # m -- pista da arena, medida na planta; a bacia plana
                         #      ao redor dela e bem maior
FPS = 30
LARGURA_RENDER = 2760    # 2:1, 2x o nativo do painel P2,9 (1379x690)
ALTURA_RENDER = 1380

# Duracao alvo do percurso. A referencia do cliente tem ~2 min; sobra margem de
# lapidacao cortando trecho, nunca esticando -- esticar mata o ritmo.
DURACAO_ALVO = 148.0     # s

# Camera. O quadro de conferencia anterior mostrava telhado de estande porque a
# camera voava a 12 m com 18 graus de inclinacao fixos, parando em cima do
# proprio assunto -- de cima do assunto so se ve cobertura. Agora sao tres
# mudancas: a altura varia por trecho (aereo nas transicoes, baixa nos pontos),
# a camera para a uma distancia de recuo ANTES do assunto, e a mira e um alvo
# animado, nao um angulo fixo. Assim cada bloco do roteiro entra em quadro pela
# frente, que e como o cliente descreve o percurso no audio.
ALTURA_TRANSICAO = 52.0   # m acima do terreno, no meio dos trechos longos
TRECHO_MINIMO_AEREO = 5.0 # s -- trecho mais curto que isso nao sobe
RECUO_PADRAO = 55.0       # m entre a camera parada e o assunto
ALTURA_ALVO = 4.0         # m acima do solo do assunto -- mira na massa, nao no chao
# Mira do ultimo quadro, la fora do portal. Um pouco acima do horizonte: ao
# atravessar o vao a camera levanta para o ceu de fim de tarde. Mirando no
# horizonte o filme terminaria em campo vazio (nada foi modelado do lado de
# fora); mirando muito alto termina em ceu puro. Com 30 mm o meio angulo
# vertical e de 17 graus, entao 22 m a 130 m de distancia deixam a linha do
# horizonte no terco inferior do quadro.
ALTURA_ALVO_SAIDA = 22.0
LENTE_MM = 30.0
MOTOR_PADRAO = "CYCLES"

# Sol de fim de tarde, coerente com o LOOK LOCK das imagens de apoio.
# Azimute medido a partir do norte, no sentido horario (295 = oeste-noroeste).
# Um unico par de angulos alimenta o sol e o ceu -- se divergirem, a sombra vai
# para um lado e o disco solar para o outro, e o render inteiro denuncia.
AZIMUTE_SOL = 295.0
ELEVACAO_SOL = 12.0

# Percurso: a ordem e a do roteiro em docs/BRIEFING.md, que veio do audio.
# Cada ponto e um dicionario:
#   bloco      numero do bloco no roteiro ("--" para no de passagem sem titulo)
#   nome       identificacao interna, vira nome do marcador na viewport
#   rotulo     rotulo da planta a procurar em data/mapa_agroshow26.json
#   ocorrencia qual ocorrencia do rotulo, ordenada por (y, x)
#   titulo     texto do titulo vermelho do roteiro, na prancha (busca por
#              trecho); e a fonte certa para os blocos que nao tem rotulo CAD
#   ponto_pt   coordenada crua da prancha, em pontos PDF, para o unico bloco
#              que nao tem nem rotulo nem titulo
#   altura     m acima do terreno naquele ponto
#   recuo      m entre a camera parada e o assunto; negativo passa do assunto
#   alvo       m acima do solo do assunto onde a camera mira (padrao ALTURA_ALVO)
#   pausa      s parado no ponto, para o titulo respirar
#   provisorio posicao ainda nao confirmada pelo cliente
#
# Os quatro diferenciais -- Fazendinha, Rodeio, Cafe Colonial e Mercado do
# Produtor -- sao os unicos com pausa longa. Tela e tempo sao a mesma moeda.
PERCURSO = [
    dict(bloco="00", nome="Estacionamento", rotulo="ESTACIONAMENTO",
         ocorrencia=5, altura=46.0, recuo=120.0, pausa=1.5),
    dict(bloco="01", nome="Portal de Entrada", rotulo="Portal de Entrada",
         altura=9.0, recuo=45.0, pausa=3.0),
    # Faixa norte: os galpoes tem 8 m de pe direito e ate 90 m de comprido.
    # Recuo curto aqui poe a cobertura na cara da lente e o bloco some.
    dict(bloco="02", nome="Pavilhao 1", rotulo="PAVILHÃO 1",
         altura=32.0, recuo=110.0, alvo=9.0, pausa=1.5),
    dict(bloco="03", nome="Alimentacao Coberta", rotulo="Coberta",
         altura=28.0, recuo=95.0, alvo=9.0, pausa=1.5),
    dict(bloco="04", nome="Pavilhao 2", rotulo="PAVILHÃO 2",
         altura=32.0, recuo=110.0, alvo=9.0, pausa=1.5),
    dict(bloco="05", nome="Mercado do Produtor", rotulo="Mercado do Produtor",
         altura=26.0, recuo=90.0, alvo=8.0, pausa=3.0),
    dict(bloco="06", nome="Agroindustrias", rotulo="PAVILHÃO 3",
         altura=32.0, recuo=110.0, alvo=9.0, pausa=1.5),
    dict(bloco="07", nome="Cafe Colonial", rotulo="Café Colonial",
         altura=26.0, recuo=90.0, alvo=8.0, pausa=3.0),
    dict(bloco="--", nome="Bosque", rotulo="Bosque", ocorrencia=0,
         altura=24.0, pausa=0.0),
    dict(bloco="08", nome="Alimentacao Aberta", rotulo="Aberta",
         altura=18.0, pausa=1.5),
    dict(bloco="09", nome="Recinto de Leiloes", rotulo="RECINTO DE LEILÕES",
         altura=18.0, pausa=1.5),
    dict(bloco="10", nome="Pavilhoes de Animais", rotulo="PAVILHÃO - GADO LEITE",
         altura=26.0, recuo=90.0, pausa=2.0),
    dict(bloco="11", nome="Pista de Julgamentos", rotulo="PISTA DE JULGAMENTOS",
         altura=22.0, recuo=80.0, pausa=1.5),
    # Estes blocos nao tem rotulo CAD, mas tem titulo vermelho na prancha --
    # o desenhista do mapa marcou cada um deles. Uma primeira versao os
    # posicionou por geometria da bacia e errou de 88 a 182 m; a conferencia
    # contra a planta trocou a estimativa pela posicao real.
    dict(bloco="12", nome="Expositores Externos", titulo="Expositores Externo",
         altura=30.0, recuo=80.0, pausa=1.5),
    dict(bloco="13", nome="Fazendinha", titulo="Fazendinha",
         altura=20.0, recuo=60.0, alvo=5.0, pausa=3.5),
    dict(bloco="14", nome="Maquinas e Implementos",
         titulo="Exposição de Máquinas", altura=22.0, recuo=70.0, pausa=1.5),
    # Unico bloco sem rotulo e sem titulo: a prancha marca os veiculos so pela
    # cor da legenda. Posicao = centroide dos pixels azuis (VEICULOS E MOTOS
    # NAUTICAS) do bitmap, fora da caixa de legenda.
    dict(bloco="15", nome="Veiculos e Nauticas", ponto_pt=(647.5, 294.2),
         altura=22.0, recuo=70.0, pausa=1.5),
    dict(bloco="16", nome="Area de Shows", titulo="Área de Show",
         altura=16.0, pausa=1.5),
    dict(bloco="17", nome="Arena de Rodeio", rotulo="ARENA DE RODEIO",
         altura=13.0, recuo=70.0, pausa=3.5),
    dict(bloco="18", nome="Palco Principal", rotulo="PALCO", ocorrencia=0,
         altura=12.0, recuo=60.0, pausa=3.0),
    # Plano final em dois tempos. Primeiro a camera para de frente para o
    # portal, com ele preenchendo o quadro e a assinatura entrando; depois
    # atravessa o vao central. Terminar 80 m depois do portao daria dois
    # segundos de campo vazio -- o que fecha o filme e a passagem, nao o campo.
    dict(bloco="19", nome="Saida pelo Portal", rotulo="Portal de Entrada",
         altura=3.5, recuo=40.0, pausa=2.5),
    dict(bloco="--", nome="Atravessa o Portal", rotulo="Portal de Entrada",
         altura=3.5, recuo=-8.0, pausa=0.0),
]

COLECOES = ["BASE", "EVENTO", "CAMERA", "LUZ"]

# Relevo real do entorno, baixado por scripts/fetch_dem.py. Fica em modulo
# porque elevacao() e chamada centenas de milhares de vezes e passar o dado por
# parametro so encheria as assinaturas.
RELEVO = None

# Faixa de mistura entre a planta e o relevo medido, em metros de raio a partir
# do centro da arena. Dentro do limite de dentro manda a planta -- ela enxerga
# taludes de 3,5 m que um dado de 30 m nao ve. Fora do limite de fora manda o
# relevo medido, que sabe que o terreno cai 1,4 m a cada 100 m, coisa que a
# planta nao diz. No meio, mistura suave.
MISTURA_RELEVO = (150.0, 320.0)
EXTENSAO_ENTORNO = 500.0   # m de terreno alem da prancha, para os planos altos

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


def prisma(nome, vertices, altura, colecao):
    """Extruda um poligono do plano XY em um solido de altura dada.

    Serve para as pecas que nao sao caixa -- frontao do portal, cobertura do
    palco. Os vertices vem em coordenadas locais, no sentido anti-horario.
    """
    malha = bpy.data.meshes.new(nome)
    obj = bpy.data.objects.new(nome, malha)
    colecao.objects.link(obj)

    bm = bmesh.new()
    verts = [bm.verts.new((x, 0.0, z)) for x, z in vertices]
    face = bm.faces.new(verts)
    bmesh.ops.translate(
        bm,
        vec=Vector((0, -altura / 2, 0)),
        verts=bm.verts,
    )
    ret = bmesh.ops.extrude_face_region(bm, geom=[face])
    movidos = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=Vector((0, altura, 0)), verts=movidos)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(malha)
    bm.free()
    return obj


# --------------------------------------------------------------------------
# Materiais

# (nome, cor base RGB, rugosidade, metalico, tamanho da mancha em metros)
# A mancha e um ruido que quebra a cor chapada. Vale pouco de perto e muito de
# longe, que e onde este video vive: sem ela, grama e lona leem como plastico.
# O tamanho e em METROS -- mancha de grama tem 12 m, veio de madeira tem 40 cm.
# Mancha menor que um pixel na tela vira moire, que e pior que a cor chapada.
# Troque por PBR com textura (Poly Haven, ambientCG, ambos CC0) na lapidacao;
# no ambiente remoto os dois dominios estao bloqueados pelo proxy.
MATERIAIS = {
    "MAT_TERRENO":  ((0.13, 0.22, 0.07), 0.95, 0.0, 14.0),
    "MAT_LONA":     ((0.82, 0.81, 0.78), 0.55, 0.0, 2.0),
    "MAT_PAVILHAO": ((0.55, 0.56, 0.58), 0.45, 0.3, 4.0),
    "MAT_ARENA":    ((0.38, 0.28, 0.18), 0.90, 0.0, 8.0),
    "MAT_ASFALTO":  ((0.17, 0.17, 0.18), 0.80, 0.0, 10.0),
    "MAT_MADEIRA":  ((0.16, 0.09, 0.05), 0.65, 0.0, 0.4),
    "MAT_TELHA":    ((0.07, 0.07, 0.08), 0.40, 0.6, 1.2),
    "MAT_LETREIRO": ((0.92, 0.91, 0.88), 0.35, 0.0, 0.0),
    "MAT_FERRO":    ((0.03, 0.03, 0.03), 0.30, 0.9, 0.0),
    "MAT_PALCO":    ((0.05, 0.05, 0.06), 0.55, 0.1, 1.5),
    "MAT_PASTO":    ((0.16, 0.28, 0.09), 0.95, 0.0, 6.0),
}


def variar_cor(mat, cor, tamanho):
    """Mistura um ruido na cor base, para tirar o aspecto de plastico chapado.

    O tamanho e a mancha em metros. O segundo tom sai da propria cor,
    escurecido -- assim a variacao nunca briga com a paleta.
    """
    nos = mat.node_tree.nodes
    ligacoes = mat.node_tree.links
    bsdf = nos.get("Principled BSDF")
    if not bsdf:
        return

    ruido = nos.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 1.0 / max(tamanho, 1e-3)
    ruido.inputs["Detail"].default_value = 6.0
    ruido.location = (-700, 0)

    mistura = nos.new("ShaderNodeMixRGB")
    mistura.blend_type = "MIX"
    mistura.inputs["Fac"].default_value = 0.35
    mistura.inputs["Color1"].default_value = (*cor, 1.0)
    mistura.inputs["Color2"].default_value = (
        cor[0] * 0.55, cor[1] * 0.55, cor[2] * 0.55, 1.0)
    mistura.location = (-400, 0)

    ligacoes.new(ruido.outputs["Fac"], mistura.inputs["Fac"])
    ligacoes.new(mistura.outputs["Color"], bsdf.inputs["Base Color"])


def criar_materiais():
    """Materiais base, com variacao procedural. Ponto de partida do acabamento."""
    feitos = {}
    for nome, (cor, rug, met, mancha) in MATERIAIS.items():
        mat = bpy.data.materials.new(nome)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*cor, 1.0)
            bsdf.inputs["Roughness"].default_value = rug
            if "Metallic" in bsdf.inputs:
                bsdf.inputs["Metallic"].default_value = met
        if mancha:
            variar_cor(mat, cor, mancha)
        feitos[nome] = mat
    return feitos


def aplicar(obj, mat):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.clear()
        obj.data.materials.append(mat)


# --------------------------------------------------------------------------
# Construcao

def carregar_relevo(caminho):
    """Le o recorte de elevacao e prepara a amostragem em coordenadas do mundo.

    O recorte e quadrado e centrado na coordenada do recinto; assume-se que ela
    cai no centro da prancha e que o desenho esta com o norte para cima -- e o
    que a rosa dos ventos da planta mostra. Um erro de registro desloca o
    relevo em relacao aos predios, por isso a planta e quem manda perto da
    arena, onde a posicao importa.
    """
    global RELEVO
    caminho = Path(caminho)
    if not caminho.exists():
        return None

    import numpy as np
    dados = np.load(caminho, allow_pickle=False)
    altura = dados["altura"].astype(float)
    meta = json.loads(str(dados["meta"]))
    mpp = meta["metros_por_pixel"]
    linhas, colunas = altura.shape

    def amostrar(x, y):
        """Altitude bruta, em metros, para um ponto do mundo."""
        col = colunas / 2 + x / mpp
        lin = linhas / 2 - y / mpp
        c0 = min(max(int(col), 0), colunas - 2)
        l0 = min(max(int(lin), 0), linhas - 2)
        fc, fl = col - c0, lin - l0
        fc = min(max(fc, 0.0), 1.0)
        fl = min(max(fl, 0.0), 1.0)
        a = altura[l0, c0] * (1 - fc) + altura[l0, c0 + 1] * fc
        b = altura[l0 + 1, c0] * (1 - fc) + altura[l0 + 1, c0 + 1] * fc
        return a * (1 - fl) + b * fl

    RELEVO = {"amostrar": amostrar, "meta": meta, "referencia": 0.0,
              "altura": altura, "mpp": mpp}
    return RELEVO


def referenciar_relevo(centro_arena):
    """Zera o relevo medido na faixa onde ele encosta na planta.

    Sem isso a cena inteira sobe uns 600 m (altitude absoluta) e, pior, apareceria
    um degrau no raio de mistura. A referencia e a media do anel de transicao.
    """
    if not RELEVO:
        return
    r_int, r_ext = MISTURA_RELEVO
    raio = (r_int + r_ext) / 2
    amostras = []
    for i in range(72):
        a = math.radians(i * 5)
        amostras.append(RELEVO["amostrar"](centro_arena[0] + raio * math.cos(a),
                                           centro_arena[1] + raio * math.sin(a)))
    RELEVO["referencia"] = sum(amostras) / len(amostras)


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

    z_planta = PATAMARES[-1][3]
    for r_int, r_ext, z_int, z_ext in PATAMARES:
        if r < r_ext:
            if r <= r_int:
                z_planta = z_int
            else:
                # Talude: transicao suave entre um patamar e o seguinte.
                t = (r - r_int) / (r_ext - r_int)
                t = t * t * (3.0 - 2.0 * t)   # smoothstep
                z_planta = z_int + (z_ext - z_int) * t
            break

    if not RELEVO:
        return z_planta

    # Relevo medido, trazido para o mesmo zero do plato da planta.
    z_medido = (PATAMARES[-1][3]
                + RELEVO["amostrar"](x, y) - RELEVO["referencia"])

    r_int, r_ext = MISTURA_RELEVO
    if r <= r_int:
        return z_planta
    if r >= r_ext:
        return z_medido
    t = (r - r_int) / (r_ext - r_int)
    t = t * t * (3.0 - 2.0 * t)
    return z_planta * (1 - t) + z_medido * t


def construir_arena(centro_arena, col, mats):
    """Piso de terra da pista, no fundo da bacia."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=RAIO_PISTA, depth=0.4,
                                        location=(centro_arena[0],
                                                  centro_arena[1], 0.1))
    obj = bpy.context.active_object
    obj.name = "PistaArena"
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    aplicar(obj, mats["MAT_ARENA"])
    return obj


def construir_terreno(dados, col, centro_arena):
    """Terreno da prancha inteira, esculpido na bacia da arena.

    A altura de cada vertice sai de elevacao(), que mistura a bacia da planta
    (perto da arena) com o relevo medido (no entorno). O terreno passa da
    prancha em EXTENSAO_ENTORNO metros para os planos altos terem horizonte.
    """
    larg = dados["prancha"]["largura_pt"] * ESCALA + 2 * EXTENSAO_ENTORNO
    prof = dados["prancha"]["altura_pt"] * ESCALA + 2 * EXTENSAO_ENTORNO
    # Uma divisao a cada ~4 m, que e a amostragem do recorte de elevacao.
    div = int(max(larg, prof) / 4.3)

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


def suavizar_curvas(obj):
    """Poe as chaves em bezier auto-clamped.

    Auto-clamped acelera e freia sozinho nas paradas e nao inventa overshoot
    nos trechos de velocidade constante -- que e exatamente o comportamento
    desejado num percurso com pausas nos diferenciais.
    """
    for fc in fcurves_da_acao(obj):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


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


# Galpoes da faixa norte, onde acontecem seis blocos do roteiro: Pavilhao 1,
# Alimentacao Coberta, Pavilhao 2, Mercado do Produtor, Agroindustrias e Cafe
# Colonial. Sem eles a camera para de frente para grama vazia nos seis.
#
# As dimensoes vieram da CONFERENCIA CONTRA A PLANTA (scripts/overlay_check.py),
# medidas no bitmap da prancha, e nao de suposicao. Duas descobertas la:
#   - Pavilhao 1, Sagua o Aberto e Praca Coberta nao sao predios separados. Sao
#     um unico bloco comprido de ~176 x 33 m, com o Pavilhao 2 na outra ponta.
#   - "PAVILHAO 3" e o bloco laranja estreito do Galpao do Produtor, de ~20 x
#     37 m, que abriga Mercado do Produtor, Cafe Colonial e Cozinha Didatica.
# A leitura do bitmap tem uns 2 m de incerteza; confirme com o cliente se
# alguma medida virar decisao de producao.
#
# (nome, x_pt, y_pt, largura leste-oeste, profundidade norte-sul)
GALPOES = [
    ("GALPAO Faixa Norte", 626.5, 162.5, 176.0, 33.0),
    ("GALPAO do Produtor",  437.5, 166.0,  20.0, 37.0),
]
ALTURA_GALPAO = 8.0      # m -- pe direito, acima dos 3,2 m dos estandes


def construir_galpoes(dados, col, mats, centro_arena):
    """Galpoes da faixa norte: cobertura em duas aguas sobre pilares.

    Sem parede: os estandes de dentro continuam visiveis, que e o que o roteiro
    pede em cada um dos seis blocos. Duas aguas em vez de laje plana porque a
    laje, vista da altura da camera, vira um retangulo cinza sem leitura.
    """
    origem = dados["_origem"]
    feitos = 0
    for nome, x_pt, y_pt, larg, prof in GALPOES:
        x, y = para_mundo(x_pt, y_pt, origem)
        solo = elevacao(x, y, centro_arena)

        meia = larg / 2
        cobertura = prisma(f"{nome} cobertura",
                           [(-meia, 0.0), (meia, 0.0), (meia, 1.2),
                            (0.0, 3.4), (-meia, 1.2)], prof, col)
        cobertura.location = (x, y, solo + ALTURA_GALPAO)
        aplicar(cobertura, mats["MAT_PAVILHAO"])
        cobertura["medido_no_bitmap"] = True

        # Pilares a cada ~12 m nas duas laterais compridas.
        passos = max(2, int(larg // 12.0))
        for i in range(passos + 1):
            px = x - meia + larg * i / passos
            for py in (y - prof / 2, y + prof / 2):
                pilar = caixa(f"{nome} pilar {i}", 0.7, 0.7,
                              ALTURA_GALPAO, col)
                pilar.location = (px, py, solo)
                aplicar(pilar, mats["MAT_FERRO"])
        feitos += 1
    return feitos


# Tres lugares que o roteiro visita e que a planta desenha, mas que a cena nao
# tinha. As dimensoes foram medidas no bitmap da prancha (ver ESTADO.md); a
# rotacao sai da direcao do rotulo.

RAIO_LEILOES = 19.0      # m -- a estrela do recinto tem ~38 m de ponta a ponta
ALTURA_LEILOES = 7.0
PISTA_JULGAMENTO = (42.0, 59.0)   # m -- retangulo de pasto com pontas redondas
FAZENDINHA = (28.0, 90.0)         # m -- faixa de grama entre duas fileiras


def construir_leiloes(dados, col, mats, centro_arena):
    """Recinto de Leiloes: pavilhao em estrela de oito pontas, ~38 m.

    E o bloco 09 do roteiro e, ate agora, a camera parava de frente para o
    nada. Na prancha e uma estrela regular hachurada; dezesseis lados com raio
    alternado dao a mesma silhueta com custo de um cilindro.
    """
    z = achar_zona(dados, "RECINTO DE LEILÕES", 0)
    if z is None:
        return None
    x, y = para_mundo(z["x"], z["y"], dados["_origem"])
    solo = elevacao(x, y, centro_arena)

    malha = bpy.data.meshes.new("RecintoDeLeiloes")
    obj = bpy.data.objects.new("RecintoDeLeiloes", malha)
    col.objects.link(obj)

    bm = bmesh.new()
    base = []
    for i in range(16):
        ang = math.pi * 2 * i / 16
        raio = RAIO_LEILOES if i % 2 == 0 else RAIO_LEILOES * 0.72
        base.append(bm.verts.new((raio * math.cos(ang), raio * math.sin(ang), 0.0)))
    face = bm.faces.new(base)
    ret = bmesh.ops.extrude_face_region(bm, geom=[face])
    topo = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=Vector((0, 0, ALTURA_LEILOES)), verts=topo)
    # Cume: junta o topo num ponto so, virando telhado conico.
    bmesh.ops.pointmerge(bm, verts=topo,
                         merge_co=Vector((0, 0, ALTURA_LEILOES + 6.0)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(malha)
    bm.free()

    obj.location = (x, y, solo)
    obj.rotation_euler = (0.0, 0.0, angulo_do_rotulo(z))
    aplicar(obj, mats["MAT_PAVILHAO"])
    return obj


def cercar(nome, x, y, larg, prof, angulo, altura, col, mats, centro_arena,
           passo=6.0):
    """Mouroes a cada passo metros, no contorno de um retangulo girado."""
    feitos = 0
    for lado, comprimento in ((0, larg), (1, prof)):
        n = max(2, int(comprimento / passo))
        for i in range(n + 1):
            t = -comprimento / 2 + comprimento * i / n
            for sinal in (-1, 1):
                if lado == 0:
                    lx, ly = t, sinal * prof / 2
                else:
                    lx, ly = sinal * larg / 2, t
                px = x + lx * math.cos(angulo) - ly * math.sin(angulo)
                py = y + lx * math.sin(angulo) + ly * math.cos(angulo)
                mourao = caixa(f"{nome} mourao {feitos}", 0.22, 0.22, altura, col)
                mourao.location = (px, py, elevacao(px, py, centro_arena))
                aplicar(mourao, mats["MAT_MADEIRA"])
                feitos += 1
    return feitos


def construir_pista_julgamento(dados, col, mats, centro_arena):
    """Pista de Julgamentos: pasto cercado, ~42 x 59 m.

    Bloco 11 do roteiro. Na prancha e um retangulo de pontas arredondadas com
    hachura de grama; aqui vira um tapete rente ao chao mais a cerca, que e o
    que da a leitura de area de pasto vista de cima.
    """
    z = achar_zona(dados, "PISTA DE JULGAMENTOS", 0)
    if z is None:
        return 0
    x, y = para_mundo(z["x"], z["y"], dados["_origem"])
    larg, prof = PISTA_JULGAMENTO
    ang = angulo_do_rotulo(z)

    tapete = caixa("PistaJulgamento", larg, prof, 0.12, col)
    tapete.location = (x, y, elevacao(x, y, centro_arena))
    tapete.rotation_euler = (0.0, 0.0, ang)
    aplicar(tapete, mats["MAT_PASTO"])
    return 1 + cercar("PistaJulgamento", x, y, larg, prof, ang, 1.3,
                      col, mats, centro_arena)


def construir_fazendinha(dados, col, mats, centro_arena):
    """Fazendinha: faixa cercada com porteira de destaque na entrada.

    Diferencial do cliente, e no audio ele pede nominalmente uma porteira
    bacana. Na planta o rotulo cai numa faixa de grama entre duas fileiras de
    estandes, descendo o talude -- nao e predio, e area aberta. A porteira fica
    na ponta que olha para o percurso.
    """
    t = achar_titulo(dados, "Fazendinha")
    if t is None:
        return 0
    x, y = para_mundo(t["x"], t["y"], dados["_origem"])
    larg, prof = FAZENDINHA
    # A faixa desce o talude, ou seja, corre no rumo do centro da arena.
    ang = math.atan2(y - centro_arena[1], x - centro_arena[0]) + math.pi / 2

    feitos = cercar("Fazendinha", x, y, larg, prof, ang, 1.3,
                    col, mats, centro_arena, passo=8.0)

    # Porteira: dois esteios, travessa e placa. O nome vai grande na placa e a
    # descricao pequena embaixo -- hierarquia pedida nominalmente pelo cliente.
    #
    # Fica na ponta de CIMA da faixa, a que olha para os expositores externos:
    # e por ali que o percurso desce, e porteira de destaque so cumpre o papel
    # se estiver na chegada. Na ponta de baixo ela ficaria de costas.
    frente_x = x + math.sin(ang) * (prof / 2)
    frente_y = y - math.cos(ang) * (prof / 2)
    solo = elevacao(frente_x, frente_y, centro_arena)
    for sinal in (-1, 1):
        px = frente_x + math.cos(ang) * sinal * (larg / 2)
        py = frente_y + math.sin(ang) * sinal * (larg / 2)
        esteio = caixa(f"Fazendinha esteio {sinal}", 0.5, 0.5, 5.0, col)
        esteio.location = (px, py, elevacao(px, py, centro_arena))
        aplicar(esteio, mats["MAT_MADEIRA"])
        feitos += 1

    travessa = caixa("Fazendinha travessa", larg + 1.0, 0.4, 0.6, col)
    travessa.location = (frente_x, frente_y, solo + 4.4)
    travessa.rotation_euler = (0.0, 0.0, ang)
    aplicar(travessa, mats["MAT_MADEIRA"])

    placa = caixa("Fazendinha placa", larg * 0.55, 0.3, 1.6, col)
    placa.location = (frente_x, frente_y, solo + 5.0)
    placa.rotation_euler = (0.0, 0.0, ang)
    aplicar(placa, mats["MAT_LETREIRO"])
    placa["texto"] = "FAZENDINHA"
    placa["descricao"] = "Area infantil"   # menor, embaixo do nome
    return feitos + 2


def construir_estacionamentos(dados, col, mats, centro_arena):
    """Manchas de asfalto nos estacionamentos.

    O bloco 00 e o ponto de vista de quem chega, e sem elas o primeiro quadro
    do filme e grama vazia. Sao lajes finas: a leitura vem da cor, nao do
    volume. Dimensao aproximada e deliberadamente modesta: a planta rotula o
    estacionamento mas nao delimita a area, e laje grande demais invade o
    galpao da faixa norte -- coisa que a conferencia em planta mostra na hora.
    """
    origem = dados["_origem"]
    feitos = 0
    for z in dados["zonas"]:
        if z["rotulo"] != "ESTACIONAMENTO":
            continue
        x, y = para_mundo(z["x"], z["y"], origem)
        obj = caixa(f"Estacionamento {feitos}", 70.0, 40.0, 0.15, col)
        obj.location = (x, y, elevacao(x, y, centro_arena))
        aplicar(obj, mats["MAT_ASFALTO"])
        feitos += 1
    return feitos


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
        obj.rotation_euler = (0.0, 0.0, angulo_do_rotulo(z))
        obj["area_m2"] = area
        feitos += 1
    return feitos


# --------------------------------------------------------------------------
# Portal, palco e camarotes -- as tres pecas que a camera encosta

def construir_portal(dados, col, mats, centro_arena, mira):
    """Portal de entrada, conceito celeiro, na leitura economica.

    Segue reference/PORTAL-referencia.md: frontao em duas aguas com trelica em
    V invertido, tabuas verticais, letreiro em relevo, alas laterais mais
    baixas com beiral curto, tres vaos de passagem, barris ladeando. O cliente
    disse que a versao construida sera mais barata que a foto -- na duvida
    entre duas leituras de um detalhe, esta aqui a mais economica.

    E o primeiro e o ultimo plano do video, entao vale a geometria de verdade:
    o plano final atravessa o vao central.
    """
    origem = dados["_origem"]
    z = achar_zona(dados, "Portal de Entrada", 0)
    x, y = para_mundo(z["x"], z["y"], origem)
    solo = elevacao(x, y, centro_arena)

    grupo = bpy.data.objects.new("PORTAL", None)
    grupo.empty_display_type = "PLAIN_AXES"
    grupo.empty_display_size = 6.0
    grupo.location = (x, y, solo)
    # Os pilares correm no X local e a passagem acontece no Y local, entao o
    # Y local e que tem de apontar para fora -- dai o quarto de volta somado ao
    # rumo da mira. Sem ele o portao vira corredor paralelo ao caminho, e a
    # camera passa por fora em vez de atravessar o vao.
    grupo.rotation_euler = (0.0, 0.0,
                            math.atan2(y - mira[1], x - mira[0]) + math.pi / 2)
    col.objects.link(grupo)

    def peca(nome, larg, prof, alt, pos, mat):
        obj = caixa(nome, larg, prof, alt, col)
        obj.parent = grupo
        obj.location = pos
        aplicar(obj, mat)
        return obj

    largura_vao = 4.0
    largura_pilar = 1.6
    altura_pilar = 5.0
    # Quatro pilares definem os tres vaos de passagem.
    for i in range(4):
        deslocamento = (i - 1.5) * (largura_vao + largura_pilar)
        peca(f"PORTAL_Pilar{i}", largura_pilar, 3.0, altura_pilar,
             (deslocamento, 0.0, 0.0), mats["MAT_MADEIRA"])

    largura_corpo = 4 * largura_pilar + 3 * largura_vao
    peca("PORTAL_Verga", largura_corpo, 3.0, 1.6,
         (0.0, 0.0, altura_pilar), mats["MAT_MADEIRA"])

    # Frontao em duas aguas por cima da verga, com a trelica aparente.
    meia = largura_corpo / 2
    frontao = prisma("PORTAL_Frontao",
                     [(-meia, 0.0), (meia, 0.0), (0.0, 3.6)], 2.6, col)
    frontao.parent = grupo
    frontao.location = (0.0, 0.0, altura_pilar + 1.6)
    aplicar(frontao, mats["MAT_MADEIRA"])

    # Trelica aparente em V invertido, encaixada no frontao: cada barra sai do
    # beiral e sobe ate a cumeeira. Angulo e comprimento derivados da propria
    # agua do telhado -- barra fora do triangulo fura o frontao, e o quadro de
    # conferencia denuncia na hora.
    altura_frontao = 3.6
    comprimento = math.hypot(meia, altura_frontao)
    inclinacao_agua = math.atan2(altura_frontao, meia)
    for lado in (-1, 1):
        trelica = caixa("PORTAL_Trelica", 0.3, 0.3, comprimento, col)
        trelica.parent = grupo
        trelica.location = (lado * meia, -1.35, altura_pilar + 1.6)
        trelica.rotation_euler = (0.0,
                                  -lado * (math.pi / 2 - inclinacao_agua),
                                  0.0)
        aplicar(trelica, mats["MAT_MADEIRA"])

    # Letreiro em relevo: PARQUE DE EXPOSICOES / DE DOIS VIZINHOS - PR.
    # Entra como placa; o texto e composto na pos com mascara, nunca gerado.
    letreiro = peca("PORTAL_Letreiro", largura_corpo * 0.62, 0.25, 1.1,
                    (0.0, -1.6, altura_pilar + 0.25), mats["MAT_LETREIRO"])
    letreiro["texto"] = "PARQUE DE EXPOSIÇÕES · DE DOIS VIZINHOS - PR"

    # Alas laterais, mais baixas, com beiral curto.
    for lado in (-1, 1):
        peca(f"PORTAL_Ala{lado}", 8.0, 4.0, 3.6,
             (lado * (largura_corpo / 2 + 4.0), 0.0, 0.0),
             mats["MAT_MADEIRA"])
        peca(f"PORTAL_Beiral{lado}", 8.8, 4.8, 0.4,
             (lado * (largura_corpo / 2 + 4.0), 0.0, 3.6),
             mats["MAT_TELHA"])

    # Luminarias de parede em ferro preto -- seis na fachada, como na foto.
    for i in range(6):
        peca(f"PORTAL_Luminaria{i}", 0.35, 0.35, 0.5,
             ((i - 2.5) * (largura_corpo / 6), -1.6, 3.9), mats["MAT_FERRO"])

    # Barris ladeando a passagem central.
    for i, lado in enumerate((-1, 1)):
        for j in range(3):
            barril = peca(f"PORTAL_Barril{i}{j}", 0.9, 0.9, 1.0,
                          (lado * (largura_vao * 0.75 + j * 1.2), -2.6, 0.0),
                          mats["MAT_MADEIRA"])
            barril.rotation_euler = (0.0, 0.0, math.radians(20.0 * j))

    return grupo, (x, y)


def construir_palco(dados, col, mats, centro_arena):
    """Palco principal, de frente para a pista, no fundo da bacia.

    Deck elevado, duas torres de PA e cobertura em duas aguas. Sem trelica
    detalhada: a camera passa a 12 m e o que le e a silhueta.
    """
    origem = dados["_origem"]
    z = achar_zona(dados, "PALCO", 0)
    x, y = para_mundo(z["x"], z["y"], origem)
    solo = elevacao(x, y, centro_arena)

    grupo = bpy.data.objects.new("PALCO", None)
    grupo.empty_display_type = "PLAIN_AXES"
    grupo.empty_display_size = 6.0
    grupo.location = (x, y, solo)
    # De frente para o centro da pista -- o cliente foi explicito no audio. O
    # deck e largo no X local e a boca de cena e o -Y local, dai o quarto de
    # volta: sem ele o palco aponta a lateral para o publico.
    grupo.rotation_euler = (0.0, 0.0,
                            math.atan2(centro_arena[1] - y,
                                       centro_arena[0] - x) + math.pi / 2)
    col.objects.link(grupo)

    def peca(nome, larg, prof, alt, pos, mat):
        obj = caixa(nome, larg, prof, alt, col)
        obj.parent = grupo
        obj.location = pos
        aplicar(obj, mat)
        return obj

    # 22 x 16 m: o poligono do palco na prancha mede uns 22 m de frente por 20
    # de fundo, contando a area de servico atras. Medido no bitmap, com a
    # incerteza de sempre.
    peca("PALCO_Deck", 22.0, 16.0, 2.0, (0.0, 0.0, 0.0), mats["MAT_PALCO"])
    for lado in (-1, 1):
        peca(f"PALCO_Torre{lado}", 3.0, 3.0, 11.0,
             (lado * 12.5, 0.0, 0.0), mats["MAT_FERRO"])
        peca(f"PALCO_PA{lado}", 2.2, 2.2, 4.0,
             (lado * 12.5, -1.5, 6.5), mats["MAT_FERRO"])

    cobertura = prisma("PALCO_Cobertura",
                       [(-12.0, 0.0), (12.0, 0.0), (12.0, 1.0),
                        (0.0, 3.2), (-12.0, 1.0)], 17.0, col)
    cobertura.parent = grupo
    cobertura.location = (0.0, 0.0, 11.0)
    aplicar(cobertura, mats["MAT_TELHA"])
    return grupo


def construir_camarotes(dados, col, mats, centro_arena):
    """Camarotes nos dois lados da pista. SEM ARQUIBANCADA.

    Restricao dura do cliente: a arena tem so pista, camarotes nos dois lados e
    palco de frente. Arquibancada e rejeicao -- nao acrescente por conta de
    "ficar mais cheio". Cada lado vira uma fileira de modulos de dois andares
    seguindo o arco da pista, apoiada no patamar dos shows.
    """
    origem = dados["_origem"]
    feitos = 0
    for rotulo in ("CAMAROTES - LADO A", "CAMAROTES - LADO B"):
        z = achar_zona(dados, rotulo, 0)
        if z is None:
            continue
        x, y = para_mundo(z["x"], z["y"], origem)

        # A faixa corre no eixo do proprio rotulo -- conferido contra a planta,
        # onde os camarotes sao duas faixas retas ladeando a pista, e nao um
        # arco. Lado A fica a -54 graus e lado B a -70.
        eixo = angulo_do_rotulo(z)
        largura, profundidade = 8.0, 6.0
        passo = largura + 1.5
        for i in range(8):
            cx = x + math.cos(eixo) * (i - 3.5) * passo
            cy = y + math.sin(eixo) * (i - 3.5) * passo
            obj = caixa(f"{rotulo} {i}", largura, profundidade, 6.0, col)
            obj.location = (cx, cy, elevacao(cx, cy, centro_arena))
            # A largura corre na faixa; a frente (-Y local) tem de olhar para a
            # pista, entao escolhe-se o sentido que aponta para o centro.
            para_centro = math.atan2(centro_arena[1] - cy, centro_arena[0] - cx)
            giro = eixo if math.cos(para_centro - (eixo - math.pi / 2)) > 0 \
                else eixo + math.pi
            obj.rotation_euler = (0.0, 0.0, giro)
            aplicar(obj, mats["MAT_PALCO"])
            feitos += 1
    return feitos


# --------------------------------------------------------------------------
# Percurso e camera

def achar_zona(dados, rotulo, ocorrencia=0):
    achados = [z for z in dados["zonas"] if z["rotulo"] == rotulo]
    if not achados:
        return None
    achados.sort(key=lambda z: (z["y"], z["x"]))
    return achados[min(ocorrencia, len(achados) - 1)]


def angulo_do_rotulo(z, padrao=0.0):
    """Angulo do elemento, em radianos no mundo, tirado da direcao do rotulo.

    O rotulo da prancha corre no eixo do que ele nomeia: "PAVILHAO - GADO
    LEITE" corre no eixo do pavilhao, "CAMAROTES - LADO A" corre na faixa dos
    camarotes. O y do PDF cresce para baixo e o do mundo para cima, dai o sinal
    invertido em dy. Sem isto tudo nasce alinhado aos eixos e a planta acusa:
    os seis pavilhoes de animais estao a 18 graus.
    """
    direcao = z.get("dir")
    if not direcao:
        return padrao
    dx, dy = direcao
    return math.atan2(-dy, dx)


def achar_titulo(dados, trecho, ocorrencia=0):
    """Titulo do roteiro na prancha, buscado por trecho do texto.

    Busca por trecho e nao por igualdade porque o titulo da prancha traz mais
    do que o titulo da tela: "Fazendinha Area Infantil", "Exposicao de
    Maquinas,Equipamentos e Veiculos e Implementos".
    """
    achados = [t for t in dados.get("titulos", []) if trecho in t["texto"]]
    if not achados:
        return None
    achados.sort(key=lambda t: (t["y"], t["x"]))
    return achados[min(ocorrencia, len(achados) - 1)]


def resolver_pontos(dados, centro_arena):
    """Converte cada entrada do PERCURSO em coordenada de mundo.

    Tres fontes, nesta ordem de confianca: o rotulo CAD da zona, o titulo
    vermelho do roteiro na prancha, e a coordenada crua em pontos PDF. Nenhuma
    delas e estimativa -- todas saem do desenho.
    """
    origem = dados["_origem"]
    pontos, ausentes = [], []

    for spec in PERCURSO:
        if "ponto_pt" in spec:
            x, y = para_mundo(*spec["ponto_pt"], origem)
        elif "titulo" in spec:
            t = achar_titulo(dados, spec["titulo"], spec.get("ocorrencia", 0))
            if t is None:
                ausentes.append((spec["nome"], spec["titulo"]))
                continue
            x, y = para_mundo(t["x"], t["y"], origem)
        else:
            z = achar_zona(dados, spec["rotulo"], spec.get("ocorrencia", 0))
            if z is None:
                ausentes.append((spec["nome"], spec["rotulo"]))
                continue
            x, y = para_mundo(z["x"], z["y"], origem)
        ponto = dict(spec)
        ponto["x"], ponto["y"] = x, y
        pontos.append(ponto)

    return pontos, ausentes


def no_de_saida(pontos, mira):
    """Ponto extra do caminho, do lado de fora do portal.

    O plano final atravessa o portao -- entao o caminho precisa continuar para
    fora dele, senao a camera para debaixo da verga.
    """
    fim = pontos[-1]
    dx, dy = fim["x"] - mira[0], fim["y"] - mira[1]
    norma = math.hypot(dx, dy) or 1.0
    return (fim["x"] + dx / norma * 140.0, fim["y"] + dy / norma * 140.0)


def no_de_entrada(pontos):
    """Ponto extra do caminho, antes do primeiro bloco.

    O recuo so existe se houver caminho atras do assunto. Sem este no, a camera
    comeca em cima do estacionamento olhando para os proprios pes -- o primeiro
    quadro do filme, justamente.
    """
    inicio, seguinte = pontos[0], pontos[1]
    dx = inicio["x"] - seguinte["x"]
    dy = inicio["y"] - seguinte["y"]
    norma = math.hypot(dx, dy) or 1.0
    return (inicio["x"] + dx / norma * 260.0, inicio["y"] + dy / norma * 260.0)


def ritmar(pontos, entrada, saida):
    """Distribui a duracao alvo entre os trechos e devolve os quadros-chave.

    Tempo de marcha proporcional ao comprimento do trecho -- velocidade
    constante, sem o solavanco de dar o mesmo tempo a um pulo de 400 m e a um
    de 40 m. As pausas saem do bolo antes do rateio, entao acrescentar pausa
    encurta a marcha em vez de esticar o filme.

    O recuo de cada ponto vira deslocamento no parametro do caminho: a camera
    para antes do assunto (ou depois dele, com recuo negativo) enquanto o alvo
    continua no assunto. E o que faz o bloco entrar em quadro pela frente.
    """
    nos = [entrada] + [(p["x"], p["y"]) for p in pontos] + [saida]
    comprimentos = [math.dist(a, b) for a, b in zip(nos, nos[1:])]
    total = sum(comprimentos) or 1.0

    # 1) Onde a camera para para cada bloco: a distancia do assunto ao longo do
    #    caminho, menos o recuo. Sempre adiante da parada anterior -- o caminho
    #    nunca anda para tras.
    percorrido = comprimentos[0]
    anterior = 0.0
    for i, p in enumerate(pontos):
        if i:
            # comprimentos[i] e o trecho entre o assunto anterior e este --
            # o indice ja conta com o no de entrada na frente da lista.
            percorrido += comprimentos[i]
        recuo = p.get("recuo", RECUO_PADRAO)
        u = max(anterior + 1e-4, min(1.0, (percorrido - recuo) / total))
        anterior = u
        p["u"] = u

    # 2) Tempo: proporcional ao caminho REALMENTE percorrido entre paradas, nao
    #    ao caminho inteiro. Os nos de entrada e saida existem para dar sobra de
    #    curva nas pontas; ratear tempo por eles encolheria o filme.
    andados = [(b["u"] - a["u"]) * total for a, b in zip(pontos, pontos[1:])]
    andado_total = sum(andados) or 1.0
    pausa_total = sum(p.get("pausa", 0.0) for p in pontos)
    marcha = max(DURACAO_ALVO - pausa_total, len(andados) * 1.0)

    t = 0.0
    for i, p in enumerate(pontos):
        if i:
            t += andados[i - 1] / andado_total * marcha
        p["t_chegada"] = t
        t += p.get("pausa", 0.0)
        p["t_saida"] = t

    duracao = t
    for p in pontos:
        p["quadro_chegada"] = max(1, round(p["t_chegada"] * FPS) + 1)
        p["quadro_saida"] = max(1, round(p["t_saida"] * FPS) + 1)
    return pontos, duracao, comprimentos, nos


def construir_percurso(dados, col, centro_arena, mira):
    """Curva bezier pelos pontos do roteiro, com camera animada por cima.

    A camera nao anda colada na curva: a curva e a linha de solo do percurso, a
    camera e filha do rig com altura propria por ponto, e a mira e um alvo
    animado que caminha de assunto em assunto. Separar as tres coisas e o que
    permite descer nos pontos de interesse, subir nas transicoes e ainda
    manter o assunto enquadrado -- sem tocar na geometria do caminho.
    """
    pontos, ausentes = resolver_pontos(dados, centro_arena)
    entrada = no_de_entrada(pontos)
    saida = no_de_saida(pontos, mira)
    pontos, duracao, comprimentos, nos = ritmar(pontos, entrada, saida)

    curva = bpy.data.curves.new("PercursoCamera", type="CURVE")
    curva.dimensions = "3D"
    spline = curva.splines.new("BEZIER")
    spline.bezier_points.add(len(nos) - 1)

    for i, (x, y) in enumerate(nos):
        bp = spline.bezier_points[i]
        bp.co = (x, y, elevacao(x, y, centro_arena))
        bp.handle_left_type = bp.handle_right_type = "AUTO"

    obj_curva = bpy.data.objects.new("PercursoCamera", curva)
    col.objects.link(obj_curva)

    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = LENTE_MM
    cam = bpy.data.objects.new("Camera", cam_data)
    col.objects.link(cam)

    # Rig anda no caminho; a camera e filha e so cuida da altura. Sem
    # use_curve_follow: quem orienta a camera agora e o alvo, e deixar a
    # constraint girar o rig junto so faria a altura pender nos taludes.
    rig = bpy.data.objects.new("RigCamera", None)
    rig.empty_display_type = "ARROWS"
    rig.empty_display_size = 12.0
    col.objects.link(rig)

    seguir = rig.constraints.new("FOLLOW_PATH")
    seguir.target = obj_curva
    seguir.use_curve_follow = False
    seguir.use_fixed_location = True

    cam.parent = rig

    # Alvo: caminha de assunto em assunto e leva a mira junto. E o que faz o
    # bloco entrar em quadro pela frente em vez de passar por baixo da camera.
    alvo = bpy.data.objects.new("AlvoCamera", None)
    alvo.empty_display_type = "SPHERE"
    alvo.empty_display_size = 6.0
    col.objects.link(alvo)

    mirar = cam.constraints.new("TRACK_TO")
    mirar.target = alvo
    mirar.track_axis = "TRACK_NEGATIVE_Z"
    mirar.up_axis = "UP_Y"

    cena = bpy.context.scene
    cena.frame_start = 1
    cena.frame_end = max(2, round(duracao * FPS))

    # 1) Avanco no caminho: chega e para, chega e para.
    for p in pontos:
        seguir.offset_factor = p["u"]
        seguir.keyframe_insert("offset_factor", frame=p["quadro_chegada"])
        if p["quadro_saida"] != p["quadro_chegada"]:
            seguir.keyframe_insert("offset_factor", frame=p["quadro_saida"])
    suavizar_curvas(rig)

    # 2) Mira. No ultimo bloco o alvo vai para fora do portal: o plano final
    #    olha para fora enquanto atravessa o vao, como o cliente pediu.
    for i, p in enumerate(pontos):
        if i == len(pontos) - 1:
            destino = (saida[0], saida[1],
                       elevacao(saida[0], saida[1], centro_arena)
                       + ALTURA_ALVO_SAIDA)
        else:
            destino = (p["x"], p["y"],
                       elevacao(p["x"], p["y"], centro_arena)
                       + p.get("alvo", ALTURA_ALVO))
        alvo.location = destino
        alvo.keyframe_insert("location", frame=p["quadro_chegada"])
        if p["quadro_saida"] != p["quadro_chegada"]:
            alvo.keyframe_insert("location", frame=p["quadro_saida"])
    suavizar_curvas(alvo)

    # 3) Altura: valor do ponto na parada, valor aereo no meio do trecho.
    #    Trecho curto nao sobe -- subir e descer em dois segundos vira solucao,
    #    e o cliente nota.
    def chavear(quadro, altura):
        cam.location = (0.0, 0.0, altura)
        cam.keyframe_insert("location", frame=quadro)

    aereos = 0
    for i, p in enumerate(pontos):
        chavear(p["quadro_chegada"], p["altura"])
        if p["quadro_saida"] != p["quadro_chegada"]:
            chavear(p["quadro_saida"], p["altura"])
        if i + 1 < len(pontos):
            prox = pontos[i + 1]
            duracao_trecho = prox["t_chegada"] - p["t_saida"]
            if duracao_trecho >= TRECHO_MINIMO_AEREO:
                meio = round((p["quadro_saida"] + prox["quadro_chegada"]) / 2)
                chavear(meio, ALTURA_TRANSICAO)
                aereos += 1
    suavizar_curvas(cam)

    bpy.context.scene.camera = cam

    # Marcadores nomeados, para localizar cada bloco do roteiro na viewport.
    for p in pontos:
        m = bpy.data.objects.new(f"PT_{p['bloco']}_{p['nome']}", None)
        m.empty_display_type = "PLAIN_AXES"
        m.empty_display_size = 8.0
        m.location = (p["x"], p["y"],
                      elevacao(p["x"], p["y"], centro_arena) + p["altura"])
        col.objects.link(m)

    return pontos, ausentes, duracao, aereos, sum(comprimentos)


def configurar_render(cena, motor=None):
    # AgX puro deixa o verde do recinto lavado, e quadro lavado num painel de
    # 951.510 pixels significa titulo brigando com fundo. Punchy devolve o
    # contraste sem estourar o ceu de fim de tarde.
    ajustes = cena.view_settings
    try:
        ajustes.look = "AgX - Punchy"
    except TypeError:
        pass
    ajustes.exposure = -0.6

    cena.render.resolution_x = LARGURA_RENDER
    cena.render.resolution_y = ALTURA_RENDER
    cena.render.resolution_percentage = 100
    cena.render.fps = FPS
    cena.render.image_settings.file_format = "PNG"
    cena.render.film_transparent = False

    # Cycles por padrao. EEVEE e mais rapido, mas exige contexto grafico
    # (libEGL) e no ambiente remoto nao existe: a chamada nao falha na
    # atribuicao do motor, falha no meio do render. Em maquina com GPU passe
    # --motor BLENDER_EEVEE. Cycles em CPU custa ~90 s por quadro a 25% da
    # resolucao aqui; render final e trabalho de maquina local.
    cena.render.engine = motor or MOTOR_PADRAO


def construir_ceu(cena):
    """Ceu fisico de fim de tarde, com o disco solar no mesmo lugar do sol.

    Substitui a cor chapada anterior. O ideal continua sendo um HDRI real de
    golden hour (Poly Haven, CC0), mas no ambiente remoto o proxy bloqueia o
    dominio -- e um ceu Nishita com azimute e elevacao corretos entrega a maior
    parte do salto: gradiente do horizonte, ceu quente perto do sol e luz de
    preenchimento azul do lado oposto, que a cor chapada nunca deu.
    """
    mundo = bpy.data.worlds.new("Mundo")
    cena.world = mundo
    mundo.use_nodes = True
    nos = mundo.node_tree.nodes
    fundo = nos.get("Background")
    if not fundo:
        return mundo

    ceu = nos.new("ShaderNodeTexSky")
    ceu.location = (-300, 0)
    for tipo in ("NISHITA", "MULTIPLE_SCATTERING", "HOSEK_WILKIE"):
        try:
            ceu.sky_type = tipo
            break
        except TypeError:
            continue

    if hasattr(ceu, "sun_elevation"):
        ceu.sun_elevation = math.radians(ELEVACAO_SOL)
        # O azimute do projeto e medido do norte no sentido horario; o no do
        # ceu mede a partir de +X no sentido anti-horario. Dai a conversao.
        ceu.sun_rotation = math.radians(90.0 - AZIMUTE_SOL)
    if hasattr(ceu, "sun_disc"):
        ceu.sun_disc = True
    # Aerossol: pouca poeira. Muito aerossol lava o quadro inteiro de branco,
    # e num painel de 951.510 pixels quadro lavado significa titulo ilegivel.
    # Na 5.0 a propriedade se chama aerosol_density; ate a 4.x era dust_density.
    for atributo in ("aerosol_density", "dust_density"):
        if hasattr(ceu, atributo):
            setattr(ceu, atributo, 0.6)

    mundo.node_tree.links.new(ceu.outputs["Color"], fundo.inputs["Color"])
    fundo.inputs["Strength"].default_value = 1.0
    return mundo


def construir_luz(col):
    """Sol em golden hour, no mesmo azimute e elevacao do ceu."""
    dados_sol = bpy.data.lights.new("Sol", type="SUN")
    dados_sol.energy = 2.5
    dados_sol.angle = math.radians(0.526)
    sol = bpy.data.objects.new("Sol", dados_sol)
    # A lampada emite pelo -Z local. Inclinar X de (90 - elevacao) poe o raio
    # na altura certa; girar Z de (180 - azimute) o poe no rumo certo.
    sol.rotation_euler = (math.radians(90.0 - ELEVACAO_SOL), 0.0,
                          math.radians(180.0 - AZIMUTE_SOL))
    col.objects.link(sol)
    return sol


# --------------------------------------------------------------------------
# Conferencia

def render_conferencia(cena, destino, pontos, blocos=None):
    """Renderiza um quadro por bloco do roteiro, em baixa resolucao.

    Serve para checar enquadramento antes de gastar render longo: se a camera
    ve telhado de estande ou perde o assunto, aparece aqui em minutos.
    """
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    largura, altura = cena.render.resolution_x, cena.render.resolution_y
    porcento = cena.render.resolution_percentage
    cena.render.resolution_percentage = 25
    # Amostragem baixa: conferencia e sobre enquadramento, nao sobre ruido.
    if hasattr(cena, "eevee"):
        cena.eevee.taa_render_samples = 16
    if hasattr(cena, "cycles"):
        cena.cycles.samples = 32
        cena.cycles.use_denoising = True

    feitos = []
    for p in pontos:
        if blocos and p["bloco"] not in blocos:
            continue
        quadro = round((p["quadro_chegada"] + p["quadro_saida"]) / 2)
        cena.frame_set(quadro)
        caminho = destino / f"quadro-{p['bloco']}-{p['nome'].lower().replace(' ', '-')}.png"
        cena.render.filepath = str(caminho)
        bpy.ops.render.render(write_still=True)
        feitos.append(caminho)

    cena.render.resolution_percentage = porcento
    cena.render.resolution_x, cena.render.resolution_y = largura, altura
    return feitos


# --------------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dados", default="data/mapa_agroshow26.json")
    ap.add_argument("--relevo", default="data/dem_recinto.npz",
                    help="recorte de elevacao medida (scripts/fetch_dem.py)")
    ap.add_argument("--sem-relevo", action="store_true",
                    help="ignora a elevacao medida e usa so a bacia da planta")
    ap.add_argument("--out", default=None, help="salva um .blend no caminho")
    ap.add_argument("--conferencia", default=None,
                    help="renderiza um quadro por bloco do roteiro no diretorio")
    ap.add_argument("--motor", default=None,
                    help=f"motor de render; padrao {MOTOR_PADRAO}")
    ap.add_argument("--blocos", default=None,
                    help="restringe a conferencia a alguns blocos: --blocos 01,17,19")
    args = ap.parse_args(argv)

    dados = json.loads(Path(args.dados).read_text(encoding="utf-8"))
    # Origem no centro da prancha, para a cena nascer centrada no mundo.
    dados["_origem"] = (dados["prancha"]["largura_pt"] / 2,
                        dados["prancha"]["altura_pt"] / 2)

    limpar_cena()
    cols = criar_colecoes()
    centro = centro_da_arena(dados)
    if not args.sem_relevo:
        carregar_relevo(args.relevo)
        referenciar_relevo(centro)
    mats = criar_materiais()

    print("construindo terreno...")
    terreno = construir_terreno(dados, cols["BASE"], centro)
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

    n_est = construir_estacionamentos(dados, cols["BASE"], mats, centro)
    n_galp = construir_galpoes(dados, cols["EVENTO"], mats, centro)
    construir_leiloes(dados, cols["BASE"], mats, centro)
    n_pasto = construir_pista_julgamento(dados, cols["BASE"], mats, centro)
    n_faz = construir_fazendinha(dados, cols["EVENTO"], mats, centro)

    print("construindo portal, palco e camarotes...")
    pav1 = achar_zona(dados, "PAVILHÃO 1", 0)
    mira = para_mundo(pav1["x"], pav1["y"], dados["_origem"])
    construir_portal(dados, cols["EVENTO"], mats, centro, mira)
    construir_palco(dados, cols["EVENTO"], mats, centro)
    n_cam = construir_camarotes(dados, cols["EVENTO"], mats, centro)

    print("construindo percurso...")
    pontos, ausentes, duracao, aereos, extensao = construir_percurso(
        dados, cols["CAMERA"], centro, mira)

    construir_luz(cols["LUZ"])
    construir_ceu(bpy.context.scene)
    configurar_render(bpy.context.scene, args.motor)

    larg_m = dados["prancha"]["largura_pt"] * ESCALA + 2 * EXTENSAO_ENTORNO
    prof_m = dados["prancha"]["altura_pt"] * ESCALA + 2 * EXTENSAO_ENTORNO
    provisorios = [p["nome"] for p in pontos if p.get("provisorio")]

    print("\n" + "=" * 58)
    print(f"  escala .............. {ESCALA} m/pt")
    print(f"  extensao do terreno . {larg_m:.0f} x {prof_m:.0f} m "
          f"(prancha + {EXTENSAO_ENTORNO:.0f} m de entorno)")
    print(f"  pavilhoes ........... {n_pav}")
    print(f"  estandes ............ {cont['instanciado']} instanciados "
          f"+ {cont['proprio']} proprios")
    print(f"  estacionamentos ..... {n_est}")
    print(f"  galpoes da faixa norte {n_galp}")
    print(f"  camarotes ........... {n_cam} modulos, sem arquibancada")
    print(f"  recinto de leiloes .. estrela de 8 pontas, {2*RAIO_LEILOES:.0f} m")
    print(f"  pista de julgamentos  {PISTA_JULGAMENTO[0]:.0f} x "
          f"{PISTA_JULGAMENTO[1]:.0f} m, {n_pasto} pecas")
    print(f"  fazendinha .......... {FAZENDINHA[0]:.0f} x {FAZENDINHA[1]:.0f} m "
          f"com porteira, {n_faz} pecas")
    print(f"  pontos do percurso .. {len(pontos)} de {len(PERCURSO)}")
    print(f"  extensao do percurso  {extensao:.0f} m")
    print(f"  trechos aereos ...... {aereos}")
    print(f"  camera .............. {LENTE_MM:.0f} mm, "
          f"{min(p['altura'] for p in pontos):.0f}-{ALTURA_TRANSICAO:.0f} m")
    print(f"  render .............. {LARGURA_RENDER}x{ALTURA_RENDER} "
          f"({LARGURA_RENDER/ALTURA_RENDER:.0f}:1)")
    print(f"  animacao ............ {bpy.context.scene.frame_end} quadros "
          f"({duracao:.0f} s a {FPS} fps)")
    print(f"  sol ................. azimute {AZIMUTE_SOL:.0f}°, "
          f"elevacao {ELEVACAO_SOL:.0f}°")
    if RELEVO:
        m = RELEVO["meta"]
        print(f"  relevo medido ....... {m['metros_por_pixel']:.1f} m/px, "
              f"origem {m['dado_de_origem'].split(',')[0]}")
        print(f"  mistura planta/dem .. {MISTURA_RELEVO[0]:.0f} a "
              f"{MISTURA_RELEVO[1]:.0f} m do centro da arena")
    else:
        print("  relevo medido ....... ausente, so a bacia da planta")
    print(f"  patamares ........... arena 0 m -> shows {PATAMARES[2][2]} m "
          f"-> anel {PATAMARES[4][2]} m -> plato {PATAMARES[6][2]} m")
    if provisorios:
        print("  POSICAO PROVISORIA (confirmar com o cliente):")
        for nome in provisorios:
            print(f"     {nome}")
    if ausentes:
        print("  AUSENTES no percurso:")
        for nome, rotulo in ausentes:
            print(f"     {nome} -> rotulo {rotulo!r} nao encontrado")
    print("=" * 58)

    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.out).resolve()))
        print(f"\nsalvo: {args.out}")

    if args.conferencia:
        print("\nrenderizando quadros de conferencia...")
        blocos = {b.strip() for b in args.blocos.split(",")} if args.blocos else None
        feitos = render_conferencia(bpy.context.scene, args.conferencia, pontos,
                                    blocos)
        print(f"  {len(feitos)} quadros em {args.conferencia}")


if __name__ == "__main__":
    main()
