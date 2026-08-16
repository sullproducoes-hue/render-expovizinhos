"""Q1 -- o portal, quadro-heroi parado, match-frame contra a foto do cliente.

O portal NAO aparece em nenhum dos 173 videos do acervo (docs/MATERIAIS-referencia.md),
entao nao ha nuvem de pontos nem telemetria dele. A unica imagem que existe e' a
foto que o cliente mandou em 12/08, e ela e' REGISTRO -- o portal esta construido.
Por isso o `real | 3D` deste quadro e' comparacao direta, e a camera casa com a
perspectiva da foto. Ver PENDENCIAS.md P01.

MEDIDA, e nao mais estimativa
-----------------------------
As constantes daqui foram medidas EM PIXEL na propria foto (1448x1086), com
ancora no vao de passagem, que precisa liberar caminhao (~4,2 m de altura livre).
Isso da 47,6 px/m no plano da fachada. As estimativas antigas de estruturas.py
sobreviveram bem a conferencia -- cumeeira estimada em 9,0 contra 9,1 medida.

O que a foto mostra e o codigo antigo nao tinha
-----------------------------------------------
`estruturas.py:107` decidiu, com razao para o filme, deixar de fora luminaria,
barril e vaso -- "a camera passa por aqui em 9 s no P02". O Q1 derruba essa
premissa: e' quadro PARADO e PROXIMO. Vale o que esta escrito em
reference/PORTAL-referencia.md:33 -- "Reproduza esta fachada". A ressalva do
audio ("fazer mais barato") governa leitura de detalhe ambiguo, nao omissao do
que esta na foto.

Uso:
  blender --background --factory-startup --python scripts/heroi_portal.py -- \
      --blend out/cena-heroi-q1.blend --saida F:/heroi/Q1/teste.png \
      --largura 960 --altura 540 --samples 64
"""

import sys
import json
import math
import argparse
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Matrix

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import sol as sol_mod  # noqa: E402


# ==========================================================================
# MEDIDAS -- todas com a procedencia em pixel da foto do cliente
# foto: "WhatsApp Image 2026-08-12 at 13.15.32.jpeg", 1448x1086
# chao da fachada em y=805 px; escala 47,6 px/m

ESC = 47.6                      # px por metro, no plano da fachada
PX0 = 662.5                     # x do centro do corpo central, em px

def _mx(px):   return (px - PX0) / ESC      # x em metros, a partir do centro
def _mz(py):   return (805.0 - py) / ESC    # z em metros, a partir do chao

# Corpo central -- e ele e' ASSIMETRICO.
#
# Duas leituras minhas estavam erradas e a terceira e' medida em recorte
# ampliado 3x das duas juntas (out/heroi/_portal-junta-{esquerda,direita}.jpg):
#
#   ombro ESQUERDO  x 375 px, y 460 px   (a leitura de 370 estava boa)
#   ombro DIREITO   x 1037 px, y 450 px  (eu lia 955 -- o que esta em 935 e' um
#                                         MONTANTE, nao o ombro)
#   topo achatado   x 596..907 px, y 372 px
#
# A prova de que agora esta certo e' a inclinacao, que sai como CONSEQUENCIA e
# nao como ajuste: esquerda 21,3 graus e direita 31,0 graus, contra 22,3 e 30,9
# medidos na foto pelo verificador. Frontao simetrico NUNCA daria os dois.
CORPO_X0, CORPO_X1 = _mx(375.0), _mx(1037.0)        # -6.04 .. +7.87
CORPO_OMBRO_E      = _mz(460.0)                     # 7.25 m
CORPO_OMBRO_D      = _mz(450.0)                     # 7.46 m
CORPO_OMBRO        = CORPO_OMBRO_E                  # compatibilidade
CORPO_CUMEEIRA     = _mz(372.0)                     # 9.10 m
CUME_X0, CUME_X1   = _mx(596.0), _mx(907.0)         # -1.40 .. +5.14
CUMEEIRA_MEIA      = (CUME_X1 - CUME_X0) / 2.0      # 3.27 m -- so para quem le
PROFUNDIDADE       = 3.2                            # m -- nao medivel em foto frontal

# Ala esquerda (x 150..370 px, topo 570 px, beiral de telha 635 px)
ALA_E_X0, ALA_E_X1 = _mx(150.0), _mx(370.0)         # -10.77 .. -6.14
ALA_E_TOPO         = _mz(531.0)                     # 5.76 m. ERA _mz(570) = 4,94.
#   O verificador mediu por RAZAO NA MESMA VERTICAL (D083), que nao depende de
#   escala nem de altura de camera: topo/beiral da ala esquerda da' 1,62 na foto
#   e dava 1,36 no render -- 17% baixa. A prova que se enxerga na folha: na foto
#   o topo da ala esquerda cruza a linha "PARQUE DE EXPOSICOES"; no render ele
#   cruzava a linha de baixo, "DE DOIS VIZINHOS - PR". Uma linha de texto
#   inteira mais baixo.
#   A leitura antiga de 570 e a de 552 ficam abaixo, como registro:
#   552 px do t04 subiu a ala acima da linha do letreiro, o que a foto desmente:
#   la o topo da ala esquerda fica ABAIXO da base do letreiro. Quem tinha errado
#   era a cota das luminarias, nao a do telhado. Corrigidas abaixo.
ALA_E_BEIRAL       = _mz(635.0)                     # 3.57 m

# Ala direita (x 955..1390 px, topo 460 px, beiral 600 px)
ALA_D_X0, ALA_D_X1 = _mx(1037.0), _mx(1390.0)       # +7.87 .. +15.28
ALA_D_TOPO         = _mz(452.0)                     # 7.42 m. ERA _mz(495) = 6,51.
#   Mesma medida por razao: 1,59 a 1,74 na foto contra 1,54 no render. 452 px e'
#   a leitura NO ENCONTRO com o corpo central (x 1049), e e' a mais
#   conservadora das duas: no canto (x 1355) a foto le 423 px.
#   AINDA EM ABERTO, e declarado: na foto o topo da ala direita SOBE 36 px
#   (~0,76 m) do encontro ate o canto. Aqui ele e' PLANO. Consertar isso e'
#   mudanca de forma, nao de parametro -- e o D086 ensinou que quando o ajuste
#   erra dos dois lados com a mesma magnitude, o problema e' a forma.
#   A leitura antiga de 495 fica abaixo, como registro:
#   visivel entre o ombro do corpo central (7,25) e a ala direita. Ler os dois
#   na mesma cota apagava o degrau e a fachada virava um bloco so.
ALA_D_BEIRAL       = _mz(600.0)                     # 4.31 m

# Vaos de passagem (abertura 425..870 px, verga 600 px)
VAO_LARGURA_TOTAL  = (820.0 - 425.0) / ESC          # 8.30 m -- a jamba direita
#   comeca em 820 px, nao 870: os 870 pegavam ja o portao em X da ala.
VAO_ALTURA_LIVRE   = _mz(600.0)                     # 4.31 m -- a ancora da escala
VAO_N              = 3                              # "tres vaos", PORTAL-referencia.md:20
MOURAO_LADO        = 0.46                           # m, o mourao roliço da foto

# Letreiro
LETREIRO_L1_Z      = _mz(525.0)                     # 5.88 m, centro da linha 1
LETREIRO_L1_CAPS   = 40.0 / ESC                     # 0.84 m de altura de caixa alta
LETREIRO_L2_Z      = _mz(565.0)                     # 5.04 m
LETREIRO_L2_CAPS   = 20.0 / ESC                     # 0.42 m
LETREIRO_RELEVO    = 0.035                          # m -- letra aplicada, nao pintada

