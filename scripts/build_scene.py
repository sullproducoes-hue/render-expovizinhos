#!/usr/bin/env python3
"""
Gera a cena 3D do Parque de Exposicoes de Dois Vizinhos para a AGROSHOW 2026,
a partir da planta extraida em data/mapa_agroshow26.json.

Constroi terreno, os 134 estandes instanciados, os pavilhoes, a arena e as
cameras dos planos do filme (data/planos.json, resolvidas por scripts/planos.py).
Deixa tudo em colecoes separadas para que a camada permanente (terreno,
pavilhoes) sobreviva a troca da camada do evento (estandes, palco, sinalizacao)
no ano seguinte.

Uso:
    blender --background --python scripts/build_scene.py -- --out cena.blend
    blender --background --python scripts/build_scene.py -- --relevo dem.png

Ou com o modulo bpy instalado (pip install bpy):
    python3 scripts/build_scene.py --out cena.blend

Constroi so a regiao de um plano (ou lista de planos), para caber em GPU de
8-12 GB sem carregar o recinto inteiro:

    python3 scripts/build_scene.py --plano P19 --out out/P19.blend

Exporta para o Twinmotion (Plano A da proposta de render). O FBX carrega
BASE + EVENTO + cones da coleção MARCOS_CAMERA -- um cone por ponta de plano,
porque o Twinmotion importa geometria mas nao importa camera animada:

    python3 scripts/build_scene.py --export-fbx out/cena.fbx

Escala, bacia da arena e leitura da planta vivem em scripts/terreno.py -- e a
fonte unica, compartilhada com scripts/planos.py. Escala 0,5611 m/pt, derivada
da propria planta. NAO CONFERIDA com medida real em campo.
"""

import argparse
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpy
import bmesh
from mathutils import Matrix, Vector

import avulsas
import cobertura_entorno
import estimativas
import estruturas
import letreiros
import mobiliario
import planos as planos_mod
import povoamento
import sol
import relevo_entorno
import terreno
import texturas

# --------------------------------------------------------------------------
# Constantes proprias do gerador (geometria e bacia vivem em terreno.py)

LARGURA_RENDER = 2760    # 2:1, 2x o nativo do painel P2,9 (1379x690)
ALTURA_RENDER = 1380

# ESTIMADO fica separada de proposito: e a colecao do que NAO foi medido, e
# poder esconder ela inteira no .blend e o que deixa ver, num clique, quanto da
# cena ainda e palpite. Ver data/estimativas.json e docs/FOOTPRINTS.md.
COLECOES = ["BASE", "EVENTO", "ESTIMADO", "CAMERA", "MARCOS_CAMERA", "LUZ"]

RAIZ = Path(__file__).resolve().parent.parent

# Rumo das estruturas, em graus. Nao sao chute: saem do angulo com que a planta
# escreve o rotulo de cada uma -- `angulo_graus` em data/locais.json. O rotulo
# de um galpao e escrito no eixo dele.
# RUMO_PAVILHOES nao e mais usado para construir: desde 14/08 o rumo de cada
# pavilhao vem medido em data/footprints.json e passa por `azimute_para_giro`.
# Fica aqui porque `conferir_norte.py` imprime este valor como referencia.
RUMO_PAVILHOES = 341.0   # = azimute 108,4 depois da conversao. Ver azimute_para_giro
RUMO_PORTAL = 73.0       # de frente para quem chega pela Dorvalino Tosi
RUMO_PALCO = 334.0       # de frente para a arena

RUMO_CONCHA = 116.6
"""Rumo de mapa do footprint `PALCO PALCO`, medido do desenho.

`footprints.json` marca `rumo_confiavel: false` neste item -- o preenchimento
da mancha e 0,816 e a particao veio de watershed. Entra assim mesmo porque a
alternativa e chutar, e fica DITO: se a concha aparecer torta contra o aereo,
e daqui que vem."""

ESPERA_PALCO = (520.0, -285.0)
"""Onde o palco DE EVENTO passa a ficar: ao lado da AREA_DE_ESPERA (520, -240),
45 m ao sul para nao encostar nas 11 pecas que ja estao la."""


# --------------------------------------------------------------------------
# Utilitarios de cena

def limpar_cena():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def criar_colecoes():
    for nome in COLECOES:
        col = bpy.data.collections.new(nome)
        bpy.context.scene.collection.children.link(col)
    return {c.name: c for c in bpy.data.collections}


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

# (nome, cor base RGB, rugosidade, metalico)
#
# Ainda sao cores chapadas -- o PBR calibrado pelas provas do footage e a
# Rodada 2. O que mudou aqui e que as superficies deixaram de ser cinco: o
# portal era fachada de tabua saindo como metal escovado, porque `MAT_MADEIRA`
# simplesmente nao existia e o dispatch mandava tudo para MAT_PAVILHAO.
MATERIAIS = {
    # MEDIDOS no footage do proprio recinto em 14/08, por scripts/medir_materiais.py
    # -- quadro de golden hour com todas as classes juntas, cor-base tirada
    # dividindo pelo iluminante que a lona branca entrega. Ver
    # data/materiais-medidos.json e docs/MATERIAIS-referencia.md.
    #
    # O achado que muda o quadro: **a grama do recinto nao e verde de lavoura.**
    # O controle do metodo foi amostrar a lavoura ao fundo, que qualquer um olha
    # e diz que e verde -- ela sai com G > R (0.233 / 0.272 / 0.127). A grama do
    # recinto, no mesmo quadro e na mesma luz, e verde-oliva escura e bem menos
    # clara: 0.129 de albedo, dentro da faixa fisica da grama (0,10-0,25).
    #
    # Cuidado que custou um render: a primeira amostra caiu na grama PISADA da
    # beira da alameda (0.278 / 0.235 / 0.108) e, chapada sobre 170.000 m², ela
    # deixou o recinto inteiro com cara de deserto. Trecho gasto e desgaste, nao
    # e a cor do campo -- ele volta como variacao de textura, nao como cor base.
    "MAT_TERRENO":  ((0.129, 0.124, 0.037), 0.95, 0.0),   # medido: grama sa
    "MAT_LONA":     ((0.750, 0.750, 0.750), 0.55, 0.0),   # ancora: PVC branco 0,75
    "MAT_PAVILHAO": ((0.55, 0.56, 0.58), 0.45, 0.3),
    "MAT_ARENA":    ((0.266, 0.187, 0.155), 0.90, 0.0),   # medido: chao batido
    "MAT_ASFALTO":  ((0.09, 0.09, 0.10), 0.80, 0.0),

    # tabua de celeiro: marrom-tabaco, fosca, NADA de metalico
    "MAT_MADEIRA":  ((0.21, 0.11, 0.055), 0.85, 0.0),
    # telha trapezoidal branca/galvanizada nova -- e o que o footage mostra em
    # todo o recinto; telha oxidada seria proposta, nao dado (MATERIAIS-referencia.md)
    #
    # ESTA NAO SE MEDE pelo metodo dos outros, e o proprio numero avisou: a
    # medicao ESTOUROU (albedo 1,00 / 1,00 / 0,95, no teto da escala). Telha
    # metalica reflete o CEU de forma especular, entao o que a camera ve nao e
    # a cor dela -- e o ceu. Fica o cinza galvanizado com metallic 0,55, que e
    # o que faz o reflexo aparecer no render em vez de vir pintado.
    "MAT_TELHA":    ((0.62, 0.63, 0.64), 0.40, 0.55),
    "MAT_DECK":     ((0.30, 0.22, 0.15), 0.75, 0.0),
    "MAT_GRADIL":   ((0.86, 0.87, 0.88), 0.35, 0.20),
    "MAT_TRELICA":  ((0.72, 0.73, 0.75), 0.32, 0.85),
    "MAT_PRETO":    ((0.03, 0.03, 0.035), 0.60, 0.0),
    # saibro das vias internas: o footage diz "asfalto -> saibro -> cascalho".
    # 36 vias internas pretas num campo verde denunciam sozinhas.
    # Medido em 14/08 e bem mais escuro do que eu tinha posto (0,34 -> 0,14):
    # piso solto de area de maquina, com oleo e terra pisada.
    "MAT_SAIBRO":   ((0.136, 0.098, 0.070), 0.92, 0.0),

    # copa: MEDIDA, e custou tres recortes. Os dois primeiros devolveram copa
    # MAIS CLARA que o gramado (0,35 e 0,43), o que nao existe -- um pegava vao
    # de ceu entre as copas, o outro pegava o veu do flare perto do sol. Longe
    # do sol e em massa fechada ela da 0,132 / 0,154 / 0,045: verde de verdade
    # (G > R), no mesmo patamar da grama e um pouco mais verde.
    "MAT_COPA":     ((0.132, 0.154, 0.045), 0.88, 0.0),
    # tronco NAO e medido: no quadro aereo ele tem poucos pixels e esta sob a
    # copa. Casca de arvore de parque, faixa fisica 0,08-0,12.
    "MAT_TRONCO":   ((0.095, 0.078, 0.062), 0.90, 0.0),

    # ---- A PALETA DO PARQUE, medida no footage de 13/08 e aprovada por ele em
    # 15/08 (*"a paleta de cores esta ok"*). scripts/medir_materiais_quinta.py,
    # data/materiais-quinta.json.
    #
    # O metodo NAO e o mesmo de 14/08, e a diferenca esta registrada em D018:
    # aquele footage e golden hour e a ancora foi a lona ao sol; este e dia
    # encoberto, e em ceu encoberto a irradiancia depende da ORIENTACAO da
    # superficie -- telhado ve o hemisferio inteiro, parede ve metade. Ancorar
    # no telhado devolveu tijolo com albedo 1,000 no vermelho. Aqui o
    # iluminante e MEDIDO no proprio ceu do quadro.
    "MAT_TIJOLO":        ((0.564, 0.073, 0.071), 0.85, 0.0),  # medido
    "MAT_CHAPA_AZUL":    ((0.036, 0.274, 0.592), 0.42, 0.45),  # medido
    "MAT_COLUNA_AZUL":   ((0.018, 0.060, 0.165), 0.78, 0.0),  # medido
    "MAT_CHAPA_PORTAO":  ((0.066, 0.077, 0.098), 0.45, 0.40),  # medido
    "MAT_TERRA_BATIDA":  ((0.097, 0.033, 0.016), 0.93, 0.0),  # medido

    # DECLARADO POR ELE em 15/08: *"e concreto envelhecido, o albedo o daquela
    # coluna"*. Faixa de mercado 0,20-0,30; 0,25 e o meio. Nao e medicao minha
    # -- nas mangueiras nao ha ceu medivel nem superficie de refletancia
    # conhecida, e sem uma palavra dele o quadro nao fechava.
    "MAT_CONCRETO":      ((0.250, 0.250, 0.250), 0.88, 0.0),

    # ---- PROPOSTA, nao medida, e o motivo e um so: o video `1 (4)` e o UNICO
    # dos dezessete filmado em golden hour, e o metodo do ceu (D018) so vale em
    # dia encoberto. Estas tres sao leitura de olho sobre quadro quente, e ele
    # pode trocar qualquer uma numa linha.
    "MAT_CONCHA_AZUL":   ((0.045, 0.115, 0.330), 0.55, 0.0),  # PROPOSTA
    "MAT_CONCHA_CLARO":  ((0.600, 0.585, 0.545), 0.80, 0.0),  # PROPOSTA
    # tercas e rufos da cobertura. Nao entrou por medicao: so existe em peca de
    # 20 a 40 px, e croma 4:2:0 de peca fina e mistura inventada (D021).
    "MAT_ESTRUTURA_VERMELHA": ((0.190, 0.055, 0.040), 0.82, 0.0),  # PROPOSTA
}


