"""Q3 -- a boca do Pavilhao 1, quadro-heroi parado, plano baixo.

Por que este quadro (NOITE-3-QUADROS.md, Fase D): estrutura RESOLVIDA em volume
pequeno -- pilar com sapata, cobertura com espessura, oitao fechado ate a
cumeeira, cumeeira e terca aparentes. E' o quadro que prova que o 3D aguenta
detalhe construtivo, e nao so silhueta de longe.

De onde sai cada numero
-----------------------
**Planta manda em footprint** (D016). `data/footprints.json` -> `PAVILHAO 1`:
51,85 x 25,59 m, area 936,2 m2, rumo 90,0 graus. O item traz
`rumo_confiavel: false` e `preenchimento 0,706` -- o footprint serve, o rumo
nao, e por isso esta cena e' montada em EIXOS LOCAIS (ver mais abaixo).

**Footage manda em forma, proporcao e cor** (D016). A foto de referencia e'
`out/quadros-ia/P03_pavilhao-1-industria-comercio-e-prestacao-de/real/
2_img-9131-004_176.00s.jpg` (3840x2160, plano baixo, dia encoberto). E' o unico
quadro do acervo onde pilar, sapata, trelica, terca, tijolo vazado e a espessura
da agua aparecem TODOS de uma vez, e em plano baixo -- que e' exatamente o
pedido da Fase D. Os dois outros candidatos foram olhados e ficaram de fora:
`3_1-1_008.00s.jpg` mostra o oitao e as tercas, mas de dentro e sem a boca;
`1_1-16_110.00s.jpg` tem a boca e a espessura da agua, mas nao tem trelica.

O que a foto entrega, item a item:

  - pilar de SECAO QUADRADA, azul escuro, com alargamento na base -- NAO e'
    tubo redondo. Olhado no recorte ampliado 2x `q3-pilar-direita.jpg`;
  - trelica de BANZO PARALELO cor ferrugem, montante vertical e diagonal
    alternada, correndo transversal e apoiada nos pilares;
  - terca fina sobre o banzo superior, e a agua com espessura visivel;
  - faixa de TIJOLO VAZADO (cobogo) no alto da parede de tijolo, logo abaixo do
    beiral -- e' o detalhe que mais denuncia o lugar;
  - luminaria tubular pendurada em fileira, e o eletroduto vermelho corrido;
  - lado esquerdo ABERTO: a boca, com verde e ceu estourado.

**Alturas: NAO sao trena.** `PE_DIREITO` sai de `estruturas.py:68`
(PAVILHAO_PE_DIREITO = 5,0 m ate o beiral), que ja estava declarado com ~20% de
incerteza. Aqui ele se parte em 4,60 m de pe-direito livre + 0,90 m de trelica,
porque na foto o banzo inferior fica claramente abaixo do beiral. A soma
respeita o numero herdado. **Isto e' proporcao lida em foto, nao medida.**

**Eixos locais, e isso e' declarado.** O `rumo_graus: 90,0` do footprint vem com
`rumo_confiavel: false`. Aplicar um rumo em que a propria planta nao confia so
mudaria de que lado o sol entra pela boca -- ou seja, trocaria a luz do quadro
por um numero que nao se sustenta. A cena e' local: comprimento em Y, largura em
X, boca em -Y, lado aberto em -X. Fica em PENDENCIAS.md.

**A cor da agua vista POR BAIXO e' PROPOSTA, e tem motivo.** `MAT_TELHA` em
`data/materiais-medidos.json` esta em albedo (1,0 / 1,0 / 0,95) -- foi amostrada
na agua VIRADA PARA O SOL, e saiu grampeada no branco. Serve para a agua vista
de cima; nao serve para a face de baixo, que e' o que este quadro mostra.
Tijolo, azul do pilar e ferrugem da trelica tambem sao PROPOSTA: nao ha medida
de nenhum dos tres no acervo (mesma situacao do azul da concha, D024).

A regra que este arquivo obedece de cabo a rabo
-----------------------------------------------
**Quando duas pecas se encontram, UMA funcao decide a cota das duas.** E' a
licao que apareceu tres vezes na noite de 16/08 (pilar x telhado do pavilhao,
mourao x portal, parede x cobertura da concha). Aqui a funcao e' `_cota_agua(x)`
e leem dela: o caibro, a terca, a agua, o oitao e o topo do pilar. Nada nesta
cena calcula altura de telhado por conta propria.

E **contato e' sobreposicao, nunca encostar rente**: 5 cm em toda juncao.

Uso:
  blender --background --factory-startup --python scripts/heroi_pavilhao.py -- \\
      --blend out/cena-heroi-q3.blend --saida F:/heroi/Q3/final-2560.png \\
      --largura 2560 --altura 1440 --samples 50
"""