# Janelas brancas de caixilho quadriculado
JANELAS = [   # (x_centro_px, z_centro_px, largura_px, altura_px)
    (200.0, 722.0, 50.0, 65.0),
    (297.0, 722.0, 55.0, 65.0),
    (1045.0, 725.0, 90.0, 90.0),
    (1212.0, 725.0, 105.0, 90.0),
]

# Portoes de correr com travessa em X -- "elemento mais caracteristico"
PORTOES_X = [   # (x_centro_px, largura_px, altura_m)
    (352.0, 92.0, 3.6),
    (905.0, 96.0, 4.1),
    (1045.0, 150.0, 4.2),
    (1225.0, 165.0, 4.2),
]

# Luminarias de ferro preto -- "seis visiveis na fachada"
LUMINARIAS_PX = [(195.0, 610.0), (300.0, 600.0), (400.0, 505.0),
                 (872.0, 505.0), (1035.0, 545.0), (1250.0, 535.0)]

BARRIS_PX   = [478.0, 512.0, 545.0, 918.0]     # x, apoiados no chao
VASOS_PX    = [372.0, 415.0, 795.0, 845.0]

MASTRO_X    = -10.6            # mastro de bandeira azul, a esquerda. NAO e'
#   _mx(30): o mastro esta 3 m A FRENTE da fachada, e nesse plano a meia-largura
#   do quadro e' menor. Ler a cota dele no plano da fachada jogava o mastro para
#   fora do enquadramento.
MASTRO_ALT  = 12.0

FONTE = RAIZ.parent / "fontes 2026" / "ArchivoNarrow-Bold.ttf"


# ==========================================================================
# Utilitarios de malha

def _novo(nome, colecao):
    malha = bpy.data.meshes.new(nome)
    obj = bpy.data.objects.new(nome, malha)
    colecao.objects.link(obj)
    return obj, bmesh.new()


def _fechar(obj, bm):
    """Fecha a malha SOLDANDO e recalculando normal.

    `estruturas.py:84` nao fazia nem um nem outro, e por isso a cumeeira dos
    pavilhoes ficava com vertice duplicado e costura aberta. Aqui vai corrigido.
    """
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.shade_smooth() if False else None
    return obj


def _cubo(bm, cx, cy, cz, sx, sy, sz):
    """Caixa CENTRADA em (cx,cy,cz), com os LADOS dados (nao meia-extensao)."""
    m = bmesh.ops.create_cube(bm, size=1.0)
    vs = list(m["verts"])
    bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=vs)
    bmesh.ops.translate(bm, vec=Vector((cx, cy, cz)), verts=vs)
    return vs


def _cilindro(bm, cx, cy, cz, raio, altura, lados=16, eixo="Z"):
    m = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=lados,
                              radius1=raio, radius2=raio, depth=altura)
    vs = list(m["verts"])
    if eixo == "Y":
        bmesh.ops.rotate(bm, verts=vs, cent=Vector((0, 0, 0)),
                         matrix=Matrix.Rotation(math.radians(90), 4, "X"))
    bmesh.ops.translate(bm, vec=Vector((cx, cy, cz)), verts=vs)
    return vs


def _prisma(bm, pontos_xz, y0, y1):
    """Extruda um poligono do plano XZ ao longo de Y. Usado na empena."""
    frente = [bm.verts.new((x, y0, z)) for x, z in pontos_xz]
    fundo = [bm.verts.new((x, y1, z)) for x, z in pontos_xz]
    bm.faces.new(frente)
    bm.faces.new(list(reversed(fundo)))
    n = len(pontos_xz)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((frente[i], frente[j], fundo[j], fundo[i]))
    return frente + fundo


# ==========================================================================
# Materiais

def _mat(nome, cor, rug, met=0.0, emis=None):
    m = bpy.data.materials.get(nome)
    if m:
        return m
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*cor, 1.0)
    b.inputs["Roughness"].default_value = rug
    b.inputs["Metallic"].default_value = met
    if emis is not None:
        b.inputs["Emission Color"].default_value = (*emis, 1.0)
        b.inputs["Emission Strength"].default_value = 3.0
    m.diffuse_color = (*cor, 1.0)
    m.roughness = rug
    m.metallic = met
    return m


def criar_materiais():
    """Cores da paleta MEDIDA do projeto (build_scene.py:163 em diante).

    MAT_MADEIRA saiu do footage do recinto; nao e' escolha. Se a textura
    deiluminada da foto do cliente ja existir em assets/textura/, ela entra
    por normal e roughness -- nunca por albedo, que e' a regra travada de
    data/texturas.json.
    """
    return {
        "madeira":  _mat("MAT_MADEIRA", (0.21, 0.11, 0.055), 0.85),
        "telha":    _mat("MAT_TELHA", (0.62, 0.63, 0.64), 0.40, 0.55),
        "telha_esc": _mat("MAT_TELHA_ESCURA", (0.075, 0.095, 0.080), 0.55, 0.35),
        "saibro":   _mat("MAT_SAIBRO", (0.136, 0.098, 0.070), 0.92),
        "branco":   _mat("MAT_ESQUADRIA", (0.80, 0.80, 0.78), 0.35),
        "vidro":    _mat("MAT_VIDRO", (0.045, 0.055, 0.065), 0.12),
        "ferro":    _mat("MAT_FERRO_PRETO", (0.018, 0.018, 0.020), 0.45, 0.6),
        "letra":    _mat("MAT_LETREIRO", (0.86, 0.86, 0.84), 0.42),
        "azul":     _mat("MAT_MASTRO", (0.035, 0.20, 0.55), 0.35, 0.3),
        # MAT_COPA, com a cor MEDIDA -- e nao um verde meu. O verde que
        # estava aqui (0,055 / 0,13 / 0,035) e a mesma familia do
        # `MAT_GRAMA = 0,055/0,145/0,030` que o D084 mandou tirar do Q2: o
        # conserto foi feito no `heroi_arena.py` e NUNCA foi portado para ca.
        # Matiz medida no render: 107,4 graus (verde-ciano) contra 71,9 da
        # medida em materiais-medidos.json. E' o mesmo desvio para o ciano, e
        # a mesma falha de "consertei num arquivo e deixei o outro" que o
        # D083 item 3 ja tinha registrado uma vez.
        "folha":    _mat("MAT_COPA", (0.1324, 0.1538, 0.0455), 0.70),
        "muro":     _mat("MAT_MURO", (0.72, 0.72, 0.70), 0.75),
        "aro":      _mat("MAT_ARO_BARRIL", (0.10, 0.085, 0.065), 0.55, 0.5),
    }


def _atribuir(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)


_MEDIDAS_LUM = None


def _media_medida(nome_material):
    """Luminancia media do mapa Diffuse, de data/texturas-medidas.json.

    E' o divisor que normaliza a mancha para media 1,0. Sem ele nao da para
    fazer a variacao sem mexer na cor -- entao, sem ele, nao se faz.
    """
    global _MEDIDAS_LUM
    if _MEDIDAS_LUM is None:
        try:
            _MEDIDAS_LUM = json.loads(
                (RAIZ / "data" / "texturas-medidas.json").read_text(encoding="utf-8")
            ).get("itens", {})
        except Exception:
            _MEDIDAS_LUM = {}
    ficha = _MEDIDAS_LUM.get(nome_material)
    return ficha.get("luminancia_media") if ficha else None


