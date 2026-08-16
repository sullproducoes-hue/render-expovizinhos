"""Q2 -- a arena de rodeio e o palco fixo, quadro-heroi parado.

Por que este quadro: a folha `out/quadros-ia/P19_arena-de-rodeio/CONTATO.jpg` e' a
mais feia do lote. No REAL ha uma caixa cenica branca sobre base azul com um
telhado de UMA AGUA EM BALANCO sustentado por TRELICA METALICA ESPACIAL
APARENTE; no 3D de hoje ha uma tabua fina flutuando torta sobre uma caixa. O
antes/depois deste quadro vende sozinho.

De onde sai cada numero
-----------------------
**Planta manda em footprint** (D016): `data/footprints.json` -> `PALCO PALCO`,
20,28 x 17,67 m. As constantes de altura ja existiam em `estruturas.py:403` e
saem de proporcao medida no quadro `1 (4)__0012s`, com ~20% de incerteza
declarada -- nao sao trena.

**Footage manda em forma.** O que este arquivo acrescenta veio de olhar
`out/quadros-ia/P19_arena-de-rodeio/real/2_img-9133_005.00s.jpg` (3840x2160,
palco vazio, de dia, do nivel do chao): a trelica sob o balanco, o quadro de
trelica no topo dos fundos, os respiros da base azul e a profundidade do deck.

O que NAO se mediu: a cor. O `1 (4)` e' golden hour e o metodo do ceu (D018) so
vale em dia encoberto. O azul e o claro daqui sao PROPOSTA e estao marcados
como tal.

Uso:
  blender --background --factory-startup --python scripts/heroi_arena.py -- \
      --blend out/cena-heroi-q2.blend --saida F:/heroi/Q2/teste.png
"""

import sys
import math
import argparse
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Matrix

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from heroi_portal import (            # noqa: E402
    _novo, _fechar, _cubo, _cilindro, _prisma, _mat, _atribuir,
    vestir_com_textura, montar_luz, _anexar,
)

# ==========================================================================
# MEDIDAS

LARGURA      = 20.28     # planta, footprints.json PALCO PALCO -- este e' o
#   footprint INTEIRO (base + deck), nao a caixa cenica.
CAIXA_LARGURA = 13.60    # m -- a caixa cenica e' MAIS ESTREITA que a base: no
#   quadro do chao a base azul sobra para a direita, alem da parede branca. Ler
#   os dois na mesma largura (teste t01) deixou a caixa larga e baixa demais --
#   razao altura/largura 0,44 contra 0,67 medida na foto.
PROFUNDIDADE = 17.67     # planta
BASE_AZUL    = 1.50      # m -- formas-quinta.json: "base azul de ~1,2 m";
#   o quadro do chao mostra a base chegando a meia altura de um adulto de pe
#   sobre o deck, entao 1,5 e' a leitura desta foto, nao dos 2,4 do porao.
DECK_ESP     = 0.30
BOCA         = 5.50      # pe-direito da caixa cenica acima do deck.
#   ERA 8,90 e estava ~60% alto. O verificador mediu na foto por RAZAO ENTRE
#   ALTURAS NA MESMA VERTICAL, que nao depende de escala nem de altura de
#   camera (a camera da foto esta nivelada -- deriva de 1 grau em 200 px):
#   coluna x=930, chao y=1270, topo do deck y=1146, face de baixo da cobertura
#   y=767  ->  cobertura/deck = 503/124 = 4,06 no real, contra 6,51 no modelo.
PAREDE       = 0.35
COB_FUNDO    = 6.90      # a agua desce DO FUNDO PARA A FRENTE.
COB_FRENTE   = 5.50      #   Rebaixadas junto com a BOCA, mesma razao medida.
BALANCO      = 5.20      # m -- o telhado avanca muito alem da parede da boca,
#   e e' esse avanco que a trelica sustenta. Lido na foto contra a
#   profundidade conhecida do volume.
COB_ESP      = 0.22
TRELICA_H    = 1.15      # altura da trelica espacial sob o balanco
TRELICA_TUBO = 0.075