def criar_materiais():
    """Materiais base. Sao ponto de partida para o acabamento -- troque por
    PBR com textura (Poly Haven, ambientCG: ambos CC0) na etapa de lapidacao.
    No terreno, antes de textura nova: ruido de baixa frequencia (escala 1-3)
    em Overlay a 0,2-0,35 sobre a cor base quebra o padrao repetido visto do
    alto -- e o que mais entrega CG num terreno de 800 m, nao a textura."""
    feitos = {}
    com_textura = []
    for nome, (cor, rug, met) in MATERIAIS.items():
        mat = bpy.data.materials.new(nome)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (*cor, 1.0)
            bsdf.inputs["Roughness"].default_value = rug
            if "Metallic" in bsdf.inputs:
                bsdf.inputs["Metallic"].default_value = met
        # cor de viewport: o Principled so vale no render. Sem isto a cena
        # abre TODA CINZA no modo solido -- que e como o Natan vai olhar o
        # .blend -- e o Workbench (usado na conferencia de posicao) tambem.
        mat.diffuse_color = (*cor, 1.0)
        mat.roughness = rug
        mat.metallic = met
        if nome == "MAT_COPA":
            _variar_por_instancia(mat, bsdf, cor)
        if nome == "MAT_TERRENO":
            _manchar_terreno(mat, bsdf)
        # Textura PBR CC0 por cima, onde data/texturas.json declara. Vem DEPOIS
        # da mancha do terreno de proposito: a mancha decide a cor (duas gramas
        # medidas) e a textura decide relevo e brilho. Uma nao pisa na outra --
        # o contrato proibe biblioteca virar albedo do terreno.
        if texturas.aplicar(mat, bsdf, nome, cor, rug):
            com_textura.append(nome)
        feitos[nome] = mat

    if com_textura:
        print(f"textura PBR ....... {len(com_textura)} materiais: "
              f"{', '.join(sorted(com_textura))}")
    return feitos


# As duas gramas MEDIDAS no footage (scripts/medir_materiais.py). Nao sao duas
# invencoes: sao dois trechos reais do mesmo quadro, na mesma luz.
GRAMA_SA = (0.129, 0.124, 0.037)
GRAMA_PISADA = (0.278, 0.235, 0.108)


def _manchar_terreno(mat, bsdf):
    """Quebra a cor chapada do terreno com as DUAS gramas medidas.

    O comentario de `criar_materiais` ja dizia isto desde o inicio e ninguem
    tinha feito: o que mais entrega CG num terreno de 800 m nao e falta de
    textura fina, e cor uniforme -- de cima, 170.000 m² de um verde so leem como
    feltro. A vista de topo de 14/08 mostra isso de olho fechado.

    O que entra na mistura nao e invencao: sao as DUAS amostras de grama do
    mesmo quadro do footage. A sa (albedo 0,129) e a pisada da beira da alameda
    (0,278), aquela que sozinha tinha deixado o recinto com cara de deserto.
    Como mancha, ela e exatamente o que faltava -- capim gasto onde passa gente.

    Duas frequencias, porque uma so volta a ser padrao: manchas largas de ~60 m
    (onde o gado e o publico circulam) e quebra de ~8 m por cima.
    """
    nt = mat.node_tree

    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-1100, -200)

    largo = nt.nodes.new("ShaderNodeTexNoise")
    largo.location = (-900, -80)
    largo.inputs["Scale"].default_value = 0.017      # ~60 m de periodo
    largo.inputs["Detail"].default_value = 3.0
    largo.inputs["Roughness"].default_value = 0.55

    fino = nt.nodes.new("ShaderNodeTexNoise")
    fino.location = (-900, -320)
    fino.inputs["Scale"].default_value = 0.13        # ~8 m
    fino.inputs["Detail"].default_value = 2.0

    soma = nt.nodes.new("ShaderNodeMix")
    soma.data_type = "FLOAT"
    soma.location = (-700, -200)
    soma.inputs["Factor"].default_value = 0.35       # o fino so tempera o largo

    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.location = (-520, -200)
    # CALIBRADA em 14/08 a noite, e ela estava mentindo. O comentario dizia
    # "mais campo que desgaste" e o valor 0,38/0,72 entregava meio a meio: a cor
    # media do recinto saia 0,192 / 0,175 / 0,076 -- 42% do caminho ate a grama
    # PISADA -- e o p05 dava 0,151, ou seja, em lugar NENHUM o gramado chegava
    # aos 0,129 medidos no footage. E a mesma falha que ja tinha deixado a cena
    # "com cara de deserto", em dose menor e por isso mais dificil de ver.
    #
    # Medido por render ortografico de topo com mundo branco e view transform
    # Standard (o pixel vira o albedo), varrendo a posicao da rampa:
    #
    #   0,38 / 0,72 -> media 0,1923   42,5% de desgaste   <- estava aqui
    #   0,50 / 0,85 -> media 0,1508   14,6%               <- esta aqui
    #   0,58 / 0,90 -> media 0,1427    9,2%
    #   0,65 / 0,95 -> media 0,1416    8,5%  (satura: o ruido fino nao deixa cair mais)
    #
    # 0,50/0,85 e o unico ponto da varredura que atende as duas coisas ao mesmo
    # tempo: a grama SA domina (a media encosta nos 0,129 medidos) e a mancha de
    # passagem continua existindo. Passar disso a mancha morre sem baratear nada.
    rampa.color_ramp.elements[0].position = 0.50
    rampa.color_ramp.elements[1].position = 0.85

    sa = nt.nodes.new("ShaderNodeRGB")
    sa.location = (-520, 80)
    sa.outputs[0].default_value = (*GRAMA_SA, 1.0)

    pisada = nt.nodes.new("ShaderNodeRGB")
    pisada.location = (-520, -60)
    pisada.outputs[0].default_value = (*GRAMA_PISADA, 1.0)

    mistura = nt.nodes.new("ShaderNodeMix")
    mistura.data_type = "RGBA"
    mistura.location = (-300, -60)

    nt.links.new(coord.outputs["Object"], largo.inputs["Vector"])
    nt.links.new(coord.outputs["Object"], fino.inputs["Vector"])
    nt.links.new(largo.outputs["Fac"], soma.inputs[2])   # A (float)
    nt.links.new(fino.outputs["Fac"], soma.inputs[3])    # B (float)
    nt.links.new(soma.outputs[0], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], mistura.inputs["Factor"])
    nt.links.new(sa.outputs[0], mistura.inputs[6])       # A (RGBA)
    nt.links.new(pisada.outputs[0], mistura.inputs[7])   # B (RGBA)
    nt.links.new(mistura.outputs[2], bsdf.inputs["Base Color"])


def _variar_por_instancia(mat, bsdf, cor):
    """Faz cada arvore ter a sua cor, sem criar um material por arvore.

    As 232 arvores compartilham UMA malha e UM material -- e por isso a mata
    saiu como uma massa unica, do mesmo verde do primeiro ao ultimo tufo. Mata
    de verdade nao e monocromatica.

    `Object Info > Random` da um numero fixo por instancia; ele entra num Mix
    que clareia ou escurece a cor base em ate 30%. Custo de render: nenhum
    mensuravel -- e um no, nao geometria -- e a malha continua uma so.
    """
    nt = mat.node_tree
    info = nt.nodes.new("ShaderNodeObjectInfo")
    info.location = (-620, -120)

    escuro = nt.nodes.new("ShaderNodeRGB")
    escuro.outputs[0].default_value = (cor[0] * 0.70, cor[1] * 0.70,
                                       cor[2] * 0.78, 1.0)
    escuro.location = (-420, -40)

    claro = nt.nodes.new("ShaderNodeRGB")
    claro.outputs[0].default_value = (min(cor[0] * 1.30, 1.0),
                                      min(cor[1] * 1.28, 1.0),
                                      min(cor[2] * 1.15, 1.0), 1.0)
    claro.location = (-420, -220)

    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.location = (-220, -120)
    nt.links.new(info.outputs["Random"], mix.inputs["Factor"])
    nt.links.new(escuro.outputs[0], mix.inputs[6])   # A (RGBA)
    nt.links.new(claro.outputs[0], mix.inputs[7])    # B (RGBA)
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])


def vestir_com_a_paleta(col, mats):
    """Poe a paleta MEDIDA nos predios que a planta desenha de verdade.

    Ate 15/08 os predios do recinto sairam todos em `MAT_PAVILHAO`, um cinza
    (0,55 / 0,56 / 0,58) que ninguem mediu e que eu inventei numa sessao
    anterior. E exatamente o *design system default* que o `CLAUDE.md` proibe --
    decisao estetica que ninguem declarou, repetida em 37 objetos.

    Agora ha medida: `data/materiais-quinta.json`, tirada do footage de 13/08 do
    proprio recinto, com o iluminante medido no ceu do quadro (D018) e aprovada
    por ele em 15/08 -- *"a paleta de cores esta ok"*.

    ## Por que dois materiais por predio, e nao um

    Caixa com um material so pinta o TELHADO de tijolo. E o filme e quase todo
    aereo: o que a camera mais ve destes volumes e a agua de cima. Entao a caixa
    ganha dois slots e a face de cima vai para o telhado -- `normal.z` decide,
    nao o nome do objeto (nome de objeto nao decide material neste arquivo, e a
    correcao do portal de 14/08 esta escrita logo abaixo).

    ## O que sustenta a escolha, e o que NAO entra

    - **parede = `MAT_TIJOLO`.** `1 (16)` percorre os pavilhoes por dentro e por
      fora e mostra alvenaria de tijolo vermelho; `1 (17)` mostra a mesma
      alvenaria de perto e de longe. Vermelho + azul se repete em tres videos --
      e identidade construida do parque, nao gosto meu.
    - **telhado = `MAT_TELHA`.** O aereo nadir `1 (2)` mostra as aguas CLARAS
      vistas de cima. O azul medido existe (`MAT_CHAPA_AZUL`), mas ele e de UM
      galpao especifico do `1 (17)`; espalhar azul por todos seria inventar.
    - **so quem tem `footprint_medido`.** Sao os predios que a planta desenha de
      verdade. As zonas da colecao ESTIMADO continuam no cinza de propósito:
      elas SAO estimativa, precisam ler como tal, e vivem numa colecao que ele
      esconde num clique.
    - **cobertura sobre pilar nao entra.** Ela nao tem parede; o material dela
      ja esta declarado e continua valendo.

    Devolve quantos predios foram vestidos.
    """
    parede, telhado = mats["MAT_TIJOLO"], mats["MAT_TELHA"]
    n = 0
    for o in col.objects:
        if o.type != "MESH" or not o.get("footprint_medido"):
            continue
        if o.get("material") in (None, "MAT_LONA", "MAT_GRADIL", "MAT_ASFALTO"):
            continue
        me = o.data
        me.materials.clear()
        me.materials.append(parede)
        me.materials.append(telhado)
        for f in me.polygons:
            f.material_index = 1 if f.normal.z > 0.7 else 0
        o["paleta"] = "medida em 13/08 -- parede MAT_TIJOLO, telhado MAT_TELHA"
        n += 1
    return n


def aplicar(obj, mat):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.clear()
        obj.data.materials.append(mat)


# --------------------------------------------------------------------------
# Corte por regiao -- o que segura a cena em 8-12 GB de VRAM

def bbox_dos_planos(planos_sel, centro, margem=80.0):
    """Caixa envolvente (x0, x1, y0, y1) das cameras e miras dos planos dados.

    Margem de 80 m cobre o maior estande (100 m², lado 10 m) mais folga de
    enquadramento. Usada para construir so o que aparece nos planos pedidos
    -- decisivo numa GPU de 8-12 GB, que nao segura o recinto inteiro vestido.
    """
    xs, ys = [], []
    for p in planos_sel:
        for t in (0.0, 1.0):
            pos, mira = planos_mod.amostra(p, t, centro)
            xs += [pos[0], mira[0]]
            ys += [pos[1], mira[1]]
    return (min(xs) - margem, max(xs) + margem,
            min(ys) - margem, max(ys) + margem)


def dentro(bbox, x, y):
    if bbox is None:
        return True
    x0, x1, y0, y1 = bbox
    return x0 <= x <= x1 and y0 <= y <= y1