def vestir_com_textura(mat, slug, lado_m, forca_normal=1.0, com_albedo=True,
                       forca_variacao=0.30):
    """Liga os mapas PBR de assets/textura/ num material ja existente.

    Projecao BOX porque NADA nesta cena tem UV -- e' a mesma escolha de
    scripts/texturas.py:206, pelo mesmo motivo. `lado_m` e' o lado REAL da
    mancha em metros; errar isso e' o que faz a madeira virar compensado.

    `com_albedo` so e' verdadeiro para textura tirada da FOTO DO PROPRIO
    OBJETO e ja deiluminada e normalizada para a cor medida. Textura de
    biblioteca entra por normal e roughness, nunca por albedo -- e' a regra
    travada em data/texturas.json.
    """
    pasta = RAIZ / "assets" / "textura"
    def achar(mapa):
        for ext in (".jpg", ".png"):
            p = pasta / f"{slug}_{mapa}_2k{ext}"
            if p.exists():
                return p
        return None

    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapa_no = nt.nodes.new("ShaderNodeMapping")
    esc = 1.0 / lado_m
    mapa_no.inputs["Scale"].default_value = (esc, esc, esc)
    nt.links.new(coord.outputs["Object"], mapa_no.inputs["Vector"])

    def tex(caminho, colorspace):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(str(caminho))
        t.image.colorspace_settings.name = colorspace
        t.projection = "BOX"
        t.projection_blend = 0.25
        t.extension = "REPEAT"
        nt.links.new(mapa_no.outputs["Vector"], t.inputs["Vector"])
        return t

    usados = []
    if com_albedo:
        # Caminho do CONTRATO (data/texturas.json): a cor-base MEDIDA nao e'
        # sobrescrita. O que entra e' VARIACAO DE LUMINANCIA NORMALIZADA -- o
        # mapa neutro dividido pela propria media, o que deixa a media da
        # mancha em 1,0 e faz a cor final ter exatamente a cor medida como
        # media. Ligar o Albedo colorido direto (teste t04 do Q2) pinta a cor
        # duas vezes e a terra sai rosada.
        dif, media = achar("Diffuse"), _media_medida(mat.name)
        if dif and media:
            base = tuple(bsdf.inputs["Base Color"].default_value)[:3]
            t = tex(dif, "Non-Color")
            bw = nt.nodes.new("ShaderNodeRGBToBW")
            div = nt.nodes.new("ShaderNodeMath"); div.operation = "DIVIDE"
            div.inputs[1].default_value = media
            sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"
            sub.inputs[1].default_value = 1.0
            mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
            mul.inputs[1].default_value = forca_variacao
            add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"
            add.inputs[1].default_value = 1.0
            mixn = nt.nodes.new("ShaderNodeMix")
            mixn.data_type = "RGBA"; mixn.blend_type = "MULTIPLY"
            mixn.inputs["Factor"].default_value = 1.0
            mixn.inputs[6].default_value = (*base, 1.0)
            nt.links.new(t.outputs["Color"], bw.inputs["Color"])
            nt.links.new(bw.outputs["Val"], div.inputs[0])
            nt.links.new(div.outputs["Value"], sub.inputs[0])
            nt.links.new(sub.outputs["Value"], mul.inputs[0])
            nt.links.new(mul.outputs["Value"], add.inputs[0])
            nt.links.new(add.outputs["Value"], mixn.inputs[7])
            nt.links.new(mixn.outputs[2], bsdf.inputs["Base Color"])
            usados.append(f"{dif.name} (variacao/{media:.3f} x{forca_variacao})")
        else:
            alb = achar("Albedo") or achar("Diffuse")
            if alb:
                nt.links.new(tex(alb, "sRGB").outputs["Color"],
                             bsdf.inputs["Base Color"])
                usados.append(alb.name + " (albedo direto -- sem media medida)")
    r = achar("Rough")
    if r:
        nt.links.new(tex(r, "Non-Color").outputs["Color"], bsdf.inputs["Roughness"])
        usados.append(r.name)
    n = achar("nor_gl")
    if n:
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = forca_normal
        nt.links.new(tex(n, "Non-Color").outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        usados.append(n.name)
    print(f"textura {mat.name}: {usados or 'NENHUMA'}  lado {lado_m} m")
    return bool(usados)


# ==========================================================================
# Pecas

SOBREPOSICAO = 0.06     # m -- pecas se ENCAIXAM, nao se beijam


def fachada(col, mats):
    """Corpo central com empena e vaos, mais as duas alas.

    Montada POR PARTES, sem booleano. A primeira versao abria os vaos com um
    modificador BOOLEAN EXACT e o resultado foi perder o corpo central inteiro:
    a empena em prisma e as caixas das alas se tocavam em FACE COINCIDENTE, e
    solver exato sobre face coincidente devolve lixo, sem erro nenhum na tela.

    Duas jambas, uma verga por cima do vao e a empena em cima -- o vao nasce do
    espaco entre as pecas, que e determinístico. E cada peca SOBREPOE a vizinha
    em 6 cm, aplicando na propria fachada a regra que o portao de contato vai
    exigir do resto da cena: encostar rente nao e' juncao.
    """
    obj, bm = _novo("Portal - fachada", col)
    cy = PROFUNDIDADE / 2.0
    vw = VAO_LARGURA_TOTAL

    # Jambas do corpo central, dos dois lados do vao
    for x0, x1, ombro in ((CORPO_X0, -vw / 2.0, CORPO_OMBRO_E),
                          (vw / 2.0, CORPO_X1, CORPO_OMBRO_D)):
        _cubo(bm, (x0 + x1) / 2.0, cy, ombro / 2.0,
              abs(x1 - x0), PROFUNDIDADE, ombro)

    # Verga sobre os tres vaos
    alt = CORPO_OMBRO_E - VAO_ALTURA_LIVRE + SOBREPOSICAO
    _cubo(bm, 0.0, cy, VAO_ALTURA_LIVRE - SOBREPOSICAO + alt / 2.0,
          vw, PROFUNDIDADE, alt)

    # Empena TRAPEZOIDAL e ASSIMETRICA, pelos quatro pontos medidos. Nao e'
    # triangulo (leria como chale) nem simetrica (as duas aguas tem inclinacao
    # diferente na foto, e e' isso que prova a leitura).
    _prisma(bm, [(CORPO_X0, CORPO_OMBRO_E - SOBREPOSICAO),
                 (CORPO_X1, CORPO_OMBRO_D - SOBREPOSICAO),
                 (CUME_X1, CORPO_CUMEEIRA),
                 (CUME_X0, CORPO_CUMEEIRA)], 0.0, PROFUNDIDADE)

    # Alas, entrando 6 cm no corpo central
    for x0, x1, topo in ((ALA_E_X0, ALA_E_X1 + SOBREPOSICAO, ALA_E_TOPO),
                         (ALA_D_X0 - SOBREPOSICAO, ALA_D_X1, ALA_D_TOPO)):
        _cubo(bm, (x0 + x1) / 2.0, cy, topo / 2.0,
              abs(x1 - x0), PROFUNDIDADE, topo)

    obj = _fechar(obj, bm)
    _atribuir(obj, mats["madeira"])
    obj["referencia"] = "foto do cliente 12/08, medida em pixel a 47,6 px/m"
    return obj


def emolduramento(col, mats):
    """Banzo horizontal na base do frontao e montantes de canto.

    O verificador apontou a falta: na foto ha uma peca escura correndo toda a
    largura na base do frontao, e montantes verticais grossos nos ombros e nas
    juncoes com as alas. E' o que faz a fachada ler como ESTRUTURA EMOLDURADA
    em vez de superficie continua de tabua do chao ao telhado.
    """
    obj, bm = _novo("Portal - emolduramento", col)
    y = -0.16
    z_base = CORPO_OMBRO - SOBREPOSICAO

    # banzo horizontal na base do frontao, de ombro a ombro
    _cubo(bm, (CORPO_X0 + CORPO_X1) / 2.0, y, z_base - 0.16,
          CORPO_X1 - CORPO_X0 + 0.20, 0.26, 0.34)

    # montantes: os dois ombros do corpo e as duas juncoes com as alas
    for x, z0, z1 in ((CORPO_X0, 0.0, CORPO_OMBRO_E + 0.18),
                      (CORPO_X1, 0.0, CORPO_OMBRO_D + 0.18),
                      (ALA_E_X1, 0.0, ALA_E_TOPO),
                      (ALA_D_X0, 0.0, ALA_D_TOPO)):
        _cubo(bm, x, y, (z0 + z1) / 2.0, 0.34, 0.26, z1 - z0)

    # travessa sob o letreiro, que a foto tambem mostra
    _cubo(bm, (CORPO_X0 + CORPO_X1) / 2.0, y, LETREIRO_L2_Z - 0.62,
          CORPO_X1 - CORPO_X0 - 0.6, 0.22, 0.24)

    obj = _fechar(obj, bm)
    _atribuir(obj, mats["madeira"])
    return obj


def vao_de_passagem(col, mats):
    """Abre os tres vaos e poe os quatro mouroes.

    O mourao ENTRA 5 cm na verga em vez de encostar rente. Encostar rente e'
    z-fighting e nao e' juncao -- e' a regra nova do portao de contato.
    """
    largura_util = VAO_LARGURA_TOTAL - (VAO_N + 1) * MOURAO_LADO
    bao = largura_util / VAO_N
    xs = []
    x = -VAO_LARGURA_TOTAL / 2.0 + MOURAO_LADO / 2.0
    for i in range(VAO_N + 1):
        xs.append(x)
        x += bao + MOURAO_LADO

    # buraco: solido que sera subtraido da fachada por booleano
    furo, bmf = _novo("Portal - furo do vao", col)
    _cubo(bmf, 0.0, PROFUNDIDADE / 2.0, VAO_ALTURA_LIVRE / 2.0,
          VAO_LARGURA_TOTAL, PROFUNDIDADE * 2.0, VAO_ALTURA_LIVRE)
    furo = _fechar(furo, bmf)

    obj, bm = _novo("Portal - mouroes", col)
    for xi in xs:
        # +0.05 de penetracao na verga: sobreposicao, nao beijo
        _cilindro(bm, xi, PROFUNDIDADE / 2.0, (VAO_ALTURA_LIVRE + 0.05) / 2.0,
                  MOURAO_LADO / 2.0, VAO_ALTURA_LIVRE + 0.05, lados=12)
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["madeira"])
    obj["contato"] = "mourao penetra 0,05 m na verga"
    return furo, obj, xs, bao