ARENA_RAIO_X = 42.0      # a pista de terra, oval
ARENA_RAIO_Y = 20.0      # menor que a leitura do t01: com 34 a camera ficava
#   DENTRO da pista e o primeiro plano virava um plano de terra chapado. Na
#   foto quem esta na frente e' grama, e a terra comeca a alguns metros.


def _tubo_entre(bm, a, b, raio=TRELICA_TUBO, lados=6):
    """Barra de A ate B por vertice explicito.

    NAO se cria cilindro e se gira por Euler para apontar numa direcao: a
    ordem XYZ poe a peca no eixo errado sem dar erro. E' a armadilha que a
    skill blender-assembly do proprio projeto nomeia, e foi ela que virou as
    tabuas do coroamento do portal do avesso no teste t03.
    """
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    if L < 1e-6:
        return []
    m = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=lados,
                              radius1=raio, radius2=raio, depth=L)
    vs = list(m["verts"])
    rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=rot, verts=vs)
    bmesh.ops.translate(bm, verts=vs, vec=(a + b) / 2.0)
    return vs


def criar_materiais():
    return {
        # saturacao subida: o verificador mediu S=0,49 no render contra 0,86 na
        # foto, com a MATIZ batendo (209,4 contra 207,2). Esta cor e
        # PROPOSTA declarada -- nao ha medida do azul no acervo (D024).
        "azul":     _mat("MAT_CONCHA_BASE", (0.008, 0.055, 0.345), 0.48),
        "claro":    _mat("MAT_CONCHA_PAREDE", (0.72, 0.72, 0.70), 0.72),
        "cobertura": _mat("MAT_CONCHA_COBERTURA", (0.115, 0.055, 0.040), 0.62, 0.35),
        "aco":      _mat("MAT_TRELICA", (0.145, 0.075, 0.055), 0.52, 0.55),
        "concreto": _mat("MAT_DECK", (0.36, 0.355, 0.34), 0.80),
        "terra":    _mat("MAT_ARENA", (0.072, 0.048, 0.036), 0.93),
        # MAT_TERRENO, e nao um verde meu: assim a cor sai MEDIDA e o mapa
        # entra pela variacao normalizada. O verde inventado dava matiz
        # 157 graus (ciano) contra 78 na foto, e o gramado lia como AGUA
        # PARADA, com as arvores parecendo submersas.
        "grama":    _mat("MAT_TERRENO", (0.1286, 0.1239, 0.0369), 0.88),
        "esquadria": _mat("MAT_ESQ_CONCHA", (0.80, 0.80, 0.78), 0.40),
        "poste":    _mat("MAT_POSTE", (0.045, 0.22, 0.52), 0.45, 0.3),
    }


def base_azul(col, mats):
    """Porao azul com os respiros, e o deck de concreto por cima."""
    obj, bm = _novo("Concha - base azul", col)
    _cubo(bm, 0.0, 0.0, BASE_AZUL / 2.0, LARGURA, PROFUNDIDADE, BASE_AZUL)
    # o deck AVANCA para a frente, e e' sobre ele que a plateia ve o show
    _cubo(bm, 0.0, -(PROFUNDIDADE / 2.0 + BALANCO / 2.0), BASE_AZUL / 2.0,
          LARGURA, BALANCO, BASE_AZUL)
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["azul"])

    jan, bj = _novo("Concha - respiros do porao", col)
    n = 7
    for k in range(n):
        x = -LARGURA / 2.0 + (k + 0.5) * (LARGURA / n)
        _cubo(bj, x, -(PROFUNDIDADE / 2.0 + BALANCO) - 0.02,
              BASE_AZUL * 0.62, 0.95, 0.10, 0.52)
    jan = _fechar(jan, bj)
    _atribuir(jan, mats["esquadria"])

    dk, bd = _novo("Concha - deck", col)
    _cubo(bd, 0.0, -BALANCO / 2.0, BASE_AZUL + DECK_ESP / 2.0,
          LARGURA + 0.30, PROFUNDIDADE + BALANCO + 0.30, DECK_ESP)
    dk = _fechar(dk, bd)
    _atribuir(dk, mats["concreto"])
    return obj, jan, dk