# --------------------------------------------------------------------------
# Construcao

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

    Constroi sempre a prancha inteira, mesmo com --plano ativo: e uma unica
    malha, o custo de esculpir alguns vertices a mais e desprezivel perto do
    que --plano economiza em estandes e pavilhoes instanciados.

    Com --relevo, um heightmap em escala de cinza entra por deslocamento por
    cima da bacia -- util para o entorno (vale, encostas distantes), onde os
    30 m de resolucao bastam. Para o recinto, quem manda e a bacia.
    """
    larg = dados["prancha"]["largura_pt"] * terreno.ESCALA * 1.2
    prof = dados["prancha"]["altura_pt"] * terreno.ESCALA * 1.2
    div = 400

    bpy.ops.mesh.primitive_grid_add(x_subdivisions=div, y_subdivisions=div,
                                    size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Terreno"
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)

    for v in obj.data.vertices:
        v.co.x *= larg
        v.co.y *= prof
        v.co.z = terreno.elevacao(v.co.x, v.co.y, centro_arena)

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


def _material_do_entorno(mats, raio):
    """Material proprio do entorno: cobertura do solo REAL, com cor MEDIDA.

    Se `cobertura_entorno.py` nao tiver rodado, devolve o MAT_TERRENO de sempre
    -- o entorno volta a ser verde uniforme, e o build avisa.

    O par de fontes e o que faz isto valer: o ESA WorldCover (10 m, CC-BY, sem
    chave) diz O QUE e cada pedaco de chao -- lavoura, mata, campo, agua, cidade
    --, e `data/materiais-medidos.json` diz QUE COR aquilo tem naquela luz. A
    lavoura em especial usa a amostra `campo`, que tinha sido medida so como
    controle do metodo e nunca tinha virado material.
    """
    png = cobertura_entorno.caminho()
    if png is None:
        print("  entorno: SEM cobertura do solo -- verde uniforme. Rode "
              "`python scripts/cobertura_entorno.py`")
        return mats["MAT_TERRENO"]

    meta = json.loads((RAIZ / "data" / "cobertura-entorno.json").read_text(
        encoding="utf-8"))
    lado = float(meta["lado_m"])

    mat = bpy.data.materials.new("MAT_ENTORNO")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.95

    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.location = (-900, 0)
    mapa = nt.nodes.new("ShaderNodeMapping")
    mapa.location = (-700, 0)
    # o PNG cobre `lado` metros centrados na origem; a UV vai de 0 a 1
    for eixo in range(2):
        mapa.inputs["Scale"].default_value[eixo] = 1.0 / lado
        mapa.inputs["Location"].default_value[eixo] = 0.5
    nt.links.new(coord.outputs["Object"], mapa.inputs["Vector"])

    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.location = (-480, 0)
    tex.image = bpy.data.images.load(str(png), check_existing=True)
    tex.extension = "EXTEND"   # fora do PNG repete a borda; REPEAT espelharia
    # a cidade do outro lado do mapa
    nt.links.new(mapa.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    # cor de viewport: a media do censo, so para o modo solido nao abrir cinza
    mat.diffuse_color = (0.18, 0.19, 0.09, 1.0)
    mat.roughness = 0.95

    censo = meta["censo"]
    print("  entorno: cobertura do solo REAL -- " + ", ".join(
        f"{n} {c['fracao_pct']:.0f}%" for n, c in list(censo.items())[:4]))
    return mat


def construir_entorno(col, centro, mats, raio=None):
    """Terreno regional que fecha o horizonte -- agora com o relevo REAL.

    Sem isto o terreno acaba em 969 x 545 m e, com o sol a 10 graus e a camera
    baixa, aparece CEU ABAIXO DA LINHA DO HORIZONTE -- o tell classico de CG,
    que mata o quadro por melhor que esteja a luz.

    Fora de r=150 m do centro da arena, `terreno.elevacao` e constante em 10 m
    (ver PATAMARES), entao o disco casa com a borda sem costura. Fica 5 cm
    abaixo para nao brigar em z com o terreno detalhado.

    **Deixou de ser liso em 14/08.** `scripts/relevo_entorno.py` baixa o DEM
    publico (AWS Terrain Tiles / SRTM, sem chave) e grava o desnivel em relacao
    ao sitio; aqui ele entra por cima da elevacao da planta. O sitio esta a
    602 m e a regiao cai ate -435 m dentro de 12 km -- o terreno DESPENCA para
    o norte, e e isso que da perfil ao horizonte em vez de linha de regua.

    O DEM foi conferido contra o opentopodata (SRTM 30 m, outra fonte) em 5
    pontos ao longo de 16 km: bate dentro de +-5 m.

    Se o DEM nao tiver sido baixado, cai no disco chapado de antes e AVISA --
    a cena continua saindo, so que com a limitacao antiga e dita em voz alta.
    """
    # Grid grosso que usa a MESMA funcao de elevacao do terreno detalhado, e
    # fica 5 cm abaixo dele. Assim os dois casam sem costura e sem z-fighting:
    # onde o detalhado existe ele cobre, e fora dele o entorno aparece.
    #
    # A primeira versao disto era um disco chapado em z=10 (o nivel do plato).
    # Estava errado e escondia a cena: a bacia da arena e ESCAVADA ate z=0,
    # entao o disco passava por cima dela e da metade do terreno. So apareceu
    # na conferencia de topo -- de frente, com a camera baixa, nao dava para ver.
    dem = relevo_entorno.carregar()
    if dem is None:
        grid_dem, mpp, lado = None, None, None
        raio = raio or 3000.0
        div = 120
        print("  entorno: SEM relevo real -- disco chapado de 3 km. Rode "
              "`python scripts/relevo_entorno.py` para o horizonte ganhar perfil")
    else:
        grid_dem, mpp, lado = dem
        # o disco vai ate onde o DEM vai, e nem um metro alem: fora dele o
        # desnivel seria zero e voltaria a reta que estamos consertando
        raio = raio or lado / 2.0
        # 34 m/px de DEM em 24 km pedem malha fina o bastante para a silhueta
        # do morro nao virar escada. 500 divisoes = 48 m por quad.
        div = 500

    bpy.ops.mesh.primitive_grid_add(x_subdivisions=div, y_subdivisions=div,
                                    size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Entorno"
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)

    for v in obj.data.vertices:
        v.co.x *= raio * 2.0
        v.co.y *= raio * 2.0
        z = terreno.elevacao(v.co.x, v.co.y, centro) - 0.05
        if grid_dem is not None:
            # o desnivel ja vem amortecido a zero dentro de 600 m do centro,
            # entao a soma nao toca no recinto medido
            z += relevo_entorno.altura(grid_dem, mpp, v.co.x, v.co.y)
        v.co.z = z

    mat_entorno = _material_do_entorno(mats, raio)
    # entra no dicionario: o despacho do final do main() reaplica material pelo
    # NOME que o objeto declara, e um nome fora do dicionario derruba o build
    mats[mat_entorno.name] = mat_entorno
    aplicar(obj, mat_entorno)
    # declara tambem na propriedade, senao o dispatch do main o acusa de "sem
    # material declarado" a cada build -- aviso falso que ja despistou uma vez
    obj["material"] = mat_entorno.name
    if grid_dem is not None:
        obj["nota"] = (f"horizonte ate {raio/1000:.1f} km com relevo REAL "
                       f"(AWS Terrain Tiles/SRTM, conferido contra opentopodata "
                       f"em +-5 m). Falta cobertura do solo: lavoura e mata "
                       f"regional ainda saem com a cor da grama do recinto")
        print(f"  entorno: relevo real, {raio/1000:.1f} km de raio, "
              f"{div}x{div} ({(div+1)**2//1000}k vertices)")
    else:
        obj["nota"] = ("horizonte ate 3 km, disco CHAPADO -- limitacao "
                       "declarada, ver scripts/relevo_entorno.py")
    return obj


def orientar_estandes(postos):
    """Alinha cada estande ao eixo da sua fileira.

    Estandes vizinhos numa fileira compartilham o eixo da fileira, entao a
    direcao ate o vizinho mais proximo serve de referencia. Isso resolve tanto
    as grades ortogonais quanto os arcos concentricos da arena, sem precisar
    tratar os dois casos separadamente.

    Com --plano ativo, so os estandes dentro da bbox entram nesta lista -- a
    orientacao de um estande na borda do corte pode ficar imprecisa se o
    vizinho mais proximo dele ficou de fora. Aceitavel: e um corte de trabalho,
    nao a build de entrega.
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


def construir_estandes(dados, col, centro_arena, bbox=None):
    """Instancia os estandes a partir de dois modulos base.

    39 estandes de 100 m² e 35 de 25 m² sao instancias, nao modelagens
    separadas. Os demais recebem caixa propria dimensionada pela area.
    """
    modulos = {}
    for area, lado in ((100.0, 10.0), (25.0, 5.0)):
        base = caixa(f"MODULO_{int(area)}m2", lado, lado, terreno.ALTURA_ESTANDE, col)
        base.hide_render = base.hide_viewport = True
        modulos[area] = base

    origem = dados["_origem"]
    contagem = {"instanciado": 0, "proprio": 0, "fora_do_corte": 0}
    postos = []

    for st in dados["estandes"]:
        area = st.get("area_m2")
        if area is None:
            continue
        x, y = terreno.para_mundo(st["x"], st["y"], origem)
        if not dentro(bbox, x, y):
            contagem["fora_do_corte"] += 1
            continue

        if area in modulos:
            obj = bpy.data.objects.new(st["codigo"], modulos[area].data)
            col.objects.link(obj)
            contagem["instanciado"] += 1
        else:
            lado = math.sqrt(area)
            obj = caixa(st["codigo"], lado, lado, terreno.ALTURA_ESTANDE, col)
            contagem["proprio"] += 1

        obj.location = (x, y, terreno.elevacao(x, y, centro_arena))
        obj["area_m2"] = area
        obj["serie"] = st["serie"]
        postos.append((obj, x, y))

    orientar_estandes(postos)
    return contagem


def carregar_footprints(caminho=None):
    """Footprints medidos do desenho, em LISTA. Ver docs/FOOTPRINTS.md.

    Lista e nao dicionario por rotulo, e o motivo custou uma rodada: **ha nomes
    repetidos no recinto**. Sao tres RESIDENCIA, oito ESTACIONAMENTO, seis Bar.
    Indexar por rotulo colapsava as tres residencias em uma e o gerador
    construia sete zonas onde deveria construir nove -- sem erro nenhum na tela.

    Devolve [] se o arquivo nao existir: o gerador segue com a proporcao
    assumida e avisa. Nunca falhar calado por falta de um json.
    """
    p = Path(caminho) if caminho else RAIZ / "data" / "footprints.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8")).get("itens", [])


def procurar_footprint(fp, rotulo, x_pt=None, y_pt=None):
    """O item daquele rotulo -- e, havendo repetidos, o mais perto do ponto."""
    iguais = [it for it in fp if it["rotulo"] == rotulo]
    if not iguais:
        return None
    if x_pt is None or len(iguais) == 1:
        return iguais[0]
    return min(iguais, key=lambda it: (it["x_pt"] - x_pt) ** 2 + (it["y_pt"] - y_pt) ** 2)


def azimute_para_giro(azimute):
    """Azimute de compasso -> o angulo que `estruturas._girar` espera.

    `_girar` poe o valor direto em `rotation_euler.z`, ou seja e angulo
    matematico, anti-horario a partir do +X. A constante `RUMO_PAVILHOES = 341`
    esta escrita como se fosse azimute e da azimute 109 quando aplicada -- o
    RETOMAR marca isso como "certo por sorte" e manda nao mexer. Aqui a
    conversao fica explicita para nao depender mais da sorte.
    """
    return (90.0 - azimute) % 360.0