import sys
import math
import argparse
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from heroi_portal import (            # noqa: E402
    _novo, _fechar, _cubo, _cilindro, _mat, _atribuir,
    vestir_com_textura, montar_luz, _anexar,
)
from heroi_arena import _tubo_entre   # noqa: E402


# ==========================================================================
# MEDIDAS

COMPRIMENTO = 51.85     # planta, footprints.json PAVILHAO 1 -- eixo Y
LARGURA     = 25.59     # planta -- eixo X
LX          = LARGURA / 2.0

PE_DIREITO  = 4.60      # chao -> banzo INFERIOR da trelica
TRELICA_H   = 1.05      # banzo inferior -> banzo superior
BANZO_SUP   = PE_DIREITO + TRELICA_H          # 5,65
CAIBRO_H    = 0.16      # o caibro que sobe do banzo superior ate a cumeeira
FLECHA      = 1.05      # subida do beiral ate a cumeeira -> 4,7 graus
TELHA_ESP   = 0.12      # "cobertura de 12 cm", NOITE-3-QUADROS.md Fase D
TERCA_LADO  = 0.10

PILAR_LADO  = 0.32      # secao quadrada
SAPATA_LADO = 0.56
SAPATA_H    = 0.34
PORTICO_N   = 13        # porticos ao longo do comprimento.
#   ERA 9 (passo de 6,5 m). Na foto a fileira de trelicas e DENSA e e ela que
#   da a profundidade do quadro; com 9 o teto lia como plano vazio. 13 da
#   passo de 4,32 m, que e o que o ritmo da foto mostra.
PILAR_XS    = (-12.30, -4.10, 4.10, 12.30)    # 4 pilares por portico

PAREDE_ESP  = 0.23      # tijolo de meia vez, aparente dos dois lados
TIJOLO_TOPO = 3.60      # tijolo cheio ate aqui
VAZADO_TOPO = 4.45      # e a faixa de cobogo dali ate aqui

LUM_Z       = 4.32      # luminaria tubular pendurada
TIRANTE_Z   = 4.78      # o eletroduto vermelho corrido


def _cota_agua(x):
    """Cota da face de BAIXO da agua, num x qualquer. FONTE UNICA.

    Duas aguas de inclinacao baixa, cumeeira em x=0. Leem daqui, e so daqui:
    o caibro, a terca, a propria agua, o oitao do fundo e o topo do pilar.
    """
    return BANZO_SUP + CAIBRO_H + (1.0 - min(abs(x), LX) / LX) * FLECHA


