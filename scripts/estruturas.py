#!/usr/bin/env python3
"""
Constroi as estruturas que a cena precisa ter modeladas, e nao como caixa:
portal, palco, camarotes, pavilhoes com telhado e as vias.

Chamado por build_scene.py. Todas as funcoes recebem a colecao onde vao morar e
devolvem os objetos criados, para que quem chama aplique material e faca o
corte por regiao.

## De onde vem cada forma

Nada aqui e inventado; cada peca tem uma prova, e ela esta citada na funcao.

- **Portal**: a foto que o cliente mandou em 12/08, descrita em
  `reference/PORTAL-referencia.md`. E o primeiro e o ultimo plano do filme
  (P02 e P22). Regra do cliente, no audio: *"nos vamos dar um jeito dele, fazer
  mais barato"*. Na duvida entre duas leituras de um detalhe, a mais economica.
  Nunca mais ornamentado que a foto.
- **Palco**: `DJI_20251127184447_0110_D` 00:00:02, montado e vazio. Cobertura
  tensionada cinza sobre torres de treliça, telao de LED nas duas laterais,
  faixa de patrocinio na testeira, deck preto, caixas de som empilhadas.
- **Camarotes**: `DJI_20251128224305_0163_D` 00:00:09 e o mesmo 0110. Deck de
  madeira elevado, dividido em faixas por gradil branco de tubo, mesas altas
  redondas. **Nao ha arquibancada em nenhum quadro do recinto inteiro** -- em
  todos os eventos filmados o publico senta no talude gramado. A restricao 1 do
  cliente nao e so uma ordem: e como o parque funciona.

## O que e estimado, e esta declarado

As MEDIDAS. Nenhuma estrutura do recinto foi medida com trena -- a pendencia 4
do cliente continua aberta. O que existe e uma pessoa em pe no quadro
`1 (4)` 00:00:02, no mesmo enquadramento que o palco fixo, dando ~1,70 m. As
constantes abaixo saem dessa proporcao e do que a planta desenha. Todas estao
nomeadas e num lugar so, para trocar quando a medida real chegar.
"""

import math

import bpy
import bmesh
from mathutils import Vector

# --------------------------------------------------------------------------
# Medidas. Estimadas por proporcao contra a pessoa de ~1,70 m do quadro
# `1 (4)` 00:00:02. Trocar quando a medida em campo chegar.

# Portal celeiro
PORTAL_LARGURA = 24.0        # m, os tres vaos mais as alas laterais
PORTAL_ALTURA_ALA = 4.2      # m, ala lateral mais baixa
PORTAL_ALTURA_CUMEEIRA = 9.0  # m, topo do frontao central
PORTAL_CORPO_LARGURA = 11.0  # m, o corpo central com o frontao
PORTAL_PROFUNDIDADE = 3.0    # m

# Palco
PALCO_LARGURA = 16.0
PALCO_PROFUNDIDADE = 11.0
PALCO_DECK = 1.7             # m, altura do praticavel
PALCO_COBERTURA = 9.5        # m, ponto mais alto da cobertura
PALCO_TORRE = 10.5           # m, torre de trelica
PALCO_TORRE_LADO = 0.6       # m, secao quadrada da trelica

# Camarote
CAMAROTE_DECK = 0.9          # m, altura do deck de madeira
CAMAROTE_FAIXA = 6.0         # m, largura de cada faixa entre gradis
CAMAROTE_GRADIL = 1.1        # m, altura do gradil branco de tubo

# Pavilhao de animais
PAVILHAO_PE_DIREITO = 5.0    # m, ate o beiral
PAVILHAO_CUMEEIRA = 7.5      # m, ate a cumeeira

VIA_LARGURA = 7.0            # m, pista de mao dupla de recinto


# --------------------------------------------------------------------------
# Utilitarios

def _novo(nome, colecao):
    malha = bpy.data.meshes.new(nome)
    obj = bpy.data.objects.new(nome, malha)
    colecao.objects.link(obj)
    return obj, bmesh.new()


def _fechar(obj, bm):
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def _cubo(bm, cx, cy, cz, sx, sy, sz):
    """Caixa centrada em (cx, cy, cz) com os lados dados."""
    m = bmesh.ops.create_cube(bm, size=1.0)
    verts = [v for v in m["verts"]]
    bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=verts)
    bmesh.ops.translate(bm, vec=Vector((cx, cy, cz)), verts=verts)
    return verts


