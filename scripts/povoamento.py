#!/usr/bin/env python3
"""Povoa o recinto a partir do censo em data/povoamento.json.

O recinto estava VAZIO, e o audio do cliente descreve gente e bicho em cada
ambiente -- o `ESTADO.md` chama esse audio de "a regua do que vai dentro de cada
ambiente". O censo saiu de la, minuto a minuto.

**Estas figuras sao PROXY, e isso esta escrito em cada objeto.** Nao existe
figura humana nem gado em CC0 que sirva direto: o Poly Haven tem 521 modelos e
nenhum e gente ou animal. Kenney e Quaternius tem, em CC0 de verdade, mas em
estilo de jogo -- num golden hour a 4-15 m de camera, boneco estilizado fica
pior que recinto vazio.

Qual o certo depende do Plano A vs Plano B, que e escolha do Natan (ESTADO.md):
no Plano A os quadros viram entrada de IA geradora e proxy e exatamente o que se
quer -- massa, silhueta, escala e composicao, com a IA pondo a pele. No Plano B
o render local e a entrega e ai gente e gado precisam de modelo e animacao.

Enquanto ele nao decide, o proxy da a densidade e a composicao, fica na colecao
POVOAMENTO (esconde num clique, igual a ESTIMADO) e nao atrapalha nenhum dos
dois caminhos.

Malha COMPARTILHADA por especie: 1.600 figuras sao 1.600 matrizes e 5 malhas.
"""

import json
import math
import random
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

import terreno

RAIZ = Path(__file__).resolve().parent.parent
CONTRATO = RAIZ / "data" / "povoamento.json"

# Cor de cada especie. As dos bovinos NAO sao invencao: sao a palavra do
# cliente no audio -- "corpo do animal vermelho e a cabeca e cara branca",
# "gado nelore, que e o gado branco". As outras sao faixa comum da especie e
# estao declaradas como tal no contrato.
CORES = {
    "pessoa":             ((0.16, 0.17, 0.21), (0.42, 0.30, 0.24)),
    "touro":              ((0.05, 0.04, 0.04), (0.05, 0.04, 0.04)),
    "bovino_leite":       ((0.62, 0.60, 0.58), (0.09, 0.08, 0.08)),
    "bovino_cara_branca": ((0.28, 0.09, 0.05), (0.78, 0.76, 0.72)),
    "bovino_nelore":      ((0.72, 0.70, 0.66), (0.72, 0.70, 0.66)),
    "equino":             ((0.19, 0.11, 0.07), (0.19, 0.11, 0.07)),
    "ovino":              ((0.70, 0.68, 0.63), (0.14, 0.12, 0.11)),
    "cao":                ((0.09, 0.08, 0.08), (0.80, 0.79, 0.76)),
}


def _material(nome, cor):
    m = bpy.data.materials.get(nome)
    if m:
        return m
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (*cor, 1.0)
        b.inputs["Roughness"].default_value = 0.85
    m.diffuse_color = (*cor, 1.0)     # viewport solido: senao abre tudo cinza
    m.roughness = 0.85
    return m


def _malha_pessoa(esc):
    """Figura em pe, de poucos poligonos, na altura MEDIDA de 1,70 m.

    Nao tenta ser bonita: tenta ter a silhueta certa. O que le como pessoa a
    10 m e a proporcao cabeca-tronco-perna e o fato de estar em pe -- nao o
    detalhe do rosto, que nesta distancia tem meio pixel.
    """
    h = esc["pessoa_m"]
    malha = bpy.data.meshes.new("ProxyPessoa")
    bm = bmesh.new()
    # slot 0 = roupa/corpo, slot 1 = cabeca/pele
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8,
                          radius1=h * 0.105, radius2=h * 0.075,
                          depth=h * 0.46,
                          matrix=Matrix.Translation(Vector((0, 0, h * 0.71))))
    for lado in (-1, 1):
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=6,
                              radius1=h * 0.045, radius2=h * 0.035,
                              depth=h * 0.48,
                              matrix=Matrix.Translation(
                                  Vector((lado * h * 0.05, 0, h * 0.24))))
    bm.faces.ensure_lookup_table()
    n_corpo = len(bm.faces)
    bmesh.ops.create_icosphere(
        bm, subdivisions=1, radius=h * 0.072,
        matrix=Matrix.Translation(Vector((0, 0, h * 0.94))))
    for f in bm.faces[n_corpo:]:
        f.material_index = 1
    bm.to_mesh(malha)
    bm.free()
    for p in malha.polygons:
        p.use_smooth = True
    return malha


