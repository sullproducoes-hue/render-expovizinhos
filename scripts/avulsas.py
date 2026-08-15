#!/usr/bin/env python3
"""Pecas avulsas: silo, tendas, porteira, guiche, curral, torre, inflavel, trator.

Ordem do Natan em 15/08: *"faça o silo ao lado do mapa que eu reposiciono no
blender depois, quero que crie todos as tendas e estruturas e posicione no lugar
que ja sabe mas o que não sabe quero que deixe do lado"*.

Entao: quem tem posicao medida vai para o lugar; quem NAO tem vai para a
**AREA DE ESPERA**, ao lado do mapa, cada peca com uma etiqueta de texto em
cima. Contrato em `data/pecas-avulsas.json`.

**Por que nao veio de biblioteca:** os dois silos gratuitos do free3d sao
"Licenca de Uso Pessoal" e isto e entrega de cliente; o TurboSquid exige conta
ate no gratuito; o Poly Haven nao tem silo nem tenda de evento. Os dois caminhos
estao fechados por LICENCA e por CADASTRO, nao por dificuldade -- e silo, tenda
e porteira sao geometria de revolucao e caixa, que sai mais rapido feita do que
negociada, na escala certa e ja com os materiais MEDIDOS da cena.
"""

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

import terreno

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO = RAIZ / "data" / "pecas-avulsas.json"


def _obj(nome, bm, mats, col):
    malha = bpy.data.meshes.new(nome)
    bm.to_mesh(malha)
    bm.free()
    for m in mats:
        malha.materials.append(m)
    o = bpy.data.objects.new(nome, malha)
    col.objects.link(o)
    return o


def _cil(bm, r, h, z, seg=24, mat=0, cap=True):
    ini = len(bm.faces)
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=seg,
                          radius1=r, radius2=r, depth=h,
                          matrix=Matrix.Translation(Vector((0, 0, z + h / 2))))
    bm.faces.ensure_lookup_table()
    for f in bm.faces[ini:]:
        f.material_index = mat
    return bm


def _caixa(bm, sx, sy, sz, loc, mat=0, giro=0.0):
    ini = len(bm.faces)
    m = (Matrix.Translation(Vector(loc)) @ Matrix.Rotation(giro, 4, "Z")
         @ Matrix.Diagonal(Vector((sx, sy, sz, 1.0))))
    bmesh.ops.create_cube(bm, size=1.0, matrix=m)
    bm.faces.ensure_lookup_table()
    for f in bm.faces[ini:]:
        f.material_index = mat
    return bm


# --------------------------------------------------------------------------
# As pecas