def _girar(obj, graus):
    obj.rotation_euler = (0.0, 0.0, math.radians(graus))
    return obj


# --------------------------------------------------------------------------
# Portal

def portal(nome, x, y, z, colecao, rumo_graus=0.0):
    """Fachada de celeiro: corpo central com frontao, duas alas mais baixas.

    A leitura e a economica, como o cliente pediu. Entram: tabuado vertical (a
    textura resolve), frontao em duas aguas com trelica em V invertido, tres
    vaos de passagem, letreiro em relevo e alas laterais com beiral curto. Nao
    entram barril, vaso, luminaria nem mastro -- sao adereco de foto, e a
    camera passa por aqui em 9 s no P02 e 6 s no P22.
    """
    obj, bm = _novo(nome, colecao)
    meia = PORTAL_CORPO_LARGURA / 2.0
    p = PORTAL_PROFUNDIDADE / 2.0
    ala = (PORTAL_LARGURA - PORTAL_CORPO_LARGURA) / 2.0

    # Alas laterais, mais baixas
    for lado in (-1, 1):
        cx = lado * (meia + ala / 2.0)
        _cubo(bm, cx, 0.0, PORTAL_ALTURA_ALA / 2.0,
              ala, PORTAL_PROFUNDIDADE, PORTAL_ALTURA_ALA)

    # Corpo central ate o beiral
    altura_beiral = PORTAL_ALTURA_CUMEEIRA - 2.6
    _cubo(bm, 0.0, 0.0, altura_beiral / 2.0,
          PORTAL_CORPO_LARGURA, PORTAL_PROFUNDIDADE, altura_beiral)

    # Frontao em duas aguas. As duas empenas viram triangulo, e as duas aguas
    # do telhado ligam uma empena a outra. Guardar os vertices em variavel, e
    # nao contar indice no fim da lista, evita quebrar quando outra peca entrar
    # antes desta.
    empenas = {}
    for sinal in (-1, 1):
        a = bm.verts.new((-meia, sinal * p, altura_beiral))
        b = bm.verts.new((meia, sinal * p, altura_beiral))
        c = bm.verts.new((0.0, sinal * p, PORTAL_ALTURA_CUMEEIRA))
        bm.faces.new((a, b, c))
        empenas[sinal] = (a, b, c)

    (ae, be, ce), (af, bf, cf) = empenas[-1], empenas[1]
    bm.faces.new((ae, ce, cf, af))     # agua esquerda
    bm.faces.new((be, ce, cf, bf))     # agua direita

    # Trelica em V invertido no frontao: duas barras que SOBEM DO BEIRAL PARA A
    # CUMEEIRA. A primeira versao ia ao contrario -- saia do centro e subia
    # para fora -- e as barras furavam o telhado.
    altura_frontao = PORTAL_ALTURA_CUMEEIRA - altura_beiral
    for sinal in (-1, 1):
        for lado in (-1, 1):
            dx = lado * meia * 0.62
            comp = math.hypot(dx, altura_frontao)
            barra = _cubo(bm, 0, 0, 0, 0.22, 0.14, comp)
            # Vai de (dx, beiral) ate (0, cumeeira): direcao (-dx, +altura).
            bmesh.ops.rotate(bm, verts=barra, cent=Vector((0, 0, 0)),
                             matrix=_matriz_y(math.atan2(-dx, altura_frontao)))
            bmesh.ops.translate(
                bm, verts=barra,
                vec=Vector((dx / 2.0, sinal * (p - 0.06),
                            altura_beiral + altura_frontao / 2.0)))

    # Letreiro em relevo, na testeira do corpo central
    _cubo(bm, 0.0, -p - 0.12, altura_beiral - 1.3,
          PORTAL_CORPO_LARGURA * 0.82, 0.24, 1.5)

    obj = _fechar(obj, bm)
    obj.location = (x, y, z)
    _girar(obj, rumo_graus)
    obj["referencia"] = "reference/PORTAL-referencia.md + foto do cliente 12/08"
    obj["medidas"] = "ESTIMADAS por proporcao -- ver pendencia 4"
    return obj


def _matriz_y(angulo):
    from mathutils import Matrix
    return Matrix.Rotation(angulo, 4, "Y")


# --------------------------------------------------------------------------
# Palco