def criar_materiais():
    return {
        # --- MEDIDOS (data/materiais-medidos.json) ---
        "piso":    _mat("MAT_SAIBRO", (0.1362, 0.0978, 0.0704), 0.92),
        "grama":   _mat("MAT_TERRENO", (0.1286, 0.1239, 0.0369), 0.88),
        "concreto": _mat("MAT_CONCRETO", (0.36, 0.355, 0.34), 0.80),
        # --- PROPOSTA: nao ha medida no acervo, e isso fica dito ---
        # A face de BAIXO da agua. MAT_TELHA medido esta grampeado em
        # (1,0/1,0/0,95) porque foi amostrado na agua ao sol -- inutil aqui.
        #
        # 0,44 e nao os 0,185 do t01: a face de baixo da telha galvanizada e'
        # metal CLARO, e num galpao coberto ela e' a maior superficie de
        # rebote da cena inteira. Com 0,185 o interior inteiro fechava em
        # preto e o quadro perdia da foto -- que e' a Lei 3 desta noite.
        "telha":   _mat("MAT_AGUA_PAVILHAO", (0.44, 0.445, 0.45), 0.55, 0.35),
        "azul":    _mat("MAT_PILAR_AZUL", (0.021, 0.038, 0.072), 0.55),
        "ferrugem": _mat("MAT_TRELICA_PAV", (0.128, 0.052, 0.036), 0.68, 0.15),
        "tijolo":  _mat("MAT_TIJOLO", (0.155, 0.062, 0.045), 0.85),
        "vermelho": _mat("MAT_ELETRODUTO", (0.320, 0.028, 0.022), 0.45),
        "lampada": _mat("MAT_LUMINARIA", (0.85, 0.85, 0.82), 0.30,
                        emis=(1.0, 0.96, 0.88)),
    }


def acender(mats, forca):
    """Liga as luminarias de verdade, e nao so como pontinho branco.

    `_mat` deixa `Emission Strength` em 3,0 fixo -- serve para a lampada
    APARECER, nao para ILUMINAR. Num tubo de 1,24 m isso e' quase nada dentro
    de um galpao de 25 m de vao.

    Por que isso nao e' invencao estetica: a foto de referencia foi feita de
    DIA ENCOBERTO, com o domo inteiro do ceu entrando pela boca. O contrato
    desta cena e' golden hour de ceu LIMPO as 18:15 (`data/luz.json`). Sao
    dois climas diferentes, e nenhuma hora do dia fecha essa distancia --
    medido: subir o sol de 10,1 para 26,4 graus PIORA o fundo do pavilhao, de
    78,5% para 93,2% de pixel quase preto, porque a agua passa a sombrear o
    que antes entrava rasante.

    O que fecha e' o que acontece de verdade num pavilhao as 18:15: **a luz
    esta acesa**. `_mat` nao foi tocado, porque ele e' compartilhado com o Q1
    e o Q2, que o Natan ja aprovou.
    """
    b = mats["lampada"].node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Strength"].default_value = forca
    print(f"luz artificial  emissao {forca} nas luminarias")


def piso(col, mats):
    """O chao de dentro, e a grama que aparece pela boca."""
    obj, bm = _novo("Pavilhao - piso", col)
    _cubo(bm, 0.0, 0.0, -0.06, LARGURA + 2.4, COMPRIMENTO + 2.4, 0.12)
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["piso"])

    gr, bg = _novo("Pavilhao - gramado externo", col)
    # quase rente ao piso: no t01 a laje ficava 8 cm acima da grama e a face
    # lateral dela pegava o sol rasante, virando um meio-fio branco que nao
    # existe na foto e que cortava o primeiro plano em duas faixas.
    _cubo(bg, 0.0, 0.0, -0.07, 420.0, 420.0, 0.12)
    gr = _fechar(gr, bg)
    _atribuir(gr, mats["grama"])
    return obj, gr