def forma_do_pavilhao(rotulo, fp, x_pt=None, y_pt=None):
    """largura, profundidade, giro e a procedencia de cada um desses numeros.

    A regra vem do que cada fonte sabe: **a planta cota AREA em texto** (`720,00
    m²` a 5 pt do rotulo) e isso e medida declarada por quem desenhou; **o
    desenho da a PROPORCAO e o RUMO**, que o texto nao diz. Entao usa-se a
    proporcao medida, escalada para fechar a area cotada.

    Isso tambem corrige o vies do extrator: a mascara e fechada por morfologia e
    incha o contorno em ~1,5 px de cada lado, o que aparece como +6 a +9% de
    area nos cinco pavilhoes que conferem. Escalando pela cota, o vies sai.
    """
    it = procurar_footprint(fp, rotulo, x_pt, y_pt)
    if not it or it.get("confianca") not in ("alta", "media"):
        return None

    largura = it["largura_m"]
    profundidade = it["profundidade_m"]
    cota = it.get("area_cotada_m2")
    proc = "proporcao e rumo medidos do desenho"

    # Mancha contaminada: quando a componente encosta num vizinho, ela deixa de
    # ser o predio e vira a uniao dos dois -- e isso se ve no PREENCHIMENTO.
    # Os cinco pavilhoes limpos preenchem 0,99 do proprio retangulo; o
    # PAVILHAO - EQUINOS preenche 0,71, porque a mancha dele engole um estande
    # de 5x5 e um pedaco do bloco da lavagem (conferido no recorte do desenho).
    # A saida nao e chutar: a familia toda tem a MESMA profundidade medida, de
    # 16,8 m em cinco predios, e a area dele esta cotada em texto. Entao usa-se
    # a profundidade da familia e tira-se a largura da cota.
    familia = [o for o in fp
               if o.get("categoria") == "pavilhoes" and " - " in o["rotulo"]
               and o.get("preenchimento", 0) >= 0.95 and "profundidade_m" in o]
    if familia and cota and it.get("preenchimento", 1.0) < 0.85:
        fundos = sorted(o["profundidade_m"] for o in familia)
        profundidade = fundos[len(fundos) // 2]
        largura = cota / profundidade
        proc = (f"mancha contaminada (preenche {it['preenchimento']:.2f} do proprio "
                f"retangulo contra {len(familia)} irmaos em 0,99+): profundidade "
                f"{profundidade:.1f} m e a mediana da familia medida, largura sai "
                f"da cota de {cota:.0f} m²")
        return largura, profundidade, azimute_para_giro(
            it["rumo_graus"] if it.get("rumo_confiavel") else it.get("rumo_do_bloco", 108.4)
        ), proc, it
    if cota and largura * profundidade > 0:
        k = math.sqrt(cota / (largura * profundidade))
        largura, profundidade = largura * k, profundidade * k
        proc += f"; area escalada para a cota de {cota:.0f} m²"

    azimute = it["rumo_graus"] if it.get("rumo_confiavel") else it.get("rumo_do_bloco")
    if azimute is None:
        azimute = 108.4                      # o rumo medido da fileira
        proc += "; rumo da fileira, o da fatia nao vale"
    return largura, profundidade, azimute_para_giro(azimute), proc, it


def construir_pavilhoes(dados, col, centro_arena, bbox=None, fp=None):
    """Pavilhoes: os 6 de animais mais os de expositores que a planta numera.

    Ate 14/08 isto fazia `profundidade = 12.0` com o comentario "proporcao
    assumida", e o desenho diz **45,9 x 16,8 m**. E o filtro exigia hifen no
    rotulo, entao `PAVILHAO 1`, `2` e `3` -- os de Expositores Industria,
    Comercio e Servicos, que o Natan apontou mandando o PDF -- eram descartados
    **sem aviso nenhum**. Agora a forma vem de `data/footprints.json` e o que
    nao tem footprint confiavel e nomeado na saida, nao sumido.

    A ordem fisica norte->sul dos de animais e gado leite, nucleo cara branca,
    gado corte, ovinos e caprinos, pequenos animais, equinos.
    """
    fp = fp if fp is not None else carregar_footprints()
    origem = dados["_origem"]
    feitos, pulados, assumidos = 0, [], []
    for z in dados["zonas"]:
        if z["categoria"] != "pavilhoes":
            continue
        x, y = terreno.para_mundo(z["x"], z["y"], origem)
        if not dentro(bbox, x, y):
            continue

        forma = forma_do_pavilhao(z["rotulo"], fp, z["x"], z["y"])
        if forma is None:
            it = procurar_footprint(fp, z["rotulo"], z["x"], z["y"]) or {}
            motivo = "; ".join(it.get("suspeitas", [])) or "sem footprint no desenho"
            pulados.append((z["rotulo"], motivo))
            continue
        largura, profundidade, giro, proc, it = forma

        # Galpao de duas aguas, nao caixa: o telhado e o que se ve do alto no
        # sobrevoo do P11, e caixa chapada denuncia CG antes de qualquer
        # textura.
        obj = estruturas.pavilhao(z["rotulo"], x, y,
                                  terreno.elevacao(x, y, centro_arena),
                                  largura, profundidade, col, rumo_graus=giro)
        obj["area_m2"] = round(largura * profundidade, 1)
        obj["forma_procedencia"] = proc
        obj["confianca_footprint"] = it["confianca"]
        feitos += 1
        if not it.get("area_cotada_m2"):
            assumidos.append(z["rotulo"])

    for rotulo, motivo in pulados:
        print(f"  pavilhao NAO construido: {rotulo} -- {motivo}")
    if assumidos:
        print(f"  sem cota em texto, so o desenho: {', '.join(assumidos)}")
    return feitos


def construir_medidos(dados, col, centro_arena, bbox=None, fp=None):
    """As zonas que TEM footprint medido e nao tinham construcao nenhuma.

    Sao nove, e elas mudam o filme: a Praca de Alimentacao Coberta (145 x 34 m,
    o P04), o Recinto de Leiloes (o audio: *"entra no recinto, tem leiloes, os
    leiloes acontecendo"*), o Cafe Colonial -- um dos quatro diferenciais do
    cliente --, o Auditorio, o Palco After, a Lavagem de Animais e as tres
    residencias. Antes de 14/08 o extrator media todas elas e ninguem lia.

    **Aqui a procedencia se parte em duas, e o objeto carrega as duas.** O
    footprint (largura, profundidade, rumo) e MEDIDO do desenho; a ALTURA e
    estimada, porque planta baixa nao tem altura. Sai `footprint_medido = True`
    e `altura_estimada = True` em cada objeto, e a altura de cada uma esta
    declarada em `data/estimativas.json`, secao `altura_das_zonas_medidas`.
    """
    fp = fp if fp is not None else carregar_footprints()
    tabela = estimativas.carregar() or {}
    secao = tabela.get("altura_das_zonas_medidas", {})
    alturas = secao.get("zonas", {})
    proprias = secao.get("ja_tem_construcao_propria", {})

    origem = dados["_origem"]
    feitos, sem_altura = 0, []
    for it in fp:
        rotulo = it["rotulo"]
        if it.get("confianca") not in ("alta", "media"):
            continue
        if it["categoria"] == "pavilhoes" or rotulo in proprias:
            continue                      # ja construidos, cada um no seu lugar
        decl = alturas.get(rotulo)
        if decl is None:
            sem_altura.append(rotulo)
            continue

        x, y = terreno.para_mundo(it["x_pt"], it["y_pt"], origem)
        if not dentro(bbox, x, y):
            continue
        z = terreno.elevacao(x, y, centro_arena)
        largura, profundidade = it["largura_m"], it["profundidade_m"]
        azimute = it["rumo_graus"] if it.get("rumo_confiavel") else it.get("rumo_do_bloco")
        giro = azimute_para_giro(azimute if azimute is not None else 90.0)

        if decl["forma"] == "cobertura":
            obj = caixa(rotulo, largura, profundidade, 0.3, col)
            obj.location = (x, y, z + decl["altura_m"])
            pilares(rotulo, x, y, z, largura, profundidade, decl["altura_m"],
                    giro, col, marca="footprint_medido")
        else:
            obj = caixa(rotulo, largura, profundidade, decl["altura_m"], col)
            obj.location = (x, y, z)

        obj.rotation_euler = (0.0, 0.0, math.radians(giro))
        obj["material"] = decl["material"]
        obj["area_m2"] = round(largura * profundidade, 1)
        obj["footprint_medido"] = True
        obj["altura_estimada"] = True
        obj["confianca_footprint"] = it["confianca"]
        obj["procedencia"] = (
            f"footprint medido do desenho ({it['particao']}); "
            f"altura estimada: {decl['fundamento']}")
        feitos += 1

    for rotulo in sem_altura:
        print(f"  medido mas NAO construido: {rotulo} -- sem altura declarada em "
              "estimativas.json")
    return feitos


def malha_de_arvore(porte):
    """UMA malha de arvore, para todas as instancias compartilharem.

    Nao ha verba de asset (so CC0) e o teto e uma RTX 4060 de 8 GB. Arvore de
    biblioteca com folha por geometria multiplicada por 300 nao cabe; malha
    compartilhada cabe com folga, porque o Blender guarda os vertices uma vez so
    e cada instancia e uma matriz.

    A forma e grosseira de proposito -- tronco mais tres copas deslocadas. A
    distancia de sobrevoo isso le como arvore; o que denuncia CG num plano
    aereo e copa ESFERICA E IGUAL, e e por isso que cada instancia sai com
    escala, giro e proporcao proprios.
    """
    malha = bpy.data.meshes.new("ArvoreBase")
    bm = bmesh.new()

    # dois slots: 0 = tronco, 1 = copa. Sem isso a arvore inteira sai verde, e
    # a 4 m de altura -- que e a regua de camera dele para lugar aberto -- o
    # tronco aparece.
    tronco = porte["altura_tronco_m"]
    r_tronco = porte["raio_tronco_m"]
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=7,
                          radius1=r_tronco * 1.35, radius2=r_tronco,
                          depth=tronco,
                          matrix=Matrix.Translation(Vector((0, 0, tronco / 2))))

    bm.faces.ensure_lookup_table()
    faces_do_tronco = len(bm.faces)

    copa_r = porte["raio_copa_m"]
    copa_z = porte["altura_m"]
    # Sete tufos, nao tres. Com tres bolhas grandes a copa fecha num ovoide liso
    # e a mata inteira le como brocolis -- foi o que apareceu no render de prova.
    # Tufo menor e mais numeroso quebra a silhueta e, principalmente, cria
    # SOMBRA DE UM NO OUTRO, que e o que da volume a uma massa de folha.
    #
    # E a copa e ACHATADA (0,55 em z, contra 0,72 antes): arvore adulta de parque
    # abre para os lados, nao cresce em bola -- as do quadro de referencia tem
    # copa mais larga que alta.
    for dx, dy, dz, k in ((0.00, 0.00, 0.02, 0.82),
                          (0.52, -0.34, -0.16, 0.62),
                          (-0.46, 0.40, -0.10, 0.58),
                          (0.30, 0.52, -0.20, 0.54),
                          (-0.55, -0.30, -0.24, 0.50),
                          (0.10, -0.60, 0.08, 0.46),
                          (-0.18, 0.14, 0.26, 0.52)):
        # subdivisions=2 (80 faces por bolha). Com 1 a copa e um icosaedro de 20
        # faces e, alisada, ela vira um balao -- foi exatamente o que apareceu no
        # render de prova. O custo e zero na pratica: a malha e UMA so, e as 232
        # arvores sao instancias dela.
        bmesh.ops.create_icosphere(
            bm, subdivisions=2, radius=copa_r * k,
            matrix=Matrix.Translation(Vector((dx * copa_r, dy * copa_r,
                                              copa_z * 0.72 + dz * copa_r)))
            @ Matrix.Diagonal(Vector((1.0, 1.0, 0.55, 1.0))))

    bm.faces.ensure_lookup_table()
    for i, f in enumerate(bm.faces):
        copa = i >= faces_do_tronco
        f.material_index = 1 if copa else 0
        # copa lisa, tronco facetado. Icosfera com face chapada desenha cada
        # triangulo com sombra propria, e no primeiro render a copa apareceu
        # como um poliedro escuro em vez de massa de folha.
        f.smooth = copa

    bm.to_mesh(malha)
    bm.free()
    return malha


def malha_de_arbusto(porte):
    """UMA malha de arbusto, compartilhada -- mesma economia da arvore.

    Nao tem tronco: arbusto de contencao de talude e massa de folha encostando
    no chao. Sao tres bolhas baixas e achatadas, deslocadas, com o mesmo
    material MEDIDO da copa.
    """
    malha = bpy.data.meshes.new("ArbustoBase")
    bm = bmesh.new()
    for dx, dy, dz, k in ((0.00, 0.00, 0.10, 1.00),
                          (0.55, 0.30, -0.12, 0.72),
                          (-0.48, -0.36, -0.15, 0.66)):
        bmesh.ops.create_icosphere(
            bm, subdivisions=1, radius=k,
            matrix=Matrix.Translation(Vector((dx, dy, dz)))
            @ Matrix.Diagonal(Vector((1.0, 0.92, 0.60, 1.0))))
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector((0, 0, 0.55))),
                        verts=bm.verts)
    bm.to_mesh(malha)
    bm.free()
    for p in malha.polygons:
        p.use_smooth = True
    return malha