def caixa_cenica(col, mats):
    """Tres paredes claras em U: fundo e duas alas. A frente e' a boca, aberta.

    A PAREDE SOBE ATE A COBERTURA, seguindo `_cota_cobertura(y)`. A primeira
    versao usava altura CONSTANTE (`BOCA`) e a cobertura e' INCLINADA -- entao
    sobrava uma faixa de ceu aberto de 1,02 m na frente e 2,10 m no fundo, em
    todo o perimetro, com nuvem visivel no render. O verificador achou por
    amostragem de pixel; nenhum log acusaria.

    E' a mesma licao do pavilhao e da mesma familia do vao de 16-26 cm entre
    pilar e telhado: quando duas pecas se encontram, UMA funcao decide a cota
    das duas.
    """
    obj, bm = _novo("Concha - caixa cenica", col)
    z0 = BASE_AZUL + DECK_ESP - 0.05          # entra 5 cm no deck
    lx, ly = CAIXA_LARGURA / 2.0, PROFUNDIDADE / 2.0

    # parede de fundo: sobe ate a cobertura no y dela, penetrando 5 cm
    z_fundo = _cota_cobertura(ly - PAREDE / 2.0) + 0.05
    _cubo(bm, 0.0, ly - PAREDE / 2.0, (z0 + z_fundo) / 2.0,
          CAIXA_LARGURA, PAREDE, z_fundo - z0)

    # alas laterais: o topo ACOMPANHA a inclinacao, entao sao prismas no YZ
    y0, y1 = -ly, ly
    for s in (-1, 1):
        pts = [(y0, z0), (y1, z0),
               (y1, _cota_cobertura(y1) + 0.05), (y0, _cota_cobertura(y0) + 0.05)]
        x_int, x_ext = s * (lx - PAREDE), s * lx
        a = [bm.verts.new((x_int, y, z)) for y, z in pts]
        b = [bm.verts.new((x_ext, y, z)) for y, z in pts]
        bm.faces.new(a if s > 0 else list(reversed(a)))
        bm.faces.new(list(reversed(b)) if s > 0 else b)
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((a[i], a[j], b[j], b[i]))
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["claro"])
    obj["contato"] = "parede entra 0,05 m no deck"
    return obj


def _cota_cobertura(y):
    """Cota da face de baixo da agua, num y qualquer.

    FONTE UNICA. A cobertura, a trelica e o pilar leem daqui -- e' a licao do
    pavilhao, onde pilar e telhado tinham cada um a sua conta e divergiam de
    16 a 26 cm sem ninguem ver.
    """
    y_fundo = PROFUNDIDADE / 2.0
    y_frente = -(PROFUNDIDADE / 2.0 + BALANCO)
    t = (y_fundo - y) / (y_fundo - y_frente)
    return BASE_AZUL + DECK_ESP + COB_FUNDO + t * (COB_FRENTE - COB_FUNDO)