def pilares(col, mats):
    """Pilar de secao quadrada com SAPATA aparente na base.

    O topo LE de `_cota_agua`? Nao: o pilar morre no banzo inferior da
    trelica, que e' horizontal. Mas ele penetra 5 cm nela -- encostar rente
    nao e' juncao, e' z-fighting.
    """
    obj, bm = _novo("Pavilhao - pilares", col)
    sap, bs = _novo("Pavilhao - sapatas", col)
    ys = [-COMPRIMENTO / 2.0 + k * COMPRIMENTO / (PORTICO_N - 1)
          for k in range(PORTICO_N)]
    n = 0
    for y in ys:
        for x in PILAR_XS:
            topo = PE_DIREITO + 0.05
            _cubo(bm, x, y, topo / 2.0, PILAR_LADO, PILAR_LADO, topo)
            _cubo(bs, x, y, SAPATA_H / 2.0 - 0.05,
                  SAPATA_LADO, SAPATA_LADO, SAPATA_H)
            n += 1
    obj = _fechar(obj, bm)
    sap = _fechar(sap, bs)
    _atribuir(obj, mats["azul"])
    _atribuir(sap, mats["concreto"])
    obj["contato"] = "pilar penetra 0,05 m no banzo inferior da trelica"
    sap["contato"] = "sapata entra 0,05 m no piso"
    print(f"pilares  {n} em {PORTICO_N} porticos")
    return obj, sap


def trelicas(col, mats):
    """Trelica de banzo paralelo, transversal, um por portico.

    Banzo inferior a PE_DIREITO, superior a BANZO_SUP, montante sobre cada
    pilar e diagonal alternando o sentido -- que e' o que a foto mostra.
    """
    obj, bm = _novo("Pavilhao - trelicas", col)
    ys = [-COMPRIMENTO / 2.0 + k * COMPRIMENTO / (PORTICO_N - 1)
          for k in range(PORTICO_N)]
    passo = 1.42
    n_no = int(round(LARGURA / passo)) + 1
    xs = [-LX + k * (LARGURA / (n_no - 1)) for k in range(n_no)]
    for y in ys:
        for k in range(n_no - 1):
            a, b = xs[k], xs[k + 1]
            _tubo_entre(bm, (a, y, PE_DIREITO), (b, y, PE_DIREITO), 0.075)
            _tubo_entre(bm, (a, y, BANZO_SUP), (b, y, BANZO_SUP), 0.075)
            _tubo_entre(bm, (a, y, PE_DIREITO), (a, y, BANZO_SUP), 0.052)
            if k % 2 == 0:
                _tubo_entre(bm, (a, y, PE_DIREITO), (b, y, BANZO_SUP), 0.046)
            else:
                _tubo_entre(bm, (a, y, BANZO_SUP), (b, y, PE_DIREITO), 0.046)
        _tubo_entre(bm, (xs[-1], y, PE_DIREITO), (xs[-1], y, BANZO_SUP), 0.052)
    # travamento longitudinal: liga portico a portico no banzo superior
    for x in (-LX + 0.7, -4.10, 4.10, LX - 0.7):
        for k in range(len(ys) - 1):
            _tubo_entre(bm, (x, ys[k], BANZO_SUP), (x, ys[k + 1], BANZO_SUP), 0.042)
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["ferrugem"])
    return obj