def portao_de_ferro(col, mats, xs, bao):
    """Portoes decorativos ao fundo dos vaos: barra vertical e arco no topo."""
    obj, bm = _novo("Portal - portoes de ferro", col)
    y = PROFUNDIDADE + 0.55
    alt = 3.0
    for i in range(VAO_N):
        cx = (xs[i] + xs[i + 1]) / 2.0
        # barras verticais
        n = max(3, int(bao / 0.16))
        for k in range(n + 1):
            bx = cx - bao / 2.0 + k * (bao / n)
            _cilindro(bm, bx, y, alt / 2.0, 0.018, alt, lados=8)
        # travessas
        for z in (0.10, alt - 0.10):
            _cubo(bm, cx, y, z, bao, 0.05, 0.06)
        # arco decorativo no topo
        for k in range(17):
            t = k / 16.0
            ax = cx - bao / 2.0 + t * bao
            az = alt - 0.10 + 0.42 * math.sin(math.pi * t)
            _cilindro(bm, ax, y, az, 0.02, 0.10, lados=6)
    obj = _fechar(obj, bm)
    # FERRO PRETO, e nao branco. O verificador mediu na 3a conferencia: dentro
    # do vao central a foto tem mediana de luminancia 0,0495 com faixa de
    # 430:1 (renda preta contra lona clara), e o render tinha mediana 0,3411
    # com faixa de 35:1 -- o vao inteiro num tom so. O elemento grafico mais
    # forte do CENTRO do quadro tinha sumido. `MAT_FERRO_PRETO` (0,018) ja
    # existia na cena, sem uso.
    _atribuir(obj, mats["ferro"])
    return obj


def letreiro(col, mats):
    """PARQUE DE EXPOSICOES / *** DE DOIS VIZINHOS - PR ***, em relevo.

    Letra APLICADA na tabua, com 3,5 cm de relevo -- e' o que a foto mostra, e
    e' a diferenca entre ler como placa e ler como pintura. As estrelas viram
    geometria porque nao se pode contar com o glifo existir na fonte.
    """
    feitos = []
    fonte = None
    if FONTE.exists():
        fonte = bpy.data.fonts.load(str(FONTE))

    for texto, z, caps, nome, larg_alvo in (
        ("PARQUE DE EXPOSIÇÕES", LETREIRO_L1_Z, LETREIRO_L1_CAPS, "L1", 6.28),
        ("DE DOIS VIZINHOS - PR", LETREIRO_L2_Z, LETREIRO_L2_CAPS, "L2", 3.55),
    ):
        bpy.ops.object.text_add(location=(0, -LETREIRO_RELEVO, z))
        o = bpy.context.object
        o.name = f"Portal - letreiro {nome}"
        o.data.body = texto
        if fonte:
            o.data.font = fonte
        o.data.size = caps / 0.55          # ArchivoNarrow: caixa alta MEDIDA
        #   pelo verificador em ~0,55 do em, nao os 0,72 que eu tinha assumido.
        #   Com 0,72 a letra saia 0,72 m em vez dos 0,84 medidos na foto.
        o.data.align_x = "CENTER"
        o.data.align_y = "CENTER"
        o.data.extrude = LETREIRO_RELEVO
        o.data.space_character = 1.06
        o.rotation_euler = (math.radians(90), 0, 0)
        bpy.ops.object.convert(target="MESH")
        o = bpy.context.object
        # A placa real usa letra CONDENSADA. Com a caixa alta certa (0,84 m) a
        # ArchivoNarrow ainda sai 58% larga demais -- medido pelo verificador:
        # 9,90 m contra 6,28 m na foto. Comprime-se em X, que e' o que o
        # letrista faz, em vez de encolher a letra inteira e perder a altura.
        if o.dimensions.x > 0.01:
            o.scale.x = larg_alvo / o.dimensions.x
            bpy.ops.object.transform_apply(scale=True)
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        _atribuir(o, mats["letra"])
        feitos.append(o)

    # Seis estrelas, tres de cada lado da linha 2
    obj, bm = _novo("Portal - estrelas", col)
    r_ext, r_int = LETREIRO_L2_CAPS * 0.52, LETREIRO_L2_CAPS * 0.21
    largura_l2 = feitos[1].dimensions.x if len(feitos) > 1 else 3.55
    for lado in (-1, 1):
        for k in range(3):
            cx = lado * (largura_l2 / 2.0 + 0.30 + k * (r_ext * 2.4))
            pts = []
            for i in range(10):
                ang = math.pi / 2 + i * math.pi / 5
                r = r_ext if i % 2 == 0 else r_int
                pts.append((cx + r * math.cos(ang), r * math.sin(ang) + LETREIRO_L2_Z))
            _prisma(bm, pts, -LETREIRO_RELEVO, 0.0)
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["letra"])
    feitos.append(obj)
    return feitos