def cobertura(col, mats):
    """Uma agua so, caindo do fundo para a frente, em balanco sobre a plateia."""
    obj, bm = _novo("Concha - cobertura", col)
    y0 = PROFUNDIDADE / 2.0 + 0.35
    y1 = -(PROFUNDIDADE / 2.0 + BALANCO)
    lx = CAIXA_LARGURA / 2.0 + 0.55
    z0, z1 = _cota_cobertura(y0), _cota_cobertura(y1)
    for s in (-1, 1):
        _prisma(bm, [(y0, z0), (y1, z1), (y1, z1 + COB_ESP), (y0, z0 + COB_ESP)],
                s * lx, s * lx)      # placeholder, trocado abaixo
    bm.clear()
    # prisma no plano YZ: monta a mao, que e' mais claro que girar
    pts = [(y0, z0), (y1, z1), (y1, z1 + COB_ESP), (y0, z0 + COB_ESP)]
    frente = [bm.verts.new((-lx, y, z)) for y, z in pts]
    fundo = [bm.verts.new((lx, y, z)) for y, z in pts]
    bm.faces.new(frente)
    bm.faces.new(list(reversed(fundo)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((frente[i], frente[j], fundo[j], fundo[i]))
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["cobertura"])
    return obj


def trelica_espacial(col, mats):
    """A trelica aparente sob o balanco -- o assunto do quadro.

    Tres banzos longitudinais por plano, diagonal em zigue-zague entre eles, e
    travamento transversal. E' o que se ve por baixo no quadro do chao, e e' a
    diferenca entre 'estrutura' e 'tabua flutuando'.
    """
    obj, bm = _novo("Concha - trelica da cobertura", col)
    y_fundo = PROFUNDIDADE / 2.0
    y_frente = -(PROFUNDIDADE / 2.0 + BALANCO)
    n_plano = 5                       # planos de trelica ao longo da largura
    n_no = 12                         # nos ao longo do comprimento

    xs = [(-CAIXA_LARGURA / 2.0) + k * (CAIXA_LARGURA / (n_plano - 1))
          for k in range(n_plano)]
    ys = [y_fundo + k * (y_frente - y_fundo) / (n_no - 1) for k in range(n_no)]

    def _altura(y):
        """MISULA: a trelica AFINA ate quase nada na ponta livre.

        A primeira versao tinha TRELICA_H constante. Na foto o balanco e' uma
        misula -- alta onde nasce, fina onde termina -- e altura constante le
        como caixote pendurado.
        """
        t = (y_fundo - y) / (y_fundo - y_frente)
        return 1.35 + t * (0.42 - 1.35)

    # Banzo INFERIOR duplo + banzo SUPERIOR: seccao TRIANGULAR, que e' o que
    # faz a trelica ser ESPACIAL. Cinco trelicas planas lado a lado, que era o
    # que estava aqui, nao sao uma trelica espacial -- e o docstring prometia
    # tres banzos e o codigo montava dois.
    meia = (xs[1] - xs[0]) * 0.28
    for x in xs:
        sup = [(x, y, _cota_cobertura(y) - 0.03) for y in ys]
        inf_a = [(x - meia, y, _cota_cobertura(y) - _altura(y)) for y in ys]
        inf_b = [(x + meia, y, _cota_cobertura(y) - _altura(y)) for y in ys]
        for k in range(n_no - 1):
            _tubo_entre(bm, sup[k], sup[k + 1])
            _tubo_entre(bm, inf_a[k], inf_a[k + 1])
            _tubo_entre(bm, inf_b[k], inf_b[k + 1])
            if k % 2 == 0:
                _tubo_entre(bm, inf_a[k], sup[k + 1], 0.055)
                _tubo_entre(bm, inf_b[k], sup[k + 1], 0.055)
            else:
                _tubo_entre(bm, sup[k], inf_a[k + 1], 0.055)
                _tubo_entre(bm, sup[k], inf_b[k + 1], 0.055)
            _tubo_entre(bm, inf_a[k], inf_b[k], 0.05)
            _tubo_entre(bm, sup[k], inf_a[k], 0.055)
            _tubo_entre(bm, sup[k], inf_b[k], 0.055)
    # travamento transversal, a cada tres nos
    for k in range(0, n_no, 3):
        for j in range(n_plano - 1):
            z = _cota_cobertura(ys[k]) - _altura(ys[k])
            _tubo_entre(bm, (xs[j] + meia, ys[k], z), (xs[j + 1] - meia, ys[k], z), 0.05)
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["aco"])
    return obj


