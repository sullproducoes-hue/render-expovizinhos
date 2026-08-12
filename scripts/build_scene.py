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
ALTURA_CAMERA = 12.0     # m -- altura de voo do percurso
LARGURA_RENDER = 2760    # 2:1, 2x o nativo do painel P2,9 (1379x690)
ALTURA_RENDER = 1380

# Percurso ditado pelo cliente, em rotulos da planta. A ordem e a do audio.
# Cada entrada: (nome do ponto, rotulo procurado, ocorrencia desejada)
PERCURSO = [
    ("00 Estacionamento",      "ESTACIONAMENTO",        5),
    ("01 Portal de Entrada",   "Portal de Entrada",     0),
    ("02 Pavilhao 1",          "PAVILHÃO 1",            0),
    ("03 Alimentacao Coberta", "Coberta",               0),
    ("04 Pavilhao 2",          "PAVILHÃO 2",            0),
    ("05 Pavilhao 3",          "PAVILHÃO 3",            0),
    ("06 Mercado do Produtor", "Mercado do Produtor",   0),
    ("07 Cafe Colonial",       "Café Colonial",         0),
    ("08 Bosque",              "Bosque",                2),
    ("09 Alimentacao Aberta",  "Aberta",                0),
    ("10 Recinto de Leiloes",  "RECINTO DE LEILÕES",    0),
    ("11 Pavilhoes de Animais", "PAVILHÃO - GADO LEITE", 0),
    ("12 Pista de Julgamentos", "PISTA DE JULGAMENTOS",  0),
    ("13 Arena de Rodeio",     "ARENA DE RODEIO",       0),
    ("14 Palco",               "PALCO",                 0),
    ("15 Saida pelo Portal",   "Portal de Entrada",     0),
]

COLECOES = ["BASE", "EVENTO", "CAMERA", "LUZ"]


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
# Construcao

def construir_terreno(dados, col, relevo=None):
    """Plano do terreno cobrindo a prancha inteira, com folga de 20%.

    Com --relevo aponta para um heightmap em escala de cinza, aplicado por
    deslocamento. Sem ele, o terreno sai plano e o relevo entra depois.
    """
    larg = dados["prancha"]["largura_pt"] * ESCALA * 1.2
    prof = dados["prancha"]["altura_pt"] * ESCALA * 1.2

    bpy.ops.mesh.primitive_grid_add(x_subdivisions=256, y_subdivisions=256,
                                    size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Terreno"
    obj.scale = (larg, prof, 1.0)
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)

    if relevo and Path(relevo).exists():
        img = bpy.data.images.load(str(relevo))
        tex = bpy.data.textures.new("RelevoTex", type="IMAGE")
        tex.image = img
        mod = obj.modifiers.new("Relevo", type="DISPLACE")
        mod.texture = tex
        mod.texture_coords = "UV"
        # Amplitude conservadora: o DEM de 30 m so descreve a forma macro.
        mod.strength = 20.0
        mod.mid_level = 0.5
        print(f"  relevo aplicado: {relevo}")
    else:
        print("  terreno plano (sem heightmap)")
    return obj


def construir_estandes(dados, col):
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

        obj.location = (x, y, 0.0)
        obj["area_m2"] = area
        obj["serie"] = st["serie"]

    return contagem


def construir_pavilhoes(dados, col):
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
        obj.location = (x, y, 0.0)
        obj["area_m2"] = area
        feitos += 1
    return feitos


def achar_zona(dados, rotulo, ocorrencia=0):
    achados = [z for z in dados["zonas"] if z["rotulo"] == rotulo]
    if not achados:
        return None
    achados.sort(key=lambda z: (z["y"], z["x"]))
    return achados[min(ocorrencia, len(achados) - 1)]