def _malha_quadrupede(alt, comp, cabeca_propria):
    """Corpo, pescoco, cabeca e quatro pernas. Slot 1 = cabeca.

    O slot separado existe por um motivo do cliente: o gado do pavilhao 2 e
    Hereford/Braford, e a palavra dele foi "o corpo do animal vermelho e a
    cabeca e cara branca". Sem dois slots isso nao se representa.
    """
    malha = bpy.data.meshes.new("ProxyQuadrupede")
    bm = bmesh.new()
    corpo = Matrix.Translation(Vector((0, 0, alt * 0.72))) @ Matrix.Diagonal(
        Vector((comp * 0.5, alt * 0.30, alt * 0.30, 1.0)))
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0, matrix=corpo)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bmesh.ops.create_cone(
                bm, cap_ends=True, cap_tris=False, segments=5,
                radius1=alt * 0.055, radius2=alt * 0.042, depth=alt * 0.55,
                matrix=Matrix.Translation(Vector((sx * comp * 0.33,
                                                  sy * alt * 0.20,
                                                  alt * 0.27))))
    bm.faces.ensure_lookup_table()
    n_corpo = len(bm.faces)
    # pescoco + cabeca, na frente (+x)
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=6,
        radius1=alt * 0.13, radius2=alt * 0.09, depth=comp * 0.26,
        matrix=Matrix.Translation(Vector((comp * 0.53, 0, alt * 0.86)))
        @ Matrix.Rotation(math.radians(62), 4, "Y"))
    bmesh.ops.create_icosphere(
        bm, subdivisions=1, radius=alt * 0.115,
        matrix=Matrix.Translation(Vector((comp * 0.62, 0, alt * 0.78))))
    if cabeca_propria:
        for f in bm.faces[n_corpo:]:
            f.material_index = 1
    bm.to_mesh(malha)
    bm.free()
    for p in malha.polygons:
        p.use_smooth = True
    return malha


def construir(dados, col_pai, centro_arena, solidos=None, bbox=None):
    if not CONTRATO.exists():
        print("  sem data/povoamento.json -- recinto segue vazio")
        return 0, 0

    cen = json.loads(CONTRATO.read_text(encoding="utf-8"))
    esc = cen["escala"]
    rnd = random.Random(cen["semente"])

    col = bpy.data.collections.new("POVOAMENTO")
    col_pai.children.link(col)

    malhas = {}

    def malha_de(tipo):
        if tipo in malhas:
            return malhas[tipo]
        c1, c2 = CORES[tipo]
        if tipo == "pessoa":
            m = _malha_pessoa(esc)
        else:
            chave = {"touro": "bovino", "bovino_leite": "bovino",
                     "bovino_cara_branca": "bovino", "bovino_nelore": "bovino",
                     "equino": "equino", "ovino": "ovino", "cao": "cao"}[tipo]
            m = _malha_quadrupede(esc[f"{chave}_altura_m"],
                                  esc[f"{chave}_comprimento_m"],
                                  cabeca_propria=(c1 != c2))
        m.materials.append(_material(f"MAT_PROXY_{tipo.upper()}_A", c1))
        m.materials.append(_material(f"MAT_PROXY_{tipo.upper()}_B", c2))
        malhas[tipo] = m
        return m

    postos, recusados = 0, 0
    for amb in cen["ambientes"]:
        p = terreno.ponto_da_zona(dados, amb["zona"])
        if p is None:
            print(f"  aviso: zona '{amb['zona']}' nao existe na planta -- "
                  f"{amb['quantos']} {amb['tipo']} nao foram postos")
            recusados += amb["quantos"]
            continue
        malha = malha_de(amb["tipo"])
        r_max = amb["raio_m"]
        r_min = amb.get("raio_minimo_m", 0.0)
        for _ in range(amb["quantos"]):
            a = rnd.uniform(0, 2 * math.pi)
            u = rnd.random()
            r = math.sqrt(r_min ** 2 + u * (r_max ** 2 - r_min ** 2))
            x, y = p[0] + r * math.cos(a), p[1] + r * math.sin(a)
            if bbox and not (bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]):
                recusados += 1
                continue
            o = bpy.data.objects.new(f"Proxy_{amb['tipo']}", malha)
            col.objects.link(o)
            o.location = (x, y, terreno.elevacao(x, y, centro_arena))
            k = 1.0 + rnd.uniform(-1, 1) * 0.07     # gente e bicho nao sao clones
            o.scale = (k, k, k * rnd.uniform(0.96, 1.05))
            o.rotation_euler = (0.0, 0.0, rnd.uniform(0, 2 * math.pi))
            o["proxy"] = True
            o["povoamento_tipo"] = amb["tipo"]
            o["audio_do_cliente"] = amb["audio"]
            o["fundamento_da_quantidade"] = amb["fundamento"]
            postos += 1

    print(f"  povoamento ......... {postos} figuras PROXY em {len(malhas)} malhas "
          f"({recusados} nao postas)")
    print(f"                       colecao POVOAMENTO -- esconde num clique. "
          f"NAO sao os personagens finais, ver data/povoamento.json")
    return postos, recusados