def trelica_do_topo(col, mats):
    """O quadro de trelica que aparece ACIMA do telhado, nos fundos.

    Na foto ele passa da linha da cobertura e le como uma treliça de
    iluminacao/faixa. Sem ele a silhueta do fundo fica limpa demais.
    """
    obj, bm = _novo("Concha - trelica do topo", col)
    y = PROFUNDIDADE / 2.0 - 1.2
    z0 = _cota_cobertura(y) + COB_ESP + 0.15
    h = 1.05
    lx = CAIXA_LARGURA / 2.0 - 0.6
    n = 14
    xs = [-lx + k * (2 * lx / (n - 1)) for k in range(n)]
    for k in range(n - 1):
        _tubo_entre(bm, (xs[k], y, z0), (xs[k + 1], y, z0), 0.06)
        _tubo_entre(bm, (xs[k], y, z0 + h), (xs[k + 1], y, z0 + h), 0.06)
        _tubo_entre(bm, (xs[k], y, z0), (xs[k + 1], y, z0 + h), 0.045)
        _tubo_entre(bm, (xs[k], y, z0), (xs[k], y, z0 + h), 0.045)
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["aco"])
    return obj


def pilares_do_fundo(col, mats):
    """Os dois pilares de canto que fecham o portico dos fundos.

    Sobem do deck ate a face de baixo da cobertura, e ENTRAM 5 cm nela --
    encostar rente nao e' juncao, e' z-fighting.
    """
    obj, bm = _novo("Concha - pilares", col)
    z0 = BASE_AZUL + DECK_ESP - 0.05
    for s in (-1, 1):
        for y in (PROFUNDIDADE / 2.0 - 0.4, -(PROFUNDIDADE / 2.0) + 0.4):
            topo = _cota_cobertura(y) + 0.05
            _cubo(bm, s * (CAIXA_LARGURA / 2.0 - 0.45), y, (z0 + topo) / 2.0,
                  0.5, 0.5, topo - z0)
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["claro"])
    obj["contato"] = "pilar penetra 0,05 m na cobertura"
    return obj


def arena(col, mats):
    """Pista de terra oval, talude de grama e o poste de luz azul."""
    obj, bm = _novo("Arena - pista de terra", col)
    n = 48
    cy = -(PROFUNDIDADE / 2.0 + BALANCO + ARENA_RAIO_Y + 2.0)
    pts = [(ARENA_RAIO_X * math.cos(2 * math.pi * k / n),
            cy + ARENA_RAIO_Y * math.sin(2 * math.pi * k / n)) for k in range(n)]
    vs = [bm.verts.new((x, y, 0.02)) for x, y in pts]
    bm.faces.new(vs)
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["terra"])

    gr, bg = _novo("Arena - gramado", col)
    _cubo(bg, 0.0, cy, -0.06, 420.0, 420.0, 0.12)
    gr = _fechar(gr, bg)
    _atribuir(gr, mats["grama"])

    po, bp = _novo("Arena - poste de luz", col)
    _cilindro(bp, 34.0, cy + 16.0, 5.5, 0.16, 11.0, lados=10)
    po = _fechar(po, bp)
    _atribuir(po, mats["poste"])
    return obj, gr, po