def _declive(x, y, centro_arena, passo=2.0):
    """Inclinacao do terreno em (x, y), em m/m. Diferenca central.

    E ela que separa talude de platao: o rotulo 'Talude' fica ONDE CABE no
    desenho, nem sempre em cima do declive. Plantar pelo rotulo puro encheria
    de arbusto o chao plano ao lado.
    """
    zx = (terreno.elevacao(x + passo, y, centro_arena)
          - terreno.elevacao(x - passo, y, centro_arena)) / (2 * passo)
    zy = (terreno.elevacao(x, y + passo, centro_arena)
          - terreno.elevacao(x, y - passo, centro_arena)) / (2 * passo)
    return math.hypot(zx, zy)


def construir_arbustos_de_talude(dados, col, centro_arena, veg, bbox=None,
                                 solidos=None):
    """Arbusto nos 15 taludes que a planta anota. Contrato em vegetacao.json.

    O que faz isto ser medida e nao enfeite: o arbusto so nasce onde o terreno
    TEM DECLIVE (`declive_minimo`, 0,08 m/m). O rotulo da a regiao, o declive da
    o lugar. Onde o talude nao existe na geometria, nao nasce nada -- e isso e
    resultado, nao falha: depois que a bacia virou ferradura, o setor aberto
    ficou plano e nao deve ganhar arbusto de contencao.
    """
    tipo = veg["tipos"].get("talude")
    if tipo is None or "Talude" not in veg.get("por_rotulo", {}):
        return 0, 0

    porte = veg["porte_arbusto"]
    malha = malha_de_arbusto(porte)
    mat = bpy.data.materials.get(porte.get("material", "MAT_COPA"))
    if mat:
        malha.materials.append(mat)

    rnd = random.Random(veg["semente"] + 17)   # semente propria: mexer no
    # arbusto nao pode reposicionar as 418 arvores ja conferidas
    origem = dados["_origem"]
    raio = tipo["raio_m"]
    dmin = tipo["declive_minimo"]
    plantados, recusados = 0, 0
    raio_livre = veg.get("raio_livre_da_arena_m", 49.0)

    for z in dados["zonas"]:
        if veg["por_rotulo"].get(z["rotulo"]) != "talude":
            continue
        cx, cy = terreno.para_mundo(z["x"], z["y"], origem)
        quantos = max(1, int(math.pi * raio ** 2 / tipo["m2_por_arbusto"]))
        for _ in range(quantos):
            a = rnd.uniform(0, 2 * math.pi)
            r = raio * math.sqrt(rnd.random())
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            if not dentro(bbox, x, y):
                recusados += 1
                continue
            if math.hypot(x - centro_arena[0], y - centro_arena[1]) < raio_livre:
                recusados += 1                      # pista da arena
                continue
            if _declive(x, y, centro_arena) < dmin:
                recusados += 1                      # chao plano: nao e talude
                continue
            if any(q[0] - 2.0 <= x <= q[2] + 2.0 and q[1] - 2.0 <= y <= q[3] + 2.0
                   for _n, q, _c in (solidos or [])):
                recusados += 1
                continue

            obj = bpy.data.objects.new("ArbustoTalude", malha)
            col.objects.link(obj)
            obj.location = (x, y, terreno.elevacao(x, y, centro_arena))
            ka = 1.0 + rnd.uniform(-1, 1) * porte["altura_variacao"]
            kr = 1.0 + rnd.uniform(-1, 1) * porte["raio_variacao"]
            obj.scale = (porte["raio_m"] * kr,
                         porte["raio_m"] * kr * rnd.uniform(0.85, 1.15),
                         porte["altura_m"] * ka)
            obj.rotation_euler = (0.0, 0.0, rnd.uniform(0, 2 * math.pi))
            obj["estimado"] = True
            obj["fundamento"] = "vegetacao.json/tipos.talude + filtro de declive"
            plantados += 1

    return plantados, recusados


def construir_vegetacao(dados, col, centro_arena, bbox=None, solidos=None):
    """Os 6 Bosques e as 2 Matas Nativas que a planta nomeia e nao desenha.

    Contrato em `data/vegetacao.json` -- porte, raio da mancha, densidade e o
    fundamento de cada numero. Aqui so se obedece.

    Tres travas, e as tres estao no contrato: nada dentro de predio, nada dentro
    da bacia da arena (o cliente descreve pista, camarotes e palco -- arvore ali
    contradiz o brief) e semente fixa, senao a cena muda a cada build e nenhuma
    conferencia de quadro vale.
    """
    caminho = RAIZ / "data" / "vegetacao.json"
    if not caminho.exists():
        print("  sem data/vegetacao.json -- vegetacao nao construida")
        return 0, 0
    veg = json.loads(caminho.read_text(encoding="utf-8"))

    malha = malha_de_arvore(veg["porte"])
    mats = {m.name: m for m in bpy.data.materials}
    for nome_mat in ("MAT_TRONCO", "MAT_COPA"):
        if nome_mat in mats:
            malha.materials.append(mats[nome_mat])
    rnd = random.Random(veg["semente"])
    origem = dados["_origem"]
    porte = veg["porte"]
    plantadas, recusadas = 0, 0

    raio_livre = veg.get("raio_livre_da_arena_m", 49.0)

    def livre(x, y):
        if math.hypot(x - centro_arena[0], y - centro_arena[1]) < raio_livre:
            return False                      # pista da arena
        for _nome, q, _c in (solidos or []):
            if q[0] - 3.0 <= x <= q[2] + 3.0 and q[1] - 3.0 <= y <= q[3] + 3.0:
                return False                  # dentro (ou colado) de predio
        return True

    por_zona = []
    for z in dados["zonas"]:
        tipo_nome = veg["por_rotulo"].get(z["rotulo"])
        if tipo_nome is None:
            continue
        if tipo_nome == "talude":
            # talude leva ARBUSTO, e quem planta e construir_arbustos_de_talude.
            # Sem esta linha o laco plantaria arvore de 12 m no talude, porque
            # "Talude" passou a existir em por_rotulo nesta rodada.
            continue
        tipo = veg["tipos"][tipo_nome]
        cx, cy = terreno.para_mundo(z["x"], z["y"], origem)
        raio = tipo["raio_m"]
        quantas = max(1, int(math.pi * raio ** 2 / tipo["m2_por_arvore"]))
        antes = plantadas

        # Borda irregular: tres harmonicas com fase sorteada deformam o raio de
        # -28% a +28% conforme a direcao. Mancha de arvore com borda de compasso
        # e o segundo tell mais obvio de CG num plano aereo, depois de copa
        # igual -- e a vista de topo de 14/08 mostrou os bosques como discos.
        fases = [(rnd.uniform(0, 2 * math.pi), rnd.uniform(0.5, 1.0)) for _ in range(3)]

        def raio_na_direcao(ang):
            d = sum(peso * math.sin((k + 2) * ang + fase)
                    for k, (fase, peso) in enumerate(fases))
            return raio * (1.0 + 0.28 * d / 2.5)

        for _ in range(quantas):
            # ponto uniforme no disco -- sqrt, senao tudo se acumula no centro
            a = rnd.uniform(0, 2 * math.pi)
            u = rnd.random()
            # e rala na borda: mata nao termina numa parede de arvore
            if u > 0.80 and rnd.random() < 0.55:
                recusadas += 1
                continue
            r = raio_na_direcao(a) * math.sqrt(u)
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            if not dentro(bbox, x, y) or not livre(x, y):
                recusadas += 1
                continue

            obj = bpy.data.objects.new(f"Arvore_{z['rotulo'][:6]}", malha)
            col.objects.link(obj)
            obj.location = (x, y, terreno.elevacao(x, y, centro_arena))
            k_alt = 1.0 + rnd.uniform(-1, 1) * porte["altura_variacao"]
            k_raio = 1.0 + rnd.uniform(-1, 1) * porte["raio_variacao"]
            obj.scale = (k_raio, k_raio * rnd.uniform(0.88, 1.12), k_alt)
            obj.rotation_euler = (0.0, 0.0, rnd.uniform(0, 2 * math.pi))
            # material vem da MALHA (dois slots), nao da propriedade -- por isso
            # nao se declara `material` aqui
            obj["estimado"] = True
            obj["procedencia"] = ("porte e densidade declarados em "
                                  "data/vegetacao.json; a planta so escreve o nome")
            plantadas += 1

        # Zona por zona, e nao so o total: um bosque inteiro pode ser barrado
        # pelas travas e o total geral esconde isso. Bosque com zero arvore e a
        # planta dizendo uma coisa e a cena dizendo outra.
        por_zona.append((z["rotulo"], round(cx, 1), round(cy, 1),
                         plantadas - antes, quantas))

    # --- alameda arborizada ---------------------------------------------
    al = veg.get("alameda", {})
    caminho_vias = RAIZ / "data" / "vias.json"
    if al.get("planta") and caminho_vias.exists():
        vias = json.loads(caminho_vias.read_text(encoding="utf-8"))["vias"]
        passo = al["espacamento_m"]
        recuo = al["recuo_do_eixo_m"]
        antes = plantadas
        for via in vias:
            if not via.get("e_via") or via.get("tipo") != al.get("so_tipo"):
                continue
            if via.get("comprimento_m", 0) < al["comprimento_minimo_m"]:
                continue
            pts = via.get("pontos_m") or []
            sobra = rnd.uniform(0, passo)       # nao comeca sempre no vertice
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                dx, dy = bx - ax, by - ay
                comp = math.hypot(dx, dy)
                if comp < 1e-6:
                    continue
                ux, uy = dx / comp, dy / comp
                nx, ny = -uy, ux                # normal do trecho
                s = sobra
                while s < comp:
                    for lado in ((-1, 1) if al.get("dos_dois_lados") else (1,)):
                        jx = rnd.uniform(-1.5, 1.5)
                        x = ax + ux * s + nx * lado * recuo + ux * jx
                        y = ay + uy * s + ny * lado * recuo + uy * jx
                        if not dentro(bbox, x, y) or not livre(x, y):
                            recusadas += 1
                            continue
                        obj = bpy.data.objects.new("Arvore_alameda", malha)
                        col.objects.link(obj)
                        obj.location = (x, y, terreno.elevacao(x, y, centro_arena))
                        k_alt = 1.0 + rnd.uniform(-1, 1) * porte["altura_variacao"] * 0.6
                        k_raio = 1.0 + rnd.uniform(-1, 1) * porte["raio_variacao"] * 0.6
                        obj.scale = (k_raio, k_raio * rnd.uniform(0.9, 1.1), k_alt)
                        obj.rotation_euler = (0.0, 0.0, rnd.uniform(0, 2 * math.pi))
                        obj["estimado"] = True
                        obj["procedencia"] = (
                            "alinhamento de alameda: espacamento e recuo declarados "
                            "em data/vegetacao.json; a alameda arborizada aparece no "
                            "footage do recinto, o alinhamento exato nao")
                        plantadas += 1
                    s += passo
        por_zona.append(("alameda", 0.0, 0.0, plantadas - antes, plantadas - antes))

    for rotulo, cx, cy, feitas, pedidas in por_zona:
        marca = "  <-- VAZIO" if feitas == 0 else ("  <-- quase vazio"
                                                   if feitas < pedidas * 0.3 else "")
        print(f"    {rotulo[:14]:16s} ({cx:7.1f},{cy:7.1f})  "
              f"{feitas:3d} de {pedidas:3d}{marca}")

    return plantadas, recusadas


def pilares(nome, x, y, z, largura, profundidade, altura, giro, col,
            passo=12.0, secao=0.4, marca=None):
    """Pilares em malha sob uma cobertura, e nao so nos quatro cantos.

    A primeira versao punha quatro pilares em qualquer cobertura, e nas provas
    de luz a Praca de Alimentacao Coberta -- 145 x 34 m -- apareceu como uma
    chapa branca flutuando. Vao de galpao nao passa de ~12 m sem apoio, e o
    telhado e o que se ve do alto no sobrevoo.
    """
    nx = max(2, int(round(largura / passo)) + 1)
    ny = max(2, int(round(profundidade / passo)) + 1)
    c, s = math.cos(math.radians(giro)), math.sin(math.radians(giro))
    postos = 0
    for i in range(nx):
        lx = -largura / 2 + 0.6 + (largura - 1.2) * i / (nx - 1)
        for j in range(ny):
            ly = -profundidade / 2 + 0.6 + (profundidade - 1.2) * j / (ny - 1)
            if 0 < i < nx - 1 and 0 < j < ny - 1:
                continue                 # so o perimetro: o miolo fica livre
            pe = caixa(f"{nome} pilar", secao, secao, altura, col)
            pe.location = (x + lx * c - ly * s, y + lx * s + ly * c, z)
            pe.rotation_euler = (0.0, 0.0, math.radians(giro))
            pe["material"] = "MAT_TRELICA"
            if marca:
                pe[marca] = True
            postos += 1
    return postos