def palco(nome, x, y, z, colecao, rumo_graus=0.0):
    """Deck, quatro torres de trelica, cobertura tensionada, teloes e faixa.

    Tirado de `DJI_20251127184447_0110_D` 00:00:02, que e o unico quadro do
    acervo com o palco montado E vazio -- os outros tem show acontecendo e a
    estrutura fica escondida atras de luz e gente.
    """
    obj, bm = _novo(nome, colecao)
    lx, ly = PALCO_LARGURA / 2.0, PALCO_PROFUNDIDADE / 2.0

    # Deck preto
    _cubo(bm, 0.0, 0.0, PALCO_DECK / 2.0,
          PALCO_LARGURA, PALCO_PROFUNDIDADE, PALCO_DECK)

    # Torres de trelica nos quatro cantos
    for sx in (-1, 1):
        for sy in (-1, 1):
            _cubo(bm, sx * (lx - 0.4), sy * (ly - 0.4), PALCO_TORRE / 2.0,
                  PALCO_TORRE_LADO, PALCO_TORRE_LADO, PALCO_TORRE)

    # Cobertura: caida leve da frente para o fundo, como a lona tensionada
    espessura = 0.35
    _cubo(bm, 0.0, 0.0, PALCO_COBERTURA,
          PALCO_LARGURA + 1.6, PALCO_PROFUNDIDADE + 1.2, espessura)

    # Faixa de patrocinio na testeira -- e o que aparece no quadro
    _cubo(bm, 0.0, -ly - 0.7, PALCO_COBERTURA - 0.9,
          PALCO_LARGURA + 1.6, 0.15, 1.4)

    # Telao de LED nas duas laterais da boca de cena
    for sx in (-1, 1):
        _cubo(bm, sx * (lx - 1.4), -ly + 0.6, PALCO_DECK + 3.2,
              2.4, 0.3, 4.4)

    # Cortina de fundo e laterais, ate o deck
    _cubo(bm, 0.0, ly - 0.2, PALCO_DECK + 3.6,
          PALCO_LARGURA - 0.8, 0.12, 7.2)

    # Pilhas de caixa de som no chao, nas duas pontas
    for sx in (-1, 1):
        _cubo(bm, sx * (lx + 0.9), -ly + 1.2, 1.1, 1.1, 1.1, 2.2)

    obj = _fechar(obj, bm)
    obj.location = (x, y, z)
    _girar(obj, rumo_graus)
    obj["referencia"] = "DJI_20251127184447_0110_D 00:00:02"
    return obj


# --------------------------------------------------------------------------
# Camarote