def cortina_de_arvores(col):
    """A linha de arvores do fundo. Instancia de colecao, malha uma vez so."""
    base = RAIZ / "assets" / "modelo"
    arv = _anexar(base / "island_tree_01" / "island_tree_01_1k.blend")
    if not arv:
        return []
    # A colecao do Poly Haven traz 17 objetos e SO UM e' a arvore. Os outros
    # sao os cartoes-fonte do geometry nodes (`branches_a..d`, `leaves_a..c`,
    # em LOD0 e LOD1) mais o proprio `geometry_nodes`, deslocado 7,71 m. Todos
    # com hide_render False -- instanciados 19 vezes, viraram gravetos de pe
    # sobre a grama, e uma copia inteira da arvore 12 a 20 m fora do lugar.
    # Mesmo filtro do Q1: asset de biblioteca nao entra inteiro, entra filtrado.
    def _serve(o):
        n = o.name.lower()
        if any(k in n for k in ("geometry_nodes", "lod1", "lod2",
                                "branch", "leaf", "leaves", "card")):
            return False
        return abs(o.location.x) < 1.0 and abs(o.location.y) < 1.0

    uteis = [o for o in arv if _serve(o)] or arv[:1]
    fonte = bpy.data.collections.new("ASSET_arvore_arena")   # NAO linkada
    for o in uteis:
        fonte.objects.link(o)
    feitos = []
    # ATRAS do palco, em cota ABSOLUTA. A versao anterior media a partir do
    # centro do oval; quando o oval encolheu, a cortina inteira caiu EM CIMA
    # do palco e as copas apareceram dentro da boca cenica (teste t04).
    y_cortina = PROFUNDIDADE / 2.0 + 34.0
    postos = []
    for k in range(16):
        t = k / 15.0
        # passo IRREGULAR: fileira de passo constante le como pomar, nao
        # como mata de borda. O deslocamento sai de um seno incomensuravel
        # com o passo, entao nao fecha padrao.
        jitter = 9.0 * math.sin(k * 2.399)
        postos.append((-95.0 + t * 200.0 + jitter,
                       y_cortina + 13.0 * math.sin(k * 1.77),
                       1.55 + 0.95 * abs(math.sin(k * 0.97))))
    postos += [(-46.0, 6.0, 2.6), (-58.0, 20.0, 2.2), (44.0, 12.0, 2.4)]
    # nenhuma dentro da pegada do palco: |x|>20 ou y>PROFUNDIDADE
    postos = [(x, y, s) for x, y, s in postos
              if abs(x) > LARGURA / 2.0 + 6.0 or y > PROFUNDIDADE]
    for i, (x, y, s) in enumerate(postos):
        e = bpy.data.objects.new(f"Arvore arena {i + 1}", None)
        e.instance_type = "COLLECTION"
        e.instance_collection = fonte
        e.location = (x, y, 0.0)
        e.scale = (s, s, s)
        e.rotation_euler = (0.0, 0.0, math.radians(41 * i))
        col.objects.link(e)
        feitos.append(e)
    print(f"arvores  {len(feitos)} instancias de 1 colecao "
          f"({len(uteis)} de {len(arv)} objetos; "
          f"{len(arv) - len(uteis)} cartoes/LOD descartados)")
    return feitos


def argumentos():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--blend", default=None)
    p.add_argument("--saida", default=None)
    p.add_argument("--largura", type=int, default=1600)
    p.add_argument("--altura", type=int, default=900)
    p.add_argument("--samples", type=int, default=50)
    p.add_argument("--dist", type=float, default=62.0)
    p.add_argument("--alt", type=float, default=2.30)
    p.add_argument("--lente", type=float, default=24.0)
    p.add_argument("--alvo-z", type=float, default=6.0)
    p.add_argument("--desloc-x", type=float, default=-20.0)
    p.add_argument("--alvo-x", type=float, default=9.0)
    p.add_argument("--hora", default=None,
                   help="HH:MM. Omitido, usa data/luz.json (18:15).")
    p.add_argument("--exr", action="store_true")
    return p.parse_args(argv)


def limpar():
    for c in (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
              bpy.data.cameras, bpy.data.lights, bpy.data.worlds,
              bpy.data.collections):
        for item in list(c):
            try:
                c.remove(item, do_unlink=True)
            except Exception:
                pass