def _pegada_xy(obj):
    xs = [(obj.matrix_world @ v.co).x for v in obj.data.vertices]
    ys = [(obj.matrix_world @ v.co).y for v in obj.data.vertices]
    return min(xs), min(ys), max(xs), max(ys)


def pegada_prevista(x, y, largura, profundidade, giro_graus):
    """Caixa envolvente XY de um retangulo girado, sem depender do depsgraph.

    `matrix_world` so vale depois que o Blender atualiza a cena, e dentro do
    laco de construcao ele ainda nao atualizou -- a primeira versao disto leu
    todas as pegadas na origem e concluiu que a cena inteira estava dentro do
    PAVILHAO - EQUINOS, afastando 33 objetos em 20 m cada. Aqui a conta e
    fechada e nao depende de estado nenhum.
    """
    c = abs(math.cos(math.radians(giro_graus)))
    s = abs(math.sin(math.radians(giro_graus)))
    hx = (c * largura + s * profundidade) / 2.0
    hy = (s * largura + c * profundidade) / 2.0
    return x - hx, y - hy, x + hx, y + hy


def afastar_do_medido(obj, largura, profundidade, giro, medidos,
                      limite=0.10, margem=1.0, passos=40):
    # 0.10 e a MESMA regua de conferir_estimados.py, de proposito: construtor e
    # conferidor com limite diferente e como ter dois juizes -- o CCO passava
    # com 12% de si dentro do AUDITORIO e a conferencia depois acusava.
    """Tira a caixa estimada de dentro de geometria MEDIDA, e conta que tirou.

    A ancora de uma zona estimada e a posicao do ROTULO, nao do predio, e as
    duas nem sempre coincidem: um `Bar` nascia 99% dentro do CAMAROTES - LADO B
    e a ORDENHADEIRA nascia 51% dentro do PAVILHAO - GADO LEITE.

    Afasta na direcao que sai do objeto medido, de meio metro por vez, ate
    passar do limite de sobreposicao. **Nao inventa posicao nova**: so recusa a
    posicao impossivel, e grava `deslocado_m` no objeto para aparecer na
    conferencia.

    Vias ficam de fora da conta de proposito: sao fitas diagonais lidas do
    bitmap, e a caixa envolvente de uma diagonal cobre um retangulo enorme --
    daria falso positivo em quase tudo. Alem disso portao e quiosque ficam
    mesmo na beira da via.
    """
    def sobrepoe(p, q):
        dx = min(p[2], q[2]) - max(p[0], q[0])
        dy = min(p[3], q[3]) - max(p[1], q[1])
        return dx * dy if dx > 0 and dy > 0 else 0.0

    p = pegada_prevista(obj.location.x, obj.location.y, largura, profundidade, giro)
    area = max((p[2] - p[0]) * (p[3] - p[1]), 1e-6)
    culpado = None
    for nome, q, centro in medidos:
        if sobrepoe(p, q) / area > limite:
            culpado = (q, centro, nome)
            break
    if culpado is None:
        return 0.0, None

    q, centro, nome = culpado
    dx = obj.location.x - centro[0]
    dy = obj.location.y - centro[1]
    n = math.hypot(dx, dy)
    if n < 1e-6:                      # concentricos: sai para o leste
        dx, dy, n = 1.0, 0.0, 1.0
    dx, dy = dx / n, dy / n

    andado = 0.0
    for _ in range(passos):
        obj.location.x += dx * 0.5
        obj.location.y += dy * 0.5
        andado += 0.5
        p = pegada_prevista(obj.location.x, obj.location.y,
                            largura, profundidade, giro)
        if sobrepoe(p, q) / area <= 0.01:
            obj.location.x += dx * margem
            obj.location.y += dy * margem
            return andado + margem, nome
    return andado, nome


def construir_estimados(col, centro_arena, bbox=None, origem=None, medidos=None):
    """As zonas que a planta nomeia e nao desenha, no tamanho ESTIMADO.

    Autorizado pelo Natan em 14/08: *"pode fazer com uma estimativa
    aproximada"*. Sem isto, metade do recinto -- praca de alimentacao aberta,
    banheiros, portaria, estacionamentos, mangueiras -- ficava sem nada.

    Elas vao para a colecao **ESTIMADO**, separada de proposito: no .blend da
    para esconder tudo de uma vez e ver quanto da cena e palpite. Cada objeto
    leva `estimado = True` e a procedencia do numero colada nele.

    Tamanho, tipo e fundamento vivem em `data/estimativas.json`; quem resolve e
    `scripts/estimativas.py`, que roda sem bpy.
    """
    est, recusados = estimativas.resolver()
    feitos, deslocados = 0, []
    for e in est:
        x, y = terreno.para_mundo(e["x_pt"], e["y_pt"], origem)
        if not dentro(bbox, x, y):
            continue
        z = terreno.elevacao(x, y, centro_arena)
        largura, profundidade = e["largura_m"], e["profundidade_m"]
        alto = 0.0                      # deslocamento vertical da peca principal

        if e["forma"] == "chao":
            # Estacionamento e SUPERFICIE. Sair como caixa seria transformar
            # um patio num galpao de 3 m de altura no meio do sobrevoo.
            obj = caixa(e["rotulo"], largura, profundidade, 0.06, col)
            obj["material"] = "MAT_ASFALTO"
        elif e["forma"] == "cobertura":
            # Laje de cobertura sobre pilar: area coberta e sem parede, que e o
            # que o audio descreve na praca de alimentacao.
            obj = caixa(e["rotulo"], largura, profundidade, 0.25, col)
            alto = e["altura_m"]
            obj["material"] = "MAT_LONA"
            pilares(e["rotulo"], x, y, z, largura, profundidade, e["altura_m"],
                    e["giro_graus"], col, secao=0.3, marca="estimado")
        elif e["forma"] == "cercado":
            # Curral e cerca, nao caixa fechada: quatro panos baixos.
            obj = caixa(e["rotulo"], largura, 0.2, e["altura_m"], col)
            obj["material"] = "MAT_GRADIL"
            for lado, (dx, dy, lx, ly) in enumerate((
                    (0, profundidade / 2, largura, 0.2),
                    (0, -profundidade / 2, largura, 0.2),
                    (largura / 2, 0, 0.2, profundidade),
                    (-largura / 2, 0, 0.2, profundidade))):
                if lado == 0:
                    continue
                pano = caixa(f"{e['rotulo']} pano", lx, ly, e["altura_m"], col)
                pano.location = (x + dx, y + dy, z)
                pano["material"] = "MAT_GRADIL"
                pano["estimado"] = True
        else:
            obj = caixa(e["rotulo"], largura, profundidade, e["altura_m"], col)
            obj["material"] = "MAT_PAVILHAO"

        obj.location = (x, y, z + alto)
        obj.rotation_euler = (0.0, 0.0, math.radians(e["giro_graus"]))
        obj["estimado"] = True
        obj["tipo_estimado"] = e["tipo"]
        obj["procedencia"] = e["procedencia"]
        obj["area_m2"] = round(largura * profundidade, 1)

        if medidos:
            andado, quem = afastar_do_medido(obj, largura, profundidade,
                                             e["giro_graus"], medidos)
            if andado:
                obj["deslocado_m"] = round(andado, 1)
                obj["deslocado_de"] = quem
                deslocados.append((e["rotulo"], andado, quem))
        feitos += 1

    for rotulo, motivo in recusados:
        print(f"  estimativa recusada: {rotulo} -- {motivo}")
    for rotulo, andado, quem in deslocados:
        print(f"  estimativa afastada: {rotulo} andou {andado:.1f} m "
              f"para sair de dentro de {quem}")
    return feitos, len(recusados)


def construir_estruturas(dados, col, centro_arena, bbox=None):
    """Portal, palco e camarotes -- as tres que o filme mais mostra.

    O portal abre e fecha o filme (P02 e P22), o palco e o P20, e os camarotes
    aparecem em todo plano da arena. Ate 14/08 os tres eram caixa ou nem isso.
    """
    origem = dados["_origem"]
    feitos = []

    def posicao(rotulo, ocorrencia=0):
        p = terreno.ponto_da_zona(dados, rotulo, ocorrencia)
        if p is None or not dentro(bbox, p[0], p[1]):
            return None
        return p[0], p[1], terreno.elevacao(p[0], p[1], centro_arena)

    p = posicao("Portal de Entrada")
    if p:
        feitos.append(estruturas.portal("PortalCeleiro", *p, col,
                                        rumo_graus=RUMO_PORTAL))

    # A zona PALCO da planta e a CONCHA de alvenaria, nao o palco de evento.
    # Ordem dele em 15/08: *"a concha entra na cena"*. O rumo vem do footprint
    # medido (116,6 graus de rumo de mapa) -- e ATENCAO a convencao, que ja
    # enganou uma vez neste arquivo: `_girar()` aplica angulo MATEMATICO, e
    # `angulo = 90 - rumo`. `RUMO_PALCO = 334.0` logo acima esta escrito nessa
    # mesma convencao torta e por isso da certo; nao mexer nele.
    p = posicao("PALCO")
    if p:
        feitos.append(estruturas.concha("ConchaPalco", *p, col,
                                        rumo_graus=90.0 - RUMO_CONCHA))

        # O palco DE EVENTO continua existindo -- `nada se apaga`. Ele sai da
        # arena porque a zona PALCO e da concha, e vai para a AREA DE ESPERA,
        # que e o mecanismo que ele proprio pediu em 15/08 para peca que existe
        # mas cuja posicao e dele: *"o que nao sabe quero que deixe do lado"*.
        feitos.append(estruturas.palco("Palco de evento", ESPERA_PALCO[0],
                                       ESPERA_PALCO[1], 0.0, col,
                                       rumo_graus=RUMO_PALCO))

    # Os dois camarotes ladeiam a arena -- restricao 1 do cliente, e o mapa
    # desenha os dois. Cada um aponta para o centro da pista.
    for rotulo in ("CAMAROTES - LADO A", "CAMAROTES - LADO B"):
        p = posicao(rotulo)
        if not p:
            continue
        rumo = math.degrees(math.atan2(centro_arena[1] - p[1],
                                       centro_arena[0] - p[0]))
        feitos.append(estruturas.camarote(rotulo, *p, col, rumo_graus=rumo))

    return feitos


def construir_vias(col, centro_arena, bbox=None, caminho=None):
    """As vias lidas do bitmap da planta, viradas em fita de pista.

    So entra o que `scripts/extrair_vias.py` marcou como via de verdade -- o
    resto do que a deteccao pega e moldura de prancha e caixa de carimbo.
    """
    caminho = Path(caminho or RAIZ / "data" / "vias.json")
    if not caminho.exists():
        print("  sem data/vias.json -- rode scripts/extrair_vias.py")
        return 0

    dados_vias = json.loads(caminho.read_text(encoding="utf-8"))
    feitas = 0
    for v in dados_vias["vias"]:
        if not v.get("e_via"):
            continue
        pontos = [(x, y) for x, y in v["pontos_m"]
                  if dentro(bbox, x, y)]
        if len(pontos) < 2:
            continue
        obj = estruturas.via(f"Via_{v['id']}", pontos, col,
                             lambda x, y: terreno.elevacao(x, y, centro_arena))
        if obj:
            obj["tipo"] = v.get("tipo")
            obj["rotulo_mais_proximo"] = v.get("rotulo_mais_proximo")
            feitas += 1
    return feitas


def configurar_render(cena, motor="cycles"):
    cena.render.resolution_x = LARGURA_RENDER
    cena.render.resolution_y = ALTURA_RENDER
    cena.render.resolution_percentage = 100
    cena.render.fps = 30
    cena.render.image_settings.file_format = "PNG"
    cena.render.film_transparent = False
    escolher_motor(cena, motor)

    if cena.render.engine == "CYCLES":
        configurar_cycles(cena)
    else:
        configurar_eevee(cena)

    # Ceu de fim de tarde em 2:1 e um degrade grande; painel LED costuma
    # trabalhar em 8 bits e bandeia. Dither e a primeira defesa, sem custo.
    cena.render.dither_intensity = 1.0
    print(f"  motor de render ..... {cena.render.engine}")