def silo(med, mats, col, nome="Silo"):
    """Fuste cilindrico + cone de teto + escada + aneis de chapa corrugada."""
    d, hc, hcone = med["diametro"], med["altura_cilindro"], med["altura_cone"]
    r = d / 2.0
    bm = bmesh.new()
    _cil(bm, r, hc, 0.0, seg=32, mat=0, cap=False)
    # cone do teto
    ini = len(bm.faces)
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=32,
                          radius1=r * 1.03, radius2=r * 0.10, depth=hcone,
                          matrix=Matrix.Translation(Vector((0, 0, hc + hcone / 2))))
    bm.faces.ensure_lookup_table()
    for f in bm.faces[ini:]:
        f.material_index = 0
    # aneis da chapa: e o que faz o silo LER como silo de longe, porque cada
    # anel pega uma faixa de sol rasante diferente
    for k in range(1, int(hc // 2.4)):
        _cil(bm, r * 1.012, 0.10, k * 2.4, seg=32, mat=0)
    # escada lateral, no lado +x
    for k in range(int(hc // 0.45)):
        _caixa(bm, 0.60, 0.05, 0.05, (r + 0.35, 0, 0.5 + k * 0.45), mat=1)
    for lado in (-0.28, 0.28):
        _caixa(bm, 0.06, 0.06, hc, (r + 0.35, lado, hc / 2), mat=1)
    return _obj(nome, bm, mats, col)


def silo_conjunto(med, mats, col):
    n, esp = int(med["unidades"]), med["espacamento"]
    base = {"diametro": 9.0, "altura_cilindro": 16.0, "altura_cone": 3.2}
    pai = bpy.data.objects.new("ConjuntoDeSilos", None)   # vazio, para arrastar junto
    col.objects.link(pai)
    for i in range(n):
        o = silo(base, mats, col, nome=f"Silo_conjunto_{i+1}")
        o.location = ((i - (n - 1) / 2.0) * esp, 0, 0)
        o.parent = pai
    return pai


def tenda_piramidal(med, mats, col):
    """Tenda 10x10 de feira: quatro pes, lona em piramide."""
    lado, pe, alt = med["lado"], med["pe_direito"], med["altura_total"]
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
    # lona: piramide de quatro aguas com beiral
    ini = len(bm.faces)
    v = [bm.verts.new((sx * h * 1.06, sy * h * 1.06, pe))
         for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    topo = bm.verts.new((0, 0, alt))
    for i in range(4):
        bm.faces.new((v[i], v[(i + 1) % 4], topo))
    bm.faces.ensure_lookup_table()
    for f in bm.faces[ini:]:
        f.material_index = 0
    return _obj("TendaPiramidal", bm, mats, col)


def tenda_galpao(med, mats, col):
    """Tenda de duas aguas: a que cobre praca de alimentacao e leilao."""
    larg, comp = med["largura"], med["comprimento"]
    pe, alt = med["pe_direito"], med["altura_total"]
    bm = bmesh.new()
    n_pares = max(2, int(comp // 5.0) + 1)
    for i in range(n_pares):
        y = -comp / 2 + i * (comp / (n_pares - 1))
        for sx in (-1, 1):
            ini = len(bm.faces)
            bmesh.ops.create_cone(
                bm, cap_ends=True, cap_tris=False, segments=6,
                radius1=0.07, radius2=0.07, depth=pe,
                matrix=Matrix.Translation(Vector((sx * larg / 2, y, pe / 2))))
            bm.faces.ensure_lookup_table()
            for f in bm.faces[ini:]:
                f.material_index = 1
    ini = len(bm.faces)
    e = [bm.verts.new((-larg / 2 * 1.05, -comp / 2, pe)),
         bm.verts.new((-larg / 2 * 1.05, comp / 2, pe)),
         bm.verts.new((larg / 2 * 1.05, comp / 2, pe)),
         bm.verts.new((larg / 2 * 1.05, -comp / 2, pe))]
    c = [bm.verts.new((0, -comp / 2, alt)), bm.verts.new((0, comp / 2, alt))]
    bm.faces.new((e[0], e[1], c[1], c[0]))
    bm.faces.new((e[3], c[0], c[1], e[2]))
    bm.faces.ensure_lookup_table()
    for f in bm.faces[ini:]:
        f.material_index = 0
    return _obj("TendaGalpao", bm, mats, col)


def porteira(med, mats, col):
    """Porteira de entrada da Fazendinha -- pedido literal em [03:18]."""
    vao, hm, ht = med["vao"], med["altura_moirao"], med["altura_travessa"]
    bm = bmesh.new()
    for sx in (-1, 1):
        _caixa(bm, 0.34, 0.34, hm, (sx * vao / 2, 0, hm / 2), mat=1)
    _caixa(bm, vao + 0.9, 0.28, 0.34, (0, 0, ht), mat=1)
    _caixa(bm, vao + 0.5, 0.20, 0.22, (0, 0, ht - 0.75), mat=1)
    # folha da porteira, entreaberta
    for sx in (-1, 1):
        for k in range(4):
            _caixa(bm, vao / 2 - 0.2, 0.10, 0.16,
                   (sx * (vao / 4 + 0.1), sx * 0.35, 0.55 + k * 0.55),
                   mat=1, giro=sx * 0.22)
    return _obj("PorteiraFazendinha", bm, mats, col)


def guiche(med, mats, col):
    """Quiosque de balcao com toldo -- 'os guichezinhos' [01:04]."""
    l, p, h = med["largura"], med["profundidade"], med["altura"]
    bm = bmesh.new()
    _caixa(bm, l, p, h * 0.78, (0, 0, h * 0.39), mat=2)
    _caixa(bm, l * 1.05, 0.30, 0.12, (0, -p / 2 - 0.1, h * 0.42), mat=1)
    _caixa(bm, l * 1.25, p * 0.8, 0.10, (0, -p * 0.25, h), mat=0)
    return _obj("Guiche", bm, mats, col)


def curral(med, mats, col):
    """Curral de manejo em baias -- o que as MANGUEIRAS deveriam ser."""
    larg, comp, h = med["largura"], med["comprimento"], med["altura"]
    baias = int(med["baias"])
    bm = bmesh.new()
    for i in range(baias + 1):
        y = -comp / 2 + i * (comp / baias)
        for k in range(3):
            _caixa(bm, larg, 0.07, 0.10, (0, y, 0.45 + k * 0.55), mat=1)
        for sx in (-1, 1):
            _caixa(bm, 0.12, 0.12, h, (sx * larg / 2, y, h / 2), mat=1)
    for sx in (-1, 1):
        for k in range(3):
            _caixa(bm, 0.07, comp, 0.10, (sx * larg / 2, 0, 0.45 + k * 0.55), mat=1)
    return _obj("CurralDeManejo", bm, mats, col)


def torre_luz(med, mats, col):
    h, b = med["altura"], med["base"]
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            ini = len(bm.faces)
            bmesh.ops.create_cone(
                bm, cap_ends=True, cap_tris=False, segments=5,
                radius1=0.06, radius2=0.04, depth=h,
                matrix=Matrix.Translation(Vector((sx * b / 2, sy * b / 2, h / 2))))
            bm.faces.ensure_lookup_table()
            for f in bm.faces[ini:]:
                f.material_index = 1
    for k in range(1, int(h // 1.5)):
        _caixa(bm, b, 0.06, 0.06, (0, -b / 2, k * 1.5), mat=1)
        _caixa(bm, b, 0.06, 0.06, (0, b / 2, k * 1.5), mat=1)
    for i in range(4):
        _caixa(bm, 0.55, 0.30, 0.40, (-0.8 + i * 0.55, 0, h + 0.3), mat=1)
    return _obj("TorreDeIluminacao", bm, mats, col)


def inflavel(med, mats, col):
    l, p, h = med["largura"], med["profundidade"], med["altura"]
    bm = bmesh.new()
    _caixa(bm, l, p, h * 0.55, (0, 0, h * 0.28), mat=0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            ini = len(bm.faces)
            bmesh.ops.create_cone(
                bm, cap_ends=True, cap_tris=False, segments=8,
                radius1=0.9, radius2=0.35, depth=h * 0.55,
                matrix=Matrix.Translation(Vector((sx * l / 2 * 0.82,
                                                  sy * p / 2 * 0.82,
                                                  h * 0.55 + h * 0.27))))
            bm.faces.ensure_lookup_table()
            for f in bm.faces[ini:]:
                f.material_index = 0
    return _obj("BrinquedoInflavel", bm, mats, col)


def trator(med, mats, col):
    """PROXY GROSSEIRO, e esta dito no contrato: e a pendencia 14d."""
    c, l, h = med["comprimento"], med["largura"], med["altura"]
    bm = bmesh.new()
    _caixa(bm, c * 0.55, l * 0.75, h * 0.34, (c * 0.05, 0, h * 0.45), mat=2)
    _caixa(bm, c * 0.34, l * 0.72, h * 0.40, (-c * 0.24, 0, h * 0.75), mat=1)
    for sx, r in ((-0.30, 0.78), (0.32, 0.45)):
        for sy in (-1, 1):
            ini = len(bm.faces)
            bmesh.ops.create_cone(
                bm, cap_ends=True, cap_tris=False, segments=14,
                radius1=r, radius2=r, depth=l * 0.24,
                matrix=Matrix.Translation(Vector((sx * c, sy * l * 0.40, r)))
                @ Matrix.Rotation(math.radians(90), 4, "X"))
            bm.faces.ensure_lookup_table()
            for f in bm.faces[ini:]:
                f.material_index = 3
    return _obj("Trator_PROXY", bm, mats, col)


CONSTRUTORES = {
    "silo": silo, "silo_conjunto": silo_conjunto,
    "tenda_piramidal": tenda_piramidal, "tenda_galpao": tenda_galpao,
    "porteira": porteira, "guiche": guiche, "curral": curral,
    "torre_luz": torre_luz, "inflavel": inflavel, "trator": trator,
}


def construir(dados, col_pai, centro_arena, fonte=None):
    if not CONTRATO.exists():
        return 0

    cont = json.loads(CONTRATO.read_text(encoding="utf-8"))
    esp = cont["area_de_espera"]

    mats_cena = {m.name: m for m in bpy.data.materials}
    # ordem dos slots: 0 lona, 1 metal/madeira, 2 pavilhao, 3 preto
    mats = [mats_cena.get(n) for n in
            ("MAT_LONA", "MAT_TRELICA", "MAT_PAVILHAO", "MAT_PRETO")]
    mats = [m for m in mats if m is not None]

    col = bpy.data.collections.new("AREA_DE_ESPERA")
    col_pai.children.link(col)

    x0, y0 = esp["canto_m"]
    passo, cols = esp["passo_m"], int(esp["colunas"])

    # A area de espera e, por definicao, "peca cujo lugar eu nao sei". Assim que
    # o lugar aparece, a peca sai daqui -- senao o Blender abre com uma copia
    # sobrando ao lado do mapa e ninguem sabe qual das duas vale. Foi o que
    # aconteceu com as tres tendas em 15/08: elas passaram a ser instanciadas
    # nas 134 posicoes medidas (scripts/tendas.py) e continuavam paradas aqui.
    na_espera = [p for p in cont["pecas"] if p.get("posicao", "espera") == "espera"]
    saidas = [p["nome"] for p in cont["pecas"] if p not in na_espera]

    postos = 0
    for i, peca in enumerate(na_espera):
        f = CONSTRUTORES.get(peca["tipo"])
        if f is None:
            continue
        o = f(peca["medidas_m"], mats, col)
        lin, colu = divmod(i, cols)
        x = x0 + colu * passo
        y = y0 + lin * passo
        z = terreno.elevacao(x, y, centro_arena)
        o.location = (o.location.x + x, o.location.y + y, z)
        o["na_espera"] = True
        o["nome_da_peca"] = peca["nome"]
        o["fundamento"] = peca.get("fundamento", "")
        if peca.get("audio_ou_prova"):
            o["audio_ou_prova"] = peca["audio_ou_prova"]
        postos += 1

        # etiqueta: sem ela ele teria de clicar objeto por objeto no outliner
        cur = bpy.data.curves.new(f"Etq_{peca['nome']}", type="FONT")
        cur.body = peca["nome"]
        cur.align_x = "CENTER"
        cur.size = 2.2
        if fonte:
            cur.font = fonte
        etq = bpy.data.objects.new(f"Etiqueta_{peca['nome']}", cur)
        col.objects.link(etq)
        etq.location = (x, y - passo * 0.42, z + 1.0)
        etq.rotation_euler = (math.radians(90), 0, 0)
        if mats:
            etq.data.materials.append(mats[0])

    print(f"  area de espera ..... {postos} pecas ao lado do mapa, em "
          f"({x0:.0f}, {y0:.0f}), etiquetadas -- ele reposiciona no Blender")
    if saidas:
        print(f"  sairam da espera ... {len(saidas)} ja posicionadas: "
              f"{', '.join(saidas)}")
    return postos