def main():
    a = argumentos()
    limpar()
    cena = bpy.context.scene
    col = cena.collection
    mats = criar_materiais()

    # Texturas do PROPRIO RECINTO, deiluminadas, com a media do albedo
    # normalizada para a cor medida (erro < 0,5% em todas). Entram com albedo
    # porque nao sao biblioteca de outro lugar: sao a terra, a grama e a telha
    # deste parque. O `_Albedo` colorido e' a fonte de cor de quem nao passa
    # pelo no de variacao -- que e' o caso aqui.
    vestir_com_textura(mats["terra"], "recinto_terra_pista", 8.0, 0.85, True)
    # agora COM variacao: o material se chama MAT_TERRENO, que TEM media
    # medida em texturas-medidas.json -- e' o que destrava o caminho do contrato.
    vestir_com_textura(mats["grama"], "recinto_grama_sa", 4.5, 0.55, True)
    vestir_com_textura(mats["concreto"], "recinto_concreto_pavilhao", 2.0, 0.6, False)
    # 2,432 m: passo da onda MEDIDO por autocorrelacao no footage. A telha do
    # recinto e' ONDULADA, nao trapezoidal -- o asset CC0 antigo era o perfil
    # errado.
    vestir_com_textura(mats["cobertura"], "recinto_telha_metalica", 2.432, 1.0, False)

    base_azul(col, mats)
    caixa_cenica(col, mats)
    pilares_do_fundo(col, mats)
    cobertura(col, mats)
    trelica_espacial(col, mats)
    trelica_do_topo(col, mats)
    arena(col, mats)
    cortina_de_arvores(col)
    montar_luz(col, a.hora)

    dados = bpy.data.cameras.new("CAM_Q2")
    dados.lens = a.lente
    dados.sensor_width = 36.0
    cam = bpy.data.objects.new("CAM_Q2", dados)
    col.objects.link(cam)
    pos = Vector((a.desloc_x, -(PROFUNDIDADE / 2.0 + a.dist), a.alt))
    alvo = Vector((a.alvo_x, 0.0, a.alvo_z))
    cam.location = pos
    cam.rotation_euler = (alvo - pos).to_track_quat("-Z", "Y").to_euler()
    cena.camera = cam
    print(f"camera  dist {a.dist} m  lente {a.lente} mm  desloc x {a.desloc_x}")

    cena.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"
    try:
        prefs.get_devices()
    except Exception:
        pass
    ativos = [d.name for d in prefs.devices if (setattr(d, "use", d.type == "OPTIX")
                                               or d.use)]
    cena.cycles.device = "GPU"
    cena.cycles.use_adaptive_sampling = True
    cena.cycles.adaptive_min_samples = 10
    cena.cycles.samples = a.samples
    cena.cycles.use_denoising = True
    cena.cycles.denoiser = "OPTIX"
    cena.render.use_persistent_data = True
    cena.render.resolution_x = a.largura
    cena.render.resolution_y = a.altura
    cena.render.resolution_percentage = 100
    cena.render.image_settings.file_format = "OPEN_EXR" if a.exr else "PNG"
    if a.exr:
        cena.render.image_settings.color_depth = "32"

    n_tri = 0
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            n_tri += len(o.data.loop_triangles)
    print(f"cena    {len([o for o in bpy.data.objects if o.type=='MESH'])} malhas  "
          f"{n_tri} triangulos  dispositivo {ativos}")

    if a.blend:
        Path(a.blend).parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(a.blend).resolve()))
        print(f"blend   {a.blend}")
    if a.saida:
        s = Path(a.saida)
        s.parent.mkdir(parents=True, exist_ok=True)
        cena.render.filepath = str(s)
        if not ativos:
            print("ABORTA: nenhum OPTIX ativo -- cairia na CPU (D009)")
            sys.exit(3)
        bpy.ops.render.render(write_still=True)
        print(f"OK      {s}")


if __name__ == "__main__":
    main()