def escolher_motor(cena, pedido="cycles"):
    """Crava o motor pedido, e ABORTA se ele nao existir.

    O codigo antigo tentava 'BLENDER_EEVEE_NEXT' e, no except, caia em Cycles.
    No Blender 5.2 o identificador voltou a ser 'BLENDER_EEVEE' -- entao o
    except disparava sempre e a cena saia em **Cycles CPU, em silencio**, com
    o resto do arquivo (overscan, motion blur por acumulacao) configurado para
    EEVEE. Um render de 4.635 quadros comecaria e nao terminaria nunca, e
    ninguem saberia por que.

    Motor e declaracao, nao tentativa. Se o pedido nao existe nesta build, o
    programa para e diz qual existe.
    """
    if pedido == "cycles":
        garantir_addon_cycles()

    candidatos = {
        "cycles": ["CYCLES"],
        # 'NEXT' e o nome da 4.2 a 4.5; a 5.x voltou ao nome curto.
        "eevee": ["BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"],
    }[pedido]

    # Atribui e CONFERE. Nao da para consultar a lista antes: o enum de
    # `render.engine` so anuncia os motores embutidos, e o Cycles, que e addon,
    # nao aparece nele nem quando esta ligado e funcionando. Consultando a
    # lista, o gerador abortava dizendo que a build nao tem Cycles -- e tinha.
    for nome in candidatos:
        try:
            cena.render.engine = nome
        except TypeError:
            continue
        if cena.render.engine == nome:
            return nome

    raise SystemExit(
        f"nao consegui cravar o motor {pedido!r} nesta build do Blender "
        f"(tentei {candidatos}). O render NAO vai sair no motor pedido.")


def garantir_addon_cycles():
    """Religa o addon do Cycles, que `limpar_cena()` derruba.

    `bpy.ops.wm.read_factory_settings()` -- usado para nascer com a cena vazia
    -- volta as preferencias de fabrica e, com elas, desabilita os addons da
    sessao. O Cycles some do enum de motores e o gerador aborta dizendo que a
    build nao tem Cycles, o que e falso. Religar aqui custa nada e evita o
    diagnostico errado.
    """
    import addon_utils
    for nome in ("cycles", "bl_ext.blender_org.cycles"):
        try:
            addon_utils.enable(nome, default_set=False, persistent=True)
        except Exception:
            continue
        if "cycles" in bpy.context.preferences.addons:
            return True
    return "cycles" in bpy.context.preferences.addons


def configurar_cycles(cena):
    """A configuracao que o Natan ditou em 14/08, gravada na cena.

    Ele abre o .blend e renderiza: nada aqui e para ser remarcado a mao.
    Max samples 128 com limiar de ruido 0,1 -- o limiar e quem manda, e os 128
    sao o teto para o pixel que nao converge. Denoise ligado no fim, prefiltro
    Fast, qualidade Balanced, na GPU.
    """
    c = cena.cycles
    c.device = "GPU"
    c.samples = 128
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.1
    c.use_denoising = True
    for atributo, valor in (("denoising_use_gpu", True),
                            ("denoising_prefilter", "FAST"),
                            ("denoising_quality", "BALANCED"),
                            ("use_fast_gi", True)):
        if hasattr(c, atributo):
            setattr(c, atributo, valor)

    # Sem isto o Blender aceita device='GPU' e renderiza na CPU assim mesmo:
    # o device so vale se houver placa habilitada nas preferencias.
    habilitar_gpu()

    cena.render.use_motion_blur = True
    print(f"  cycles .............. {c.samples} samples, limiar "
          f"{c.adaptive_threshold}, denoise "
          f"{getattr(c, 'denoising_prefilter', '?')}/"
          f"{getattr(c, 'denoising_quality', '?')}")


def habilitar_gpu():
    """Liga a placa nas preferencias do Cycles, tentando OptiX e depois CUDA.

    `cycles.device = 'GPU'` sozinho nao basta: se nenhum dispositivo estiver
    marcado nas preferencias, o Cycles cai para a CPU sem reclamar. Numa RTX
    4060 isso e a diferenca entre minutos e uma noite.
    """
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except KeyError:
        print("  AVISO: addon cycles indisponivel; render vai para a CPU")
        return None

    for tipo in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
        try:
            prefs.compute_device_type = tipo
        except TypeError:
            continue
        prefs.get_devices()
        placas = [d for d in prefs.devices if d.type == tipo]
        if not placas:
            continue
        for d in prefs.devices:
            d.use = (d.type == tipo)
        print(f"  gpu ................. {tipo}: "
              f"{', '.join(d.name for d in placas)}")
        return tipo

    print("  AVISO: nenhuma GPU encontrada; render vai para a CPU")
    return None


def configurar_eevee(cena):
    """Alternativa rapida, para conferencia -- nao e o motor da entrega."""
    # Overscan: com camera em movimento, efeitos de tela do EEVEE (SSR, SSAO)
    # somem perto da borda do quadro. 5-10% os traz de volta.
    for alvo, atributo, valor in (
            (cena.eevee, "use_overscan", True),
            (cena.eevee, "overscan_size", 7.0),
            (cena.render, "use_motion_blur", True),
            (cena.eevee, "motion_blur_steps", 6),
            (cena.eevee, "taa_render_samples", 64)):
        if hasattr(alvo, atributo):
            setattr(alvo, atributo, valor)


def alvo_do_sol(luz):
    """(elevacao, azimute_na_cena) do sol, e a rotacao a aplicar no ceu.

    Hierarquia, e ela e o contrato -- sem isso `sol.py` e o HDRI discordam e
    quem ler o codigo daqui a duas rodadas reintroduz a ambiguidade:

        1. sol.py (NOAA)   -> o azimute-alvo do sitio          <- O DONO
        2. medir_hdri.py   -> onde o sol esta DENTRO do HDRI
        3. rotacao do ceu  =  alvo - medido
        4. a SUN           -> posicionada pelo ALVO

    O azimute do HDRI e arbitrario: depende de como o fotografo apontou a
    camera ao montar o panorama. Por isso ele nunca manda -- ele so informa
    quanto girar para o sol cair onde o NOAA diz que ele estava.
    """
    ano, mes, dia = (int(p) for p in luz["momento"]["data"].split("-"))
    hh, mm = (int(p) for p in luz["momento"]["hora"].split(":"))
    elev, azim_real = sol.posicao(ano, mes, dia, hh + mm / 60.0,
                                  luz["local"]["lat"], luz["local"]["lon"],
                                  luz["local"]["tz"])

    # o mundo da cena esta girado em relacao ao norte verdadeiro
    azim_cena = (azim_real - luz["norte_do_mapa_graus"]) % 360.0

    medido = _hdri_medido(luz)
    rot = (azim_cena - medido["azimute_deg"]) % 360.0 if medido else 0.0
    return elev, azim_cena, rot, medido


def _hdri_medido(luz):
    """A medicao de scripts/medir_hdri.py para o HDRI escolhido."""
    caminho = RAIZ / "data" / "hdri-medido.json"
    if not caminho.exists():
        return None
    escolhido = luz["hdri"]["escolhido"]
    for item in json.loads(caminho.read_text(encoding="utf-8"))["itens"]:
        if Path(item["arquivo"]).stem == escolhido:
            return item
    return None


def construir_ceu(cena, luz, rotacao_z):
    """HDRI de golden hour, girado para o sol cair no azimute do sitio.

    O ceu chapado que havia aqui era azul (0.35, 0.48, 0.72) -- azul de
    meio-dia, o oposto do que a cena pede.
    """
    arquivo = RAIZ / f"assets/hdri/{luz['hdri']['escolhido']}.hdr"
    mundo = bpy.data.worlds.new("Mundo")
    cena.world = mundo
    mundo.use_nodes = True
    nt = mundo.node_tree
    nt.nodes.clear()

    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapa = nt.nodes.new("ShaderNodeMapping")
    mapa.inputs["Rotation"].default_value[2] = math.radians(rotacao_z)
    fundo = nt.nodes.new("ShaderNodeBackground")
    fundo.inputs["Strength"].default_value = luz["hdri"].get("forca", 1.0)
    saida = nt.nodes.new("ShaderNodeOutputWorld")

    if arquivo.exists():
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(str(arquivo), check_existing=True)
        # .hdr ja e linear: marcar como sRGB aqui escurece o ceu inteiro
        env.image.colorspace_settings.name = "Linear Rec.709"
        env.projection = "EQUIRECTANGULAR"
        nt.links.new(coord.outputs["Generated"], mapa.inputs["Vector"])
        nt.links.new(mapa.outputs["Vector"], env.inputs["Vector"])
        nt.links.new(env.outputs["Color"], fundo.inputs["Color"])
    else:
        # Sem HDRI a cena ainda tem que montar, mas nao finge que esta certa.
        print(f"  AVISO: {arquivo.name} nao existe -- ceu chapado de emergencia."
              f" Rode: python scripts/assets.py --hdri <slug>")
        fundo.inputs["Color"].default_value = (0.35, 0.28, 0.20, 1.0)

    nt.links.new(fundo.outputs["Background"], saida.inputs["Surface"])

    # Importance sampling do mundo. Sem isto um ceu de fim de tarde, que tem
    # quase toda a energia num disco pequeno, vira granulado em 128 samples.
    if hasattr(mundo, "cycles"):
        mundo.cycles.sampling_method = "MANUAL"
        mundo.cycles.sample_map_resolution = 2048
    return mundo


def construir_luz(col, luz, elevacao, azimute_cena, medido):
    """A SUN, posicionada pelo alvo do NOAA e colorida pelo disco do HDRI.

    O que havia aqui era um sol a 25 graus de elevacao, branco puro e com o
    azimute apontando para o lado errado -- nem golden hour, nem coerente com
    o ceu do fundo.

    A cor sai medida do proprio disco solar do HDRI em vez de convertida de
    Kelvin: casa exatamente com o ceu que esta atras, que e o ponto.
    """
    dados = bpy.data.lights.new("Sol", type="SUN")
    dados.energy = luz["sol"]["energia"]
    dados.angle = math.radians(luz["sol"]["angulo_deg"])

    kelvin = luz["sol"].get("temperatura_k")
    if kelvin:
        dados.color = sol.cor_de_temperatura(kelvin)
    elif medido:
        dados.color = tuple(medido["cor_do_disco"])[:3]

    obj = bpy.data.objects.new("Sol", dados)
    d = Vector(sol.direcao(elevacao, azimute_cena))
    # to_track_quat mapeia +Z local em d; a SUN emite ao longo do -Z local,
    # entao a luz viaja em -d: do sol para o chao. Escrever isso com Euler a
    # mao e onde se troca sinal sem perceber.
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    col.objects.link(obj)
    obj["azimute_cena"] = azimute_cena
    obj["elevacao"] = elevacao
    return obj


def configurar_cor(cena, luz):
    """Regua de visualizacao. Atribuir e conferir, nunca perguntar ao enum.

    Em background o RNA lista view_transform e look como vazios, mas aceita a
    atribuicao -- e o MESMO defeito do render.engine com o Cycles, que ja custou
    uma rodada a este projeto quando renderizou em CPU calado.
    """
    c = luz.get("cor", {})
    for prop in ("view_transform", "look"):
        valor = c.get(prop)
        if not valor:
            continue
        try:
            setattr(cena.view_settings, prop, valor)
        except TypeError:
            raise SystemExit(f"o OCIO desta build nao tem {prop}={valor!r}")
        if getattr(cena.view_settings, prop) != valor:
            raise SystemExit(f"{prop} nao pegou: pedi {valor!r}, ficou "
                             f"{getattr(cena.view_settings, prop)!r}")

    cena.view_settings.exposure = c.get("exposure", 0.0)
    cena.view_settings.gamma = 1.0

    # dither SO age na conversao para 8 bits. Sem cravar a profundidade ele
    # vira decoracao e o telao bandeia no degrade do ceu.
    profundidade = str(c.get("color_depth", "8"))
    cena.render.image_settings.color_depth = profundidade

    print(f"  cor: {cena.view_settings.view_transform} / "
          f"{cena.view_settings.look} / exposure "
          f"{cena.view_settings.exposure:+.2f} / {profundidade} bits")