def cobertura(col, mats):
    """Caibro, TERCA APARENTE e as duas aguas com 12 cm de espessura.

    Tudo le de `_cota_agua(x)`. A terca fica ABAIXO da agua e por isso aparece
    -- e' o pedido literal da Fase D ("cumeeira e terca aparentes").
    """
    # caibros: sobem do banzo superior ate a cumeeira, um por portico
    cb, bc = _novo("Pavilhao - caibros", col)
    ys = [-COMPRIMENTO / 2.0 + k * COMPRIMENTO / (PORTICO_N - 1)
          for k in range(PORTICO_N)]
    for y in ys:
        for s in (-1, 1):
            a = (s * LX, y, _cota_agua(LX) - CAIBRO_H / 2.0)
            b = (0.0, y, _cota_agua(0.0) - CAIBRO_H / 2.0)
            _tubo_entre(bc, a, b, CAIBRO_H / 2.0, lados=4)
    cb = _fechar(cb, bc)
    _atribuir(cb, mats["ferrugem"])

    # tercas: longitudinais, apoiadas nos caibros, SOB a agua
    tc, bt = _novo("Pavilhao - tercas", col)
    n_terca = 8
    for s in (-1, 1):
        for k in range(n_terca + 1):
            x = s * LX * (k / n_terca)
            z = _cota_agua(x) - TERCA_LADO / 2.0
            _cubo(bt, x, 0.0, z, TERCA_LADO, COMPRIMENTO + 1.6, TERCA_LADO)
    tc = _fechar(tc, bt)
    _atribuir(tc, mats["ferrugem"])

    # as duas aguas: prisma no plano XZ, 12 cm de espessura
    ag, ba = _novo("Pavilhao - agua", col)
    beiral = 0.55
    y0, y1 = -(COMPRIMENTO / 2.0 + beiral), COMPRIMENTO / 2.0 + beiral
    for s in (-1, 1):
        xb = s * (LX + beiral)
        pts = [(xb, _cota_agua(LX)), (0.0, _cota_agua(0.0)),
               (0.0, _cota_agua(0.0) + TELHA_ESP),
               (xb, _cota_agua(LX) + TELHA_ESP)]
        a = [ba.verts.new((x, y0, z)) for x, z in pts]
        b = [ba.verts.new((x, y1, z)) for x, z in pts]
        ba.faces.new(a if s > 0 else list(reversed(a)))
        ba.faces.new(list(reversed(b)) if s > 0 else b)
        for i in range(4):
            j = (i + 1) % 4
            ba.faces.new((a[i], a[j], b[j], b[i]))
    ag = _fechar(ag, ba)
    _atribuir(ag, mats["telha"])
    ag["contato"] = "agua apoia na terca, que apoia no caibro -- _cota_agua(x)"
    return cb, tc, ag


def parede_lateral(col, mats):
    """Tijolo aparente no lado FECHADO (+X), com a faixa de cobogo no alto.

    O lado -X e' a BOCA e fica aberto. A faixa vazada e' o detalhe que mais
    denuncia o lugar na foto.
    """
    obj, bm = _novo("Pavilhao - parede de tijolo", col)
    x = LX - PAREDE_ESP / 2.0
    _cubo(bm, x, 0.0, TIJOLO_TOPO / 2.0, PAREDE_ESP, COMPRIMENTO, TIJOLO_TOPO)
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["tijolo"])

    vz, bv = _novo("Pavilhao - tijolo vazado", col)
    h = VAZADO_TOPO - TIJOLO_TOPO
    n = int(COMPRIMENTO / 0.42)
    for k in range(n):
        y = -COMPRIMENTO / 2.0 + (k + 0.5) * (COMPRIMENTO / n)
        # cada elemento vazado: dois montantes e duas travessas ao redor do furo
        _cubo(bv, x, y - 0.145, TIJOLO_TOPO + h / 2.0, PAREDE_ESP, 0.13, h)
        _cubo(bv, x, y, TIJOLO_TOPO + 0.055, PAREDE_ESP, 0.42, 0.11)
        _cubo(bv, x, y, VAZADO_TOPO - 0.055, PAREDE_ESP, 0.42, 0.11)
        _cubo(bv, x, y, TIJOLO_TOPO + h / 2.0, PAREDE_ESP, 0.42, 0.09)
    vz = _fechar(vz, bv)
    _atribuir(vz, mats["tijolo"])
    return obj, vz