def janelas(col, mats):
    """Janela branca de caixilho quadriculado: marco, montante e travessa."""
    marco, bm = _novo("Portal - janelas", col)
    vidro, bv = _novo("Portal - vidros", col)
    for xpx, zpx, wpx, hpx in JANELAS:
        cx, cz = _mx(xpx), _mz(zpx)
        w, h = wpx / ESC, hpx / ESC
        # marco
        for dx, dz, sx, sz in ((0, h / 2, w, 0.10), (0, -h / 2, w, 0.10),
                               (-w / 2, 0, 0.10, h), (w / 2, 0, 0.10, h)):
            _cubo(bm, cx + dx, -0.06, cz + dz, sx, 0.13, sz)
        # quadriculado 2 x 3
        for k in (-1, 1):
            _cubo(bm, cx + k * w / 6.0, -0.05, cz, 0.045, 0.10, h)
        _cubo(bm, cx, -0.05, cz, w, 0.10, 0.045)
        # vidro, recuado
        _cubo(bv, cx, 0.02, cz, w - 0.10, 0.02, h - 0.10)
    marco = _fechar(marco, bm)
    vidro = _fechar(vidro, bv)
    _atribuir(marco, mats["branco"])
    _atribuir(vidro, mats["vidro"])
    return marco, vidro


def portoes_em_x(col, mats):
    """Portao de correr com travessa em X -- o elemento mais caracteristico.

    Moldura, trilho superior e as duas diagonais. As diagonais sao construidas
    de canto a canto por vertice explicito: rotacionar cilindro por Euler poe a
    peca no eixo errado, que e' a armadilha que a skill blender-assembly nomeia.
    """
    obj, bm = _novo("Portal - portoes em X", col)
    for xpx, wpx, alt in PORTOES_X:
        cx, w = _mx(xpx), wpx / ESC
        z0, z1 = 0.05, alt
        h = z1 - z0
        # moldura
        for dz in (z0, z1):
            _cubo(bm, cx, -0.05, dz, w, 0.11, 0.14)
        for dx in (-w / 2, w / 2):
            _cubo(bm, cx + dx, -0.05, (z0 + z1) / 2, 0.14, 0.11, h)
        # trilho de correr
        _cubo(bm, cx, -0.14, z1 + 0.16, w * 1.06, 0.09, 0.10)
        # as duas diagonais, canto a canto
        comp = math.hypot(w, h)
        ang = math.atan2(h, w)
        for s in (-1, 1):
            vs = _cubo(bm, 0, 0, 0, comp, 0.09, 0.13)
            bmesh.ops.rotate(bm, verts=vs, cent=Vector((0, 0, 0)),
                             matrix=Matrix.Rotation(s * ang, 4, "Y"))
            bmesh.ops.translate(bm, verts=vs,
                                vec=Vector((cx, -0.05, (z0 + z1) / 2.0)))
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["madeira"])
    return obj


def coroamento(col, mats):
    """Testeira escura no topo da empena e das alas.

    Sem isto a fachada termina numa aresta viva de madeira e le como caixa. Na
    foto existe uma faixa escura correndo o topo inteiro -- e' o rufo/testeira
    do telhado, e e' o que da espessura ao remate visto de baixo.
    """
    obj, bm = _novo("Portal - coroamento", col)
    esp, proj = 0.16, 0.26

    # Duas aguas da empena, cada uma com a SUA inclinacao, mais o rufo do topo
    _cubo(bm, (CUME_X0 + CUME_X1) / 2.0, PROFUNDIDADE / 2.0 - proj / 2.0,
          CORPO_CUMEEIRA + esp / 2.0 - 0.03,
          CUME_X1 - CUME_X0 + 0.30, PROFUNDIDADE + proj, esp)
    for x_ombro, z_ombro, x_cume in ((CORPO_X0, CORPO_OMBRO_E, CUME_X0),
                                     (CORPO_X1, CORPO_OMBRO_D, CUME_X1)):
        meia = abs(x_cume - x_ombro)
        subida = CORPO_CUMEEIRA - (z_ombro - SOBREPOSICAO)
        comp = math.hypot(meia, subida)
        s = 1 if x_ombro > x_cume else -1
        ang = math.atan2(subida, meia)
        # SINAL: a tabua vai do OMBRO a CUMEEIRA, entao o eixo e'
        # (x_ombro - x_cume, -subida). Com o sinal trocado ela apontava para
        # CIMA E PARA FORA e as duas viravam asas acima do telhado (teste t03).
        vs = _cubo(bm, 0, 0, 0, comp + 0.30, PROFUNDIDADE + proj, esp)
        bmesh.ops.rotate(bm, verts=vs, cent=Vector((0, 0, 0)),
                         matrix=Matrix.Rotation(s * ang, 4, "Y"))
        bmesh.ops.translate(bm, verts=vs, vec=Vector(
            ((x_ombro + x_cume) / 2.0, PROFUNDIDADE / 2.0 - proj / 2.0,
             (z_ombro - SOBREPOSICAO + CORPO_CUMEEIRA) / 2.0)))

    # Topo das duas alas e dos ombros do corpo
    for x0, x1, z in ((ALA_E_X0, ALA_E_X1, ALA_E_TOPO),
                      (ALA_D_X0, ALA_D_X1, ALA_D_TOPO)):
        larg = abs(x1 - x0)
        _cubo(bm, (x0 + x1) / 2.0, PROFUNDIDADE / 2.0 - proj / 2.0,
              z + esp / 2.0 - 0.03, larg + 0.20, PROFUNDIDADE + proj, esp)

    obj = _fechar(obj, bm)
    _atribuir(obj, mats["telha_esc"])
    return obj


def trelica_do_frontao(col, mats):
    """Treliça em V invertido, aparente na empena.

    `estruturas.py:148` deixou escrito o erro que a primeira versao cometeu:
    as barras saiam do centro e subiam PARA FORA, e furavam o telhado. O certo
    e' o contrario -- elas SOBEM DO OMBRO PARA A CUMEEIRA. Precedente aplicado.
    """
    obj, bm = _novo("Portal - trelica do frontao", col)
    z0 = CORPO_OMBRO_E - SOBREPOSICAO
    subida = CORPO_CUMEEIRA - z0
    y = -0.34                      # 34 cm a frente: com o sol a 10 graus
    #   e' a saliencia que faz a trelica jogar sombra na propria tabua.
    #   A 7 cm ela sumia por falta de relevo; a 13 cm ela sumia porque o
    #   CORAOMENTO avanca ate y=-0,26 e passava na frente dela. Duas causas
    #   diferentes para o mesmo sintoma -- por isso a primeira correcao nao
    #   resolveu, e por isso ela fica escrita.

    # travessa horizontal na base do frontao
    _cubo(bm, (CORPO_X0 + CORPO_X1) / 2.0, y, z0 + 0.22,
          (CORPO_X1 - CORPO_X0) * 0.58, 0.22, 0.30)

    # as duas barras do V invertido.
    #
    # DUAS CORRECOES da 3a conferencia, e as duas medidas na foto:
    #
    # a) o V NAO fecha em vertice. Na terceira conferencia o apice estava em
    #    z=9,23 contra o rufo em z=9,24, mas 0,19 m ATRAS dele -- e projetado
    #    a ponta saia 4 px ACIMA da linha do telhado. E' a familia "peca
    #    furando o telhado" do D080. Na foto o topo da empena e' ACHATADO e as
    #    duas pernas PARAM SEPARADAS ~1,3 m na cota da cumeeira. Agora elas
    #    param separadas, e 0,32 m abaixo do rufo: nao ha vertice para furar.
    # b) o V ocupava 40,0% da largura da empena; a foto le px 480..789 de
    #    375..1037 = 46,7%. Cada perna passa de 0,200 para 0,2335.
    #
    # O angulo NAO foi ajustado -- ele sai como CONSEQUENCIA das duas medidas
    # acima, em 26,4 graus contra os 24,9 medidos na foto. Numero que se
    # persegue direto e' numero que esconde a forma errada (D086).
    cx = (CORPO_X0 + CORPO_X1) / 2.0
    Z_TOPO = CORPO_CUMEEIRA - 0.32       # para de subir ANTES do rufo
    MEIA_FOLGA = 0.65                    # ~1,3 m entre as duas pontas
    for lado in (-1, 1):
        dx = lado * ((CORPO_X1 - CORPO_X0) * 0.2335)
        x_pe, z_pe = cx + dx, z0 + 0.30
        x_topo, z_topo = cx + lado * MEIA_FOLGA, Z_TOPO
        comp = math.hypot(x_topo - x_pe, z_topo - z_pe)
        vs = _cubo(bm, 0, 0, 0, comp, 0.22, 0.30)
        bmesh.ops.rotate(bm, verts=vs, cent=Vector((0, 0, 0)),
                         matrix=Matrix.Rotation(
                             math.atan2(z_topo - z_pe, x_topo - x_pe), 4, "Y"))
        bmesh.ops.translate(bm, verts=vs,
                            vec=Vector(((x_pe + x_topo) / 2.0, y,
                                        (z_pe + z_topo) / 2.0)))
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["madeira"])
    return obj