# --------------------------------------------------------------------------
# Exportacao para o Twinmotion (Plano A)

def exportar_fbx(caminho):
    """BASE + EVENTO + os cones de MARCOS_CAMERA, sem as cameras animadas.

    O Twinmotion importa geometria mas nao importa camera animada -- os cones
    dizem ao Natan onde cravar cada chave la dentro. object_types={'MESH'}
    deixa de fora tanto as cameras reais quanto as miras (empties), que nao
    tem uso no Twinmotion.
    """
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(Path(caminho).resolve()),
        use_selection=False,
        object_types={"MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="Y",
        axis_up="Z",
        global_scale=1.0,
    )


# --------------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dados", default="data/mapa_agroshow26.json")
    ap.add_argument("--planos-json", dest="planos_json", default="data/planos.json")
    ap.add_argument("--motor", choices=("cycles", "eevee"), default="cycles",
                    help="motor gravado na cena. cycles e o da entrega, com a "
                         "configuracao que o Natan ditou; eevee e so para "
                         "conferencia rapida")
    ap.add_argument("--relevo", default=None,
                    help="heightmap em escala de cinza para deslocar o terreno")
    ap.add_argument("--out", default=None, help="salva um .blend no caminho")
    ap.add_argument("--export-fbx", default=None,
                    help="exporta BASE+EVENTO+MARCOS_CAMERA em FBX, para o Twinmotion")
    ap.add_argument("--plano", default=None,
                    help="constroi so a regiao dos planos com este id "
                         "(ou lista separada por virgula, ex: P13,P14,P15). "
                         "Sem isso, constroi o recinto inteiro")
    ap.add_argument("--sem-camera", action="store_true",
                    help="pula a montagem das cameras -- so para conferir geometria")
    args = ap.parse_args(argv)

    dados = terreno.carregar_mapa(args.dados)

    limpar_cena()
    cols = criar_colecoes()
    centro = terreno.centro_da_arena(dados)
    mats = criar_materiais()

    pacote = planos_mod.carregar(args.planos_json, dados=dados)
    selecionados = pacote["planos"]
    if args.plano:
        ids_pedidos = set(args.plano.split(","))
        selecionados = [p for p in pacote["planos"] if p["id"] in ids_pedidos]
        faltando = ids_pedidos - {p["id"] for p in selecionados}
        if faltando:
            raise SystemExit(f"plano(s) inexistente(s) em {args.planos_json}: {sorted(faltando)}")

    bbox = bbox_dos_planos(selecionados, centro) if args.plano else None
    if bbox:
        print(f"corte por --plano {args.plano}: "
              f"x [{bbox[0]:.0f}, {bbox[1]:.0f}]  y [{bbox[2]:.0f}, {bbox[3]:.0f}]")

    print("construindo terreno...")
    terreno_obj = construir_terreno(dados, cols["BASE"], centro, args.relevo)
    aplicar(terreno_obj, mats["MAT_TERRENO"])
    construir_entorno(cols["BASE"], centro, mats)
    construir_arena(centro, cols["BASE"], mats)

    print("construindo pavilhoes...")
    n_pav = construir_pavilhoes(dados, cols["BASE"], centro, bbox)

    print("construindo portal, palco e camarotes...")
    feitas = construir_estruturas(dados, cols["BASE"], centro, bbox)

    print("construindo as zonas com footprint medido...")
    n_med = construir_medidos(dados, cols["BASE"], centro, bbox)

    print("construindo vias...")
    n_vias = construir_vias(cols["BASE"], centro, bbox)

    # Cada estrutura declara o material que a define, em estruturas.py, e aqui
    # so se obedece. O que havia antes era `if "Camarote" not in o.name`, um
    # teste sensivel a caixa contra nomes que estao em MAIUSCULAS: dava
    # verdadeiro para os quatro objetos, e o portal -- fachada de tabua, o
    # primeiro e o ultimo quadro do filme -- saia com metallic 0.3, cinza.
    # Nome de objeto nao volta a decidir material neste arquivo.
    sem_material = []
    for o in cols["BASE"].objects:
        nome_mat = o.get("material")
        if nome_mat:
            aplicar(o, mats[nome_mat])
        elif o.type == "MESH" and o.name not in ("Terreno", "PistaArena"):
            sem_material.append(o.name)
    if sem_material:
        print(f"  AVISO: sem material declarado: {sem_material[:6]}")

    n_vestidos = vestir_com_a_paleta(cols["BASE"], mats)
    print(f"  paleta medida .... {n_vestidos} predios vestidos "
          "(parede tijolo, telhado telha). O cinza inventado saiu.")

    print("construindo as zonas estimadas...")
    # so os solidos entram na conta de colisao -- terreno, pista e as vias
    # ficam de fora (ver afastar_do_medido). O update e obrigatorio: sem ele
    # `matrix_world` ainda esta na origem e toda pegada sai errada.
    bpy.context.view_layer.update()
    solidos = [(o.name, _pegada_xy(o),
                ((_pegada_xy(o)[0] + _pegada_xy(o)[2]) / 2,
                 (_pegada_xy(o)[1] + _pegada_xy(o)[3]) / 2))
               for o in cols["BASE"].objects
               if o.type == "MESH" and not o.name.startswith("Via_")
               and o.name not in ("Terreno", "PistaArena", "Entorno")]
    n_est, n_rec = construir_estimados(cols["ESTIMADO"], centro, bbox,
                                       origem=dados["_origem"], medidos=solidos)

    for o in cols["ESTIMADO"].objects:
        nome_mat = o.get("material")
        if nome_mat:
            aplicar(o, mats[nome_mat])

    print("construindo estandes...")
    cont = construir_estandes(dados, cols["EVENTO"], centro, bbox)
    for o in cols["EVENTO"].objects:
        aplicar(o, mats["MAT_LONA"])

    # A vegetacao vem DEPOIS dos estandes de proposito: arvore nao pode nascer
    # em cima de estande, e para conferir isso os estandes precisam existir.
    # Na primeira versao ela vinha antes e a conferencia so via a colecao BASE.
    print("plantando bosques e matas...")
    bpy.context.view_layer.update()
    ocupado = solidos + [
        (o.name, _pegada_xy(o),
         ((_pegada_xy(o)[0] + _pegada_xy(o)[2]) / 2,
          (_pegada_xy(o)[1] + _pegada_xy(o)[3]) / 2))
        for o in cols["EVENTO"].objects if o.type == "MESH"]
    n_arv, n_arv_rec = construir_vegetacao(dados, cols["ESTIMADO"], centro, bbox,
                                           solidos=ocupado)

    caminho_veg = RAIZ / "data" / "vegetacao.json"
    n_arb = n_arb_rec = 0
    if caminho_veg.exists():
        n_arb, n_arb_rec = construir_arbustos_de_talude(
            dados, cols["ESTIMADO"], centro,
            json.loads(caminho_veg.read_text(encoding="utf-8")),
            bbox, solidos=ocupado)
        print(f"  arbustos de talude .. {n_arb} ({n_arb_rec} recusados: "
              f"chao plano, pista ou predio)")

    n_pov, n_pov_rec = povoamento.construir(dados, bpy.context.scene.collection,
                                            centro, solidos=ocupado, bbox=bbox)
    mobiliario.construir(dados, bpy.context.scene.collection, centro,
                         solidos=ocupado, bbox=bbox)
    letreiros.construir(dados, bpy.context.scene.collection, centro, pacote)
    avulsas.construir(dados, bpy.context.scene.collection, centro,
                      fonte=letreiros._fonte(json.loads(
                          (RAIZ / "data" / "letreiros.json").read_text(
                              encoding="utf-8"))["tipografia"]["arquivo"]))

    n_cam = 0
    if not args.sem_camera:
        print("montando cameras dos planos...")
        n_cam = planos_mod.montar_cameras(pacote if not args.plano
                                          else {**pacote, "planos": selecionados,
                                                "total_quadros": max(p["_quadro_fim"] for p in selecionados)},
                                          cols["CAMERA"])

    n_marcos = 0
    if args.export_fbx:
        n_marcos = planos_mod.montar_marcos(pacote, cols["MARCOS_CAMERA"])

    cena = bpy.context.scene
    luz = json.loads((RAIZ / "data" / "luz.json").read_text(encoding="utf-8"))
    elev, azim, rot, medido = alvo_do_sol(luz)

    print(f"luz: {luz['momento']['data']} {luz['momento']['hora']}  "
          f"elevacao {elev:.1f}  azimute real "
          f"{(azim + luz['norte_do_mapa_graus']) % 360:.1f}")
    print(f"  norte do mapa: {luz['norte_do_mapa_graus']:+.1f} -> "
          f"azimute na cena {azim:.1f}")
    if medido:
        print(f"  HDRI: sol medido em {medido['azimute_deg']:.1f} / "
              f"{medido['elevacao_deg']:.1f}  -> girar ceu {rot:.1f}")
    else:
        print("  AVISO: sem data/hdri-medido.json -- ceu nao girado. Rode "
              "blender --background --python scripts/medir_hdri.py")
    print(f"  sombra: {sol.comprimento_da_sombra(elev):.1f}x a altura")

    construir_luz(cols["LUZ"], luz, elev, azim, medido)
    construir_ceu(cena, luz, rot)
    configurar_cor(cena, luz)

    # Mist como AOV: custa ~zero e e composto depois, sem re-renderizar. A 10
    # graus de elevacao sobre 170.000 m2, a perspectiva aerea e o que impede o
    # parque de ler como miniatura.
    if luz.get("atmosfera", {}).get("mist"):
        bpy.context.view_layer.use_pass_mist = True
        mundo_mist = cena.world.mist_settings
        mundo_mist.use_mist = True
        mundo_mist.start = 80.0
        mundo_mist.depth = 900.0
        mundo_mist.falloff = "INVERSE_QUADRATIC"
    configurar_render(bpy.context.scene, args.motor)

    larg_m = dados["prancha"]["largura_pt"] * terreno.ESCALA
    prof_m = dados["prancha"]["altura_pt"] * terreno.ESCALA
    dur_s = pacote["total_quadros"] / pacote["fps"]

    print("\n" + "=" * 58)
    print(f"  escala .............. {terreno.ESCALA} m/pt")
    print(f"  extensao do terreno . {larg_m:.0f} x {prof_m:.0f} m")
    print(f"  pavilhoes ........... {n_pav} (duas aguas, nao caixa)")
    print(f"  zonas medidas ....... {n_med} (footprint do desenho, altura declarada)")
    print(f"  zonas estimadas ..... {n_est} na colecao ESTIMADO "
          f"({n_rec} recusadas) -- NAO SAO MEDIDA")
    print(f"  arvores ............. {n_arv} instancias de 1 malha "
          f"({n_arv_rec} recusadas por predio ou pela bacia)")
    print(f"  estruturas .......... {len(feitas)}: "
          f"{', '.join(o.name for o in feitas) or 'nenhuma'}")
    print(f"  vias ................ {n_vias}")
    print(f"  estandes ............ {cont['instanciado']} instanciados "
          f"+ {cont['proprio']} proprios"
          + (f" (+{cont['fora_do_corte']} fora do corte)" if bbox else ""))
    print(f"  planos ............... {len(selecionados)} de {len(pacote['planos'])}"
          + (f" (corte --plano {args.plano})" if args.plano else " (filme completo)"))
    print(f"  cameras montadas ..... {n_cam}")
    if args.export_fbx:
        print(f"  marcos de camera ..... {n_marcos} (2 por plano, ida e volta)")
    print(f"  render .............. {LARGURA_RENDER}x{ALTURA_RENDER} "
          f"({LARGURA_RENDER/ALTURA_RENDER:.0f}:1)")
    print(f"  duracao do filme ..... {pacote['total_quadros']} quadros "
          f"({dur_s:.0f} s a {pacote['fps']} fps)")
    print(f"  patamares ........... arena 0 m -> shows {terreno.PATAMARES[2][2]} m "
          f"-> anel {terreno.PATAMARES[4][2]} m -> plato {terreno.PATAMARES[6][2]} m")
    print("=" * 58)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.out).resolve()))
        print(f"\nsalvo: {args.out}")

    if args.export_fbx:
        exportar_fbx(args.export_fbx)
        print(f"exportado para o Twinmotion: {args.export_fbx}")


if __name__ == "__main__":
    main()