def construir_percurso(dados, col):
    """Curva bezier passando pelos pontos do roteiro, com camera acoplada."""
    origem = dados["_origem"]
    pontos, ausentes = [], []

    for nome, rotulo, ocorrencia in PERCURSO:
        z = achar_zona(dados, rotulo, ocorrencia)
        if z is None:
            ausentes.append((nome, rotulo))
            continue
        x, y = para_mundo(z["x"], z["y"], origem)
        pontos.append((nome, x, y))

    curva = bpy.data.curves.new("PercursoCamera", type="CURVE")
    curva.dimensions = "3D"
    spline = curva.splines.new("BEZIER")
    spline.bezier_points.add(len(pontos) - 1)

    for i, (nome, x, y) in enumerate(pontos):
        bp = spline.bezier_points[i]
        bp.co = (x, y, ALTURA_CAMERA)
        bp.handle_left_type = bp.handle_right_type = "AUTO"

    obj_curva = bpy.data.objects.new("PercursoCamera", curva)
    col.objects.link(obj_curva)

    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 28.0
    cam = bpy.data.objects.new("Camera", cam_data)
    col.objects.link(cam)
    cam.rotation_euler = (math.radians(75), 0, 0)

    seguir = cam.constraints.new("FOLLOW_PATH")
    seguir.target = obj_curva
    seguir.use_curve_follow = True

    bpy.context.scene.camera = cam

    # Marcadores nomeados, para localizar cada ponto do roteiro na viewport.
    for nome, x, y in pontos:
        m = bpy.data.objects.new(f"PT_{nome}", None)
        m.empty_display_type = "PLAIN_AXES"
        m.empty_display_size = 8.0
        m.location = (x, y, ALTURA_CAMERA)
        col.objects.link(m)

    return pontos, ausentes


def configurar_render(cena):
    cena.render.resolution_x = LARGURA_RENDER
    cena.render.resolution_y = ALTURA_RENDER
    cena.render.resolution_percentage = 100
    cena.render.fps = 30
    cena.render.image_settings.file_format = "PNG"
    cena.render.film_transparent = False
    try:
        cena.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        cena.render.engine = "CYCLES"


def construir_luz(col):
    """Sol em golden hour, coerente com o LOOK LOCK das imagens de apoio."""
    dados_sol = bpy.data.lights.new("Sol", type="SUN")
    dados_sol.energy = 3.0
    dados_sol.angle = math.radians(0.526)
    sol = bpy.data.objects.new("Sol", dados_sol)
    # Elevacao baixa: sol de fim de tarde, sombras longas.
    sol.rotation_euler = (math.radians(65), 0, math.radians(-135))
    col.objects.link(sol)
    return sol


# --------------------------------------------------------------------------

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dados", default="data/mapa_agroshow26.json")
    ap.add_argument("--relevo", default=None,
                    help="heightmap em escala de cinza para deslocar o terreno")
    ap.add_argument("--out", default=None, help="salva um .blend no caminho")
    args = ap.parse_args(argv)

    dados = json.loads(Path(args.dados).read_text(encoding="utf-8"))
    # Origem no centro da prancha, para a cena nascer centrada no mundo.
    dados["_origem"] = (dados["prancha"]["largura_pt"] / 2,
                        dados["prancha"]["altura_pt"] / 2)

    limpar_cena()
    cols = criar_colecoes()

    print("construindo terreno...")
    construir_terreno(dados, cols["BASE"], args.relevo)

    print("construindo pavilhoes...")
    n_pav = construir_pavilhoes(dados, cols["BASE"])

    print("construindo estandes...")
    cont = construir_estandes(dados, cols["EVENTO"])

    print("construindo percurso...")
    pontos, ausentes = construir_percurso(dados, cols["CAMERA"])

    construir_luz(cols["LUZ"])
    configurar_render(bpy.context.scene)

    larg_m = dados["prancha"]["largura_pt"] * ESCALA
    prof_m = dados["prancha"]["altura_pt"] * ESCALA

    print("\n" + "=" * 58)
    print(f"  escala .............. {ESCALA} m/pt")
    print(f"  extensao do terreno . {larg_m:.0f} x {prof_m:.0f} m")
    print(f"  pavilhoes ........... {n_pav}")
    print(f"  estandes ............ {cont['instanciado']} instanciados "
          f"+ {cont['proprio']} proprios")
    print(f"  pontos do percurso .. {len(pontos)} de {len(PERCURSO)}")
    print(f"  render .............. {LARGURA_RENDER}x{ALTURA_RENDER} "
          f"({LARGURA_RENDER/ALTURA_RENDER:.0f}:1)")
    if ausentes:
        print("  AUSENTES no percurso:")
        for nome, rotulo in ausentes:
            print(f"     {nome} -> rotulo {rotulo!r} nao encontrado")
    print("=" * 58)

    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.out).resolve()))
        print(f"\nsalvo: {args.out}")


if __name__ == "__main__":
    main()