def beirais(col, mats):
    """Telha ondulada escura em beiral curto sobre as duas alas."""
    obj, bm = _novo("Portal - beirais das alas", col)
    for x0, x1, z in ((ALA_E_X0, ALA_E_X1, ALA_E_BEIRAL),
                      (ALA_D_X0, ALA_D_X1, ALA_D_BEIRAL)):
        larg = abs(x1 - x0)
        cx = (x0 + x1) / 2.0
        # laje fina inclinada para fora, projetando 0,85 m
        _cubo(bm, cx, -0.42, z, larg, 0.95, 0.07)
        # a onda: sarrafos finos, que e' o que pega o sol rasante
        n = int(larg / 0.19)
        for k in range(n):
            ox = x0 + (k + 0.5) * (larg / n)
            _cubo(bm, ox, -0.42, z + 0.055, 0.075, 0.95, 0.045)
        # testeira
        _cubo(bm, cx, -0.88, z - 0.05, larg, 0.06, 0.16)
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["telha_esc"])
    return obj


def luminarias(col, mats):
    """Luminaria de parede em ferro preto: braco, cone e a lampada."""
    obj, bm = _novo("Portal - luminarias", col)
    lamp, bl = _novo("Portal - lampadas", col)
    for xpx, zpx in LUMINARIAS_PX:
        cx, cz = _mx(xpx), _mz(zpx)
        _cubo(bm, cx, -0.12, cz + 0.30, 0.07, 0.26, 0.07)       # braco
        _cubo(bm, cx, -0.03, cz + 0.42, 0.10, 0.09, 0.22)       # costa
        m = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=10,
                                  radius1=0.20, radius2=0.075, depth=0.24)
        vs = list(m["verts"])
        bmesh.ops.translate(bm, verts=vs, vec=Vector((cx, -0.26, cz + 0.16)))
        _cilindro(bl, cx, -0.26, cz + 0.06, 0.055, 0.10, lados=8)
    obj = _fechar(obj, bm)
    lamp = _fechar(lamp, bl)
    _atribuir(obj, mats["ferro"])
    _atribuir(lamp, _mat("MAT_LAMPADA", (0.95, 0.80, 0.55), 0.3,
                         emis=(1.0, 0.78, 0.45)))
    return obj, lamp


def barris_e_vasos(col, mats):
    """Barril de madeira e vaso com folhagem, ladeando a passagem central."""
    bar, bb = _novo("Portal - barris", col)
    aro, ba = _novo("Portal - aros dos barris", col)
    for xpx in BARRIS_PX:
        cx = _mx(xpx)
        _cilindro(bb, cx, -0.75, 0.44, 0.30, 0.88, lados=14)
        for z in (0.14, 0.44, 0.74):
            m = bmesh.ops.create_cone(ba, cap_ends=False, cap_tris=False,
                                      segments=14, radius1=0.315, radius2=0.315,
                                      depth=0.07)
            bmesh.ops.translate(ba, verts=list(m["verts"]),
                                vec=Vector((cx, -0.75, z)))
    bar = _fechar(bar, bb)
    aro = _fechar(aro, ba)
    _atribuir(bar, mats["madeira"])
    _atribuir(aro, mats["aro"])

    vas, bv = _novo("Portal - vasos", col)
    fol, bf = _novo("Portal - folhagem", col)
    for xpx in VASOS_PX:
        cx = _mx(xpx)
        m = bmesh.ops.create_cone(bv, cap_ends=True, cap_tris=False, segments=14,
                                  radius1=0.20, radius2=0.29, depth=0.52)
        bmesh.ops.translate(bv, verts=list(m["verts"]),
                            vec=Vector((cx, -0.70, 0.26)))
        # folhagem: leque de laminas, que le melhor que esfera a 5 m
        for k in range(9):
            ang = k * (2 * math.pi / 9)
            incl = math.radians(26 + (k % 3) * 13)
            vs = _cubo(bf, 0, 0, 0, 0.075, 0.012, 0.78)
            bmesh.ops.rotate(bf, verts=vs, cent=Vector((0, 0, 0)),
                             matrix=Matrix.Rotation(incl, 4, "Y"))
            bmesh.ops.rotate(bf, verts=vs, cent=Vector((0, 0, 0)),
                             matrix=Matrix.Rotation(ang, 4, "Z"))
            bmesh.ops.translate(bf, verts=vs, vec=Vector((cx, -0.70, 0.86)))
    vas = _fechar(vas, bv)
    fol = _fechar(fol, bf)
    _atribuir(vas, mats["ferro"])
    _atribuir(fol, mats["folha"])
    return bar, aro, vas, fol


def cenario(col, mats):
    """So o que a lente pega: chao, o muro branco ao fundo e o mastro azul."""
    chao, bc = _novo("Cenario - chao de saibro", col)
    _cubo(bc, 0.0, -22.0, -0.05, 200.0, 200.0, 0.10)
    chao = _fechar(chao, bc)
    _atribuir(chao, mats["saibro"])

    # O que se ve PELOS VAOS na foto: um galpao claro e um muro. So isso --
    # o resto do recinto nao esta em quadro e, pela Lei 1 da noite, nao existe.
    muro, bm = _novo("Cenario - galpao ao fundo", col)
    _cubo(bm, 0.0, PROFUNDIDADE + 17.0, 3.1, 44.0, 12.0, 6.2)
    _cubo(bm, -26.0, PROFUNDIDADE + 9.0, 1.6, 14.0, 0.4, 3.2)
    muro = _fechar(muro, bm)
    _atribuir(muro, mats["muro"])

    mas, bt = _novo("Cenario - mastro azul", col)
    _cilindro(bt, MASTRO_X, -3.0, MASTRO_ALT / 2.0, 0.16, MASTRO_ALT, lados=12)
    mas = _fechar(mas, bt)
    _atribuir(mas, mats["azul"])

    # Canteiro curvo de meio-fio branco, a esquerda -- esta na foto e e' onde o
    # olho cai na borda do quadro. Sem ele o lado esquerdo fica um vazio de
    # brita que a foto nao tem.
    cant, bq = _novo("Cenario - canteiro de meio-fio", col)
    cx, cy_, raio = -11.3, -6.2, 3.0     # mesma razao do mastro
    n = 26
    for k in range(n):
        a0 = math.pi * (0.15 + 0.72 * k / n)
        a1 = math.pi * (0.15 + 0.72 * (k + 1) / n)
        for a in (a0,):
            _cubo(bq, cx + raio * math.cos(a), cy_ + raio * math.sin(a) * 0.62,
                  0.19, 0.42, 0.42, 0.38)
    _cubo(bq, cx, cy_, 0.10, raio * 1.9, raio * 1.18, 0.20)
    cant = _fechar(cant, bq)
    _atribuir(cant, mats["muro"])

    # Folhagem do canteiro: leque de laminas, que le melhor que esfera a 20 m
    fol, bf = _novo("Cenario - folhagem do canteiro", col)
    for k in range(22):
        ang = k * 2.399
        r = raio * 0.62 * (0.25 + 0.72 * ((k * 7) % 11) / 11.0)
        px = cx + r * math.cos(ang)
        py = cy_ + r * math.sin(ang) * 0.62
        alt = 0.55 + 0.55 * (((k * 5) % 7) / 7.0)
        for j in range(7):
            vs = _cubo(bf, 0, 0, 0, 0.07, 0.012, alt)
            bmesh.ops.rotate(bf, verts=vs, cent=Vector((0, 0, 0)),
                             matrix=Matrix.Rotation(math.radians(22 + j * 9), 4, "Y"))
            bmesh.ops.rotate(bf, verts=vs, cent=Vector((0, 0, 0)),
                             matrix=Matrix.Rotation(j * (2 * math.pi / 7) + ang, 4, "Z"))
            bmesh.ops.translate(bf, verts=vs, vec=Vector((px, py, 0.22 + alt / 2.4)))
    fol = _fechar(fol, bf)
    _atribuir(fol, mats["folha"])
    return chao, muro, mas, cant, fol