def oitao(col, mats):
    """O fundo, FECHADO ATE A CUMEEIRA -- pedido literal da Fase D.

    O topo le de `_cota_agua(x)`, entao ele fecha na agua por construcao. Foi
    exatamente aqui que a concha do Q2 deixou 2,10 m de ceu aberto: parede de
    altura constante debaixo de cobertura inclinada.
    """
    obj, bm = _novo("Pavilhao - oitao do fundo", col)
    y = COMPRIMENTO / 2.0 - PAREDE_ESP / 2.0
    n = 40
    for k in range(n):
        x0 = -LX + k * (LARGURA / n)
        x1 = x0 + LARGURA / n
        xm = (x0 + x1) / 2.0
        z = _cota_agua(xm) + 0.05          # penetra 5 cm na agua
        _cubo(bm, xm, y, z / 2.0, LARGURA / n + 0.01, PAREDE_ESP, z)
    obj = _fechar(obj, bm)
    _atribuir(obj, mats["tijolo"])
    obj["contato"] = "oitao penetra 0,05 m na agua, cota de _cota_agua(x)"
    return obj


def instalacoes(col, mats):
    """Luminaria tubular em fileira e o eletroduto vermelho corrido.

    Nao e' enfeite: e' o que da RITMO ao quadro em perspectiva. Sem essa
    fileira o fundo do pavilhao vira um tunel vazio.
    """
    lum, bl = _novo("Pavilhao - luminarias", col)
    n = 14
    for k in range(n):
        y = -COMPRIMENTO / 2.0 + (k + 0.5) * (COMPRIMENTO / n)
        for x in (-4.10, 4.10):
            _cubo(bl, x, y, LUM_Z, 0.11, 1.24, 0.09)
    lum = _fechar(lum, bl)
    _atribuir(lum, mats["lampada"])

    el, be = _novo("Pavilhao - eletroduto", col)
    for x in (-8.2, 0.0, 8.2):
        _cilindro(be, x, 0.0, TIRANTE_Z, 0.035, COMPRIMENTO, lados=8, eixo="Y")
    for k in range(PORTICO_N):
        y = -COMPRIMENTO / 2.0 + k * COMPRIMENTO / (PORTICO_N - 1)
        # `_tubo_entre`, e NAO `_cilindro(eixo="X")`: o helper so trata "Y" e
        # o "Z" default -- um eixo="X" cai no default EM SILENCIO e devolve um
        # tubo VERTICAL de 24,6 m atravessando piso e telhado. Foi o que
        # aconteceu no teste t01, e e' a mesma familia do motor que caia para
        # CPU sem avisar: parametro ignorado em silencio e' pior que erro.
        _tubo_entre(be, (-LX + 0.5, y, TIRANTE_Z), (LX - 0.5, y, TIRANTE_Z),
                    0.03, lados=8)
    el = _fechar(el, be)
    _atribuir(el, mats["vermelho"])
    return lum, el