def camarote(nome, x, y, z, colecao, comprimento=48.0, faixas=2,
             rumo_graus=0.0):
    """Deck de madeira elevado, dividido em faixas por gradil branco de tubo.

    SEM ARQUIBANCADA -- restricao 1 do cliente, e confirmada por imagem: nao ha
    arquibancada em nenhum quadro do recinto inteiro. Quem quiser sentar senta
    no talude gramado, que ja esta no terreno.

    O deck e raso de proposito (0,9 m). Nos quadros ele mal levanta do chao; o
    que o desenha e o gradil branco e as mesas altas, nao a altura.
    """
    obj, bm = _novo(nome, colecao)
    largura = faixas * CAMAROTE_FAIXA
    c, l = comprimento / 2.0, largura / 2.0

    # Deck
    _cubo(bm, 0.0, 0.0, CAMAROTE_DECK / 2.0, comprimento, largura,
          CAMAROTE_DECK)

    # Gradil de tubo: nas duas bordas e entre as faixas
    for i in range(faixas + 1):
        yy = -l + i * CAMAROTE_FAIXA
        _cubo(bm, 0.0, yy, CAMAROTE_DECK + CAMAROTE_GRADIL - 0.05,
              comprimento, 0.06, 0.09)                      # travessa de cima
        _cubo(bm, 0.0, yy, CAMAROTE_DECK + CAMAROTE_GRADIL * 0.45,
              comprimento, 0.05, 0.07)                      # travessa do meio
        for k in range(int(comprimento // 2.4) + 1):        # montantes
            _cubo(bm, -c + k * 2.4, yy,
                  CAMAROTE_DECK + CAMAROTE_GRADIL / 2.0,
                  0.06, 0.06, CAMAROTE_GRADIL)

    # Mesas altas redondas, o elemento que mais aparece de cima
    for i in range(faixas):
        yy = -l + CAMAROTE_FAIXA * (i + 0.5)
        for k in range(int(comprimento // 5.0)):
            xx = -c + 2.5 + k * 5.0
            _cubo(bm, xx, yy, CAMAROTE_DECK + 0.55, 0.09, 0.09, 1.1)
            _cubo(bm, xx, yy, CAMAROTE_DECK + 1.12, 0.62, 0.62, 0.05)

    obj = _fechar(obj, bm)
    obj.location = (x, y, z)
    _girar(obj, rumo_graus)
    obj["referencia"] = "DJI_20251128224305_0163_D 00:00:09"
    obj["sem_arquibancada"] = True
    return obj


# --------------------------------------------------------------------------
# Pavilhao

def pavilhao(nome, x, y, z, largura, profundidade, colecao, rumo_graus=0.0):
    """Galpao de duas aguas, no lugar da caixa que havia antes.

    Os pavilhoes de animais sao galpao aberto nas laterais, com telha
    trapezoidal. O telhado importa: e o que se ve do alto no sobrevoo do P11, e
    caixa chapada denuncia CG antes de qualquer textura.
    """
    obj, bm = _novo(nome, colecao)
    lx, ly = largura / 2.0, profundidade / 2.0

    # Pes-direitos: duas fileiras de pilar, laterais abertas
    for sy in (-1, 1):
        for k in range(int(largura // 6.0) + 1):
            xx = -lx + k * 6.0
            _cubo(bm, xx, sy * ly, PAVILHAO_PE_DIREITO / 2.0,
                  0.32, 0.32, PAVILHAO_PE_DIREITO)

    # Oitoes fechados nas duas pontas
    for sx in (-1, 1):
        _cubo(bm, sx * lx, 0.0, PAVILHAO_PE_DIREITO / 2.0,
              0.25, profundidade, PAVILHAO_PE_DIREITO)

    # Duas aguas
    beiral = 0.7
    for sy in (-1, 1):
        a = bm.verts.new((-lx - beiral, sy * (ly + beiral),
                          PAVILHAO_PE_DIREITO))
        b = bm.verts.new((lx + beiral, sy * (ly + beiral),
                          PAVILHAO_PE_DIREITO))
        c = bm.verts.new((lx + beiral, 0.0, PAVILHAO_CUMEEIRA))
        d = bm.verts.new((-lx - beiral, 0.0, PAVILHAO_CUMEEIRA))
        bm.faces.new((a, b, c, d))

    obj = _fechar(obj, bm)
    obj.location = (x, y, z)
    _girar(obj, rumo_graus)
    return obj


# --------------------------------------------------------------------------
# Vias

def via(nome, pontos_m, colecao, elevacao, largura=VIA_LARGURA):
    """Fita de pista a partir de uma polilinha lida do mapa.

    Recebe os pontos ja em metros no mundo, e a funcao de elevacao do terreno,
    para a pista acompanhar a bacia em vez de flutuar. A fita sobe 6 cm do
    chao: no render, coplanar com o terreno da z-fighting, e 6 cm nao aparecem
    em plano nenhum desta decupagem.
    """
    if len(pontos_m) < 2:
        return None

    obj, bm = _novo(nome, colecao)
    meia = largura / 2.0
    esquerda, direita = [], []

    for i, (x, y) in enumerate(pontos_m):
        if i == 0:
            dx, dy = (pontos_m[1][0] - x, pontos_m[1][1] - y)
        elif i == len(pontos_m) - 1:
            dx, dy = (x - pontos_m[-2][0], y - pontos_m[-2][1])
        else:
            dx = pontos_m[i + 1][0] - pontos_m[i - 1][0]
            dy = pontos_m[i + 1][1] - pontos_m[i - 1][1]
        n = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / n * meia, dx / n * meia
        z = elevacao(x, y) + 0.06
        esquerda.append(bm.verts.new((x + nx, y + ny, z)))
        direita.append(bm.verts.new((x - nx, y - ny, z)))

    for i in range(len(pontos_m) - 1):
        bm.faces.new((esquerda[i], esquerda[i + 1],
                      direita[i + 1], direita[i]))

    obj = _fechar(obj, bm)
    obj["fonte"] = "data/vias.json -- tracado lido do bitmap da planta"
    return obj