def _anexar(caminho_blend):
    """Anexa todos os objetos MESH de um .blend de biblioteca."""
    p = Path(caminho_blend)
    if not p.exists():
        print(f"aviso: asset ausente -- {p}")
        return []
    antes = set(bpy.data.objects)
    with bpy.data.libraries.load(str(p), link=False) as (de, para):
        para.objects = list(de.objects)
    novos = [o for o in bpy.data.objects if o not in antes and o.type == "MESH"]
    return novos


def vegetacao(col):
    """A arvore da borda direita e o macico do canteiro esquerdo.

    Instancia, nunca copia: a mesma malha entra uma vez e e' reusada. Os
    assets sao CC0 do Poly Haven, com licenca gravada em
    assets/_procedencia.json -- e' job de cliente, licenca de uso pessoal nao
    serve aqui.
    """
    base = RAIZ / "assets" / "modelo"
    arv = _anexar(base / "island_tree_01" / "island_tree_01_1k.blend")
    if not arv:
        return []

    # O asset vem em 17 objetos. A primeira versao movia so o arv[0] e linkava
    # os outros 16 na cena -- eles ficaram na ORIGEM, e um deles apareceu
    # plantado no meio do vao de passagem no teste t06.
    #
    # O jeito certo e' INSTANCIA DE COLECAO: a colecao de origem nao entra na
    # cena (logo nao renderiza no lugar errado) e cada Empty a instancia
    # inteira. Malha uma vez so na VRAM, que e a ordem de 8 GB.
    # A colecao do Poly Haven traz LOD0 E LOD1 sobrepostos, mais um objeto
    # `geometry_nodes` deslocado -7,71 m em X. Com escala 2,4 esse deslocamento
    # vira -18,5 m e a copia aterrissa DENTRO do vao de passagem, 2,9 m acima da
    # cumeeira -- o verificador achou uma arvore de 12 m plantada no meio do
    # portao, que e' justamente o plano de fechamento do filme.
    def _serve(o):
        n = o.name.lower()
        if "geometry_nodes" in n or "lod1" in n or "lod2" in n:
            return False
        return abs(o.location.x) < 1.0 and abs(o.location.y) < 1.0

    uteis = [o for o in arv if _serve(o)] or arv[:1]
    descartados = len(arv) - len(uteis)
    fonte = bpy.data.collections.new("ASSET_island_tree_01")   # NAO linkada
    for o in uteis:
        fonte.objects.link(o)

    # A arvore da foto passa do telhado da ala direita (6,5 m); o asset tem
    # 5,0 m, entao 2,4x poe a copa em ~12 m. Escalar folha fotogrametrica muda
    # o tamanho da folha -- aceitavel na BORDA do quadro, nao no centro.
    # A arvore 1 estava em (19,5 / 6,0) e a copa cruzava a ala direita
    # (fachada ate x=15,28, y 0..3,2) subindo 2,92 m acima da cumeeira.
    # Nao aparecia porque o enquadramento estava errado -- consertar o
    # quadro revelaria a arvore. Afastada para tras e para fora.
    postos = [(24.0, 17.0, 2.4), (-16.5, 12.0, 1.6), (31.0, 26.0, 2.0),
              (-24.0, 20.0, 1.8)]
    feitos = []
    for i, (x, y, s) in enumerate(postos):
        e = bpy.data.objects.new(f"Arvore {i + 1}", None)
        e.instance_type = "COLLECTION"
        e.instance_collection = fonte
        e.location = (x, y, 0.0)
        e.scale = (s, s, s)
        e.rotation_euler = (0.0, 0.0, math.radians(53 * i))
        col.objects.link(e)
        feitos.append(e)
    print(f"vegetacao  {len(feitos)} instancias de 1 colecao "
          f"({len(uteis)} de {len(arv)} objetos do asset; "
          f"{descartados} descartados por LOD duplicado ou origem deslocada)")
    return feitos


# ==========================================================================
# Luz -- contrato de data/luz.json, sem invencao

def montar_luz(col, hora_override=None):
    luz = json.loads((RAIZ / "data" / "luz.json").read_text(encoding="utf-8"))
    medido = json.loads((RAIZ / "data" / "hdri-medido.json").read_text(encoding="utf-8"))

    escolhido = luz["hdri"]["escolhido"]
    ficha = next(i for i in medido["itens"] if escolhido in i["arquivo"])
    hdr = RAIZ / ficha["arquivo"]

    data = luz["momento"]["data"]
    hora = hora_override or luz["momento"]["hora"]
    ano, mes, dia = (int(v) for v in data.split("-"))
    hh, mm = (int(v) for v in hora.split(":"))
    elev, azim = sol_mod.posicao(ano, mes, dia, hh + mm / 60.0,
                                 luz["local"]["lat"], luz["local"]["lon"],
                                 luz["local"]["tz"])
    norte = luz["norte_do_mapa_graus"]

    # A rotacao do ceu e ALVO - MEDIDO. O azimute do HDRI nunca manda: ele
    # depende de para onde o fotografo apontou a camera.
    alvo_cena = azim - norte
    giro = math.radians(alvo_cena - ficha["azimute_deg"])

    mundo = bpy.data.worlds.new("Mundo AGROSHOW")
    bpy.context.scene.world = mundo
    mundo.use_nodes = True
    nt = mundo.node_tree
    nt.nodes.clear()
    saida = nt.nodes.new("ShaderNodeOutputWorld")
    fundo = nt.nodes.new("ShaderNodeBackground")
    tex = nt.nodes.new("ShaderNodeTexEnvironment")
    mapa = nt.nodes.new("ShaderNodeMapping")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    img = bpy.data.images.load(str(hdr))
    img.colorspace_settings.name = "Linear Rec.709"   # sRGB aqui escureceria tudo
    tex.image = img
    mapa.inputs["Rotation"].default_value[2] = giro
    fundo.inputs["Strength"].default_value = luz["hdri"]["forca"]
    nt.links.new(coord.outputs["Generated"], mapa.inputs["Vector"])
    nt.links.new(mapa.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], fundo.inputs["Color"])
    nt.links.new(fundo.outputs["Background"], saida.inputs["Surface"])

    dados = bpy.data.lights.new("SOL", type="SUN")
    dados.energy = luz["sol"]["energia"]
    dados.angle = math.radians(luz["sol"]["angulo_deg"])
    dados.color = tuple(ficha["cor_do_disco"])
    obj = bpy.data.objects.new("SOL", dados)
    col.objects.link(obj)
    # `sol.direcao` devolve o vetor que aponta DA CENA PARA O SOL.
    # `to_track_quat("Z","Y")` mapeia +Z local nesse vetor, e a SUN emite ao
    # longo do -Z local -- entao a luz viaja em -d, do sol para o chao. Mesma
    # convencao de build_scene.py:2338, que foi calibrada na cena real.
    # A primeira versao daqui usava (-d) e ficava apontando a luz PARA o sol:
    # nao dava erro, so deixava a fachada chapada e sem sombra.
    d = Vector(sol_mod.direcao(elev, azim, norte))
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()

    cena = bpy.context.scene
    try:
        cena.view_settings.view_transform = luz["cor"]["view_transform"]
        cena.view_settings.look = luz["cor"]["look"]
        cena.view_settings.exposure = luz["cor"]["exposure"]
    except Exception as e:
        print(f"aviso: regua de cor nao aplicada -- {e}")

    print(f"luz  {data} {hora}  elev {elev:.2f}  azim {azim:.2f}  "
          f"norte {norte}  giro do ceu {math.degrees(giro):.2f}  hdri {escolhido}")
    return obj