def arvores_da_boca(col):
    """A linha de arvores que aparece PELA BOCA, do lado aberto.

    Asset de biblioteca NAO entra inteiro, entra filtrado: a colecao do Poly
    Haven traz 17 objetos e so UM e' a arvore -- os outros sao cartoes-fonte
    (`branches_a..d`, `leaves_a..c` em LOD0 e LOD1) e um `geometry_nodes` com
    origem deslocada 7,71 m, que a escala multiplica. Sem filtro isso vira
    graveto de pe na grama, e ja custou uma rodada no Q1 e outra no Q2.
    """
    base = RAIZ / "assets" / "modelo"
    arv = _anexar(base / "island_tree_01" / "island_tree_01_1k.blend")
    if not arv:
        print("arvores  asset ausente -- quadro segue sem elas")
        return []

    def _serve(o):
        n = o.name.lower()
        if any(k in n for k in ("geometry_nodes", "lod1", "lod2",
                                "branch", "leaf", "leaves", "card")):
            return False
        return abs(o.location.x) < 1.0 and abs(o.location.y) < 1.0

    uteis = [o for o in arv if _serve(o)] or arv[:1]
    fonte = bpy.data.collections.new("ASSET_arvore_pavilhao")   # NAO linkada
    for o in uteis:
        fonte.objects.link(o)

    feitos = []
    postos = []
    for k in range(12):
        # so do lado ABERTO (-X) e sempre FORA da pegada do predio, senao a
        # copa aparece dentro do vao -- foi o erro do Q1.
        x = -(LX + 9.0 + 7.0 * abs(math.sin(k * 1.31)))
        y = -COMPRIMENTO / 2.0 + k * (COMPRIMENTO / 11.0) + 6.0 * math.sin(k * 2.399)
        postos.append((x, y, 1.7 + 0.9 * abs(math.sin(k * 0.97))))
    for i, (x, y, s) in enumerate(postos):
        e = bpy.data.objects.new(f"Arvore pavilhao {i + 1}", None)
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
    p.add_argument("--dist", type=float, default=6.0,
                   help="quanto a camera fica ANTES da boca, em metros")
    p.add_argument("--alt", type=float, default=1.58)
    p.add_argument("--lente", type=float, default=22.0)
    p.add_argument("--desloc-x", type=float, default=3.4)
    p.add_argument("--alvo-x", type=float, default=-1.6)
    p.add_argument("--alvo-z", type=float, default=3.1)
    p.add_argument("--alvo-y", type=float, default=14.0)
    p.add_argument("--hora", default=None,
                   help="HH:MM. Omitido, usa data/luz.json (18:15).")
    p.add_argument("--luminarias", type=float, default=3.0,
                   help="forca de emissao das luminarias. 3,0 = so aparecem, "
                        "nao iluminam. Ver acender().")
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
    acender(mats, a.luminarias)

    # Texturas do PROPRIO RECINTO, deiluminadas e normalizadas para a cor
    # medida (contrato em data/texturas.json). Entram COM albedo porque sao
    # deste parque; biblioteca de fora entraria so por normal e rugosidade.
    vestir_com_textura(mats["piso"], "recinto_brita_piso", 2.2, 0.9, True)
    vestir_com_textura(mats["grama"], "recinto_grama_sa", 4.5, 0.55, True)
    vestir_com_textura(mats["concreto"], "recinto_concreto_pavilhao", 2.0, 0.6, True)
    # 2,432 m: passo da onda MEDIDO por autocorrelacao no footage. Entra SEM
    # albedo -- a cor da face de baixo e' proposta, e o mapa so da o relevo da
    # onda, que e' o que se ve daqui de baixo.
    vestir_com_textura(mats["telha"], "recinto_telha_metalica", 2.432, 1.0, False)

    piso(col, mats)
    pilares(col, mats)
    trelicas(col, mats)
    cobertura(col, mats)
    parede_lateral(col, mats)
    oitao(col, mats)
    instalacoes(col, mats)
    arvores_da_boca(col)
    montar_luz(col, a.hora)

    dados = bpy.data.cameras.new("CAM_Q3")
    dados.lens = a.lente
    dados.sensor_width = 36.0
    cam = bpy.data.objects.new("CAM_Q3", dados)
    col.objects.link(cam)
    # A camera fica ANTES da boca (-Y) e olha para dentro. O alvo anda junto
    # com ela em X -- deslocar a camera sem deslocar o alvo nao reenquadra, so
    # guina (D087). Foi o erro que custou uma rodada inteira no Q1.
    pos = Vector((a.desloc_x, -(COMPRIMENTO / 2.0 + a.dist), a.alt))
    alvo = Vector((a.alvo_x, a.alvo_y, a.alvo_z))
    cam.location = pos
    cam.rotation_euler = (alvo - pos).to_track_quat("-Z", "Y").to_euler()
    cena.camera = cam
    print(f"camera  {a.dist} m antes da boca  lente {a.lente} mm  "
          f"alvo ({a.alvo_x}, {a.alvo_y}, {a.alvo_z})")

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
    print(f"cotas   pe-direito {PE_DIREITO}  banzo sup {BANZO_SUP}  "
          f"beiral {_cota_agua(LX):.2f}  cumeeira {_cota_agua(0.0):.2f}")

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