# ==========================================================================
# Camera -- casada com a perspectiva da foto do cliente (P01)

def montar_camera(col, dist, alt, lente, alvo_z, desloc_x, alvo_x=0.0):
    dados = bpy.data.cameras.new("CAM_Q1")
    dados.lens = lente
    dados.sensor_width = 36.0
    obj = bpy.data.objects.new("CAM_Q1", dados)
    col.objects.link(obj)
    # O ALVO tambem anda. A versao anterior mirava sempre x=0: mover so o olho
    # gira a camera e o eixo optico continua cruzando o plano da fachada em
    # x=0, que cai no centro exato do quadro. O verificador provou pelo pixel --
    # 25% da ala direita ficava cortada e o vazio a esquerda nao mudava.
    pos = Vector((desloc_x, -dist, alt))
    alvo = Vector((alvo_x, 0.0, alvo_z))
    obj.location = pos
    obj.rotation_euler = (alvo - pos).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = obj
    hfov = 2 * math.degrees(math.atan(dados.sensor_width / (2 * lente)))
    print(f"camera  dist {dist} m  alt {alt} m  lente {lente} mm  "
          f"hFOV {hfov:.1f} deg  alvo z {alvo_z}")
    return obj


# ==========================================================================

def argumentos():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--blend", default=None)
    p.add_argument("--saida", default=None)
    p.add_argument("--largura", type=int, default=960)
    p.add_argument("--altura", type=int, default=540)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--dist", type=float, default=23.6)
    p.add_argument("--alt", type=float, default=1.62)
    p.add_argument("--lente", type=float, default=28.0)
    p.add_argument("--alvo-z", type=float, default=4.2)
    p.add_argument("--desloc-x", type=float, default=2.26)
    p.add_argument("--alvo-x", type=float, default=2.26)
    # +2,26 = centro real da fachada. Ela vai de -10,77 a +15,28, e nao e
    # simetrica: com a camera em x=0 sobrava ceu a esquerda e a ala direita
    # saia cortada.
    p.add_argument("--exr", action="store_true")
    p.add_argument("--bounces", type=int, default=None,
                   help="cheio = 32. Omitido, usa o padrao do Cycles.")
    return p.parse_args(argv)


def limpar():
    for c in (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
              bpy.data.cameras, bpy.data.lights, bpy.data.worlds):
        for item in list(c):
            c.remove(item, do_unlink=True)


def main():
    a = argumentos()
    limpar()
    cena = bpy.context.scene
    col = cena.collection

    mats = criar_materiais()
    # A madeira do portal veio da FOTO DO CLIENTE, deiluminada e com a media do
    # albedo normalizada para a cor medida -- por isso entra com albedo.
    # Normal a 0,55 e nao 1,0: a madeira do mapa esta ampliada ~14x (166 px
    # nativos -> 2048), entao a fibra fina e' INTERPOLACAO, nao medida. A forca
    # cheia (teste anterior) exagerava a interpolacao e a tabua lia como palha.
    # Cadencia, largura de tabua e junta continuam reais.
    vestir_com_textura(mats["madeira"], "recinto_madeira_portal", 2.0, 0.55, True)
    vestir_com_textura(mats["telha_esc"], "recinto_telha_metalica", 1.4, 1.0, False)
    # brita do PROPRIO recinto, deiluminada. Entra pela variacao normalizada:
    # MAT_SAIBRO tem media medida em texturas-medidas.json, entao da' para
    # manchar sem mexer na cor.
    vestir_com_textura(mats["saibro"], "recinto_brita_piso", 2.2, 0.85, True)

    fachada(col, mats)
    furo, mouroes, xs, bao = vao_de_passagem(col, mats)
    bpy.data.objects.remove(furo, do_unlink=True)   # o vao ja nasce das partes

    portao_de_ferro(col, mats, xs, bao)
    letreiro(col, mats)
    janelas(col, mats)
    portoes_em_x(col, mats)
    coroamento(col, mats)
    emolduramento(col, mats)
    trelica_do_frontao(col, mats)
    beirais(col, mats)
    luminarias(col, mats)
    barris_e_vasos(col, mats)
    cenario(col, mats)
    vegetacao(col)
    montar_luz(col)
    montar_camera(col, a.dist, a.alt, a.lente, a.alvo_z, a.desloc_x, a.alvo_x)

    # -------- render
    cena.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    try:
        prefs.get_devices()
    except Exception:
        pass
    ativos = []
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
        if d.use:
            ativos.append(d.name)
    cena.cycles.device = "GPU"
    cena.cycles.use_adaptive_sampling = True
    cena.cycles.adaptive_min_samples = 10
    cena.cycles.samples = a.samples
    cena.cycles.use_denoising = True
    cena.cycles.denoiser = "OPTIX"
    cena.render.use_persistent_data = True
    if a.bounces:
        c = cena.cycles
        c.max_bounces = a.bounces
        c.diffuse_bounces = c.glossy_bounces = c.transmission_bounces = a.bounces
        c.volume_bounces = a.bounces
        c.transparent_max_bounces = a.bounces
    cena.render.resolution_x = a.largura
    cena.render.resolution_y = a.altura
    cena.render.resolution_percentage = 100
    if a.exr:
        cena.render.image_settings.file_format = "OPEN_EXR"
        cena.render.image_settings.color_depth = "32"
    else:
        cena.render.image_settings.file_format = "PNG"

    n_obj = len([o for o in bpy.data.objects if o.type == "MESH"])
    n_tri = sum(len(o.data.loop_triangles) for o in bpy.data.objects
                if o.type == "MESH" and (o.data.calc_loop_triangles() or True))
    print(f"cena    {n_obj} malhas  {n_tri} triangulos  dispositivo {ativos}")

    if a.blend:
        Path(a.blend).parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.blend).resolve()))
        print(f"blend   {a.blend}")

    if a.saida:
        saida = Path(a.saida)
        saida.parent.mkdir(parents=True, exist_ok=True)
        cena.render.filepath = str(saida)
        if not ativos:
            print("ABORTA: nenhum OPTIX ativo -- cairia na CPU (D009)")
            sys.exit(3)
        bpy.ops.render.render(write_still=True)
        print(f"OK      {saida}")


if __name__ == "__main__":
    main()
